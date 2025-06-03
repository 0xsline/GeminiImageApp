#!/bin/bash

# Gemini Image App Docker 启动脚本

echo "========================================="
echo "   Gemini Image App - Docker 启动脚本"
echo "========================================="
echo ""

# 检查 Docker 是否运行
echo "[1/4] 检查 Docker 状态..."
if ! docker version >/dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi
echo "✅ Docker 运行正常"

# 检查 .env 文件
echo ""
echo "[2/4] 检查环境变量..."
if [ ! -f ../.env ]; then
    echo "❌ 未找到 .env 文件，请在项目根目录创建"
    echo "示例内容："
    echo "GOOGLE_API_KEY=your_google_api_key"
    echo "GEMINI_API_KEY=your_gemini_api_key"
    echo ""
    exit 1
fi
echo "✅ 环境变量文件存在"

# 创建必要的目录
echo ""
echo "[3/4] 创建必要的目录..."
mkdir -p volumes/backend_cache
mkdir -p volumes/backend_logs
mkdir -p volumes/nginx_logs
mkdir -p ../storage/uploads
mkdir -p ../storage/generated
mkdir -p ../storage/models

# 设置目录权限
chmod -R 755 ../storage/
chmod -R 755 volumes/
echo "✅ 目录创建完成"

# 构建并启动服务
echo ""
echo "[4/4] 构建和启动服务..."
echo "正在停止现有容器..."
docker-compose down --remove-orphans 2>/dev/null

echo "正在构建镜像，这可能需要较长时间，请耐心等待..."
docker-compose up --build -d

if [ $? -ne 0 ]; then
    echo "❌ 服务启动失败"
    echo "查看详细错误信息："
    docker-compose logs
    exit 1
fi

echo "✅ 服务启动成功"

echo ""
echo "========================================="
echo "           🎉 启动完成！"
echo "========================================="
echo ""
echo "📱 前端应用: http://localhost:3000"
echo "🔧 后端API:  http://localhost:5005"
echo "🌐 Nginx代理: http://localhost"
echo ""
echo "🔌 端口映射详情："
echo "   80:80   -> Nginx (主入口)"
echo "   3000:80 -> 前端应用"
echo "   5005:5005 -> 后端API"
echo ""
echo "📁 存储目录："
echo "   主机: ../storage/"
echo "   容器: /storage/ 和 /var/www/storage/"
echo ""
echo "📊 查看状态: docker-compose ps"
echo "📋 查看日志: docker-compose logs -f"
echo "🛑 停止服务: docker-compose down"
echo ""

echo "等待服务完全启动..."
sleep 15

echo "检查服务状态..."
docker-compose ps

echo ""
echo "如果服务未正常启动，请查看日志："
echo "docker-compose logs"
echo ""
