import logging
from datetime import datetime
from typing import Tuple

from sqlalchemy.orm import Session

from . import models, schemas
from .codec_client import decode_disaster_id, encode_disaster_id, CodecError

logger = logging.getLogger(__name__)


def _upsert_event(
    db: Session,
    event_id: str,
    event_time: datetime,
    location_code: str,
    location_name: str = "",
) -> models.Event:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event is None:
        event = models.Event(
            id=event_id,
            location_code=location_code,
            location_name=location_name,
            event_time=event_time,
        )
        db.add(event)
    else:
        event.event_time = event_time
        event.location_code = location_code
        if location_name:
            event.location_name = location_name
    return event


def ingest_encoded(db: Session, payload: schemas.IngestEncodedRequest) -> Tuple[str, str]:
    try:
        decoded = decode_disaster_id(payload.id)
    except CodecError as e:
        logger.warning("Decode failed for id=%s error=%s", payload.id, e)
        return "error", str(e)

    event_info = decoded["event"]
    source_info = decoded["source"]
    carrier_info = decoded["carrier"]
    disaster_info = decoded["disaster"]

    event_id = payload.id[:26]
    event_time = event_info["time"]
    location_code = event_info["locationCode"]
    location_name = event_info.get("locationName", "")

    event = _upsert_event(db, event_id, event_time, location_code, location_name)

    record = models.DisasterRecord(
        id=payload.id,
        event_id=event.id,
        event_time=event_time,
        location_code=location_code,
        location_name=location_name,
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

    logger.info("Stored encoded record id=%s source=%s carrier=%s", payload.id, source_info["code"], carrier_info["code"])
    return "ok", "已成功接入（已编码模式）"


def ingest_raw(db: Session, request: schemas.IngestRawRequest) -> Tuple[str, str, str]:
    e = request.event

    info = {
        "location_code": e.location_code,
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
        logger.warning("Encoding failed for payload=%s error=%s", info, ex)
        return "error", str(ex), ""

    decoded = decode_disaster_id(new_id)
    event_info = decoded["event"]
    source_info = decoded["source"]
    carrier_info = decoded["carrier"]
    disaster_info = decoded["disaster"]

    event_id = new_id[:26]
    event_time = event_info["time"]
    location_code = event_info["locationCode"]
    location_name = event_info.get("locationName", "")

    event = _upsert_event(db, event_id, event_time, location_code, location_name)

    record = models.DisasterRecord(
        id=new_id,
        event_id=event.id,
        event_time=event_time,
        location_code=location_code,
        location_name=location_name,
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

    logger.info("Stored raw record id=%s source=%s carrier=%s", new_id, e.source_code, e.carrier_code)
    return "ok", "已成功接入（原始模式）", new_id
