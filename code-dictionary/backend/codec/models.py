from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EventInfo(BaseModel):
    location_code: str = Field(..., min_length=12, max_length=12)
    time_code: str = Field(..., min_length=14, max_length=14)

    @field_validator("location_code")
    @classmethod
    def validate_location(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("location_code must be 12 digits")
        return v

    @field_validator("time_code")
    @classmethod
    def validate_time(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("time_code must be 14 digits in yyyyMMddHHmmss format")
        return v


class SourceInfo(BaseModel):
    code: str = Field(..., min_length=3, max_length=3)

    @property
    def category(self) -> str:
        return self.code[0]

    @property
    def sub_category(self) -> str:
        return self.code[1:]


class CarrierInfo(BaseModel):
    code: str = Field(..., min_length=1, max_length=1)


class DisasterInfo(BaseModel):
    category: str = Field(..., min_length=1, max_length=1)
    sub_category: str = Field(..., min_length=2, max_length=2)
    indicator: str = Field(..., min_length=3, max_length=3)


class EncodedId(BaseModel):
    id: str = Field(..., min_length=36, max_length=36)


class DecodedRecord(BaseModel):
    id: str
    event: EventInfo
    source: SourceInfo
    carrier: CarrierInfo
    disaster: DisasterInfo
    names: Optional[dict] = None  # holds human readable names
