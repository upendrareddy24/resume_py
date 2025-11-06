"""
Compatibility shim for resume generation aligned with job description.
Delegates to the local LLMResumer implementation within this repository.
"""

from llm_generate_resume import (  # re-export for compatibility
    LLMResumer as LLMResumeJobDescription,
)
