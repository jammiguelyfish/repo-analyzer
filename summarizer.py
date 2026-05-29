from google import genai
from google.genai import types


_MODEL = "gemini-2.5-flash"

_SYSTEM_INSTRUCTION = (
    "You are an expert software architect. Analyze the provided repository data "
    "and generate a clear, highly structured 'Developer Onboarding Guide'. Include: "
    "1) High-level project purpose, "
    "2) Core Tech Stack used, "
    "3) Key architectural components/files explained, and "
    "4) A 3-sentence summary on how a new developer should get started with this codebase."
)


def generate_repo_summary(repo_data: str) -> str:
    """Generate a Developer Onboarding Guide for a repository using Gemini.

    The Gemini API key is read automatically from the ``GEMINI_API_KEY``
    environment variable by the ``google-genai`` client.

    Args:
        repo_data: A text string containing the repository's file contents
                   (as produced by ``fetch_github_repo_data``).

    Returns:
        The model's markdown-formatted onboarding guide as a plain string.

    Raises:
        google.genai.errors.APIError: On API-level failures (auth, quota, etc.).
    """
    client = genai.Client()

    response = client.models.generate_content(
        model=_MODEL,
        contents=repo_data,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
        ),
    )

    return response.text
