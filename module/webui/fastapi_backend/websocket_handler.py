"""
WebSocket handler for real-time log streaming
"""
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from module.webui.process_manager import ProcessManager
from module.logger import logger

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/logs/{instance_name}")
async def websocket_logs(websocket: WebSocket, instance_name: str):
    """WebSocket endpoint for streaming logs"""
    await manager.connect(websocket)
    
    try:
        alas = ProcessManager.get_manager(instance_name)
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "instance": instance_name
        })
        
        # Keep connection alive and send log updates
        while True:
            try:
                # Check if process is alive
                if hasattr(alas, 'alive') and alas.alive:
                    await websocket.send_json({
                        "type": "status",
                        "alive": True,
                        "state": alas.state
                    })
                
                # Wait a bit before next update
                await asyncio.sleep(1)
                
                # Check if client sent any message (to keep connection alive)
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    if data == "ping":
                        await websocket.send_text("pong")
                except asyncio.TimeoutError:
                    pass
                    
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {instance_name}")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


@router.websocket("/system")
async def websocket_system(websocket: WebSocket):
    """WebSocket endpoint for system-wide updates"""
    await manager.connect(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "System WebSocket connected"
        })
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
            except Exception as e:
                logger.error(f"Error in system WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("System WebSocket disconnected")
    except Exception as e:
        logger.exception(f"System WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
