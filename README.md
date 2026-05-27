# AstroRAG — 天文知识智能问答系统

基于 RAG（检索增强生成）的天文知识问答系统，覆盖梅西耶天体、NGC/IC 星表、星座与天文术语。内置星图渲染引擎，可实时生成高质量天空星图。

## 功能特性

- **智能问答** — 基于 LangChain4j + 本地 LLM 的 RAG 管道，流式输出
- **星图渲染** — 11.8 万颗星 + 88 星座连线 + 深空天体标记，150 DPI 高清输出
- **知识检索** — BGE-M3 嵌入模型 + ChromaDB 向量数据库，毫秒级语义搜索
- **天文数据** — 整合 Messier/NGC/IC 天体目录、星座数据、天文术语库

## 技术架构

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  React 前端   │───▶│ Spring Boot  │───▶│  LM Studio   │
│  port 3000    │    │  port 8080   │    │  port 1234   │
└──────────────┘    └──────┬───────┘    └──────────────┘
                           │                      
                     ┌─────┼─────┐                
                     ▼           ▼                
              ┌──────────┐ ┌──────────┐
              │Embedding │ │  ChromaDB │
              │  BGE-M3  │ │ port 8000 │
              │ port 8081 │ └──────────┘
              └──────────┘               
                                        
┌──────────────┐                         
│  Star Chart  │  Flask + Matplotlib     
│  port 8082   │  HYG v3.8 星表         
└──────────────┘                         
```

## 快速开始

### 前置要求

| 组件 | 说明 |
|------|------|
| **Java 17+** | Spring Boot 后端 |
| **Python 3.10+** | Embedding / 星图服务 |
| **Node.js 18+** | React 前端 |
| **LM Studio** | 本地 LLM 推理（port 1234） |
| **ChromaDB** | 向量数据库 |

### 一键启动（Windows）

```batch
# 1. 启动 LM Studio，加载 Qwen2.5-7B-Instruct 模型，开启 local server (port 1234)

# 2. 运行启动脚本
.\start.ps1

# 3. 浏览器自动打开 http://localhost:3000
```

### 手动启动

```bash
# 1. ChromaDB
chroma run --path chroma_data

# 2. Embedding 服务（首次需下载 BGE-M3，约 2GB）
cd data-pipeline
python embedding_server.py

# 3. 星图服务
python starchart_server.py

# 4. Spring Boot
cd backend
./mvnw spring-boot:run

# 5. 前端
cd frontend
npm install
npm run dev
```

### 数据准备（可选）

```bash
cd data-pipeline

# 爬取天文数据
python scraper.py

# 向量化并导入 ChromaDB
python embed.py
```

## 项目结构

```
astronomy-rag/
├── frontend/               # React + TypeScript + Tailwind
│   └── src/
│       ├── App.tsx          # 主布局
│       └── components/
│           ├── ChatPanel.tsx      # 聊天面板
│           ├── MessageBubble.tsx  # 消息渲染（Markdown + 语法高亮）
│           └── StarChartPanel.tsx # 星图控制面板
├── backend/                # Spring Boot 3.3 + LangChain4j
│   └── src/main/java/com/astrorag/
│       ├── controller/ChatController.java  # SSE 流式 API
│       ├── service/RagService.java         # RAG 检索 + LLM 调用
│       └── config/LangChain4jConfig.java   # LLM 配置
├── data-pipeline/          # Python 数据管道
│   ├── starchart_server.py  # 星图渲染服务（Flask + Matplotlib）
│   ├── embedding_server.py  # BGE-M3 嵌入 + 检索服务
│   ├── scraper.py           # 天文数据爬虫
│   ├── embed.py             # 文本向量化导入
│   ├── hyg_v38.csv          # HYG 星表（118k 恒星）
│   └── database_files/      # NGC/IC 深空天体数据
├── chroma_data/            # ChromaDB 持久化数据
├── start.ps1               # 一键启动脚本
└── docker-compose.yml      # ChromaDB Docker 配置
```

## API 端点

| 服务 | 端点 | 说明 |
|------|------|------|
| 后端 | `POST /api/chat` | SSE 流式问答 |
| 后端 | `DELETE /api/chat/{id}` | 清除会话 |
| 嵌入 | `POST /v1/search` | 语义检索 |
| 嵌入 | `POST /v1/embeddings` | 文本向量化 |
| 星图 | `GET /v1/starchart` | 生成星图 PNG |
| 星图 | `GET /health` | 服务状态 |

### 星图 API 参数

```
GET /v1/starchart?ra=83.82&dec=-5.39&fov=18&width=1800&height=2200&mag_limit=8&show_dso=true&style=mobile
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ra` | 83.82 | 赤经（度） |
| `dec` | -5.39 | 赤纬（度） |
| `fov` | 15 | 视场角（度） |
| `mag_limit` | 7.5 | 极限星等 |
| `show_dso` | true | 显示深空天体 |
| `style` | mobile | mobile / atlas |

## 技术栈

- **前端**: React 18, TypeScript, Tailwind CSS, Vite, react-markdown, rehype-highlight
- **后端**: Spring Boot 3.3, LangChain4j 0.35, Java 17
- **AI**: LM Studio (Qwen2.5-7B-Instruct), BGE-M3 Embedding, ChromaDB
- **星图**: Flask, Matplotlib, NumPy, HYG v3.8 星表, OpenNGC 目录
- **数据源**: 梅西耶天体表, NGC/IC 星表, 星座数据, 天文术语库

## License

MIT
