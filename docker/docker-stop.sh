#!/bin/bash

echo "========================================="
echo "   Gemini Image App - 停止服务脚本"
echo "========================================="
echo ""

echo "正在停止所有Docker服务..."
docker-compose down --remove-orphans

echo ""
echo "清理未使用的Docker资源..."
docker system prune -f

echo ""
echo "✅ 所有服务已停止并清理完成"
echo ""
