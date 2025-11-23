"""FastAPI application entry point"""

import uvicorn

from reversi_backend.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "reversi_backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
