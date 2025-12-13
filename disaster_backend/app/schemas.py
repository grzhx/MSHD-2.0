# app/schemas.py
"""
Pydantic 数据模型（请求/响应体）
用于 FastAPI 自动进行数据验证和文档生成。

主要包括：
1. DisasterRecord 系列 —— 用于存储/读取的统一灾情结构
2. Ingest 系列 —— 用于多源数据接入接口（已编码 / 原始模式）
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict


# --------- 核心灾情结构 ---------

class DisasterRecordBase(BaseModel):
    """
    统一灾情记录的基础结构（很多字段是可选的，视数据源情况而定）
    """
    id: str = Field(..., description="统一灾情 ID（36 位）")

    lat_code: str = Field(..., description="纬度编码 = (纬度 * 1000) 取整，6 位含符号")
    lng_code: str = Field(..., description="经度编码 = (经度 * 1000) 取整，6 位含符号")
    event_time: Optional[datetime] = None

    source_code: Optional[str] = None
    source_name: Optional[str] = None

    carrier_code: Optional[str] = None
    carrier_name: Optional[str] = None

    disaster_category_code: Optional[str] = None
    disaster_category_name: Optional[str] = None
    disaster_sub_category_code: Optional[str] = None
    disaster_sub_category_name: Optional[str] = None

    indicator_code: Optional[str] = None
    indicator_name: Optional[str] = None

    value: Optional[float] = None
    unit: Optional[str] = None

    media_path: Optional[str] = None
    raw_payload: Optional[str] = None


class DisasterRecordCreate(DisasterRecordBase):
    """
    创建灾情记录时使用的模型，
    目前和 Base 一样，可以根据需求扩展必填字段。
    """
    pass


class DisasterRecordRead(DisasterRecordBase):
    """
    对外返回的灾情记录模型（包含生命周期字段）
    """
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime
    is_archived: bool

    model_config = ConfigDict(from_attributes=True)


class DisasterRecordListResponse(BaseModel):
    """
    如果需要分页/列表返回，可以用这个结构。
    """
    total: int
    items: List[DisasterRecordRead]

    model_config = ConfigDict(from_attributes=True)


# --------- 接入模块（多源数据接入）的请求/响应模型 ---------

class IngestEncodedRequest(BaseModel):
    """
    模式一：已编码模式（上游已经生成统一灾情 ID）
    后端只需要：
    1. 调用解码模块拆出 event/source/载体/灾情信息
    2. 补全名称 & 校验
    3. 入库
    """
    id: str = Field(..., description="统一灾情 ID（36 位）")
    value: Optional[float] = None
    unit: Optional[str] = None
    media_path: Optional[str] = None
    raw_payload: Optional[str] = None


class IngestRawEventInfo(BaseModel):
    """
    模式二：原始结构化信息
    由接入模块调用编码模块生成 ID，再入库。
    """
    lat_code: str                         # 纬度编码（±纬度*1000，长度 6 含符号）
    lng_code: str                         # 经度编码（±经度*1000，长度 6 含符号）
    event_time: datetime                  # 事件发生时间
    source_code: str                      # 来源码 3 位
    carrier_code: str                     # 载体码 1 位
    disaster_category_code: str           # 灾种 1 位
    disaster_sub_category_code: str       # 灾种子类 2 位
    indicator_code: str                   # 指标码 3 位
    value: Optional[float] = None
    unit: Optional[str] = None
    media_path: Optional[str] = None
    raw_payload: Optional[str] = None


class IngestRawRequest(BaseModel):
    """
    原始模式的整体请求体结构：
    {
      "event": { ... IngestRawEventInfo ... }
    }
    """
    event: IngestRawEventInfo


class IngestResponse(BaseModel):
    """
    接入接口统一响应结构
    无论是 encoded 还是 raw，最终都会返回：
    - id：统一灾情 ID
    - status：ok / error
    - message：提示信息
    """
    id: str
    status: str
    message: Optional[str] = None
