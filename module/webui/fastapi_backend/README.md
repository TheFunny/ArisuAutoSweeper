# FastAPI Backend for ArisuAutoSweeper

This is the new FastAPI-based backend for the ArisuAutoSweeper WebUI, providing a modern REST API architecture while maintaining the same visual style as the original PyWebIO interface.

## Architecture

### Backend (FastAPI)
- **main.py**: Main FastAPI application with route registration and lifecycle management
- **routes/**: API endpoint modules
  - `config.py`: Configuration management endpoints
  - `process.py`: Process control endpoints (start/stop/restart)
  - `system.py`: System settings and update management
- **websocket_handler.py**: WebSocket endpoints for real-time log streaming
- **templates/**: Jinja2 HTML templates
- **static/**: Static assets (CSS, JS)

### Frontend
- Simple HTML/CSS/JS frontend that reuses existing CSS from `assets/gui/css/`
- Bootstrap 5 for base styling
- Native JavaScript for API interactions
- WebSocket for real-time updates

## Usage

### Starting the FastAPI Backend

```bash
# Use the new FastAPI backend
python gui_fastapi.py

# Or with custom host/port
python gui_fastapi.py --host 0.0.0.0 --port 23467
```

### API Endpoints

#### Configuration Management
- `GET /api/config/instances` - Get list of all instances
- `GET /api/config/{instance_name}` - Get configuration for an instance
- `POST /api/config/{instance_name}` - Update configuration
- `POST /api/config/create` - Create new instance
- `DELETE /api/config/{instance_name}` - Delete instance

#### Process Management
- `GET /api/process/` - Get all processes status
- `GET /api/process/{instance_name}/status` - Get process status
- `POST /api/process/{instance_name}/start` - Start process
- `POST /api/process/{instance_name}/stop` - Stop process
- `POST /api/process/{instance_name}/restart` - Restart process

#### System Management
- `GET /api/system/info` - Get system information
- `POST /api/system/language` - Set language
- `POST /api/system/theme` - Set theme
- `GET /api/system/update/status` - Get update status
- `POST /api/system/update/check` - Check for updates
- `POST /api/system/update/run` - Run update
- `POST /api/system/restart` - Restart system

#### WebSocket
- `WS /ws/logs/{instance_name}` - Real-time log streaming for an instance
- `WS /ws/system` - System-wide real-time updates

## Comparison with PyWebIO Backend

### PyWebIO Backend (Original)
- **Location**: `module/webui/app.py`
- **Entry Point**: `gui.py`
- **Architecture**: Monolithic, UI generated from Python code
- **Advantages**: Simpler development, no frontend/backend separation
- **Disadvantages**: Tightly coupled, harder to extend, limited API access

### FastAPI Backend (New)
- **Location**: `module/webui/fastapi_backend/`
- **Entry Point**: `gui_fastapi.py`
- **Architecture**: Separated backend (REST API) and frontend
- **Advantages**: 
  - Modern REST API
  - Can be used by multiple clients (web, mobile, CLI)
  - Better separation of concerns
  - Easier to test and extend
  - Real-time updates via WebSocket
- **Disadvantages**: More code to maintain, requires frontend development

## Migration Path

Both backends can coexist:
- Use `python gui.py` for the original PyWebIO interface
- Use `python gui_fastapi.py` for the new FastAPI interface

Users can gradually migrate from PyWebIO to FastAPI as features are completed.

## Development

### Adding New Endpoints

1. Create or modify files in `routes/`
2. Add Pydantic models for request/response validation
3. Register the router in `main.py`
4. Update the frontend to use the new endpoints

### Reusing Existing CSS

The frontend reuses CSS from `assets/gui/css/`:
- `alas.css` - Base styles
- `alas-pc.css` - Desktop styles
- `light-alas.css` / `dark-alas.css` - Theme styles

## Testing

```bash
# Test that the app loads
python -c "from module.webui.fastapi_backend.main import app; print('OK')"

# Start the server
python gui_fastapi.py

# Access the interface
# Open browser to http://localhost:23467
```

## Future Enhancements

- [ ] Complete configuration editor UI
- [ ] Enhanced log viewer with filtering
- [ ] Scheduler visualization
- [ ] Task queue management
- [ ] Mobile-responsive design improvements
- [ ] Authentication/authorization
- [ ] API documentation (Swagger UI at /docs)
