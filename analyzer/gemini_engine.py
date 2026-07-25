"""
Code Whisperer - Gemini AI Engine
Handles communication with Google's Gemini API.
"""

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class GeminiEngine:
    """Wrapper around Google Gemini API with retry logic and error handling."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required for GeminiEngine")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 4096,
            }
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call_api(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    def explain_code(self, code: str, parsed_summary: str) -> str:
        prompt = f"""You are a senior software architect mentoring a junior developer.
The developer inherited an AI-generated codebase and needs to understand it.

PARSED STRUCTURE:
{parsed_summary}

FULL SOURCE CODE:
```python
{code[:15000]}