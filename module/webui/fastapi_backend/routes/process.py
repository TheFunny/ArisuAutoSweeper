"""
Process management API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from module.webui.process_manager import ProcessManager
from module.webui.updater import updater
from module.logger import logger

router = APIRouter()


class ProcessCommand(BaseModel):
    """Process command model"""
    task: Optional[str] = None


@router.get("/{instance_name}/status")
async def get_process_status(instance_name: str):
    """Get process status"""
    try:
        alas = ProcessManager.get_manager(instance_name)
        return {
            "name": instance_name,
            "alive": alas.alive,
            "state": alas.state,
            "config_name": alas.config_name
        }
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=f"Process not found: {instance_name}")


@router.post("/{instance_name}/start")
async def start_process(instance_name: str, command: ProcessCommand = ProcessCommand()):
    """Start a process"""
    try:
        alas = ProcessManager.get_manager(instance_name)
        alas.start(command.task, updater.event if command.task is None else None)
        logger.info(f"Started process: {instance_name}")
        return {"status": "success", "message": f"Started {instance_name}"}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_name}/stop")
async def stop_process(instance_name: str):
    """Stop a process"""
    try:
        alas = ProcessManager.get_manager(instance_name)
        alas.stop()
        logger.info(f"Stopped process: {instance_name}")
        return {"status": "success", "message": f"Stopped {instance_name}"}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_name}/restart")
async def restart_process(instance_name: str):
    """Restart a process"""
    try:
        alas = ProcessManager.get_manager(instance_name)
        alas.stop()
        alas.start(None, updater.event)
        logger.info(f"Restarted process: {instance_name}")
        return {"status": "success", "message": f"Restarted {instance_name}"}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_all_processes():
    """Get status of all processes"""
    try:
        processes = []
        for name, alas in ProcessManager._processes.items():
            processes.append({
                "name": name,
                "alive": alas.alive,
                "state": alas.state
            })
        return {"processes": processes}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
