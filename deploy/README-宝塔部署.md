# 宝塔面板部署指南

## 服务器环境
- Ubuntu 22.04 LTS · 4核16GB
- 宝塔面板（Nginx 1.24 / MySQL 8.0 / Python环境管理器，已有）
- **无需Docker**，全部原生部署

## 整体架构

```
浏览器 :84
  └─ Nginx（宝塔已有）
       ├─ / → 前端静态文件 /www/wwwroot/work-journal/dist/
       └─ /api/ → 内部转发 → FastAPI :8090
                                └─ Ollama :11434 (本地Qwen2.5-7B)
                                └─ MySQL :3306 (宝塔已有)
```

## 一键部署

```bash
# 1. 上传代码到服务器（本地执行）
scp -r f:/work-journal root@117.72.216.227:/tmp/work-journal-src

# 2. SSH登录服务器
ssh root@117.72.216.227

# 3. 移动到标准目录，执行部署
cp -r /tmp/work-journal-src /www/wwwroot/work-journal
cd /www/wwwroot/work-journal
bash deploy/install.sh
```

## 部署脚本做了什么

| 步骤 | 内容 |
|------|------|
| 1 | 安装 Ollama，拉取 Qwen2.5-7B（约4.7GB） |
| 2 | 创建 `work_journal_db` 数据库 |
| 3 | 后端虚拟环境 + pip安装依赖 |
| 4 | 前端 `npm build` 生成静态文件 |
| 5 | 注册 systemd 服务，开机自启 |
| 6 | 复制 Nginx 虚拟主机配置，重载 |

## 部署后配置

### 1. 宝塔防火墙开放端口 84
> 宝塔面板 → 安全 → 防火墙 → 添加端口规则 → 84

### 2. 修改 .env 生产配置
```bash
nano /www/wwwroot/work-journal/backend/.env
# 修改 APP_SECRET_KEY 为随机字符串
# 修改 DEPT_NAME 为实际部门名称
```

### 3. 重启后端使配置生效
```bash
systemctl restart work-journal
```

## 常用命令

```bash
# 查看服务状态
systemctl status work-journal

# 查看实时日志
journalctl -u work-journal -f

# 重启后端
systemctl restart work-journal

# 查看Ollama状态
systemctl status ollama
ollama list         # 查看已下载模型

# Nginx重载
nginx -s reload
```

## 更新部署

```bash
cd /www/wwwroot/work-journal

# 更新后端
cp -r /tmp/新代码/backend/. backend/
source backend/venv/bin/activate
pip install -r backend/requirements.txt
systemctl restart work-journal

# 更新前端
cd frontend && npm run build
cp -r dist/. /www/wwwroot/work-journal/dist/
```

## 访问地址

| 地址 | 说明 |
|------|------|
| http://117.72.216.227:84 | 前端应用 |
| http://127.0.0.1:8090/docs | API文档（仅内网） |
