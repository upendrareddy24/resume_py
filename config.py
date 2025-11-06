import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if present
except ImportError:
    pass


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_api_key(key_name: str = "OPENAI_API_KEY") -> str:
    """Get API key from environment, with helpful error message."""
    key = os.getenv(key_name)
    if not key:
        raise ValueError(
            f"{key_name} not found. Set it in environment or create a .env file with:\n"
            f"{key_name}=your_key_here"
        )
    return key


def resolve_from_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    fetch = cfg.get("fetch", {}) if cfg else {}
    mode = fetch.get("mode")  # "free" | "serpapi" | "json" | "url" | "company"
    source = fetch.get("source")
    query = fetch.get("query")
    location = fetch.get("location")
    jobs_path = fetch.get("jobs")
    jobs_url = fetch.get("jobs_url")
    serpapi_key = fetch.get("serpapi_key") or os.getenv("SERPAPI_KEY")
    company_source = fetch.get("company_source")
    

    free_options = cfg.get("free_options", {}) if cfg else {}
    company_options = cfg.get("company_options", {}) if cfg else {}
    run_both = bool(cfg.get("run_both", False)) if cfg else False
    selenium_only = bool(cfg.get("selenium_only", False)) if cfg else False
    companies = cfg.get("companies") or []

    return {
        "resume": cfg.get("resume") if cfg else None,
        "top": int((cfg or {}).get("top", 10)),
        "country": (cfg or {}).get("country", "usa"),
        "fetch_limit": int((cfg or {}).get("fetch_limit", 200)),
        "mode": mode,
        "source": source,
        "query": query,
        "location": location,
        "jobs": jobs_path,
        "jobs_url": jobs_url,
        "serpapi_key": serpapi_key,
        "company_source": company_source,
        "companies": companies,
        "output": (cfg or {}).get("output", {}),
        "free_options": free_options,
        "company_options": company_options,
        "run_both": run_both,
        "selenium_only": selenium_only,
        "selenium_options": (cfg or {}).get("selenium_options", {}),
        "openai": (cfg or {}).get("openai", {}),
    }


