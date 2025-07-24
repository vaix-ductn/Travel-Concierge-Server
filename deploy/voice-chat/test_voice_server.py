#!/usr/bin/env python3
"""
Simple test server for Voice Chat service
"""

import os
import asyncio
import websockets
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Voice Chat Test Server")

@app.get("/")
async def root():
    return {"message": "Voice Chat Test Server is running!"}

@app.get("/health/")
async def health():
    return {"status": "healthy", "service": "voice-chat-server"}

@app.get("/test/")
async def test():
    return {"message": "Voice Chat test endpoint working!"}

# Simple WebSocket echo server
async def echo(websocket, path):
    async for message in websocket:
        await websocket.send(f"Echo: {message}")

async def websocket_server():
    port = int(os.environ.get('PORT', 8003))
    async with websockets.serve(echo, "0.0.0.0", port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)