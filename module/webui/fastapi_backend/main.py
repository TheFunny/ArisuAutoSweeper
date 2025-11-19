"""
FastAPI main application
"""
import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from module.webui.fastapi_backend.routes import config, process, system
from module.webui.fastapi_backend.websocket_handler import router as ws_router
from module.webui.setting import State
from module.webui import lang
from module.webui.updater import updater
from module.webui.process_manager import ProcessManager
from module.logger import logger

# Get base directory
BASE_DIR = Path(__file__).resolve().parent

# Create FastAPI app
app = FastAPI(
    title="ArisuAutoSweeper",
    description="FastAPI backend for ArisuAutoSweeper WebUI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Mount CSS assets from the main assets folder
assets_path = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "gui"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

# Include API routers
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("FastAPI WebUI starting up")
    State.init()
    lang.reload()
    updater.event = State.manager.Event()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("FastAPI WebUI shutting down")
    for alas in ProcessManager._processes.values():
        alas.stop()
    State.clearup()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main page"""
    from module.config.utils import alas_instance
    
    context = {
        "request": request,
        "title": "ArisuAutoSweeper",
        "instances": alas_instance(),
        "theme": State.deploy_config.Theme,
        "language": lang.LANG
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0"
    }


def create_app():
    """Factory function to create the FastAPI app"""
    return app
