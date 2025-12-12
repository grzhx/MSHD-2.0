# MSHD2.0 Codec Module (模块1)

FastAPI 服务，提供多源异构灾情 ID 的编码/解码与字典查询。

## 运行

```bash
# 安装依赖
pip install -r requirements.txt

# 开发启动
uvicorn main:app --reload --app-dir backend
```

## API
- `POST /api/codec/encode` ：传入事件/来源/载体/灾情字段，返回统一 ID。
- `GET /api/codec/decode/{id}` ：传入 36 位 ID，返回结构化信息和名称。
- `GET /api/dict/{domain}` ：domain=source|carrier|disaster|indicator
- `GET /api/dict/{domain}/{code}` ：单个编码查询。
- `GET /health` ：健康检查。

## 测试

```bash
pytest backend/tests
```
