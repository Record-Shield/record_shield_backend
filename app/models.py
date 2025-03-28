from gridfs import GridFS
from werkzeug.utils import secure_filename
import os
from .dto import RecordDTO
from .database import mongo  
from datetime import datetime, timedelta

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
                "userId": record_dto.userId,
                "deidentificationDate": record_dto.deidentificationDate
            }

            Record.get_collection().insert_one(record_data)
            return record_dto.recordId
        except Exception as e:
            raise ValueError(f"Validation error: {str(e)}")



    @staticmethod
    def get_all(userId):
        """
        Retrieves all records from the 'records' collection.
        Excludes the MongoDB '_id' field from the results.
        """
        try:
            return list(Record.get_collection().find({"userId": userId}, {"_id": 0}))
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
        
    @staticmethod
    def update_deidentification_date(record_id, deid_date):
        """
        Updates the record identified by record_id with the provided deidentification date.
        """
        try:
            Record.get_collection().update_one(
                {"recordId": record_id},
                {"$set": {"deidentificationDate": deid_date}}
            )
        except Exception as e:
            raise ValueError(f"Database error: {str(e)}")

    @staticmethod
    def get_deidentification_counts(user_id, week):
        """
        Aggregates and returns the count of de-identified files per day for the given user and week.
        The aggregation groups by the day of the week (MON-SUN) based on the deidentificationDate.
        """
        collection = Record.get_collection()
        now = datetime.utcnow()
        # Calculate current week's Monday and Sunday
        monday = now - timedelta(days=now.weekday())
        sunday = monday + timedelta(days=6)
        if week == "last":
            monday = monday - timedelta(days=7)
            sunday = sunday - timedelta(days=7)
        pipeline = [
            {
                "$match": {
                    "userId": user_id,
                    "deidentificationDate": {"$gte": monday, "$lte": sunday}
                }
            },
            {
                "$group": {
                    "_id": {"$dayOfWeek": "$deidentificationDate"},
                    "count": {"$sum": 1}
                }
            }
        ]
        results = list(collection.aggregate(pipeline))
        # MongoDB: Sunday=1, Monday=2, … Saturday=7. Map them to labels.
        mapping = {2: "MON", 3: "TUE", 4: "WED", 5: "THU", 6: "FRI", 7: "SAT", 1: "SUN"}
        counts = {"MON": 0, "TUE": 0, "WED": 0, "THU": 0, "FRI": 0, "SAT": 0, "SUN": 0}
        for doc in results:
            day_number = doc["_id"]
            day_label = mapping.get(day_number)
            if day_label:
                counts[day_label] = doc["count"]
        return counts

        