# ABOUTME: Wrapper service for hikugen extraction library.
# ABOUTME: Handles schema translation and hikugen API calls.

from hikugen import HikuExtractor

from hikuweb.services.schema_translator import json_schema_to_pydantic


class ExtractionService:
    """Service for extracting structured data from web pages using hikugen.

    This service wraps the hikugen library, providing a clean interface
    for converting JSON schemas to Pydantic models and performing extractions.

    Attributes:
        extractor: HikuExtractor instance configured with API key.
    """

    def __init__(self, openrouter_api_key: str):
        """Initialize extraction service.

        Args:
            openrouter_api_key: OpenRouter API key for LLM inference.
        """
        self.extractor = HikuExtractor(api_key=openrouter_api_key)

    def extract(self, url: str, schema: dict) -> dict:
        """Extract structured data from URL using JSON schema.

        Args:
            url: Web page URL to extract from.
            schema: JSON Schema definition for extraction.

        Returns:
            dict: Extracted data matching the provided schema.

        Raises:
            Exception: If extraction fails (network, parsing, LLM errors).
        """
        # Convert JSON schema to Pydantic model
        model = json_schema_to_pydantic(schema, model_name="ExtractionSchema")

        # Perform extraction
        result = self.extractor.extract(url, model)

        # Convert Pydantic model back to dict
        return result.model_dump()
