"""
LLM-based experience parser for extracting structured work history from resume text
"""
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

load_dotenv()


class LLMExperienceParser:
    """Parse work experience using LLM for accurate field extraction"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain-openai is required for LLM parsing")
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=api_key,
            temperature=0.1  # Low temperature for consistent parsing
        )
    
    def parse_experiences(self, experience_text: str) -> List[Dict[str, Any]]:
        """
        Parse work experience text into structured format using LLM
        
        Args:
            experience_text: Raw text containing work experience section
            
        Returns:
            List of experience dictionaries with position, company, dates, location, bullets
        """
        prompt_template = """You are an expert resume parser. Extract work experience information from the text below.

For EACH work experience entry, identify:
1. **position**: The job title/role (e.g., "Python MLOps Engineer", "Senior Software Engineer")
2. **company**: The company name (e.g., "Rivian Automotive, LLC", "Robert Bosch")
3. **dates**: The employment period (e.g., "May 2025 – Present", "August 2023 – April 2025")
4. **location**: Work location (e.g., "Remote, USA", "Michigan, USA", "Bangalore, India")
5. **bullets**: List of ALL responsibilities, achievements, and highlights combined (each as separate item)

**IMPORTANT PARSING RULES**:
- Position is the JOB TITLE, not the date
- Company is the ORGANIZATION NAME, not the location
- Dates should be in the format "Month YYYY – Month YYYY" or "Month YYYY – Present"
- Location is the geographical place (city, state, country)
- If dates appear on a separate line, they are DATES not POSITION
- If a line contains a city/state/country, it's a LOCATION not COMPANY
- Extract ALL bullet points from responsibilities, highlights, achievements sections
- Combine responsibilities and highlights into a single bullets array
- Preserve each bullet point exactly as written, in order
- Include metric-driven bullets (e.g., "Reduced X by Y%")

**INPUT TEXT**:
{experience_text}

**OUTPUT FORMAT** (valid JSON array):
Return ONLY a JSON array, no other text. Example:
[
  {{
    "position": "Python MLOps Engineer",
    "company": "Rivian Automotive, LLC",
    "dates": "May 2025 – Present",
    "location": "Remote, USA",
    "bullets": [
      "Designed automation tools for dependency updates and security patching",
      "Developed GraphQL queries for real-time risk assessment",
      "Reduced triage time by 30% through ML-based vulnerability classification",
      "Improved patch prioritization by 40% using AI-driven insights"
    ]
  }},
  {{
    "position": "Software Engineer",
    "company": "Google Inc.",
    "dates": "January 2020 – April 2025",
    "location": "Mountain View, CA",
    "bullets": [
      "Built scalable backend services handling 10M+ requests daily",
      "Optimized database performance, reducing query time by 60%",
      "Led team of 5 engineers in microservices migration",
      "Improved system reliability to 99.99% uptime"
    ]
  }}
]

Output (JSON array only):"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"experience_text": experience_text})
            
            # Clean up response - extract JSON if wrapped in markdown
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()
            
            # Parse JSON
            experiences = json.loads(result)
            
            # Validate and clean
            cleaned = []
            for exp in experiences:
                if not isinstance(exp, dict):
                    continue
                
                # Ensure required fields
                if not exp.get("position") and not exp.get("company"):
                    continue
                
                cleaned_exp = {
                    "position": exp.get("position", "").strip(),
                    "company": exp.get("company", "").strip(),
                    "dates": exp.get("dates", "").strip(),
                    "location": exp.get("location", "").strip(),
                    "bullets": [
                        b.strip() for b in exp.get("bullets", [])
                        if isinstance(b, str) and b.strip()
                    ]
                }
                cleaned.append(cleaned_exp)
            
            return cleaned
            
        except json.JSONDecodeError as e:
            print(f"[llm-parser] JSON parse error: {e}")
            print(f"[llm-parser] Raw response: {result[:500]}")
            return []
        except Exception as e:
            print(f"[llm-parser] Error parsing experiences: {e}")
            return []


def parse_experiences_with_llm(
    experience_text: str,
    openai_api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to parse experiences using LLM
    
    Args:
        experience_text: Raw work experience section text
        openai_api_key: Optional OpenAI API key (uses env var if not provided)
        
    Returns:
        List of structured experience dictionaries
    """
    try:
        parser = LLMExperienceParser(openai_api_key)
        return parser.parse_experiences(experience_text)
    except Exception as e:
        print(f"[llm-parser] Failed to initialize: {e}")
        return []

