from gridfs import GridFS
from werkzeug.utils import secure_filename
import os
from .dto import RecordDTO  # Import the DTO
from .database import mongo  # Import the MongoDB connection

class Record:
    @staticmethod
    def get_collection():
        """
        Returns the 'records' collection from MongoDB.
        Raises an exception if the collection is not accessible.
        """
        if mongo.db is None:
            raise ValueError("MongoDB connection is not established.")
        return mongo.db.records

    @staticmethod
    def get_gridfs():
        """
        Returns a GridFS instance for handling file uploads.
        """
        return GridFS(mongo.db)

    @staticmethod
    def create(file):
        """
        Creates a new record in the 'records' collection.
        Validates the input data using RecordDTO and handles file uploads.
        """
        try:
            # Validate data using the RecordDTO
            record_dto = RecordDTO()
            record_data = {
                "uuid": record_dto.uuid,
                "file_reference": None
            }

            # Handle file upload
            if file:
                fs = Record.get_gridfs()
                filename = secure_filename(file.filename)
                file_id = fs.put(file, filename=filename)
                record_data["file_reference"] = str(file_id)

            # Insert the record into the collection
            result = Record.get_collection().insert_one(record_data)
            return result.inserted_id  # Return the ID of the inserted document
        except Exception as e:
            raise ValueError(f"Validation error: {str(e)}")

    @staticmethod
    def get_all():
        """
        Retrieves all records from the 'records' collection.
        Excludes the MongoDB '_id' field from the results.
        """
        try:
            return list(Record.get_collection().find({}, {"_id": 0}))
        except Exception as e:
            raise ValueError(f"Database error: {str(e)}")

    @staticmethod
    def get_one(uuid):
        """
        Retrieves a single record by uuid.
        Excludes the MongoDB '_id' field from the result.
        """
        try:
            return Record.get_collection().find_one({"uuid": uuid}, {"_id": 0})
        except Exception as e:
            raise ValueError(f"Database error: {str(e)}")

    @staticmethod
    def delete(uuid):
        """
        Deletes a record by uuid.
        """
        try:
            result = Record.get_collection().delete_one({"uuid": uuid})
            if result.deleted_count == 0:
                raise ValueError(f"No record found with uuid: {uuid}")
            return result.deleted_count  # Return the number of documents deleted
        except Exception as e:
            raise ValueError(f"Database error: {str(e)}")