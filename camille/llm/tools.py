from langchain_core.pydantic_v1 import BaseModel, Field


class RequestsGetInput(BaseModel):
    """Input for the WikipediaQuery tool."""

    url: str = Field(description="url to make a GET request to")
