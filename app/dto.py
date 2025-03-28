import uuid
from datetime import datetime
from pydantic import BaseModel, Field, validator

class RecordDTO(BaseModel):
    userId: str = None
    recordId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recordName: str = None 
    deidentificationDate: datetime = None 

    @validator('recordId')
    def file_reference_must_be_valid(cls, v):
        if v and not isinstance(v, str):
            raise ValueError("record Id must be a string")
        return v