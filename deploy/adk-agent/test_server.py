#!/usr/bin/env python3
"""
Simple FastAPI test server for ADK Agent deployment
"""

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="ADK Agent Test Server")

@app.get("/")
async def root():
    return {"message": "ADK Agent Test Server is running!"}

@app.get("/health/")
async def health():
    return {"status": "healthy", "service": "adk-agent-server"}

@app.get("/test/")
async def test():
    return {"message": "ADK Agent test endpoint working!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)