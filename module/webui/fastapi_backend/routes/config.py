"""
Configuration management API endpoints
"""
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from module.config.utils import alas_instance, alas_template, filepath_args, read_file
from module.webui.fake import load_config, get_config_mod
from module.webui.setting import State
from module.logger import logger

router = APIRouter()


class ConfigValue(BaseModel):
    """Config value update model"""
    path: str
    value: Any


@router.get("/instances")
async def get_instances():
    """Get list of all alas instances"""
    return {
        "instances": alas_instance(),
        "templates": alas_template()
    }


@router.get("/{instance_name}")
async def get_config(instance_name: str):
    """Get configuration for a specific instance"""
    try:
        config_obj = load_config(instance_name)
        config_data = config_obj.read_file(instance_name)
        mod = get_config_mod(instance_name)
        
        # Get menu and args for this instance
        menu = read_file(filepath_args("menu", mod))
        args = read_file(filepath_args("args", mod))
        
        return {
            "name": instance_name,
            "mod": mod,
            "config": config_data,
            "menu": menu,
            "args": args
        }
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=f"Config not found: {instance_name}")


@router.post("/{instance_name}")
async def update_config(instance_name: str, updates: List[ConfigValue]):
    """Update configuration values"""
    try:
        config_obj = load_config(instance_name)
        config_data = config_obj.read_file(instance_name)
        
        # Apply updates
        for update in updates:
            path_parts = update.path.split(".")
            # Navigate to the nested dict and update
            current = config_data
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[path_parts[-1]] = update.value
        
        # Save config
        config_obj.write_file(instance_name, config_data)
        
        logger.info(f"Updated config for {instance_name}")
        return {"status": "success", "message": "Config updated"}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_instance(name: str, copy_from: str = "template-aas"):
    """Create a new alas instance"""
    try:
        # Validate name
        if name in alas_instance():
            raise HTTPException(status_code=400, detail="Instance already exists")
        
        if set(name) & set(".\\/:*?\"'<>|"):
            raise HTTPException(status_code=400, detail="Invalid characters in name")
        
        if name.lower().startswith("template"):
            raise HTTPException(status_code=400, detail="Cannot start with 'template'")
        
        # Copy config
        origin_config = load_config(copy_from).read_file(copy_from)
        State.config_updater.write_file(name, origin_config, get_config_mod(copy_from))
        
        logger.info(f"Created new instance: {name}")
        return {"status": "success", "name": name}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{instance_name}")
async def delete_instance(instance_name: str):
    """Delete an alas instance"""
    try:
        # Add implementation for deleting instance
        # This would need to be added based on how configs are stored
        raise HTTPException(status_code=501, detail="Delete not implemented")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
