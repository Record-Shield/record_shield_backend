# models.py
from .database import mongo
from .dto import RecordDTO  # Import the DTO

class Record:
    @staticmethod
    def get_collection():
        return mongo.db.records  # Access collection dynamically

    @staticmethod
    def create(data):
        try:
            # Validate data using the RecordDTO
            record_dto = RecordDTO(**data)
            record_data = {
                "uuid": record_dto.uuid,
                "name": record_dto.name,
                "email": record_dto.email
            }
            return Record.get_collection().insert_one(record_data)
        except Exception as e:
            raise ValueError(f"Validation error: {str(e)}")

    @staticmethod
    def get_all():
        return list(Record.get_collection().find({}, {"_id": 0}))  # Exclude MongoDB _id

    @staticmethod
    def get_one(email):
        return Record.get_collection().find_one({"email": email}, {"_id": 0})

    @staticmethod
    def update(email, data):
        return Record.get_collection().update_one({"email": email}, {"$set": data})

    @staticmethod
    def delete(email):
        return Record.get_collection().delete_one({"email": email})
