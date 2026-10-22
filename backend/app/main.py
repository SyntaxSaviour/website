from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router

app = FastAPI(title="BrainMint Software API", version="1.0.0")

app.include_router(api_router, prefix="/api/v1")

# Standard 404 handler for unknown routes (SCR-018)
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"The requested resource '{request.url.path}' does not exist on this server.",
                "details": None
            }
        }
    )