# app/codec_client.py
"""
与“编码/解码模块（模块 1/2）”对接的客户端封装。

目前为了方便你先把后端整体跑起来，这里写成“本地 stub”：
- decode_disaster_id：直接从 ID 字符串中切片，并用一些占位名称
- encode_disaster_id：根据传入的字段拼接一个合法的 36 位 ID

以后组员实现了真正的编码/解码服务后，你只需要：
- 在这里改为实际 HTTP 请求，对接他们的接口
- 其他模块（ingestion_service / main）都不用改
"""

from typing import Dict, Any
from datetime import datetime


class CodecError(Exception):
    """
    自定义异常：编码/解码出错时抛出，方便上层捕获并返回 400 错误
    """
    pass


def decode_disaster_id(disaster_id: str) -> Dict[str, Any]:
    """
    解码统一灾情 ID（示例实现）

    统一 ID：共 36 位：
        quake_part (26) + source_part (3) + carrier_part (1) + disaster_part (6)

    quake_part 结构：
        location_code(12) + time_code(14)  # time_code 格式：YYYYMMDDhhmmss

    返回结构示例：
    {
      "event": {
        "locationCode": "...",
        "locationName": "...",
        "time": datetime(...)
      },
      "source": { "code": "...", "name": "..." },
      "carrier": { "code": "...", "name": "..." },
      "disaster": {
         "categoryCode": "...",
         "categoryName": "...",
         "subCategoryCode": "...",
         "subCategoryName": "...",
         "indicatorCode": "...",
         "indicatorName": "..."
      }
    }
    """
    if len(disaster_id) != 36:
        raise CodecError("ID 长度必须为 36（26+3+1+6）")

    if not disaster_id.isdigit():
        raise CodecError("ID 应为纯数字")

    # 拆分各部分
    quake_part = disaster_id[:26]      # 震情码
    source_part = disaster_id[26:29]   # 来源码
    carrier_part = disaster_id[29:30]  # 载体码
    disaster_part = disaster_id[30:]   # 灾情码 6 位

    # 解析时间码（震情码后 14 位）
    time_code = quake_part[12:]
    try:
        event_time = datetime.strptime(time_code, "%Y%m%d%H%M%S")
    except ValueError:
        raise CodecError("时间码格式错误，应为 YYYYMMDDhhmmss")

    # 这里的名称先用占位字符串，
    # 真正系统中，应从字典服务查询得到正式中文名称
    return {
        "event": {
            "locationCode": quake_part[:12],
            "locationName": "（示例）某地名称",
            "time": event_time,
        },
        "source": {
            "code": source_part,
            "name": f"来源-{source_part}",
        },
        "carrier": {
            "code": carrier_part,
            "name": f"载体-{carrier_part}",
        },
        "disaster": {
            "categoryCode": disaster_part[0],
            "categoryName": f"灾种-{disaster_part[0]}",
            "subCategoryCode": disaster_part[1:3],
            "subCategoryName": f"子类-{disaster_part[1:3]}",
            "indicatorCode": disaster_part[3:6],
            "indicatorName": f"指标-{disaster_part[3:6]}",
        },
    }


def encode_disaster_id(info: Dict[str, Any]) -> str:
    """
    根据结构化信息编码生成统一灾情 ID（示例实现）

    必要字段：
      - location_code: str (12 位)
      - event_time: datetime
      - source_code: str (3 位)
      - carrier_code: str (1 位)
      - disaster_category_code: str (1 位)
      - disaster_sub_category_code: str (2 位)
      - indicator_code: str (3 位)

    返回：
      拼接好的 36 位统一 ID
    """
    location_code = info["location_code"]
    event_time: datetime = info["event_time"]
    source_code = info["source_code"]
    carrier_code = info["carrier_code"]
    category = info["disaster_category_code"]
    sub_category = info["disaster_sub_category_code"]
    indicator = info["indicator_code"]

    if len(location_code) != 12:
        raise
