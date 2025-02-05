# routes.py
from flask import Blueprint, request, jsonify
from .models import Record

api_blueprint = Blueprint('api', __name__)

# Create Record
@api_blueprint.route('/records', methods=['POST'])
def create_record():
    data = request.json
    if not data.get('name') or not data.get('email'):
        return jsonify({"error": "Missing 'name' or 'email' field"}), 400
    
    try:
        # Create a new record using the DTO for validation
        Record.create(data)
        return jsonify({"message": "Record added successfully"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# Get All Records
@api_blueprint.route('/records', methods=['GET'])
def get_records():
    records = Record.get_all()
    return jsonify(records), 200

# Get Single Record
@api_blueprint.route('/records/<email>', methods=['GET'])
def get_record(email):
    record = Record.get_one(email)
    if not record:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(record), 200

# Update Record
@api_blueprint.route('/records/<email>', methods=['PUT'])
def update_record(email):
    data = request.json
    result = Record.update(email, data)
    if result.modified_count == 0:
        return jsonify({"error": "No record updated"}), 400
    return jsonify({"message": "Record updated successfully"}), 200

# Delete Record
@api_blueprint.route('/records/<email>', methods=['DELETE'])
def delete_record(email):
    result = Record.delete(email)
    if result.deleted_count == 0:
        return jsonify({"error": "No record deleted"}), 400
    return jsonify({"message": "Record deleted successfully"}), 200
