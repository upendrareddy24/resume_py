"""
Compatibility shim for cover letter generation.
Delegates to the local adapter implementation within this repository.
"""

from llm_cover_letter_adapter import (  # re-export for compatibility
    LLMCoverLetterJobDescription as LLMCoverLetterJobDescription,
)
