from typing import Optional
from pydantic import BaseModel, Field, validator


class EventInfo(BaseModel):
    lat_code: str = Field(..., min_length=2, max_length=8)
    lng_code: str = Field(..., min_length=2, max_length=8)
    time_code: str = Field(..., min_length=14, max_length=14)

    @validator("lat_code")
    def validate_lat(cls, v: str) -> str:
        int_v = int(v)
        if int_v < -90000 or int_v > 90000:
            raise ValueError("lat_code out of range [-90000,90000]")
        return v

    @validator("lng_code")
    def validate_lng(cls, v: str) -> str:
        int_v = int(v)
        if int_v < -180000 or int_v > 180000:
            raise ValueError("lng_code out of range [-180000,180000]")
        return v

    @validator("time_code")
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
