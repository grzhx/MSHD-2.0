
# 灾情管理仪表盘 (前端)

## 项目概览

这是一个基于 Angular 框架构建的灾情管理系统前端应用。它提供了一个现代、美观且功能丰富的用户界面，用于可视化和管理多源灾情数据，旨在为应急指挥和数据分析提供支持。

### 主要功能

- **总览大屏 (Dashboard):** 通过卡片和图表直观展示关键统计数据，如灾情总数、按类别分布和近期趋势。
- **地图视图 (Map View):** 在交互式地图上展示灾情地理分布，支持点位高亮和摘要信息查看。
- **列表 + 详情视图 (List + Detail View):** 提供强大的数据表格，支持搜索、筛选，并能查看单条灾情的完整信息和多媒体资料。
- **导出功能:** 支持将当前查询结果导出为 CSV 文件，便于离线分析。
- **运维管理 (Monitoring):** 监控数据源接入状态和 API 调用情况，确保系统稳定运行。
- **字典与配置 (Dictionary):** 提供一个只读界面，方便查看系统内部使用的编码和字典表。

---

## 前端如何与后端 Python 文件关联

本前端应用是一个**客户端单页应用 (Single Page Application, SPA)**。这意味着所有的代码（HTML, CSS, TypeScript）都在用户的浏览器中下载并执行。它**不直接运行**后端的 Python 代码。

前端与后端（`disaster_backend/app/main.py` 和 `code/backend/main.py`）的交互完全通过 **HTTP API 调用** 来实现。

### 核心关联点: `ApiService`

项目中的 `src/services/api.service.ts` 文件是前端与后端通信的桥梁。该文件已配置为使用 Angular 的 `HttpClient` 模块向后端服务发起真实的 HTTP 请求。

API 的基础 URL（例如 `http://localhost:8000`）集中管理在 `src/environments/environment.ts` 文件中，方便在不同环境（开发、生产）之间切换。

---

## 如何完整地配置和运行前端程序

要完整地运行整个系统（前端+后端），请遵循以下步骤。

### 1. 运行后端服务

在启动前端之前，必须确保两个 Python FastAPI 后端服务都已经成功启动。

- **启动编码服务 (`codec_service`):**
  进入 `code/backend` 目录，并启动服务。根据配置，它将运行在 `http://localhost:8000`。

- **启动灾情数据管理服务 (`disaster_backend`):**
  进入 `disaster_backend` 目录，并按照其文档启动服务。根据配置，它将运行在 `http://localhost:8001`。

### 2. 配置前端环境

前端项目依赖于 Node.js 和 npm (Node Package Manager)。

- **安装 Node.js:**
  如果您的系统中没有 Node.js，请从 [官方网站](https://nodejs.org/) 下载并安装 LTS (长期支持) 版本。npm 会随 Node.js 一同安装。

- **安装项目依赖:**
  在项目的根目录下（包含 `index.tsx` 的目录），打开终端或命令行工具，运行以下命令来安装所有必需的库（如 Angular 框架本身）：
  ```bash
  npm install
  ```
  *(注意: 在某些在线开发环境中，此步骤可能是自动完成的。)*

### 3. 修改 API 地址 (如果需要)

所有后端的 API 地址都在 `src/environments/environment.ts` 文件中配置。如果您的后端服务运行在不同的地址或端口，请修改此文件：

```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  codecApiUrl: 'http://localhost:8000/api', // 编码服务基础 URL
  disasterApiUrl: 'http://localhost:8001/api', // 灾情数据管理服务基础 URL
};
```

### 4. 启动前端开发服务器

完成以上配置后，在项目根目录的终端中运行以下命令：

```bash
npm start
```

此命令会编译整个 Angular 应用，并启动一个本地开发服务器。编译成功后，您会在终端看到类似以下的输出：

```
** Angular Live Development Server is listening on localhost:4200, open your browser on http://localhost:4200/ **
```

现在，打开您的网页浏览器，访问 `http://localhost:4200`，您就可以看到并与灾情管理系统的前端界面进行交互了。所有操作都会通过 API 请求发送到您正在运行的后端服务。

---

## 主要接口端点

### 编码服务 (端口 8000)

- `POST /api/codec/encode` - 编码接口
- `GET /api/codec/decode/{encoded_id}` - 解码接口
- `GET /api/dict/{domain}` - 字典查询接口
- `GET /health` - 健康检查接口

### 灾情数据管理服务 (端口 8001)

- `POST /api/ingest?mode=encoded|raw` - 数据接入接口
- `POST /api/ingest/batch?mode=encoded|raw` - 批量导入接口
- `POST /api/storage/disaster-records` - 创建灾情记录
- `GET /api/storage/disaster-records/{record_id}` - 查询灾情记录
- `POST /api/storage/run-retention` - 生命周期管理
