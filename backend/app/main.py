from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="LeadFlow AI",
    description="Autonomous AI Sales Lead Nurturing Platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.APP_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO for real-time updates
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[settings.APP_URL, "http://localhost:3000", "http://localhost:5173"],
)
socket_app = socketio.ASGIApp(sio, app, socketio_path="/ws/socket.io")

@sio.event
async def connect(sid, environ):
    pass


@sio.event
async def disconnect(sid):
    pass


# Include API routes
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "leadflow-ai"}


# Export for uvicorn and socket notifications
def get_sio():
    return sio


# Main ASGI app with socket.io
app_with_sio = socket_app
