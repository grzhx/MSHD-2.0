# app/models.py
"""
SQLAlchemy ORM 模型定义
对应“灾情数据存储与生命周期管理”部分的数据库表结构。
包括：
1. Event           —— 地震事件表（震情码为主键）
2. DisasterRecord  —— 核心灾情记录表（统一灾情 ID 为主键）
3. MediaIndex      —— 多媒体索引表（记录与文件路径关系）
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Event(Base):
    """
    地震事件基本信息表
    震情码(26 位) 作为主键：
        = 纬度编码6 + 经度编码6 + 时间码14(YYYYMMDDhhmmss)
    """
    __tablename__ = "events"

    # 震情码作为主键，例如：12345678901220241201123045
    id = Column(String(26), primary_key=True, index=True)

    # 经纬度编码（±lat*1000 / ±lng*1000，含符号，总长度 6）
    lat_code = Column(String(8), index=True)
    lng_code = Column(String(8), index=True)

    # 事件发生时间（从时间码解析而来）
    event_time = Column(DateTime, index=True)

    # 可选：震级、深度、烈度等（根据需要扩展）
    magnitude = Column(Float, nullable=True)
    depth_km = Column(Float, nullable=True)
    intensity = Column(String(16), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 一个 Event 下可以有多条灾情记录
    disaster_records = relationship("DisasterRecord", back_populates="event")


class DisasterRecord(Base):
    """
    核心灾情记录表
    统一灾情 ID 长度 36：
        = 震情码(26) + 来源码(3) + 载体码(1) + 灾情码(6)
    """
    __tablename__ = "disaster_records"

    # 统一灾情 ID（主键）
    id = Column(String(36), primary_key=True, index=True)

    # 震情相关（冗余字段，方便按时间/地点查询）
    event_id = Column(String(26), ForeignKey("events.id"), index=True)
    event_time = Column(DateTime, index=True)
    lat_code = Column(String(8), index=True)
    lng_code = Column(String(8), index=True)

    # 来源信息
    source_code = Column(String(3), index=True)
    source_name = Column(String(128))

    # 载体信息
    carrier_code = Column(String(1), index=True)
    carrier_name = Column(String(32))

    # 灾情分类 + 指标
    disaster_category_code = Column(String(1), index=True)
    disaster_category_name = Column(String(64))
    disaster_sub_category_code = Column(String(2), index=True)
    disaster_sub_category_name = Column(String(64))
    indicator_code = Column(String(3), index=True)
    indicator_name = Column(String(128))

    # 指标值和单位，比如：死亡人数、受损房屋数量等
    value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)

    # 原始载体路径（比如原始图片/视频/文本文件路径或 URL）
    media_path = Column(String(256), nullable=True)

    # 原始报文或结构化数据的 JSON 字符串
    raw_payload = Column(Text, nullable=True)

    # 生命周期相关字段：
    created_at = Column(DateTime, default=datetime.utcnow)                           # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # 最后修改时间
    last_accessed_at = Column(DateTime, default=datetime.utcnow, index=True)         # 最后访问时间
    is_archived = Column(Boolean, default=False, index=True)                         # 是否已归档

    # ORM 关系：一个灾情记录属于一个事件
    event = relationship("Event", back_populates="disaster_records")

    # ORM 关系：一个灾情记录可以有多条媒体索引
    media_items = relationship("MediaIndex", back_populates="record")


class MediaIndex(Base):
    """
    多媒体索引表：
    把统一灾情 ID -> 文件路径/URL 建立索引，
    为后续多媒体检索、展示做准备。
    """
    __tablename__ = "media_index"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 对应的灾情记录 ID
    disaster_id = Column(String(36), ForeignKey("disaster_records.id"), index=True)

    # 媒体类型（文本/图片/音频/视频等，实验版先用简单字符串）
    media_type = Column(String(16))  # text / image / audio / video / other

    # 文件路径或 URL
    file_path = Column(String(256))

    # MIME 类型（可选，比如 image/png, video/mp4 等）
    mime_type = Column(String(64), nullable=True)

    # 文件大小（字节数，可选）
    size_bytes = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ORM 关系：一个 media 记录属于一条灾情记录
    record = relationship("DisasterRecord", back_populates="media_items")
