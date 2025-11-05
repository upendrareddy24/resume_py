import argparse
import json
import os
import re
import sys
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import Any

import requests
from rapidfuzz import fuzz
try:
    # centralize config helpers
    from config import load_json, resolve_from_config  # type: ignore
except Exception:
    load_json = None  # will be checked at runtime
    resolve_from_config = None

try:
    from resume_builder import tailor_resume_for_job, build_tailored_resume_doc  # type: ignore
    RESUME_BUILDER_AVAILABLE = True
except Exception:
    RESUME_BUILDER_AVAILABLE = False
try:
    from cover_letter import CoverLetterBuilder  # local module
    COVER_LETTER_AVAILABLE = True
except Exception:
    COVER_LETTER_AVAILABLE = False

# Optional Selenium imports (lazy)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False

_non_alnum = re.compile(r"[^a-z0-9+#.\-\s]")


def read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def tokenize_for_fuzz(text: str) -> str:
    text = (text or "").lower()
    text = _non_alnum.sub(" ", text)
    return " ".join(t for t in text.split() if len(t) > 1)


# Basic tech/role keywords to mine from resume text when no explicit query is provided
RESUME_KEYWORDS = [
    "python","java","c++","c#","javascript","typescript","go","rust","sql","nosql",
    "ml","ai","machine","learning","deep","pytorch","tensorflow","keras","sklearn","scikit",
    "data","engineer","scientist","analytics","pipeline","etl","airflow","dbt",
    "aws","azure","gcp","lambda","sagemaker","cloudformation","dynamodb","s3","ec2","kinesis",
    "docker","kubernetes","terraform","jenkins","ansible","gitlab","github","bitbucket",
    "graphql","rest","api","django","flask","fastapi","react","nextjs","node","spark","hadoop"
]


def build_query_from_resume(resume_text: str, max_terms: int = 12) -> str:
    tokens = set(tokenize_for_fuzz(resume_text).split())
    matched = [kw for kw in RESUME_KEYWORDS if kw in tokens]
    if not matched:
        # fallback to a few generic role terms
        matched = [t for t in tokens if len(t) > 3][:max_terms]
    return "|".join(matched[:max_terms])


## cover-letter free text generation now lives in CoverLetterBuilder.compose_concise_text


def _normalize_country_name(country: str | None) -> tuple[str, list[str]]:
    if not country:
        return "", []
    c = country.strip().lower()
    if c in {"usa", "us", "u.s.", "united states", "united states of america"}:
        return "usa", ["united states", "united states of america", "usa", "us", "u.s."]
    return c, [c]


def _matches_country(location_value: str | None, country: str | None) -> bool:
    if not country:
        return True
    if not location_value:
        return True  # keep if unknown
    loc = str(location_value).strip().lower()
    # Always allow fully remote entries
    if "remote" in loc:
        return True
    norm, aliases = _normalize_country_name(country)
    return any(alias in loc for alias in aliases)


def load_jobs(local: str | None, url: str | None, here: Path) -> list[dict[str, Any]]:
    if local:
        with open(local, "r", encoding="utf-8") as f:
            return json.load(f)
    if url:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()
    # No fallback to sample file; return empty list so other sources (e.g., Selenium) can run
    return []


def fetch_serpapi_google_jobs(query: str, location: str | None, api_key: str, fetch_limit: int) -> list[dict[str, Any]]:
    params = {
        "engine": "google_jobs",
        "q": query,
        "hl": "en",
        "api_key": api_key,
    }
    if location:
        params["location"] = location
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("jobs_results", []) or []

    results: list[dict[str, Any]] = []
    for it in items[:fetch_limit]:
        title = it.get("title") or ""
        company = it.get("company_name") or it.get("company") or ""
        loc = it.get("location") or ""
        desc = it.get("description") or ""
        url = None
        # Prefer direct apply_links if present
        apply_options = it.get("apply_options") or []
        if apply_options and isinstance(apply_options, list):
            # pick first
            url = apply_options[0].get("link") or apply_options[0].get("apply_link")
        if not url:
            related = it.get("related_links") or []
            if related:
                url = related[0].get("link")
        if not url:
            url = it.get("job_id")  # fallback id reference
        results.append({
            "title": title,
            "company": company,
            "location": loc,
            "description": desc,
            "url": url,
            "source": "serpapi_google_jobs"
        })
    return results


# ---------- Free sources (no API key required) ----------

def _query_match(text: str, query: str) -> bool:
    """Return True if text matches query.
    - Supports OR terms with '|' (any token match).
    - Otherwise requires at least 50% of query tokens to be present (lenient).
    """
    if not query:
        return True
    hay = tokenize_for_fuzz(text).split()
    hay_set = set(hay)

    # OR support with '|'
    if '|' in query:
        ors = [t.strip() for t in query.split('|') if t.strip()]
        return any(tokenize_for_fuzz(term) in ' '.join(hay) or any(tok in hay_set for tok in tokenize_for_fuzz(term).split()) for term in ors)

    q_tokens = [t for t in tokenize_for_fuzz(query).split() if t]
    if not q_tokens:
        return True
    matched = sum(1 for t in q_tokens if t in hay_set)
    return matched >= max(1, int(len(q_tokens) * 0.5))


def fetch_remotive(query: str | None, fetch_limit: int) -> list[dict[str, Any]]:
    # Docs: https://remotive.com/api/remote-jobs
    params: dict[str, Any] = {}
    if query:
        params["search"] = query
    resp = requests.get("https://remotive.com/api/remote-jobs", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    jobs = data.get("jobs", []) or []
    results: list[dict[str, Any]] = []
    for it in jobs:
        title = it.get("title") or ""
        company = it.get("company_name") or ""
        loc = it.get("candidate_required_location") or it.get("location") or "Remote"
        desc = it.get("description") or ""
        url = it.get("url") or ""
        results.append({
            "title": title,
            "company": company,
            "location": loc,
            "description": desc,
            "url": url,
            "source": "remotive"
        })
        if len(results) >= fetch_limit:
            break
    return results


def fetch_remoteok(query: str | None, fetch_limit: int) -> list[dict[str, Any]]:
    # Docs: https://remoteok.com/api
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobMatcher/1.0)"}
    resp = requests.get("https://remoteok.com/api", headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    filtered: list[dict[str, Any]] = []
    unfiltered: list[dict[str, Any]] = []
    for it in data:
        # First element can be legal notice (dict with 'legal')
        if isinstance(it, dict) and it.get("position"):
            title = it.get("position") or ""
            company = it.get("company") or ""
            loc = it.get("location") or "Remote"
            desc = it.get("description") or ""
            url = it.get("url") or it.get("apply_url") or ""
            combined = f"{title}\n{company}\n{loc}\n{desc}"
            unfiltered.append({
                "title": title,
                "company": company,
                "location": loc,
                "description": desc,
                "url": url,
                "source": "remoteok"
            })
            if _query_match(combined, query or ""):
                filtered.append(unfiltered[-1])
    # Respect fetch_limit
    if filtered:
        return filtered[:fetch_limit]
    return unfiltered[:fetch_limit]


def fetch_arbeitnow(query: str | None, fetch_limit: int) -> list[dict[str, Any]]:
    # Docs: https://www.arbeitnow.com/api/job-board-api
    resp = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("data", []) or []
    filtered: list[dict[str, Any]] = []
    unfiltered: list[dict[str, Any]] = []
    for it in items:
        title = it.get("title") or it.get("position") or ""
        company = it.get("company") or ""
        loc = it.get("location") or "Remote"
        desc = it.get("description") or ""
        url = it.get("url") or ""
        combined = f"{title}\n{company}\n{loc}\n{desc}"
        entry = {
            "title": title,
            "company": company,
            "location": loc,
            "description": desc,
            "url": url,
            "source": "arbeitnow"
        }
        unfiltered.append(entry)
        if _query_match(combined, query or ""):
            filtered.append(entry)
    if filtered:
        return filtered[:fetch_limit]
    return unfiltered[:fetch_limit]


FREE_SOURCES = {
    "remotive": fetch_remotive,
    "remoteok": fetch_remoteok,
    "arbeitnow": fetch_arbeitnow,
}


def score_job(job: dict[str, Any], resume_text: str) -> float:
    title = job.get("title", "")
    fields = "\n".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("description", ""),
    ])
    # token-set fuzzy similarity
    sim = fuzz.token_set_ratio(tokenize_for_fuzz(resume_text), tokenize_for_fuzz(fields))
    # boost relevant titles
    if re.search(r"mlops|machine\s+learning|data\s+engineer|full\s*stack|python", title.lower()):
        sim += 10
    return float(sim)


## resolve_from_config and load_json are provided by config.py


def _arg_present(flag: str) -> bool:
    # Only --config is supported now; keep helper for backward-compat if needed
    return False


def write_csv(rows: list[dict[str, Any]], csv_path: Path) -> None:
    fields = ["title", "company", "location", "country", "score", "url", "careers_url", "source", "description"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({
                "title": r.get("title", ""),
                "company": r.get("company", ""),
                "location": r.get("location", ""),
                "country": r.get("country", ""),
                "score": r.get("score", ""),
                "url": r.get("url", ""),
                "careers_url": r.get("careers_url", ""),
                "source": r.get("source", ""),
                "description": (r.get("description", "") or "").replace("\r", " ").replace("\n", " ")
            })


def create_headless_driver() -> Any:
    if not SELENIUM_AVAILABLE:
        return None
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(5)
    return driver


def fetch_selenium_sites(sites: list[Any], fetch_limit: int) -> list[dict[str, Any]]:
    if not SELENIUM_AVAILABLE:
        return []
    driver = create_headless_driver()
    if driver is None:
        return []
    results: list[dict[str, Any]] = []
    # Normalize sites to dict entries even if provided as plain URLs
    normalized: list[dict[str, Any]] = []
    for site in sites or []:
        if isinstance(site, str):
            try:
                p = urlparse(site)
                absolute_base = f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else site
                normalized.append({
                    "url": site,
                    "list_selector": "a[href*='job'], a[href*='/jobs/'], a[href*='/careers/']",
                    "title_selector": "",
                    "location_selector": "",
                    "link_selector": "a",
                    "company": "",
                    "source": f"selenium:{p.netloc or 'site'}",
                    "careers_url": site,
                    "domain_filter": "",
                    "require_path_contains": "",
                    "absolute_base": absolute_base
                })
            except Exception:
                continue
        elif isinstance(site, dict):
            normalized.append(site)
    sites = normalized
    try:
        for site in sites or []:
            url = site.get("url")
            if not url:
                continue
            list_sel = site.get("list_selector") or ""
            item_sel = site.get("item_selector") or ""
            title_sel = site.get("title_selector") or ""
            loc_sel = site.get("location_selector") or ""
            link_sel = site.get("link_selector") or "a"
            source = site.get("source") or f"selenium:{url.split('/')[2]}"
            careers_url = site.get("careers_url") or url
            domain_filter = site.get("domain_filter") or ""
            require_path_contains = site.get("require_path_contains") or ""
            absolute_base = site.get("absolute_base") or url

            try:
                print(f"[selenium] loading: {url} source={source} company={site.get('company')}")
            except Exception:
                pass
            driver.get(url)

            # Optional explicit wait for dynamic pages
            wait_sel = site.get("wait_selector")
            try:
                if wait_sel:
                    WebDriverWait(driver, 12).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_sel))
                    )
            except Exception:
                pass

            # Optional sleep for heavy JS pages
            try:
                sleep_seconds = float(site.get("sleep_seconds") or 0)
                if sleep_seconds > 0:
                    import time
                    time.sleep(sleep_seconds)
            except Exception:
                pass
            items = []
            if list_sel:
                items = driver.find_elements(By.CSS_SELECTOR, list_sel)
            elif item_sel:
                items = driver.find_elements(By.CSS_SELECTOR, item_sel)
            # Fallback to page-level if no container selector
            if not items:
                items = [driver]

            # Debug: counts per site
            try:
                print(f"[selenium] {source} containers={len(items)} url={url}")
            except Exception:
                pass

            for idx, elem in enumerate(items):
                try:
                    title = ""
                    location = ""
                    link = ""
                    # Title
                    if title_sel:
                        t_nodes = elem.find_elements(By.CSS_SELECTOR, title_sel)
                        if t_nodes:
                            title = t_nodes[0].text.strip()
                    else:
                        txt = getattr(elem, 'text', '') or ''
                        title = txt.strip()
                    # Location
                    if loc_sel:
                        l_nodes = elem.find_elements(By.CSS_SELECTOR, loc_sel)
                        if l_nodes:
                            location = l_nodes[0].text.strip()
                    # Link
                    l_nodes = elem.find_elements(By.CSS_SELECTOR, link_sel) if link_sel else []
                    if l_nodes:
                        link = l_nodes[0].get_attribute("href") or ""
                    if not link and hasattr(elem, 'get_attribute'):
                        link = elem.get_attribute('href') or ""
                    # Normalize relative links
                    if link and absolute_base and link.startswith('/'):
                        link = urljoin(absolute_base, link)
                    # Domain/path filters
                    if domain_filter:
                        try:
                            netloc = urlparse(link).netloc
                            if domain_filter not in netloc:
                                continue
                        except Exception:
                            pass
                    if require_path_contains and (require_path_contains not in (link or '')):
                        continue
                    # Skip if no title
                    if not title:
                        continue
                    results.append({
                        "title": title,
                        "company": site.get("company") or "",
                        "location": location,
                        "description": "",
                        "url": link or url,
                        "careers_url": careers_url,
                        "source": source,
                    })
                    if len(results) >= fetch_limit:
                        return results
                except Exception:
                    continue
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return results


def build_selenium_sites_from_company_opts(company_opts: dict[str, Any]) -> list[dict[str, Any]]:
    print(company_opts, "hello")
    sites: list[dict[str, Any]] = []
    if not company_opts:
        return sites
    companies =  company_opts or []
    print(companies)
    def discover_careers_url(company_slug: str) -> str | None:
        slug = company_slug.lower().strip()
        if not slug:
            return None
        candidates = [
            f"https://www.{slug}.com/careers",
            f"https://{slug}.com/careers",
            f"https://www.{slug}.com/jobs",
            f"https://{slug}.com/jobs",
            f"https://careers.{slug}.com/",
            f"https://jobs.{slug}.com/",
        ]
        headers = {"User-Agent": "Mozilla/5.0 (compatible; JobMatcher/1.0)"}
        for c in candidates:
            try:
                r = requests.get(c, headers=headers, timeout=10, allow_redirects=True)
                if r.status_code == 200 and ("career" in r.text.lower() or "job" in r.text.lower()):
                    return r.url
            except Exception:
                continue
        return None

    for slug in companies:
        s = (slug or "").strip()
        if not s:
            continue
        base = discover_careers_url(s)
        if not base:
            # last-resort guess
            base = f"https://{s}.com/careers"
        try:
            print(f"[selenium] discovered careers url for {s}: {base}")
        except Exception:
            pass
        parsed = urlparse(base)
        print(base)
        domain = parsed.netloc
        sites.append({
            "url": base,
            "list_selector": "a[href*='job'], a[href*='/jobs/'], a[href*='/careers/']",
            "title_selector": "",
            "location_selector": "",
            "link_selector": "a",
            "company": s,
            "source": f"selenium:{domain}",
            "careers_url": base,
            "domain_filter": domain,
            "require_path_contains": "",
            "absolute_base": f"{parsed.scheme}://{parsed.netloc}"
        })
    return sites


def main() -> None:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(description="Score and list top matching jobs for a given resume (config-only).")
    parser.add_argument("--config", default=None, help="Path to config JSON")
    args = parser.parse_args()

    # Load and merge config if provided (or if default exists)
    cfg_path = Path(args.config) if args.config else (here / "config.json")
    cfg_data: dict[str, Any] | None = None
    if cfg_path.exists():
        try:
            cfg_data = load_json(cfg_path)
        except Exception:
            cfg_data = None
    resolved_cfg: dict[str, Any] = resolve_from_config(cfg_data) if cfg_data else {}

    # Merge precedence with safe fallback:
    # 1) if --resume explicitly passed, use it
    # 2) else if config has resume, use it
    # 3) else try common defaults in order
    resume_path_candidate = resolved_cfg.get("resume") or None
    candidates = [
        resume_path_candidate,
        str(here / "resume.txt"),
        str(here / "input" / "resume.txt"),
        str(here.parent / "resume" / "input" / "resume.txt"),
    ]
    candidates = [c for c in candidates if c]
    resume_file: Path | None = None
    for c in candidates:
        p = Path(c)
        if p.exists():
            resume_file = p
            break
    if not resume_file:
        raise SystemExit(
            "Resume file not found. Set `resume` in config.json or pass --resume <path>. "
            "Tried: " + ", ".join(candidates)
        )

    top_n = int(resolved_cfg.get("top", 10))

    # Source selection
    free_source = resolved_cfg.get("source") if resolved_cfg.get("mode") == "free" else None
    query = resolved_cfg.get("query")
    location = resolved_cfg.get("location")
    country = resolved_cfg.get("country") or "usa"
    serpapi_key = resolved_cfg.get("serpapi_key")
    jobs_arg = resolved_cfg.get("jobs")
    jobs_url_arg = resolved_cfg.get("jobs_url")
    cfg_companies = resolved_cfg.get("companies") or []
    # Combined options from config
    free_opts = resolved_cfg.get("free_options") or {}
    company_opts = resolved_cfg.get("company_options") or {}
    selenium_opts = resolved_cfg.get("selenium_options") or {}
    # Default behavior: run both if neither CLI nor config specifies otherwise
    run_both = bool(resolved_cfg.get("run_both", True))

    # Output handling (configurable dir/prefix)
    out_cfg = resolved_cfg.get("output", {}) if resolved_cfg else {}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = str(here / "output" / f"matched_jobs_{ts}.json")
    if out_cfg:
        out_dir = out_cfg.get("dir")
        prefix = out_cfg.get("prefix", "matched_jobs")
        if out_dir:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = str(Path(here / out_dir / f"{prefix}_{stamp}.json"))

    resume_text = read_text(resume_file)
    # If no explicit query provided, derive it from the resume content
    if not query:
        try:
            query = build_query_from_resume(resume_text)
            print("[query] derived from resume:", query)
        except Exception:
            query = None

    # Fetch jobs according to chosen source(s)
    fetched: list[dict[str, Any]] = []

    def _dedupe_by_url(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for it in items:
            key = (it.get("url") or f"{it.get('title','')}|{it.get('company','')}|{it.get('location','')}")
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        return out

    if run_both:
        # Free block
        free_src = free_source or free_opts.get("source")
        free_query = query or free_opts.get("query")
        if free_src and free_query is not None:
            free_fetcher = FREE_SOURCES.get(free_src)
            if not free_fetcher:
                raise SystemExit(f"Unknown free source: {free_src}")
            fetched += free_fetcher(free_query, int(resolved_cfg.get("fetch_limit", 200)))
        fetched = _dedupe_by_url(fetched)
    else:
        if free_source and query is not None:
            fetcher = FREE_SOURCES.get(free_source)
            if not fetcher:
                raise SystemExit(f"Unknown free source: {free_source}")
            fetched = fetcher(query, int(resolved_cfg.get("fetch_limit", 200)))
        elif serpapi_key and query:
            fetched = fetch_serpapi_google_jobs(query, location, serpapi_key, int(resolved_cfg.get("fetch_limit", 200)))
        else:
            fetched = load_jobs(jobs_arg, jobs_url_arg, here)
            if isinstance(fetched, dict) and 'items' in fetched:
                fetched = fetched['items']  # normalize
            if not isinstance(fetched, list):
                fetched = []
            fetched = fetched[: args.fetch_limit]

    # Optional Selenium fetch
    use_selenium = bool(selenium_opts.get("enabled"))
    print(use_selenium)
    if use_selenium:
        # Prefer explicit sites; otherwise derive from company_options
        raw_sites = selenium_opts.get("sites") or build_selenium_sites_from_company_opts(cfg_companies)
        try:
            def _u(x):
                return x.get("url") if isinstance(x, dict) else str(x)
            print("[selenium] using sites:", [_u(s) for s in (raw_sites or [])])
        except Exception:
            pass
        if raw_sites:
            fetched += fetch_selenium_sites(raw_sites, int(resolved_cfg.get("fetch_limit", 200)))

    # Country filter (lenient, allows 'Remote')
    if country:
        fetched = [j for j in fetched if _matches_country(j.get("location"), country)]

    # Score and select
    scored = []
    for job in fetched:
        s = score_job(job, resume_text)
        # derive country value for CSV
        cval = "usa" if _matches_country(job.get("location"), "usa") else ""
        scored.append({**job, "score": round(s, 2), "country": cval})
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[: top_n]

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(top, f, indent=2)

    # CSV path for top N
    csv_path = out_file.with_suffix('.csv')
    write_csv(top, csv_path)

    # Save fetched list (JSON/CSV) if requested
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fetched_json = out_file.parent / f"fetched_jobs_{stamp}.json"
    fetched_csv = out_file.parent / f"fetched_jobs_{stamp}.csv"
    if (resolved_cfg.get("save_fetched") or False):
        with open(fetched_json, "w", encoding="utf-8") as f:
            json.dump(fetched, f, indent=2)
        # add dummy score column for CSV uniformity
        fetched_rows = [{**j, "score": "", "country": ("usa" if _matches_country(j.get("location"), "usa") else "")} for j in fetched]
        write_csv(fetched_rows, fetched_csv)

    # Always also produce top-50 alongside configured top
    top50 = scored[:50]
    top50_json = out_file.parent / f"top50_jobs_{stamp}.json"
    top50_csv = out_file.parent / f"top50_jobs_{stamp}.csv"
    with open(top50_json, "w", encoding="utf-8") as f:
        json.dump(top50, f, indent=2)
    write_csv(top50, top50_csv)

    # Generate cover letters for top 100 (concise, three-paragraph letters; no greeting/signature)
    if COVER_LETTER_AVAILABLE and top:
        try:
            letters_dir = out_file.parent / "cover_letters"
            letters_dir.mkdir(parents=True, exist_ok=True)
            # Derive candidate name from resume first non-empty line
            name_line = next((ln.strip() for ln in resume_text.splitlines() if ln.strip()), "Candidate")
            builder = CoverLetterBuilder(resume_text, name_line)
            openai_cfg = resolved_cfg.get("openai") or {}
            use_openai = bool(openai_cfg.get("enabled"))
            openai_model = (openai_cfg.get("model") or "").strip()
            openai_key = (openai_cfg.get("api_key") or os.getenv("OPENAI_API_KEY") or "").strip()
            
            # Auto-tailor resume and generate cover letter for jobs with score > 50
            auto_tailor = bool(resolved_cfg.get("auto_tailor_resume", False))
            tailored_resumes_dir = out_file.parent / "tailored_resumes"
            if auto_tailor and RESUME_BUILDER_AVAILABLE:
                tailored_resumes_dir.mkdir(parents=True, exist_ok=True)
            
            for j in top[:100]:
                score = j.get("score", 0)
                company = (j.get("company") or "").strip() or "Company"
                role = (j.get("title") or "").strip() or "Role"
                jd_text = (j.get("description") or "").strip()
                base = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{company}_{role}")[:80]
                
                # Generate tailored resume if score > 50
                if auto_tailor and RESUME_BUILDER_AVAILABLE and score > 50:
                    try:
                        tailored_text = tailor_resume_for_job(
                            resume_text, jd_text, company, role, openai_model, openai_key
                        )
                        if tailored_text and tailored_text != resume_text:
                            tailored_doc = build_tailored_resume_doc(tailored_text)
                            resume_path = tailored_resumes_dir / f"resume_{base}.docx"
                            tailored_doc.save(resume_path)
                            # Use tailored resume for cover letter generation
                            builder_tailored = CoverLetterBuilder(tailored_text, name_line)
                        else:
                            builder_tailored = builder
                    except Exception as e:
                        print(f"[resume_tailor] error for {company}: {e}")
                        builder_tailored = builder
                else:
                    builder_tailored = builder
                
                # Compose concise three-paragraph text letter per rules
                letter_txt = None
                if use_openai and openai_model and openai_key:
                    letter_txt = builder_tailored.compose_openai_text(jd_text, company, role, openai_model, openai_key)
                if not letter_txt:
                    letter_txt = builder_tailored.compose_concise_text(jd_text, company, role)
                txt_path = letters_dir / f"cover_{base}.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(letter_txt)
            
            print(f"[cover] generated concise cover letters in {letters_dir}")
            if auto_tailor and RESUME_BUILDER_AVAILABLE:
                print(f"[resume] generated tailored resumes in {tailored_resumes_dir}")
        except Exception as e:
            print("[cover] skipped:", e)

    print("Top matches:")
    for j in top:
        line = f"- [{j['score']}] {j.get('title','')} @ {j.get('company','')} ({j.get('location','')})"
        if j.get("url"):
            line += f" - {j['url']}"
        print(line)
    print("Saved to:", os.path.abspath(out_file))
    print("CSV saved to:", os.path.abspath(csv_path))
    if args.save_fetched:
        print("Fetched JSON:", os.path.abspath(fetched_json))
        print("Fetched CSV:", os.path.abspath(fetched_csv))
    print("Top50 JSON:", os.path.abspath(top50_json))
    print("Top50 CSV:", os.path.abspath(top50_csv))


if __name__ == "__main__":
    main()
