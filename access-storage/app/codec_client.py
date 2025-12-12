# app/codec_client.py
"""
与“编码/解码模块（模块 1/2）”对接的客户端封装。

此前这里是一个临时 stub，如今直接复用字典/编码模块的正式实现，
保证接入和存储模块共享同一套规则。
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .codec import codec as codec_core

logger = logging.getLogger(__name__)


class CodecError(Exception):
    """统一的编码/解码异常类型，供上层捕获并转换为 HTTP 400。"""


def _to_time_str(dt: datetime) -> str:
    # codec_core 支持 ISO8601 或 14 位时间串，这里统一输出不带微秒的 ISO8601
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def decode_disaster_id(disaster_id: str) -> Dict[str, Any]:
    """
    调用编码模块解码 ID，并转换为 ingestion_service 期望的 dict 结构。
    """
    try:
        decoded = codec_core.decode_disaster(disaster_id)
    except Exception as exc:  # codec 模块使用 ValueError 抛错
        logger.exception("Decode failed for id=%s", disaster_id)
        raise CodecError(str(exc)) from exc

    event_time = datetime.strptime(decoded.event.time_code, "%Y%m%d%H%M%S")
    names = decoded.names or {}

    return {
        "event": {
            "locationCode": decoded.event.location_code,
            "locationName": names.get("location") or "",
            "time": event_time,
        },
        "source": {
            "code": decoded.source.code,
            "name": names.get("source") or "",
        },
        "carrier": {
            "code": decoded.carrier.code,
            "name": names.get("carrier") or "",
        },
        "disaster": {
            "categoryCode": decoded.disaster.category,
            "categoryName": names.get("disaster_category") or "",
            "subCategoryCode": decoded.disaster.sub_category,
            "subCategoryName": names.get("disaster_sub_category") or "",
            "indicatorCode": decoded.disaster.indicator,
            "indicatorName": names.get("indicator") or "",
        },
    }


def encode_disaster_id(info: Dict[str, Any]) -> str:
    """
    根据结构化信息编码生成统一灾情 ID。
    """
    try:
        event_time = info["event_time"]
        time_str = _to_time_str(event_time) if isinstance(event_time, datetime) else str(event_time)

        event = codec_core.build_event_info(info["location_code"], time_str)
        source = codec_core.build_source_info(info["source_code"])
        carrier = codec_core.build_carrier_info(info["carrier_code"])
        disaster = codec_core.build_disaster_info(
            info["disaster_category_code"],
            info["disaster_sub_category_code"],
            info["indicator_code"],
        )
        encoded = codec_core.encode_disaster(event, source, carrier, disaster)
        logger.info(
            "Encoded id=%s for location=%s time=%s source=%s carrier=%s disaster=%s%s%s",
            encoded,
            info["location_code"],
            time_str,
            info["source_code"],
            info["carrier_code"],
            info["disaster_category_code"],
            info["disaster_sub_category_code"],
            info["indicator_code"],
        )
        return encoded
    except Exception as exc:  # 统一封装为 CodecError
        logger.exception("Encoding failed for payload=%s", info)
        raise CodecError(str(exc)) from exc
