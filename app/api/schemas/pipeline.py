from pydantic import BaseModel, Field


# Request Schema


class PipelineRunRequest(BaseModel):
    """Request payload for running the insight pipeline"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "Dubai Luxury Residential Real Estate Market Size And Trends Analysis"
            }
        }
    }

    query: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Search query for insight generation",
        examples=[
            "Dubai Luxury Residential Real Estate Market Size And Trends Analysis",
            "London property market analysis 2026",
            "Abu Dhabi villa rental trends",
        ],
    )
