#!/bin/bash
set -e

echo "=== Money Radar — 部署脚本 ==="
echo ""

# 配置
RSSHUB_PORT=1200
BACKEND_PORT=8000
FRONTEND_PORT=3000
PG_PASSWORD=${PG_PASSWORD:-"Mr2026RadarPg!"}
LICENSE_SECRET=${LICENSE_SECRET:-"mr-secret-key-$(date +%s)"}

# 1. 克隆 feeds.fun
if [ ! -d "feeds.fun" ]; then
    echo "[1/7] 克隆 feeds.fun..."
    git clone --depth 1 https://github.com/Tiendil/feeds.fun.git
else
    echo "[1/7] feeds.fun 已存在，跳过"
fi

cd feeds.fun

# 2. 复制配置文件
echo "[2/7] 配置文件..."
mkdir -p .configs
cp ../config/tag_processors.toml .configs/
cp ../docker-compose.override.yml . 2>/dev/null || true

# 3. 创建 .env
if [ ! -f ".env" ]; then
    echo "[3/7] 创建 .env..."
    cat > .env << EOF
# Money Radar Configuration
FFUN_ENVIRONMENT=local
FFUN_ENABLE_API_SPA=True
FFUN_ENABLE_API_ROOT=True

FFUN_POSTGRESQL__HOST=postgresql
FFUN_POSTGRESQL__USER=ffun
FFUN_POSTGRESQL__PASSWORD=${PG_PASSWORD}
FFUN_POSTGRESQL__DATABASE=ffun

FFUN_USER_SETTINGS_SECRET_KEY=$(python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())" 2>/dev/null || echo "change-me-to-32-bytes-base64!")

FFUN_AUTH_FORCE_EXTERNAL_USER_ID=dev-user
FFUN_AUTH_FORCE_EXTERNAL_IDENTITY_PROVIDER_ID=single_user

FFUN_OPENAI_API_ENTRY_POINT=https://api.deepseek.com/v1
FFUN_OPENAI_API_KEY=sk-your-deepseek-api-key-here

FFUN_LIBRARIAN_TAG_PROCESSORS_CONFIG=.configs/tag_processors.toml

LICENSE_SECRET_KEY=${LICENSE_SECRET}
LICENSE_DISABLED=true
EOF
    echo "  .env 已创建，请编辑 DeepSeek API Key"
else
    echo "[3/7] .env 已存在，跳过"
fi

# 4. 创建 docker-compose
echo "[4/7] 创建 docker-compose..."
cat > docker-compose.prod.yml << 'EOF'
services:
  postgresql:
    image: postgres:15-alpine
    restart: always
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ffun
      POSTGRES_USER: ffun
      POSTGRES_PASSWORD: ${FFUN_POSTGRESQL__PASSWORD}
    networks:
      - ffun_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ffun"]
      interval: 5s
      timeout: 5s
      retries: 5

  rsshub:
    image: diygod/rsshub:latest
    restart: always
    ports:
      - "1200:1200"
    environment:
      NODE_ENV: production
      CACHE_TYPE: memory
    networks:
      - ffun_network

  backend:
    build:
      context: .
      dockerfile: docker/prod/backend/Dockerfile
    restart: always
    working_dir: /usr/local/lib/python3.13/site-packages/ffun
    depends_on:
      postgresql:
        condition: service_healthy
    env_file: .env
    environment:
      FFUN_POSTGRESQL__HOST: postgresql
      FFUN_POSTGRESQL__DATABASE: ffun
      FFUN_POSTGRESQL__USER: ffun
      FFUN_ENVIRONMENT: local
      LICENSE_DISABLED: "true"
    volumes:
      - ./.configs:/usr/local/lib/python3.13/site-packages/ffun/.configs:ro
    networks:
      - ffun_network
    ports:
      - "8000:8000"
    entrypoint: ["uvicorn", "ffun.application.application:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

  frontend:
    image: nginx:alpine
    restart: always
    volumes:
      - ../frontend/index.html:/usr/share/nginx/html/index.html:ro
      - ../frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - ffun_network
    ports:
      - "3000:3000"

volumes:
  pgdata:

networks:
  ffun_network:
    driver: bridge
EOF

# 5. 创建 nginx 配置
echo "[5/7] 创建 nginx 配置..."
cat > ../frontend/nginx.conf << 'EOF'
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /spa/api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-License-Code $http_x_license_code;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-License-Code $http_x_license_code;
    }
}
EOF

# 6. 构建
echo "[6/7] 构建 Docker 镜像..."
docker compose -f docker-compose.prod.yml build backend

# 7. 启动
echo "[7/7] 启动服务..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "=== 部署完成 ==="
echo ""
echo "服务地址："
echo "  前端: http://localhost:${FRONTEND_PORT}"
echo "  后端: http://localhost:${BACKEND_PORT}"
echo "  RSSHub: http://localhost:${RSSHUB_PORT}"
echo ""
echo "下一步："
echo "  1. 编辑 feeds.fun/.env，设置 DeepSeek API Key"
echo "  2. 生成授权码: python3 ../backend/license_gen.py --days 30 --level pro"
echo "  3. 访问前端，输入授权码"
echo ""
echo "授权码密钥: ${LICENSE_SECRET}"
