"""
FastAPI 主应用

集成了认证、配置管理、SSE推送等功能。
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("FastAPI 应用启动")
    yield
    logger.info("FastAPI 应用关闭")


def create_app(traders: dict = None, trader_registry=None) -> FastAPI:
    """创建 FastAPI 应用实例

    Args:
        traders: 交易器字典 {symbol: trader}
        trader_registry: 交易器注册表（可选）

    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title="GridBNB Trading System API",
        description="网格交易系统后端 API",
        version="v3.2.0",
        lifespan=lifespan
    )

    # 存储依赖到 app.state
    app.state.traders = traders or {}
    app.state.trader_registry = trader_registry

    # ====== 1. 配置 CORS 中间件 ======
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该设置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ====== 2. 健康检查端点（必须在通配符路由之前） ======
    @app.get("/api/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "service": "GridBNB Trading System",
            "version": "v3.2.0"
        }
    
    # Nginx兼容端点（无/api前缀）
    @app.get("/health")
    async def health_check_nginx():
        """健康检查（Nginx兼容）"""
        return {
            "status": "healthy",
            "service": "GridBNB Trading System",
            "version": "v3.2.0"
        }

    # ====== 3. 注册路由 ======
    from src.fastapi_app.routers import (
        auth,
        config,
        history,
        template,
        sse,
        dashboard,
        logs,
        trades,
        metrics,
    )
    from src.api.routes import grid_strategy_routes

    app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    app.include_router(config.router, prefix="/api/configs", tags=["配置管理"])
    app.include_router(history.router, prefix="/api/configs", tags=["配置历史"])
    app.include_router(template.router, prefix="/api/templates", tags=["配置模板"])
    app.include_router(sse.router, prefix="/api/sse", tags=["实时推送"])
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["运行状态"])
    app.include_router(logs.router, prefix="/api/logs", tags=["日志查看"])
    app.include_router(trades.router, prefix="/api/trades", tags=["交易历史"])
    app.include_router(metrics.router, prefix="/api", tags=["系统监控"])
    app.include_router(grid_strategy_routes.router, tags=["网格策略"])

    # Prometheus 公开端点（无需认证）
    app.add_api_route(
        "/metrics",
        metrics.public_metrics_endpoint,
        methods=["GET"],
        include_in_schema=False,
    )

    logger.info("✓ 所有路由已注册（含网格策略）")

    # ====== 4. 配置静态文件服务（前端） ======
    web_dist = Path(__file__).parent.parent.parent / "web" / "dist"
    logger.info("=" * 60)
    logger.info("🔍 前端构建目录检查:")
    logger.info(f"   路径: {web_dist}")
    logger.info(f"   绝对路径: {web_dist.absolute()}")
    logger.info(f"   目录是否存在: {web_dist.exists()}")

    if web_dist.exists():
        # 列出dist目录内容以便调试
        try:
            dist_files = list(web_dist.iterdir())
            logger.info(f"   dist目录内容: {[f.name for f in dist_files[:10]]}")
        except Exception as e:
            logger.warning(f"   无法列出dist目录: {e}")
        
        # 静态资源（CSS, JS, images等）
        assets_dir = web_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static")
            logger.info(f"✓ 静态文件目录已挂载: /assets -> {assets_dir}")
        else:
            logger.warning(f"⚠ assets目录不存在: {assets_dir}")

        # SPA路由：所有非API请求都返回index.html（必须最后注册）
        index_file = web_dist / "index.html"
        if index_file.exists():
            @app.get("/{full_path:path}")
            async def serve_spa(full_path: str):
                """服务前端SPA应用"""
                return FileResponse(index_file)
            logger.info("✓ 前端SPA路由已配置")
            logger.info(f"✓ index.html: {index_file}")
        else:
            logger.error(f"❌ index.html不存在: {index_file}")
            logger.error("   前端将无法正常访问!")
    else:
        logger.error("=" * 60)
        logger.error(f"❌ 前端构建目录不存在: {web_dist}")
        logger.error("=" * 60)
        logger.error("这将导致Web界面无法访问!")
        logger.error("可能原因:")
        logger.error("  1. Docker构建时前端编译失败")
        logger.error("  2. COPY指令路径错误")
        logger.error("  3. 前端构建产物路径不是 'dist'")
        logger.error("")
        logger.error("请检查:")
        logger.error("  - Dockerfile第49行: COPY --from=frontend-builder /build/dist /app/web/dist")
        logger.error("  - 前端构建是否成功: npm run build")
        logger.error("  - 前端构建输出目录配置(vite.config.ts)")
        logger.error("=" * 60)

        # 添加兜底路由，返回友好的错误信息
        @app.get("/")
        async def root_fallback():
            return {
                "error": "Frontend not built",
                "message": "前端构建目录不存在，Web界面无法访问",
                "expected_path": str(web_dist.absolute()),
                "troubleshooting": {
                    "check_docker_build": "检查Docker构建日志中前端编译是否成功",
                    "check_copy_instruction": "验证Dockerfile中COPY指令是否正确",
                    "check_build_output": "确认前端构建输出目录配置"
                }
            }

    logger.info("=" * 60)
    logger.info("FastAPI 应用创建完成")
    logger.info("=" * 60)
    logger.info("API 端点:")
    logger.info("  认证:      POST /api/auth/login")
    logger.info("  配置:      GET  /api/configs")
    logger.info("  网格策略:  GET  /api/grid-strategies")  # 🆕
    logger.info("  模板创建:  POST /api/grid-strategies/templates/{template_name}")  # 🆕
    logger.info("  日志:      GET  /api/logs/list")
    logger.info("  交易:      GET  /api/trades/list")
    logger.info("  SSE:       GET  /api/sse/events")
    logger.info("  健康检查:  GET  /api/health")
    logger.info("  API文档:   GET  /docs")
    logger.info("前端:")
    logger.info("  主页:      GET  /")
    logger.info("=" * 60)

    return app
