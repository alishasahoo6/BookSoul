import logging
from typing import Dict
from fastapi import FastAPI
from backend_api.routes.recommend import router as recommend_router
from booksoul.common.utils import setup_logger

logger = setup_logger("API_Main")

app = FastAPI(
    title="BookSoul API",
    description="Production-grade API for BookSoul recommendation engine.",
    version="1.0.0"
)

app.include_router(
    recommend_router,
    prefix="/recommend",
    tags=["Recommendations"],
)


@app.get("/")
def root() -> Dict[str, str]:
    """
    Root endpoint to verify that the BookSoul backend API is running.
    """
    logger.info("Health check endpoint pinged.")
    return {
        "status": "BookSoul Backend Running 🚀"
    }