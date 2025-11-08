# Job Application Agent

An intelligent, autonomous AI agent that discovers job opportunities, analyzes fit, and generates tailored application materials using Large Language Models.

## 🎯 What It Does

The Job Application Agent is a complete end-to-end solution that:

1. **Discovers Jobs** - Intelligently scrapes job listings from multiple sources
   - Supports major ATS systems (Greenhouse, Lever, Workday, SmartRecruiters, Ashby)
   - Auto-detects career page structures
   - Handles dynamic content and JavaScript-rendered pages

2. **Analyzes & Scores** - Evaluates jobs against your profile
   - Matches job titles, companies, and locations
   - Scores each opportunity (0-100)
   - Prioritizes best matches

3. **Enriches Job Descriptions** - Uses LLMs to extract detailed information
   - Fetches full job postings from URLs
   - Identifies responsibilities, qualifications, and requirements
   - Structures unstructured job descriptions

4. **Generates Application Materials** - Creates tailored content
   - Customized resumes for each position
   - Personalized cover letters
   - Highlights relevant skills and experience

5. **Submits Applications** (Optional) - Automates the submission process
   - Workday autofill support
   - More platforms coming soon
   - Safety features (dry-run mode, confirmation prompts)

## 🚀 Quick Start

### Basic Usage

```bash
# Run the agent with default config
python agent_cli.py

# Dry run (don't submit applications)
python agent_cli.py --dry-run

# Target specific companies
python agent_cli.py --companies uber apple meta google

# Target specific roles
python agent_cli.py --roles "software engineer" "ml engineer" "data scientist"

# Set minimum match score
python agent_cli.py --min-score 70

# Limit number of applications
python agent_cli.py --max-jobs 5
```

### Configuration

Create or edit `config.json`:

```json
{
  "resume": "input/resume.txt",
  "companies": ["uber", "apple", "meta", "openai"],
  "fetch_limit": 500,
  "top": 15,
  "auto_tailor_resume": true,
  "selenium_options": {
    "enabled": true,
    "sites": [
      {
        "url": "https://www.uber.com/us/en/careers/list/",
        "company": "uber"
      },
      {
        "url": "https://jobs.apple.com/en-us/search?location=united-states-USA",
        "company": "apple"
      }
    ]
  },
  "openai": {
    "enabled": true,
    "model": "gpt-4o-mini"
  },
  "autofill": {
    "enabled": false,
    "providers": ["workday"],
    "max_jobs": 1,
    "profile": {
      "first_name": "Your",
      "last_name": "Name",
      "email": "your.email@example.com",
      "phone": "1234567890"
    }
  }
}
```

## 📊 Agent Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Job Application Agent                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌───────────────────────────────────────┐
         │  1. DISCOVER JOBS                     │
         │  - Scrape career pages                │
         │  - Auto-detect page structure         │
         │  - Extract job listings               │
         └───────────────────────────────────────┘
                              │
                              ▼
         ┌───────────────────────────────────────┐
         │  2. ANALYZE & SCORE                   │
         │  - Match against profile              │
         │  - Calculate scores (0-100)           │
         │  - Sort by relevance                  │
         └───────────────────────────────────────┘
                              │
                              ▼
         ┌───────────────────────────────────────┐
         │  3. ENRICH DESCRIPTIONS (LLM)         │
         │  - Fetch full job postings            │
         │  - Extract responsibilities           │
         │  - Identify qualifications            │
         └───────────────────────────────────────┘
                              │
                              ▼
         ┌───────────────────────────────────────┐
         │  4. GENERATE MATERIALS (LLM)          │
         │  - Tailored resume                    │
         │  - Personalized cover letter          │
         │  - Save to output directory           │
         └───────────────────────────────────────┘
                              │
                              ▼
         ┌───────────────────────────────────────┐
         │  5. SUBMIT APPLICATIONS (Optional)    │
         │  - Workday autofill                   │
         │  - Upload documents                   │
         │  - Track submissions                  │
         └───────────────────────────────────────┘
```

## 🧠 LLM Usage

The agent uses LLMs extensively throughout the pipeline:

### 1. Job Description Extraction
```python
# Extracts structured information from raw HTML
JobDescriptionExtractor.extract_job_description(html, company, role)
```
- Identifies section headers (Responsibilities, Qualifications, etc.)
- Removes boilerplate content
- Structures unstructured text
- **Model**: GPT-4o-mini
- **No embeddings required**

### 2. Resume Generation
```python
# Creates tailored resume for each job
JobApplicationGenerator.generate_tailored_resume(job_desc, company, role)
```
- Highlights relevant experience
- Emphasizes matching skills
- Adjusts language to job requirements
- **Model**: GPT-4o-mini

### 3. Cover Letter Generation
```python
# Writes personalized cover letter
JobApplicationGenerator.generate_cover_letter(job_desc, company, role)
```
- References specific job requirements
- Tells your story in context
- Maintains professional tone
- **Model**: GPT-4o-mini

### 4. RAG-Based Parsing (Optional)
```python
# Uses embeddings + vector search for deep analysis
LLMParser.parse_job_from_text(job_description)
```
- Semantic understanding of job requirements
- Extracts nuanced information
- **Model**: GPT-4o-mini + text-embedding-3-small
- **Requires**: OpenAI embedding access

## 🔧 Architecture

### Core Components

```
job_application_agent.py    - Main agent orchestration
├── AgentConfig             - Configuration dataclass
├── JobApplication          - Application data model
└── JobApplicationAgent     - Agent implementation

intelligent_job_scraper.py  - Auto-detecting job scraper
├── IntelligentJobScraper   - Scraper with ATS detection
├── ATS_PATTERNS            - Known ATS configurations
└── GENERIC_SELECTORS       - Fallback selectors

llm_job_description_extractor.py  - LLM-based extraction
└── JobDescriptionExtractor        - Pattern + LLM extraction

job_application_generator.py      - Application generation
└── JobApplicationGenerator        - Resume + cover letter

workday_autofill.py               - Workday automation
└── WorkdayAutofill               - Form filling logic

match.py                          - Legacy matching system
agent_cli.py                      - Command-line interface
```

### Data Flow

```
Career Page URL
      ↓
IntelligentJobScraper  →  Raw job listings
      ↓
JobApplication (scored)
      ↓
JobDescriptionExtractor  →  Enriched descriptions
      ↓
JobApplicationGenerator  →  Tailored materials
      ↓
Output files + metadata
      ↓
(Optional) WorkdayAutofill  →  Submitted application
```

## 📁 Output Structure

```
output/
├── agent_results.json          # Run summary
├── uber/
│   ├── resume_uber.txt
│   ├── cover_letter_uber.txt
│   └── metadata_uber.json
├── apple/
│   ├── resume_apple.txt
│   ├── cover_letter_apple.txt
│   └── metadata_apple.json
└── meta/
    ├── resume_meta.txt
    ├── cover_letter_meta.txt
    └── metadata_meta.json
```

### Metadata Format

```json
{
  "job_id": "https://www.uber.com/careers/...",
  "company": "uber",
  "title": "Software Engineer",
  "location": "San Francisco, CA",
  "url": "https://www.uber.com/careers/...",
  "score": 85.0,
  "description": "Full job description...",
  "tailored_resume": "Resume content...",
  "cover_letter": "Cover letter content...",
  "discovered_at": "2025-11-08T10:30:00",
  "generated_at": "2025-11-08T10:35:00",
  "submitted_at": null,
  "status": "generated",
  "error": null
}
```

## 🎛️ Configuration Options

### AgentConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resume_path` | str | required | Path to your resume file |
| `candidate_name` | str | required | Your full name |
| `target_roles` | List[str] | required | Job titles to search for |
| `target_companies` | List[str] | `[]` | Specific companies to target |
| `target_locations` | List[str] | `[]` | Preferred locations |
| `max_jobs_to_fetch` | int | `500` | Max jobs to discover |
| `max_jobs_to_apply` | int | `10` | Max applications to generate |
| `min_match_score` | float | `60.0` | Minimum score to process |
| `openai_api_key` | str | env | OpenAI API key |
| `openai_model` | str | `gpt-4o-mini` | Model for generation |
| `use_embeddings` | bool | `True` | Enable RAG parsing |
| `auto_generate_resume` | bool | `True` | Generate tailored resumes |
| `auto_generate_cover_letter` | bool | `True` | Generate cover letters |
| `auto_submit` | bool | `False` | Auto-submit applications |
| `dry_run` | bool | `True` | Safety mode (no submissions) |
| `verbose` | bool | `True` | Detailed logging |

## 🔒 Safety Features

### Dry Run Mode (Default)
```bash
python agent_cli.py --dry-run
```
- Discovers and analyzes jobs
- Generates application materials
- **Does NOT submit** applications
- Safe for testing

### Confirmation Prompts
When auto-submit is enabled:
```
⚠️  Auto-submit is ENABLED. Applications will be submitted automatically. Continue? (yes/no):
```

### Rate Limiting
- 2-second delay between LLM calls
- Configurable wait times for page loads
- Respects robots.txt (when available)

### Error Handling
- Graceful failures (logs errors, continues)
- Retry logic with exponential backoff
- Comprehensive error messages

## 📊 Example Run

```bash
$ python agent_cli.py --companies uber apple meta --max-jobs 3

Job Application Agent
============================================================
Configuration:
  Resume: input/resume.txt
  Target roles: software engineer, ml engineer
  Target companies: uber, apple, meta
  Max applications: 3
  Min score: 60.0
  Auto-submit: False (dry_run=True)
  Output: output
  Sources: 3 configured
============================================================

[2025-11-08 10:30:00] [JobAgent] INFO: Job Application Agent initialized
[2025-11-08 10:30:00] [JobAgent] INFO: Discovering jobs from 3 sources...
[2025-11-08 10:30:05] [JobAgent] INFO:   [1/3] Scraping uber
[2025-11-08 10:30:10] [JobAgent] INFO:     Found 45 jobs
[2025-11-08 10:30:10] [JobAgent] INFO:   [2/3] Scraping apple
[2025-11-08 10:30:18] [JobAgent] INFO:     Found 102 jobs
[2025-11-08 10:30:18] [JobAgent] INFO:   [3/3] Scraping meta
[2025-11-08 10:30:25] [JobAgent] INFO:     Found 67 jobs
[2025-11-08 10:30:25] [JobAgent] INFO: Total jobs discovered: 214
[2025-11-08 10:30:26] [JobAgent] INFO: Analyzing 214 jobs...
[2025-11-08 10:30:27] [JobAgent] INFO: Analysis complete: 42 jobs above threshold (60.0)
[2025-11-08 10:30:27] [JobAgent] INFO: Processing top 3 matches...

[1/3] uber - Senior Software Engineer (Score: 85.0)
  [LLM] Enriching job description for uber...
  [LLM] Enriched description: 2847 chars
  [LLM] Generating application materials for uber...
  [LLM] Generated tailored resume
  [LLM] Generated cover letter
  Saved application materials to output/uber

[2/3] apple - ML Engineer (Score: 82.5)
  [LLM] Generating application materials for apple...
  [LLM] Generated tailored resume
  [LLM] Generated cover letter
  Saved application materials to output/apple

[3/3] meta - Software Engineer, Infrastructure (Score: 78.0)
  [LLM] Generating application materials for meta...
  [LLM] Generated tailored resume
  [LLM] Generated cover letter
  Saved application materials to output/meta

============================================================
AGENT RUN COMPLETE
  Time elapsed: 95.3s
  Jobs discovered: 214
  Jobs above threshold: 42
  Resumes generated: 3
  Cover letters generated: 3
  Applications submitted: 0
  Failures: 0
============================================================

============================================================
SUMMARY
============================================================
✓ Jobs discovered: 214
✓ Jobs analyzed: 214
✓ Jobs above threshold: 42
✓ Resumes generated: 3
✓ Cover letters generated: 3
✓ Applications submitted: 0
⏱  Time: 95.3s
============================================================

Results saved to: output/agent_results.json
```

## 🚀 Advanced Usage

### Programmatic API

```python
from job_application_agent import JobApplicationAgent, AgentConfig

# Configure agent
config = AgentConfig(
    resume_path="input/resume.txt",
    candidate_name="John Doe",
    target_roles=["software engineer", "backend engineer"],
    target_companies=["uber", "apple"],
    max_jobs_to_apply=5,
    min_match_score=70.0,
    auto_generate_resume=True,
    auto_generate_cover_letter=True,
    dry_run=True
)

# Create agent
agent = JobApplicationAgent(config)

# Define job sources
sources = [
    {"url": "https://www.uber.com/us/en/careers/list/", "company": "uber"},
    {"url": "https://jobs.apple.com/en-us/search", "company": "apple"}
]

# Run agent
results = agent.run(sources)

# Access results
print(f"Generated {results['resumes_generated']} resumes")
print(f"Generated {results['cover_letters_generated']} cover letters")

for app in agent.applications[:5]:
    print(f"{app.company} - {app.title}: {app.score:.1f}")
```

### Custom LLM Configuration

```python
from job_application_generator import JobApplicationGenerator

# Use different model
generator = JobApplicationGenerator(
    api_key="your-api-key",
    model="gpt-4"  # More powerful model
)

# Generate with custom context
result = generator.generate_application_package(
    job_description="...",
    company="Company",
    role="Role",
    parallel=True,
    additional_context="I have 5 years experience in..."
)
```

## 🐛 Troubleshooting

### No jobs found
- Check that `selenium_options.sites` is configured
- Verify career page URLs are accessible
- Increase `sleep_seconds` for slow-loading pages

### Empty job descriptions
- Enable LLM extraction (it's automatic now)
- Check that job URLs are valid
- Verify OpenAI API key is set

### LLM generation fails
- Verify `OPENAI_API_KEY` environment variable
- Check API quota/credits
- Try reducing `max_jobs_to_apply`

### Selector errors
- Career pages change frequently
- Use `intelligent_job_scraper.py` for auto-detection
- Update selectors in `config.json` if needed

## 📈 Performance

- **Job Discovery**: ~5-10 seconds per career page
- **LLM Enrichment**: ~3-5 seconds per job
- **Resume Generation**: ~5-8 seconds per resume
- **Cover Letter**: ~5-8 seconds per letter
- **Total (3 jobs)**: ~1.5-2 minutes

### Optimization Tips

1. **Parallel processing**: Set `parallel=True` in generation
2. **Caching**: Reuse job descriptions across runs
3. **Batch mode**: Process multiple companies in one run
4. **Rate limiting**: Balance speed vs. API costs

## 🔮 Future Enhancements

- [ ] Multi-provider autofill (Greenhouse, Lever, etc.)
- [ ] Interview scheduling integration
- [ ] Application tracking dashboard
- [ ] Email notifications for status updates
- [ ] A/B testing for cover letter effectiveness
- [ ] LinkedIn integration
- [ ] Resume format conversion (PDF, DOCX)
- [ ] Multi-language support
- [ ] Salary negotiation assistant

## 📝 License

MIT License - Use freely for personal or commercial applications.

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional ATS integrations
- Better job description parsing
- UI/dashboard development
- Test coverage improvements

## ⚠️ Disclaimer

This tool is for personal use in your job search. Always:
- Review generated materials before submission
- Verify job descriptions are accurate
- Respect website terms of service
- Use rate limiting to avoid overwhelming servers
- Be honest in your applications

Good luck with your job search! 🎉

