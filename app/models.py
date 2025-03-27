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

    def create(record_dto):
        """
        Creates a new record in the 'records' collection.
        Accepts a RecordDTO instance and an optional file.
        
        Parameters:
        - record_dto: an instance of RecordDTO with attributes recordId, recordName, and userId.
        - file: the file to be uploaded (can be None).
        
        Returns:
        The inserted record's ID.
        
        Raises:
        ValueError: If there is an error during validation or record creation.
        """
        try:
            # Build the record data using values from the passed in record_dto.
            record_data = {
                "recordId": record_dto.recordId,
                "recordName": record_dto.recordName,
                "userId": record_dto.userId
            }

            Record.get_collection().insert_one(record_data)
            return record_dto.recordId
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
    def get_one(recordId):
        """
        Retrieves a single record by recordId.
        Excludes the MongoDB '_id' field from the result.
        """
        try:
            return Record.get_collection().find_one({"recordId": recordId}, {"_id": 0})
        except Exception as e:
            raise ValueError(f"Database error: {str(e)}")

    @staticmethod
    def delete(recordId):
        """
        Deletes a record by recordId.
        """
        try:
            result = Record.get_collection().delete_one({"recordId": recordId})
            if result.deleted_count == 0:
                raise ValueError(f"No record found with recordId: {recordId}")
            return result.deleted_count  
        except Exception as e:
            raise ValueError(f"Database error: {str(e)}")