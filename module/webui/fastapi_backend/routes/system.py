"""
System management API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from module.webui.updater import updater
from module.webui.setting import State
from module.webui import lang
from module.logger import logger

router = APIRouter()


class LanguageSetting(BaseModel):
    """Language setting model"""
    language: str


class ThemeSetting(BaseModel):
    """Theme setting model"""
    theme: str


@router.get("/info")
async def get_system_info():
    """Get system information"""
    return {
        "version": "1.0.0",
        "language": lang.LANG,
        "theme": State.deploy_config.Theme,
        "deploy_config": {
            "host": State.deploy_config.WebuiHost,
            "port": State.deploy_config.WebuiPort,
            "password_enabled": State.deploy_config.Password is not None,
            "remote_access": State.deploy_config.EnableRemoteAccess,
        }
    }


@router.post("/language")
async def set_language(setting: LanguageSetting):
    """Set system language"""
    try:
        lang.set_language(setting.language)
        State.deploy_config.Language = setting.language
        return {"status": "success", "language": setting.language}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/theme")
async def set_theme(setting: ThemeSetting):
    """Set system theme"""
    try:
        State.deploy_config.Theme = setting.theme
        State.theme = setting.theme
        return {"status": "success", "theme": setting.theme}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/update/status")
async def get_update_status():
    """Get update status"""
    try:
        return {
            "state": updater.state,
            "branch": updater.Branch,
            "local_commit": updater.get_commit(short_sha1=True),
            "upstream_commit": updater.get_commit(f"origin/{updater.Branch}", short_sha1=True)
        }
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/check")
async def check_update():
    """Check for updates"""
    try:
        updater.check_update()
        return {"status": "success", "message": "Checking for updates"}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/run")
async def run_update():
    """Run update"""
    try:
        updater.run_update()
        return {"status": "success", "message": "Update started"}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_system():
    """Restart the system"""
    try:
        if State.restart_event is not None:
            State.restart_event.set()
            return {"status": "success", "message": "Restart initiated"}
        else:
            raise HTTPException(status_code=400, detail="Restart not enabled")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
