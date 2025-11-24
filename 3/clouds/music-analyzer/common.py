import datetime
from email.utils import parsedate_to_datetime

from pydantic import BaseModel, Field, AliasChoices, field_validator
from bson import ObjectId

class ObjectIdStr:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        elif isinstance(v, str):
            return v
        else:
            raise TypeError(f"Invalid type for ObjectIdStr: {type(v)}")

class Analyze(BaseModel):
    id: ObjectIdStr = Field(validation_alias=AliasChoices('id', '_id'))
    title: str
    file_id: ObjectIdStr
    status: str
    created_at: datetime.datetime
    result_id: ObjectIdStr | None

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, v: str):
        if isinstance(v, str):
            return parsedate_to_datetime(v)
        return v

class Result(BaseModel):
    id: ObjectIdStr = Field(validation_alias=AliasChoices('id', '_id'))
    bpm: float
    sample_rate: int
    duration: float
    spectrogram_id: ObjectIdStr
