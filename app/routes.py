from flask import Blueprint, request, jsonify, send_file
from .models import Record
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import os
import uuid
from .deidentification import deidentify_pdf

api_blueprint = Blueprint('api', __name__)

# Temporary storage for uploaded files
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@api_blueprint.route('/upload', methods=['POST'])
def upload_medical_record():
    file = request.files.get('file')  # Get the uploaded file
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        # Generate a unique filename
        file_uuid = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_uuid}{file_extension}")

        # Save the file temporarily
        file.save(file_path)

        return jsonify({"message": "File uploaded successfully", "file_uuid": file_uuid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/deidentify', methods=['POST'])
def start_deidentification():

    data = request.json
    if not data or "file_uuid" not in data:
        return jsonify({"error": "file_uuid is required"}), 400

    file_uuid = data["file_uuid"]
    input_path = os.path.join(UPLOAD_DIR, f"{file_uuid}.pdf")  # Assuming PDF files
    output_path = os.path.join(UPLOAD_DIR, f"{file_uuid}_deidentified.pdf")

    print(f"Input file path: {input_path}")
    print(f"Output file path: {output_path}")

    if not os.path.exists(input_path):
        return jsonify({"error": "File not found"}), 404

    try:
        # Perform de-identification
        deidentify_pdf(input_path, output_path)

        # Verify the output file exists
        if not os.path.exists(output_path):
            return jsonify({"error": "De-identified PDF could not be created"}), 500

        # Delete the original file
        os.remove(input_path)
        print(f"Original file deleted: {input_path}")

        # Return the de-identified PDF file
        return send_file(output_path, as_attachment=True, download_name="deidentified.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/delete_deidentified/<file_uuid>', methods=['DELETE'])
def delete_deidentified_file(file_uuid):
    deidentified_path = os.path.join(UPLOAD_DIR, f"{file_uuid}_deidentified.pdf")

    if not os.path.exists(deidentified_path):
        return jsonify({"error": "De-identified file not found"}), 404

    try:
        # Delete the de-identified file
        os.remove(deidentified_path)
        return jsonify({"message": "De-identified file deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/store', methods=['POST'])
def store_deidentified_file():
    """
    API to store the de-identified file in the database.
    """
    file = request.files.get('file')  # Get the uploaded file
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        record_id = Record.create(file)
        return jsonify({"message": "De-identified file stored successfully", "record_id": str(record_id)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@api_blueprint.route('/records', methods=['GET'])
def get_records():
    """
    API to retrieve all de-identified records.
    """
    try:
        records = Record.get_all()
        return jsonify(records), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/records/<uuid>', methods=['GET'])
def get_record(uuid):
    """
    API to retrieve a single de-identified record by UUID.
    """
    try:
        record = Record.get_one(uuid)
        if record:
            return jsonify(record), 200
        else:
            return jsonify({"error": "Record not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/records/<uuid>', methods=['DELETE'])
def delete_record(uuid):
    """
    API to delete a de-identified record by UUID.
    """
    try:
        deleted_count = Record.delete(uuid)
        return jsonify({"message": "Record deleted successfully", "deleted_count": deleted_count}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400