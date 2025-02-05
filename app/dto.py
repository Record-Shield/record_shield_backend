import uuid
from pydantic import BaseModel, Field, validator

class RecordDTO(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str

    @validator('name')
    def name_must_be_non_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v
