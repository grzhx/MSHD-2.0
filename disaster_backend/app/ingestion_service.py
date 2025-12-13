from sqlalchemy.orm import Session
from datetime import datetime
from typing import Tuple
from . import models, schemas
from .codec_client import decode_disaster_id, encode_disaster_id, CodecError


def _upsert_event(
    db: Session,
    event_id: str,
    event_time: datetime,
    lat_code: str,
    lng_code: str,
) -> models.Event:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event is None:
        event = models.Event(
            id=event_id,
            lat_code=lat_code,
            lng_code=lng_code,
            event_time=event_time,
        )
        db.add(event)
    else:
        event.event_time = event_time
        event.lat_code = lat_code
        event.lng_code = lng_code
    return event


def ingest_encoded(db: Session, payload: schemas.IngestEncodedRequest) -> Tuple[str, str]:
    try:
        decoded = decode_disaster_id(payload.id)
    except CodecError as e:
        return "error", str(e)

    event_info = decoded["event"]
    source_info = decoded["source"]
    carrier_info = decoded["carrier"]
    disaster_info = decoded["disaster"]

    event_id = payload.id[:26]
    event_time = event_info["time"]
    lat_code = event_info["latCode"]
    lng_code = event_info["lngCode"]

    event = _upsert_event(db, event_id, event_time, lat_code, lng_code)

    record = models.DisasterRecord(
        id=payload.id,
        event_id=event.id,
        event_time=event_time,
        lat_code=lat_code,
        lng_code=lng_code,
        source_code=source_info["code"],
        source_name=source_info["name"],
        carrier_code=carrier_info["code"],
        carrier_name=carrier_info["name"],
        disaster_category_code=disaster_info["categoryCode"],
        disaster_category_name=disaster_info["categoryName"],
        disaster_sub_category_code=disaster_info["subCategoryCode"],
        disaster_sub_category_name=disaster_info["subCategoryName"],
        indicator_code=disaster_info["indicatorCode"],
        indicator_name=disaster_info["indicatorName"],
        value=payload.value,
        unit=payload.unit,
        media_path=payload.media_path,
        raw_payload=payload.raw_payload,
        created_at=datetime.utcnow(),
        last_accessed_at=datetime.utcnow(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    if payload.media_path:
        media = models.MediaIndex(
            disaster_id=record.id,
            media_type="auto",
            file_path=payload.media_path,
        )
        db.add(media)
        db.commit()

    return "ok", "已成功接入（已编码模式）"


def ingest_raw(db: Session, request: schemas.IngestRawRequest) -> Tuple[str, str, str]:
    e = request.event

    info = {
        "lat_code": e.lat_code,
        "lng_code": e.lng_code,
        "event_time": e.event_time,
        "source_code": e.source_code,
        "carrier_code": e.carrier_code,
        "disaster_category_code": e.disaster_category_code,
        "disaster_sub_category_code": e.disaster_sub_category_code,
        "indicator_code": e.indicator_code,
    }

    try:
        new_id = encode_disaster_id(info)
    except CodecError as ex:
        return "error", str(ex), ""

    decoded = decode_disaster_id(new_id)
    event_info = decoded["event"]
    source_info = decoded["source"]
    carrier_info = decoded["carrier"]
    disaster_info = decoded["disaster"]

    event_id = new_id[:26]
    event_time = event_info["time"]
    lat_code = event_info["latCode"]
    lng_code = event_info["lngCode"]

    event = _upsert_event(db, event_id, event_time, lat_code, lng_code)

    record = models.DisasterRecord(
        id=new_id,
        event_id=event.id,
        event_time=event_time,
        lat_code=lat_code,
        lng_code=lng_code,
        source_code=source_info["code"],
        source_name=source_info["name"],
        carrier_code=carrier_info["code"],
        carrier_name=carrier_info["name"],
        disaster_category_code=disaster_info["categoryCode"],
        disaster_category_name=disaster_info["categoryName"],
        disaster_sub_category_code=disaster_info["subCategoryCode"],
        disaster_sub_category_name=disaster_info["subCategoryName"],
        indicator_code=disaster_info["indicatorCode"],
        indicator_name=disaster_info["indicatorName"],
        value=e.value,
        unit=e.unit,
        media_path=e.media_path,
        raw_payload=e.raw_payload,
        created_at=datetime.utcnow(),
        last_accessed_at=datetime.utcnow(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    if e.media_path:
        media = models.MediaIndex(
            disaster_id=record.id,
            media_type="auto",
            file_path=e.media_path,
        )
        db.add(media)
        db.commit()

    return "ok", "已成功接入（原始模式）", new_id
