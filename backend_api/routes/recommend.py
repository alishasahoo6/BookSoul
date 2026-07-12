from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from booksoul.pipeline.recommender import get_semantic_recommendations
from booksoul.common.utils import setup_logger

logger = setup_logger("RecommendRoute")

router = APIRouter()


class RecommendationRequest(BaseModel):
    """
    Request schema for book recommendations.
    """
    query: str = Field(..., description="Natural language search query (e.g. title, mood, trope)")
    n_results: int = Field(5, description="Number of recommendation results to return", ge=1, le=50)


class BookDNAModel(BaseModel):
    """
    Detailed DNA attributes score schema (1-10 scale).
    """
    emotional_depth: int = Field(..., ge=1, le=10)
    comfort: int = Field(..., ge=1, le=10)
    humor: int = Field(..., ge=1, le=10)
    angst: int = Field(..., ge=1, le=10)
    spice: int = Field(..., ge=1, le=10)
    character_growth: int = Field(..., ge=1, le=10)
    pacing: int = Field(..., ge=1, le=10)
    atmosphere: str = Field(..., description="Semantic description of the atmosphere")


class BookSoulModel(BaseModel):
    """
    Comprehensive BookSoul profile of the book.
    """
    themes: List[str] = Field(default_factory=list)
    tropes: List[str] = Field(default_factory=list)
    emotional_tone: str
    writing_style: str
    pacing: str
    character_dynamics: str
    reader_vibe: str
    emotional_arc: str
    dna: BookDNAModel
    is_fallback: bool
    is_antigravity: bool


class BookRecommendation(BaseModel):
    """
    Single book recommendation result.
    """
    id: Optional[str] = Field(None, description="Google Books or OpenLibrary ID")
    title: str = Field(..., description="Title of the book")
    authors: Optional[str] = Field(None, description="Comma-separated authors of the book")
    description: Optional[str] = Field(None, description="Summary or description of the book")
    cover_image: Optional[str] = Field(None, description="URL of the cover image")
    subject: Optional[str] = Field(None, description="Comma-separated book categories/subjects")
    quality_score: float = Field(..., description="Calculated internal quality score")
    soul: BookSoulModel = Field(..., description="BookSoul profile")
    distance_score: float = Field(..., description="Raw vector distance score")
    soul_match: float = Field(..., description="Soul alignment score")
    hybrid_score: float = Field(..., description="Final ranked hybrid score")
    relevance_confidence: float = Field(..., description="Confidence score from relevance filter")
    relevance_reason: str = Field(..., description="Relevance judgment rationale")
    match_reasons: List[str] = Field(default_factory=list, description="User-friendly match explanations")


class RecommendationResponse(BaseModel):
    """
    Response schema containing a list of book recommendations.
    """
    results: List[BookRecommendation] = Field(..., description="List of recommended books matching the query")


@router.post("/", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """
    Retrieve semantic book recommendations based on the input query.
    
    Validates input query against request schema, queries the internal recommendation
    pipeline, and guarantees the output matches the frozen response schema.
    """
    logger.info(
    "Received recommendation request: query=%s n_results=%d",
    request.query,
    request.n_results,
    )   
    try:
        results = get_semantic_recommendations(
            request.query,
            request.n_results
        )
        if not isinstance(results, list):
            logger.error(f"Recommender returned invalid data type: {type(results)}")
            raise HTTPException(
                status_code=500,
                detail="Invalid internal recommendation output format."
            )
            
        logger.info(
            "Recommendation search completed successfully with %d results",
            len(results),
        )
        return RecommendationResponse(results=results)
        
    except HTTPException as he:
        raise he
    except Exception:
        logger.exception("Error handling recommendation request")
        raise HTTPException(
            status_code=500,
            detail="An error occurred inside the recommendation engine."
        )
