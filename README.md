# Work Journal · 工作日志系统

每日工作日志记录 + AI月度自动总结，支持PC浏览器和手机PWA，使用本地Ollama大模型生成公文格式月度总结。

## 技术栈
- **后端**: Python · FastAPI
- **前端**: Vue 3 + Vite + Element Plus
- **数据库**: MySQL 8.0
- **AI**: Ollama + Qwen2.5-7B（本地离线）
- **部署**: Docker Compose

## 快速启动（开发环境）

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env   # 配置数据库等
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 部署（生产）

```bash
cp .env.example .env   # 修改生产配置
docker-compose up -d
```

首次启动会自动下载 Qwen2.5-7B 模型（约4.7GB），请确保服务器有足够存储空间。

## 项目结构

```
work-journal/
├── backend/          FastAPI 后端
├── frontend/         Vue 3 前端
├── docker-compose.yml
├── nginx.conf
└── .env.example
```
