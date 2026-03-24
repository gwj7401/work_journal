#!/bin/bash
# =============================================================
# 工作日志系统 - 宝塔服务器一键部署脚本
# 服务器: Ubuntu 22 + 宝塔面板 + Nginx(已有) + MySQL(已有)
# 运行方式: bash deploy/install.sh
# =============================================================
set -e

APP_DIR="/www/wwwroot/work-journal"
SERVICE_NAME="work-journal"
BACKEND_PORT=8090
FRONTEND_PORT=84

echo "========================================"
echo "  工作日志系统 - 部署开始"
echo "========================================"

# ── Step 1: 安装 Ollama ─────────────────────────────────────
echo ""
echo "[1/6] 安装 Ollama 本地大模型服务..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama 安装完成"
else
    echo "Ollama 已安装，跳过"
fi

# 启动 Ollama 服务
systemctl enable --now ollama || true
sleep 3

# 拉取模型（约4.7GB，首次会较慢）
echo "正在下载 Qwen2.5-7B 模型（约4.7GB，请耐心等待）..."
ollama pull qwen2.5:7b
echo "模型下载完成 ✓"

# ── Step 2: 创建数据库 ──────────────────────────────────────
echo ""
echo "[2/6] 创建数据库..."
mysql -u root -pSzs123456@ -e "
  CREATE DATABASE IF NOT EXISTS work_journal_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
" && echo "数据库 work_journal_db 就绪 ✓"

# ── Step 3: 部署后端 ────────────────────────────────────────
echo ""
echo "[3/6] 部署后端..."
mkdir -p "$APP_DIR/backend"
cp -r backend/. "$APP_DIR/backend/"

# 创建Python虚拟环境
cd "$APP_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Python依赖安装完成 ✓"

# 配置 .env（如果不存在则从示例复制）
if [ ! -f ".env" ]; then
    cp /tmp/work-journal-env .env 2>/dev/null || \
    cat > .env << 'ENV'
APP_SECRET_KEY=please-change-this-to-random-32-chars
APP_ENV=production
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Szs123456@
DB_NAME=work_journal_db
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
JWT_EXPIRE_MINUTES=10080
DEPT_NAME=质量技术部
ENV
    echo ".env 配置文件已创建，请根据需要修改"
fi

deactivate

# ── Step 4: 构建前端 ────────────────────────────────────────
echo ""
echo "[4/6] 构建前端..."
cd /tmp  # 临时目录确保npm可用
cd "$OLDPWD"
# 回到项目根目录
cd /tmp  
# 找到工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

cd frontend
npm install -q
VITE_API_BASE=/api npm run build
mkdir -p "$APP_DIR/dist"
cp -r dist/. "$APP_DIR/dist/"
echo "前端构建完成 ✓"

# ── Step 5: 配置 systemd 服务 ───────────────────────────────
echo ""
echo "[5/6] 配置系统服务..."
cp deploy/work-journal.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME
sleep 2
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "后端服务已启动 ✓ (端口 $BACKEND_PORT)"
else
    echo "⚠ 后端服务启动失败，请检查: journalctl -u $SERVICE_NAME -n 30"
fi

# ── Step 6: 配置 Nginx ──────────────────────────────────────
echo ""
echo "[6/6] 配置 Nginx..."
cp deploy/work-journal.nginx.conf /www/server/panel/vhost/nginx/work-journal.conf
nginx -t && nginx -s reload && echo "Nginx 已重载 ✓"

# ── 完成 ────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "  访问地址: http://117.72.216.227:$FRONTEND_PORT"
echo "  API文档:  http://117.72.216.227:$BACKEND_PORT/docs"
echo ""
echo "  服务管理命令:"
echo "    状态: systemctl status $SERVICE_NAME"
echo "    重启: systemctl restart $SERVICE_NAME"
echo "    日志: journalctl -u $SERVICE_NAME -f"
echo ""
echo "  ⚠ 请在宝塔防火墙开放端口: $FRONTEND_PORT"
echo "========================================"
