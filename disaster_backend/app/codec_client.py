# app/codec_client.py
"""
与“编码/解码模块（模块 1/2）”对接的客户端封装。
现在改为真正调用编码服务的 HTTP 接口，去掉本地 stub。
"""

from typing import Dict, Any
from datetime import datetime
import requests

from .settings import CODEC_API_URL


class CodecError(Exception):
    """
    自定义异常：编码/解码出错时抛出，方便上层捕获并返回 400 错误
    """
    pass


def decode_disaster_id(disaster_id: str) -> Dict[str, Any]:
    """
    调用编码模块的解码接口并返回统一结构。
    """
    if len(disaster_id) != 36 or not disaster_id.isdigit():
        raise CodecError("ID 长度必须为 36 且为纯数字")

    try:
        resp = requests.get(
            f"{CODEC_API_URL}/codec/decode/{disaster_id}", timeout=5
        )
    except requests.RequestException as exc:  # 网络/连接错误
        raise CodecError(f"调用编码服务失败: {exc}") from exc

    if resp.status_code != 200:
        detail = resp.text
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            pass
        raise CodecError(f"编码服务返回错误: {detail}")

    payload = resp.json()
    event = payload.get("event", {})
    source = payload.get("source", {})
    carrier = payload.get("carrier", {})
    disaster = payload.get("disaster", {})
    names = payload.get("names", {}) or {}

    time_code = event.get("time_code")
    try:
        event_time = datetime.strptime(time_code, "%Y%m%d%H%M%S") if time_code else None
    except ValueError as exc:
        raise CodecError("时间码格式错误，应为 YYYYMMDDhhmmss") from exc

    return {
        "event": {
            "latCode": event.get("lat_code", ""),
            "lngCode": event.get("lng_code", ""),
            "time": event_time,
        },
        "source": {
            "code": source.get("code", ""),
            "name": names.get("source") or source.get("code", ""),
        },
        "carrier": {
            "code": carrier.get("code", ""),
            "name": names.get("carrier") or carrier.get("code", ""),
        },
        "disaster": {
            "categoryCode": disaster.get("category", ""),
            "categoryName": names.get("disaster_category") or disaster.get("category", ""),
            "subCategoryCode": disaster.get("sub_category", ""),
            "subCategoryName": names.get("disaster_sub_category") or disaster.get("sub_category", ""),
            "indicatorCode": disaster.get("indicator", ""),
            "indicatorName": names.get("indicator") or disaster.get("indicator", ""),
        },
    }


def encode_disaster_id(info: Dict[str, Any]) -> str:
    """
    调用编码模块的编码接口，返回统一灾情 ID。
    """
    lat_code = info["lat_code"]
    lng_code = info["lng_code"]
    event_time: datetime = info["event_time"]
    source_code = info["source_code"]
    carrier_code = info["carrier_code"]
    category = info["disaster_category_code"]
    sub_category = info["disaster_sub_category_code"]
    indicator = info["indicator_code"]

    payload = {
        "event": {
            "latCode": str(lat_code),
            "lngCode": str(lng_code),
            "time": event_time.strftime("%Y%m%d%H%M%S"),
        },
        "source": {"code": source_code},
        "carrier": {"code": carrier_code},
        "disaster": {
            "categoryCode": category,
            "subCategoryCode": sub_category,
            "indicatorCode": indicator,
        },
    }

    try:
        resp = requests.post(
            f"{CODEC_API_URL}/codec/encode", json=payload, timeout=5
        )
    except requests.RequestException as exc:
        raise CodecError(f"调用编码服务失败: {exc}") from exc

    if resp.status_code != 200:
        detail = resp.text
        try:
            detail = resp.json().get("detail", detail)
        except Exception:
            pass
        raise CodecError(f"编码服务返回错误: {detail}")

    data = resp.json()
    encoded_id = data.get("id")
    if not encoded_id:
        raise CodecError("编码服务未返回 ID")
    return encoded_id
