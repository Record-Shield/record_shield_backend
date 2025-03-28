from flask import Blueprint, request, jsonify, send_file

from app.dto import RecordDTO
from .models import Record
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import os
import uuid
import io
from .deidentification import deidentify_pdf
from datetime import datetime

api_blueprint = Blueprint('api', __name__)

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

DEIDNTIFIED_DIR = "deidentified"
if not os.path.exists(DEIDNTIFIED_DIR):
    os.makedirs(DEIDNTIFIED_DIR)

@api_blueprint.route('/uploadFile', methods=['POST'])
def upload_medical_record():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        recordId = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{recordId}{file_extension}")

        file.save(file_path)

        return jsonify({"message": "File uploaded successfully", "recordId": recordId}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/deidentifyFile', methods=['POST'])
def start_deidentification():
    record_id = request.args.get("recordId")
    if not record_id:
        return jsonify({"error": "recordId is required"}), 400

    input_path = os.path.join(UPLOAD_DIR, f"{record_id}.pdf")
    output_path = os.path.join(DEIDNTIFIED_DIR, f"{record_id}_deidentified.pdf")

    print(f"Input file path: {input_path}")
    print(f"Output file path: {output_path}")

    if not os.path.exists(input_path):
        return jsonify({"error": "File not found"}), 404

    try:
        deidentify_pdf(input_path, output_path)
        if not os.path.exists(output_path):
            return jsonify({"error": "De-identified PDF could not be created"}), 500

        os.remove(input_path)
        print(f"Original file deleted: {input_path}")

        # Read the de-identified file into memory
        with open(output_path, 'rb') as f:
            file_data = io.BytesIO(f.read())
        file_data.seek(0)

        return send_file(file_data,
                         as_attachment=True,
                         download_name="deidentified.pdf",
                         mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/delete/deidentifiedFile', methods=['DELETE'])
def delete_deidentified_file():
    record_id = request.args.get("recordId")
    if not record_id:
        return jsonify({"error": "recordId is required"}), 400

    deidentified_path = os.path.join(DEIDNTIFIED_DIR, f"{record_id}_deidentified.pdf")

    if not os.path.exists(deidentified_path):
        return jsonify({"error": "De-identified file not found"}), 404

    try:
        os.remove(deidentified_path)
        return jsonify({"message": "De-identified file deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/store/deidentifiedFile', methods=['POST'])
def store_deidentified_file():
    data = request.get_json()
    # Validate that all required fields are present in the JSON body
    required_fields = ["recordId", "recordName", "userId"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    record_id = data["recordId"]
    deidentified_path = os.path.join(DEIDNTIFIED_DIR, f"{record_id}_deidentified.pdf")
    if not os.path.exists(deidentified_path):
        return jsonify({"error": "De-identified file not found"}), 404

    try:
        # Create a RecordDTO instance and populate it from the JSON body.
        record_dto = RecordDTO()
        record_dto.recordId = data["recordId"]
        record_dto.recordName = data["recordName"]
        record_dto.userId = data["userId"]
        record_dto.deidentificationDate = datetime.now()


        saved_record_id = Record.create(record_dto)
            
        return jsonify({
            "message": "De-identified file stored successfully",
            "record_id": str(saved_record_id)
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@api_blueprint.route('/findAllRecords', methods=['GET'])
def get_records():
    user_id = request.args.get("userId")
    """
    API to retrieve all de-identified records.
    """
    try:
        records = Record.get_all(user_id)
        return jsonify(records), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/findRecord', methods=['GET'])
def get_record():
    """
    API to retrieve a single de-identified record by recordId using query parameters.
    """
    record_id = request.args.get("recordId")
    if not record_id:
        return jsonify({"error": "recordId is required"}), 400

    try:
        record = Record.get_one(record_id)
        if record:
            return jsonify(record), 200
        else:
            return jsonify({"error": "Record not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/delete/record', methods=['DELETE'])
def delete_record():
    """
    API to delete a de-identified record by UUID using query parameters.
    """
    record_id = request.args.get("recordId")
    if not record_id:
        return jsonify({"error": "recordId is required"}), 400

    deidentified_path = os.path.join(DEIDNTIFIED_DIR, f"{record_id}_deidentified.pdf")

    if not os.path.exists(deidentified_path):
        return jsonify({"error": "De-identified file not found"}), 404
    
    try:
        deleted_count = Record.delete(record_id)
        os.remove(deidentified_path)
        return jsonify({"message": "Record deleted successfully", "deleted_count": deleted_count}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@api_blueprint.route('/download/record', methods=['GET'])
def download_file():
    record_id = request.args.get("recordId")
    if not record_id:
        return jsonify({"error": "recordId is required"}), 400

    file_path = os.path.join(DEIDNTIFIED_DIR, f"{record_id}_deidentified.pdf")
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(file_path, 'rb') as f:
            file_data = io.BytesIO(f.read())
        file_data.seek(0)
        return send_file(file_data,
                    as_attachment=True,
                    download_name="deidentified.pdf",
                    mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@api_blueprint.route('/stats/deidentified', methods=['GET'])
def get_deidentified_stats():
    user_id = request.args.get("userId")
    week = request.args.get("week", "this")
    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    try:
        stats = Record.get_deidentification_counts(user_id, week)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
