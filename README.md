# Python Resume Tools

Python CLIs to tailor a resume to a job description (.docx) and fetch matched jobs.

## Setup

```bash
cd resume_py
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in `resume_py/` directory (optional, or export directly):

```bash
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_KEY=your_serpapi_key_here  # Optional, for Google Jobs search
```

## CLI Tools Overview

### 1. **match.py** - Job Matcher (Main Pipeline)

Fetches jobs from various sources, scores them against your resume, and optionally generates tailored resumes and cover letters for top matches.

**Config-based (recommended)**:

Edit `resume_py/config.json` to configure sources, resume path, output preferences, and LLM options.

```bash
python match.py --config config.json
```

**Features**:
- Fetches jobs from free APIs (RemoteOK, Remotive, Arbeitnow)
- Selenium-based scraping for company career pages
- SerpAPI Google Jobs integration (optional)
- Scores jobs using fuzzy matching against your resume
- Auto-generates tailored resumes and cover letters for high-scoring jobs (when `auto_tailor_resume: true`)
- Supports multiple LLM adapters: `JobApplicationGenerator`, `LLMResumer`, `LLMCoverLetterJobDescription`
- Outputs JSON and CSV files with top matches

**Output**:
- `output/matched_jobs_*.json` and `.csv` - Top N matches
- `output/cover_letters/` - Generated cover letters
- `output/tailored_resumes/` - Tailored resumes (when enabled)
- `output/parsed_jobs/` - Structured job info (when LLM parser enabled)

### 2. **tailor.py** - Resume Tailoring

Tailor your resume to a specific job description.

**Basic usage (keyword-based)**:
```bash
python tailor.py \
  --resume input/resume.txt \
  --jd input/jd.txt \
  --name "Bhavana Nare" \
  --out output/tailored.docx
```

**LLM-based tailoring (recommended)**:
```bash
export OPENAI_API_KEY=your_key
python tailor.py \
  --resume input/resume.txt \
  --jd input/jd.txt \
  --name "Bhavana Nare" \
  --company "Target Company" \
  --role "Senior ML Engineer" \
  --use-llm \
  --out output/tailored.docx
```

### 3. **cover_letter.py** - Cover Letter Generator

Generate a professional cover letter from your resume and a job description.

**Config-based**:
```bash
python cover_letter.py --config config.json
```

Edit the `cover_letter` block in `config.json`:
```json
{
  "cover_letter": {
    "resume": "input/resume.txt",
    "jd": "input/jd.txt",
    "name": "Bhavana Nare",
    "company": "Target Company",
    "role": "Senior ML Engineer",
    "out": "output/cover_letter.docx"
  },
  "openai": {
    "enabled": true,
    "model": "gpt-4o-mini"
  }
}
```

**Features**:
- Uses LLM adapter (`LLMCoverLetterJobDescription`) when OpenAI is enabled
- Falls back to keyword-based generation if LLM unavailable
- Generates professional .docx files with ATS optimization

### 4. **resume_builder.py** - Resume Builder

Build or enhance a resume from structured data in config.

```bash
python resume_builder.py
```

Reads `resume_builder` block from `config.json` and generates an enhanced resume using OpenAI (if enabled).

## Configuration Guide

### config.json Structure

```json
{
  "resume": "input/resume.txt",
  "top": 15,
  "country": "usa",
  "fetch_limit": 500,
  "run_both": true,
  "selenium_only": false,
  "save_fetched": true,
  "auto_tailor_resume": true,
  "tailor_threshold": 40,
  "use_job_app_generator": true,
  "openai": {
    "enabled": true,
    "model": "gpt-4o-mini"
  },
  "free_options": {
    "mode": "free",
    "source": "remoteok",
    "query": "Python MLOps Engineer"
  },
  "company_options": {
    "mode": "company",
    "companies": ["uber", "apple", "meta"]
  },
  "selenium_options": {
    "enabled": true,
    "sites": []
  },
  "output": {
    "dir": "output",
    "prefix": "matches_daily"
  },
  "cover_letter": {
    "resume": "input/resume.txt",
    "jd": "input/jd.txt",
    "name": "Your Name",
    "company": "",
    "role": "",
    "out": "output/cover_letter.docx"
  }
}
```

## LLM Adapters

The toolkit includes multiple LLM-powered adapters (all use LangChain + OpenAI):

1. **JobApplicationGenerator** - Unified pipeline for resume + cover letter generation (preferred)
2. **LLMResumer** - Resume tailoring with parallel cover letter generation
3. **LLMCoverLetterJobDescription** - Standalone cover letter generation
4. **LLMParser** - RAG-based job description parsing and information extraction

Set `use_job_app_generator: true` in config to use the unified generator (recommended).

## Schedule Daily Jobs (macOS/Linux)

Using cron to run job matcher daily at 8am:

```bash
crontab -e
```

Add:
```bash
0 8 * * * cd /path/to/webapp/resume_py && /path/to/venv/bin/python match.py --config config.json >> output/cron.log 2>&1
```

## Notes

- **Free sources**: RemoteOK, Remotive, Arbeitnow (no API key required)
- **SerpAPI**: Requires `SERPAPI_KEY` for Google Jobs integration
- **OpenAI**: Required for LLM-based resume tailoring and cover letter generation
- **Matching algorithm**: Uses RapidFuzz token-set ratio with title/keyword boosts
- All `.docx` files are ATS-friendly with keyword optimization

## Troubleshooting

**Import errors**: Make sure you've activated the venv and installed all requirements:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**OpenAI errors**: Verify your API key is set:
```bash
echo $OPENAI_API_KEY
```

**No jobs found**: Try different sources in config or adjust `fetch_limit`

**Selenium issues**: Install Chrome/Chromium for webdriver support
