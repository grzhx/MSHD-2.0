# 灾情管理一体化系统

将原有的三个模块（前端 `disaster-management-dashboard`，后端 `code-dictionary` 与 `access-storage`）整合为一个可直接运行的全栈系统。后端已合并编码/字典能力与接入/存储接口，前端默认直连单一后端服务。

## 目录结构
- `access-storage/`：FastAPI 后端（编码/解码 + 字典 + 数据接入 + 存储/生命周期管理），监听 `:8000`
- `disaster-management-dashboard/`：Angular 仪表盘前端，默认访问 `http://localhost:8000/api`
- `code-dictionary/`：原始编码/字典模块源码，已被 `access-storage` 复用

## 快速启动
1) 启动后端（FastAPI）
```bash
cd access-storage
python -m venv .venv
source .venv/bin/activate  # Windows 请使用 .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2) 启动前端（Angular）
```bash
cd disaster-management-dashboard
npm install
npm run dev   # 或 npm run start，默认 http://localhost:4200
```
前端会从 `http://localhost:8000/api` 拉取数据与字典。

## 主要接口（后端）
- `/api/codec/encode`、`/api/codec/decode/{id}`：统一灾情 ID 编码/解码
- `/api/dict/{domain}?flat=1`：字典查询，支持扁平化返回 `{code,name}`
- `/api/ingest?mode=encoded|raw`、`/api/ingest/batch`：多源数据接入
- `/api/storage/disaster-records`（GET/POST）：灾情记录列表/写入
- `/api/storage/disaster-records/{id}`：查询单条灾情
- `/api/storage/run-retention`：生命周期归档
- `/health`：存活探针

## 日志与调试
- 后端已开启基础请求日志与异常堆栈：每个请求都会记录入口/出口与状态码，编码/解码/接入失败会输出详细错误。
- 前端在调用后端失败时会打印 `console.error`，并回退到内置的演示数据，避免页面空白。

## 其他说明
- 地理坐标：后端暂未提供经纬度，前端会基于 `location_code` 生成可视化坐标以便地图展示。
- 如需切换后端地址，请修改 `disaster-management-dashboard/src/environments/environment.ts`。

## 一键启动（推荐）
执行根目录脚本：
```bash
chmod +x run_system.sh
./run_system.sh
```
- 后端：自动使用/创建 `access-storage/.venv`，安装依赖并启动 uvicorn（默认 8000）。
- 前端：如无 `node_modules` 自动 `npm install`，启动 Angular dev server（默认 3000）。
- 日志：`.run-logs/backend.log`、`.run-logs/frontend.log`，按 Ctrl+C 结束。

## 运行前的依赖要求
- Node.js 24.x（含 npm）—— 用于前端。
- Python 3.11+（示例环境 3.13）—— 用于后端。
- 可选 VSCode 插件：Python、Pylance、Angular Language Service（仅开发体验）。

### Python 依赖（pip）
统一需求（`access-storage/requirements.txt` + `code-dictionary/requirements.txt` 覆盖）：
- fastapi
- uvicorn
- sqlalchemy
- pydantic
- python-multipart
- pytest（仅测试需要）

### 前端依赖（npm，已写入 package.json）
- @angular/common @angular/core @angular/compiler @angular/platform-browser
- @angular/build @angular/cli @angular/compiler-cli
- rxjs
- tailwindcss
- 开发依赖：typescript (~5.9.x), @types/node, vite
