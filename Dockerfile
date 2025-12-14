# ============================================
# 第一阶段：构建前端
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# 复制前端package文件
COPY web/package*.json ./

# 安装前端依赖
RUN npm ci

# 复制前端源代码
COPY web/ ./

# 构建前端
RUN npm run build

# ============================================
# 第二阶段：Python应用
# ============================================
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 从第一阶段复制构建好的前端
COPY --from=frontend-builder /build/dist /app/web/dist

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 复制并设置启动脚本权限
COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 暴露端口
EXPOSE 58181

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:58181/api/health || exit 1

# 使用启动脚本
ENTRYPOINT ["docker-entrypoint.sh"]
