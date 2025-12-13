import datetime
from typing import Tuple
from .models import EventInfo, SourceInfo, CarrierInfo, DisasterInfo, DecodedRecord
from . import dictionaries as dicts

ID_TOTAL_LENGTH = 36
EVENT_CODE_LEN = 26
SOURCE_CODE_LEN = 3
CARRIER_CODE_LEN = 1
DISASTER_CODE_LEN = 6


def _format_coord(code: str, length: int, field: str, min_val: int, max_val: int) -> str:
    try:
        int_val = int(code)
    except ValueError as exc:
        raise ValueError(f"{field} must be integer") from exc
    if int_val < min_val or int_val > max_val:
        raise ValueError(f"{field} out of range [{min_val},{max_val}]")
    # 偏移编码，保证纯数字且固定宽度
    offset = 90000 if field == "lat_code" else 180000
    encoded = int_val + offset
    fmt = f"{{:0{length}d}}"
    return fmt.format(encoded)


def _ensure_numeric(s: str, length: int, field: str) -> None:
    if len(s) != length:
        raise ValueError(f"{field} must be {length} digits")
    if not s.isdigit():
        raise ValueError(f"{field} must be numeric")


def _format_time_code(time_str: str) -> str:
    """Accept 14-digit yyyyMMddHHmmss or ISO8601, return 14-digit code."""
    if len(time_str) == 14 and time_str.isdigit():
        # Basic sanity: try parse
        datetime.datetime.strptime(time_str, "%Y%m%d%H%M%S")
        return time_str
    # Try ISO8601 parsing (allow trailing Z)
    normalized = time_str.replace("Z", "+00:00")
    dt = datetime.datetime.fromisoformat(normalized)
    return dt.strftime("%Y%m%d%H%M%S")


def encode_disaster(event: EventInfo, source: SourceInfo, carrier: CarrierInfo, disaster: DisasterInfo) -> str:
    # Validate source via dictionary
    dicts.validate_source(source.code)
    dicts.validate_carrier(carrier.code)
    dicts.validate_disaster(disaster.category, disaster.sub_category, disaster.indicator)

    lat_code_fmt = _format_coord(event.lat_code, 6, "lat_code", -90000, 90000)
    lng_code_fmt = _format_coord(event.lng_code, 6, "lng_code", -180000, 180000)
    _ensure_numeric(source.code, 3, "source.code")
    _ensure_numeric(carrier.code, 1, "carrier.code")
    _ensure_numeric(disaster.category, 1, "disaster.category")
    _ensure_numeric(disaster.sub_category, 2, "disaster.sub_category")
    _ensure_numeric(disaster.indicator, 3, "disaster.indicator")

    event_part = lat_code_fmt + lng_code_fmt + event.time_code
    disaster_part = disaster.category + disaster.sub_category + disaster.indicator
    encoded = event_part + source.code + carrier.code + disaster_part
    if len(encoded) != ID_TOTAL_LENGTH:
        raise ValueError("encoded ID length mismatch")
    return encoded


def decode_disaster(encoded_id: str) -> DecodedRecord:
    if len(encoded_id) != ID_TOTAL_LENGTH:
        raise ValueError("encoded id length must be 36")
    if not encoded_id.isdigit():
        raise ValueError("encoded id must be numeric")

    event_part, source_part, carrier_part, disaster_part = _split_id(encoded_id)

    lat_code_offset, lng_code_offset = event_part[0], event_part[1]
    lat_int = int(lat_code_offset) - 90000
    lng_int = int(lng_code_offset) - 180000
    event = EventInfo(lat_code=str(lat_int), lng_code=str(lng_int), time_code=event_part[2])
    source = SourceInfo(code=source_part)
    carrier = CarrierInfo(code=carrier_part)
    disaster = DisasterInfo(
        category=disaster_part[0],
        sub_category=disaster_part[1],
        indicator=disaster_part[2],
    )

    # Dictionary lookups
    source_name = dicts.get_source_name(source.code)
    carrier_name = dicts.get_carrier_name(carrier.code)
    disaster_names = dicts.get_disaster_names(
        disaster.category, disaster.sub_category, disaster.indicator
    )

    dicts.validate_source(source.code)
    dicts.validate_carrier(carrier.code)
    dicts.validate_disaster(disaster.category, disaster.sub_category, disaster.indicator)

    names = {
        "source": source_name,
        "carrier": carrier_name,
        "disaster_category": disaster_names["category"],
        "disaster_sub_category": disaster_names["sub_category"],
        "indicator": disaster_names["indicator"],
    }

    return DecodedRecord(
        id=encoded_id,
        event=event,
        source=source,
        carrier=carrier,
        disaster=disaster,
        names=names,
    )


def _split_id(encoded_id: str) -> Tuple[Tuple[str, str, str], str, str, Tuple[str, str, str]]:
    idx = 0
    event_part = encoded_id[idx : idx + EVENT_CODE_LEN]
    idx += EVENT_CODE_LEN
    source_part = encoded_id[idx : idx + SOURCE_CODE_LEN]
    idx += SOURCE_CODE_LEN
    carrier_part = encoded_id[idx : idx + CARRIER_CODE_LEN]
    idx += CARRIER_CODE_LEN
    disaster_part = encoded_id[idx : idx + DISASTER_CODE_LEN]

    lat_code = event_part[:6]
    lng_code = event_part[6:12]
    time_code = event_part[12:]
    return (lat_code, lng_code, time_code), source_part, carrier_part, (
        disaster_part[0],
        disaster_part[1:3],
        disaster_part[3:6],
    )


def build_event_info(lat_code: str, lng_code: str, time_str: str) -> EventInfo:
    time_code = _format_time_code(time_str)
    return EventInfo(lat_code=lat_code, lng_code=lng_code, time_code=time_code)


def build_source_info(source_code: str) -> SourceInfo:
    return SourceInfo(code=source_code)


def build_carrier_info(carrier_code: str) -> CarrierInfo:
    return CarrierInfo(code=carrier_code)


def build_disaster_info(category: str, sub_category: str, indicator: str) -> DisasterInfo:
    return DisasterInfo(category=category, sub_category=sub_category, indicator=indicator)
