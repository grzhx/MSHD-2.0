# app/main.py
"""
FastAPI 应用入口
负责：
1. 创建数据库表
2. 定义路由（多源接入 / 存储 / 生命周期管理相关接口）
3. 提供给前端或其它模块调用的 HTTP API
"""

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Body, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from collections import Counter
import csv
from io import StringIO
from datetime import datetime, timedelta

from starlette.middleware.cors import CORSMiddleware

from .database import Base, engine, get_db
from . import models, schemas
from . import ingestion_service
from .settings import RETENTION_INACTIVE_DAYS, ADMIN_PASSWORD

# 在应用启动时根据 ORM 模型创建表（如果表不存在）
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 实例
app = FastAPI(title="多源灾情数据管理服务（模块3&4）", version="1.0.0")

origins = [
    "http://localhost:3000",
    "http://localhost:4200",
]

# 3. 将 CORS 中间件添加到您的应用中
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 允许访问的源
    allow_credentials=True,      # 支持 cookie
    allow_methods=["*"],         # 允许所有方法 (GET, POST, etc.)
    allow_headers=["*"],         # 允许所有请求头
)

# 简单的管理员口令校验（通过自定义 Header 传递，默认值在 settings 中配置）
def _ensure_admin(admin_password: str | None):
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="管理员密码不正确")


# 健康检查
@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

# ========== 模块 3：多源数据接入与校验 ==========

@app.post("/api/ingest", response_model=schemas.IngestResponse)
def ingest_data(
    # mode 作为查询参数：encoded / raw
    mode: str = Query(..., description="数据模式：encoded（已编码）或 raw（原始结构化）"),
    # body 作为请求体，暂时用 dict 接收，再手动转换
    body: dict = Body(..., description="根据 mode 不同，结构不同"),
    admin_password: str | None = Header(None, alias="X-Admin-Password"),
    db: Session = Depends(get_db),
):
    """
    多源数据接入接口（统一入口）
    - mode = encoded：上游已经生成统一 ID
    - mode = raw    ：上游提供原始结构化信息，需要本模块调用编码内核生成 ID
    """
    _ensure_admin(admin_password)

    if mode == "encoded":
        # 把 body 转成 IngestEncodedRequest 模型
        payload = schemas.IngestEncodedRequest(**body)
        status, msg = ingestion_service.ingest_encoded(db, payload)
        if status != "ok":
            raise HTTPException(status_code=400, detail=msg)
        return schemas.IngestResponse(id=payload.id, status="ok", message=msg)

    elif mode == "raw":
        # 把 body 转成 IngestRawRequest 模型
        req = schemas.IngestRawRequest(**body)
        status, msg, new_id = ingestion_service.ingest_raw(db, req)
        if status != "ok":
            raise HTTPException(status_code=400, detail=msg)
        return schemas.IngestResponse(id=new_id, status="ok", message=msg)

    else:
        raise HTTPException(status_code=400, detail="mode 只能为 'encoded' 或 'raw'")


@app.post("/api/ingest/batch", response_model=schemas.IngestResponse)
async def ingest_batch(
    mode: str = Query(..., description="数据模式：encoded 或 raw"),
    file: UploadFile = File(..., description="CSV 文件，编码为 UTF-8"),
    admin_password: str | None = Header(None, alias="X-Admin-Password"),
    db: Session = Depends(get_db),
):
    """
    批量导入接口（实验版实现为 CSV 文件）。

    - mode = encoded：
        CSV 表头应包含：id,value,unit,media_path,raw_payload
    - mode = raw：
        CSV 表头应包含：
          lat_code,lng_code,event_time,source_code,carrier_code,
          disaster_category_code,disaster_sub_category_code,
          indicator_code,value,unit,media_path,raw_payload

    event_time 字段格式建议使用 ISO8601，例如：2024-12-01T12:30:45
    """
    if file.content_type not in (
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        raise HTTPException(status_code=400, detail="目前仅支持 CSV 文件")

    _ensure_admin(admin_password)

    # 读取整个文件内容并按 UTF-8 解码为字符串
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV 文件需要使用 UTF-8 编码")

    reader = csv.DictReader(StringIO(text))

    count_ok = 0
    count_err = 0

    for row in reader:
        try:
            if mode == "encoded":
                payload = schemas.IngestEncodedRequest(
                    id=row["id"],
                    value=float(row["value"]) if row.get("value") else None,
                    unit=row.get("unit"),
                    media_path=row.get("media_path"),
                    raw_payload=row.get("raw_payload"),
                )
                status, msg = ingestion_service.ingest_encoded(db, payload)
                if status == "ok":
                    count_ok += 1
                else:
                    count_err += 1

            elif mode == "raw":
                # event_time 使用 ISO 格式字符串解析
                event_time = datetime.fromisoformat(row["event_time"])
                req = schemas.IngestRawRequest(
                    event=schemas.IngestRawEventInfo(
                        lat_code=row["lat_code"],
                        lng_code=row["lng_code"],
                        event_time=event_time,
                        source_code=row["source_code"],
                        carrier_code=row["carrier_code"],
                        disaster_category_code=row["disaster_category_code"],
                        disaster_sub_category_code=row["disaster_sub_category_code"],
                        indicator_code=row["indicator_code"],
                        value=float(row["value"]) if row.get("value") else None,
                        unit=row.get("unit"),
                        media_path=row.get("media_path"),
                        raw_payload=row.get("raw_payload"),
                    )
                )
                status, msg, _ = ingestion_service.ingest_raw(db, req)
                if status == "ok":
                    count_ok += 1
                else:
                    count_err += 1

            else:
                raise HTTPException(status_code=400, detail="mode 只能为 'encoded' 或 'raw'")

        except Exception:
            # 任意异常都计为失败一条，方便统计
            count_err += 1

    # 这里返回一个简单的结果 summary
    return schemas.IngestResponse(
        id="",
        status="ok",
        message=f"批量导入完成：成功 {count_ok} 条，失败 {count_err} 条",
    )


# ========== 模块 4：灾情数据存储与生命周期管理 ==========

@app.post("/api/storage/disaster-records", response_model=schemas.DisasterRecordRead)
def create_disaster_record(
    record: schemas.DisasterRecordCreate,
    db: Session = Depends(get_db),
):
    """
    存储层内部写入接口（一般由接入模块调用）。
    也可以作为测试接口手工写入一条记录。
    """
    existing = db.query(models.DisasterRecord).filter(
        models.DisasterRecord.id == record.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="记录已存在")

    obj = models.DisasterRecord(
        **record.dict(),
        created_at=datetime.utcnow(),
        last_accessed_at=datetime.utcnow(),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/api/storage/disaster-records", response_model=schemas.DisasterRecordListResponse)
def list_disaster_records(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    include_archived: bool = Query(True, description="是否包含已归档记录"),
):
    """
    灾情记录列表接口，支持简单分页。
    """
    q = db.query(models.DisasterRecord).order_by(models.DisasterRecord.created_at.desc())
    if not include_archived:
        q = q.filter(models.DisasterRecord.is_archived == False)  # noqa: E712

    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return schemas.DisasterRecordListResponse(total=total, items=items)


@app.get("/api/storage/disaster-records/{record_id}", response_model=schemas.DisasterRecordRead)
def get_disaster_record(
    record_id: str,
    db: Session = Depends(get_db),
):
    """
    灾情记录读取接口。
    注意：每次读取都会更新 last_accessed_at，
    为后续的“长期未访问自动归档”提供依据。
    """
    obj = db.query(models.DisasterRecord).filter(
        models.DisasterRecord.id == record_id
    ).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 更新最后访问时间
    obj.last_accessed_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


@app.delete("/api/storage/disaster-records/{record_id}")
def delete_disaster_record(
    record_id: str,
    admin_password: str | None = Header(None, alias="X-Admin-Password"),
    db: Session = Depends(get_db),
):
    """
    删除一条灾情记录（需要管理员密码）。
    """
    _ensure_admin(admin_password)
    obj = db.query(models.DisasterRecord).filter(models.DisasterRecord.id == record_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(obj)
    db.commit()
    return {"status": "ok", "id": record_id}


@app.post("/api/storage/run-retention")
def run_retention(db: Session = Depends(get_db)):
    """
    生命周期管理接口（手动触发）。

    简单策略：
    - 找出 last_accessed_at 距今超过 RETENTION_INACTIVE_DAYS 天的记录；
    - 将其 is_archived 标记为 True；
    - 返回本次被归档的记录数量。

    实际系统中可以把这个接口改成定时任务（例如每日凌晨执行一次）。
    """
    threshold = datetime.utcnow() - timedelta(days=RETENTION_INACTIVE_DAYS)
    q = db.query(models.DisasterRecord).filter(
        models.DisasterRecord.last_accessed_at < threshold,
        models.DisasterRecord.is_archived == False,
    )
    count = q.count()

    # 批量更新 is_archived 字段
    q.update({models.DisasterRecord.is_archived: True})
    db.commit()

    return {"status": "ok", "archived_count": count}


@app.get("/api/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """
    仪表盘统计接口：
    - 总数
    - 按灾害类别分布
    - 按来源分布
    - 最近 24 小时每小时的新增数量
    """
    total = db.query(models.DisasterRecord).count()

    # 按灾害类别分布（名称优先，其次代码）
    category_rows = (
        db.query(
            func.coalesce(
                models.DisasterRecord.disaster_category_name,
                models.DisasterRecord.disaster_sub_category_name,
                models.DisasterRecord.disaster_category_code,
                "其他",
            ).label("label"),
            func.count(models.DisasterRecord.id).label("count"),
        )
        .group_by("label")
        .all()
    )

    # 按来源分布
    source_rows = (
        db.query(
            func.coalesce(
                models.DisasterRecord.source_name,
                models.DisasterRecord.source_code,
                "未知来源",
            ).label("label"),
            func.count(models.DisasterRecord.id).label("count"),
        )
        .group_by("label")
        .all()
    )

    # 最近 24 小时新增数量（按小时）
    now = datetime.utcnow()
    window_start = (now - timedelta(hours=23)).replace(
        minute=0, second=0, microsecond=0
    )
    hourly_counts: Counter[datetime] = Counter()
    recent_times = (
        db.query(models.DisasterRecord.created_at)
        .filter(models.DisasterRecord.created_at >= window_start)
        .all()
    )
    for (created_at,) in recent_times:
        if created_at:
            bucket = created_at.replace(minute=0, second=0, microsecond=0)
            hourly_counts[bucket] += 1

    recent_labels = []
    recent_data = []
    for i in range(24):
        bucket_time = window_start + timedelta(hours=i)
        recent_labels.append(bucket_time.strftime("%H:00"))
        recent_data.append(hourly_counts.get(bucket_time, 0))

    return {
        "totalCount": total,
        "disasterDistribution": {
            "labels": [row.label for row in category_rows],
            "data": [row.count for row in category_rows],
        },
        "sourceDistribution": {
            "labels": [row.label for row in source_rows],
            "data": [row.count for row in source_rows],
        },
        "recentActivity": {
            "labels": recent_labels,
            "data": recent_data,
        },
    }


@app.get("/api/monitoring/summary")
def monitoring_summary(db: Session = Depends(get_db)):
    """
    基础运维监控：统计数据源活跃度和接口调用概览。
    """
    now = datetime.utcnow()
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    # 数据源活跃度统计
    source_stats = (
        db.query(
            models.DisasterRecord.source_code,
            func.max(models.DisasterRecord.event_time).label("last_time"),
            func.max(models.DisasterRecord.source_name).label("source_name"),
            func.sum(case((models.DisasterRecord.created_at >= since_24h, 1), else_=0)).label("cnt24"),
            func.sum(case((models.DisasterRecord.created_at >= since_7d, 1), else_=0)).label("cnt7d"),
        )
        .group_by(models.DisasterRecord.source_code)
        .all()
    )

    data_sources = []
    for stat in source_stats:
        data_sources.append(
            {
                "name": stat.source_name or stat.source_code or "未知来源",
                "lastReceived": stat.last_time.isoformat() if stat.last_time else "-",
                "count24h": int(stat.cnt24 or 0),
                "count7d": int(stat.cnt7d or 0),
                "errors": 0,
            }
        )

    total_records = db.query(models.DisasterRecord).count()
    api_calls = [
        {"endpoint": "/api/ingest", "caller": "数据采集模块", "requests": total_records, "avgResponse": "-", "errorRate": "0.0%"},
        {"endpoint": "/api/storage/disaster-records", "caller": "内部服务", "requests": total_records, "avgResponse": "-", "errorRate": "0.0%"},
    ]

    return {"dataSources": data_sources, "apiCalls": api_calls}
