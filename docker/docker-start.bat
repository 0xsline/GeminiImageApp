@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Gemini Image App - Docker Startup
echo ========================================
echo.

REM Check Docker status
echo [1/4] Checking Docker status...
docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running, please start Docker Desktop
    pause
    exit /b 1
)
echo OK: Docker is running

REM Check environment file
echo.
echo [2/4] Checking environment file...
if not exist "../.env" (
    echo ERROR: .env file not found in project root
    echo Please create .env file with:
    echo GOOGLE_API_KEY=your_google_api_key
    echo GEMINI_API_KEY=your_gemini_api_key
    echo.
    pause
    exit /b 1
)
echo OK: Environment file exists

REM Copy .env file to docker directory for docker-compose
copy "..\\.env" ".env" >nul 2>&1
echo OK: Environment file copied to docker directory

REM Create necessary directories
echo.
echo [3/4] Creating necessary directories...
if not exist "volumes" mkdir "volumes"
if not exist "volumes\backend_cache" mkdir "volumes\backend_cache"
if not exist "volumes\backend_logs" mkdir "volumes\backend_logs"
if not exist "volumes\nginx_logs" mkdir "volumes\nginx_logs"
if not exist "..\storage\uploads" mkdir "..\storage\uploads"
if not exist "..\storage\generated" mkdir "..\storage\generated"
if not exist "..\storage\models" mkdir "..\storage\models"
echo OK: Directories created

REM Build and start services
echo.
echo [4/4] Building and starting services...
echo Stopping existing containers...
docker-compose down --remove-orphans 2>nul

echo Building images, this may take a while, please wait...
docker-compose up --build -d

if errorlevel 1 (
    echo ERROR: Service startup failed
    echo Check detailed error information:
    docker-compose logs
    pause
    exit /b 1
)

echo OK: Services started successfully

echo.
echo ========================================
echo           Startup Complete!
echo ========================================
echo.
echo Frontend App: http://localhost:3000
echo Backend API:  http://localhost:5005
echo Nginx Proxy:  http://localhost
echo.
echo Port Mapping Details:
echo    80:80   -^> Nginx (Main Entry)
echo    3000:80 -^> Frontend App
echo    5005:5005 -^> Backend API
echo.
echo Storage Directories:
echo    Host: ..\storage\
echo    Container: /storage/ and /var/www/storage/
echo.
echo Check status: docker-compose ps
echo View logs:    docker-compose logs -f
echo Stop service: docker-compose down
echo.

echo Waiting for services to fully start...
timeout /t 15 /nobreak >nul

echo Checking service status...
docker-compose ps

echo.
echo Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
pause
