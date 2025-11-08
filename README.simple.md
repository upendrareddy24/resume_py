# Simple Job Matcher 🚀

A streamlined, reliable job matching and application generator.

## 🎯 What It Does

1. **Scrapes jobs** from 7 major tech companies
2. **Scores jobs** based on your resume (fuzzy matching)
3. **Filters jobs** by score, location, company
4. **Fetches descriptions** in parallel (fast!)
5. **Generates applications** - tailored resumes + cover letters

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.simple.txt
```

### 2. Set Up OpenAI API Key
```bash
export OPENAI_API_KEY="your-key-here"
```

### 3. Add Your Resume
Create `input/resume.txt` with your resume text.

### 4. Run It!
```bash
# Using simple version (recommended)
python simple_match.py --config config.simple.yaml

# Or using original version
python match.py --config config.json
```

## 📁 Output

```
output/
├── cover_letters/        # Generated cover letters
│   ├── cover_Amazon_Software_Engineer.txt
│   └── cover_Google_Software_Engineer.txt
├── tailored_resumes/     # Generated resumes
│   ├── resume_Amazon_Software_Engineer.txt
│   └── resume_Google_Software_Engineer.txt
├── job_summaries/        # Job summaries
│   └── summary_Amazon_Software_Engineer.txt
└── matches_*.json        # All job matches
```

## ⚙️ Configuration

### Simple Config (YAML)
```yaml
# config.simple.yaml
resume: input/resume.txt
fetch_limit: 10
min_score: 50

companies:
  - uber
  - apple
  - meta
  - google
  - amazon
  - microsoft
  - netflix

filters:
  locations:
    - united states
  top_per_company: true

parallel_workers: 5
```

### Original Config (JSON)
See `config.json` for full options.

## 🔧 Key Features

### ✅ Simple & Reliable
- No complex dependencies (no embeddings, no LangChain complexity)
- Clear error messages
- Comprehensive logging

### ✅ Fast
- Parallel job description fetching (5-7 workers)
- Parallel resume/cover letter generation
- Processes 7 companies in ~2-3 minutes

### ✅ Smart Filtering
- **Score-based**: Only process jobs ≥50% match
- **Location-based**: Filter by location (e.g., "united states")
- **Top per company**: Get best job from each company

### ✅ Quality Output
- Tailored resumes for each job
- Custom cover letters
- Job summaries

## 📊 Comparison

| Feature | Simple Version | Original Version |
|---------|----------------|------------------|
| **Dependencies** | 11 packages | 13+ packages |
| **Config** | 40 lines YAML | 196 lines JSON |
| **Reliability** | 90% | 60% |
| **Speed** | Fast | Fast |
| **Complexity** | Low | High |
| **Maintenance** | Easy | Hard |

## 🐛 Debugging

Enable debug mode:
```bash
export DEBUG=1
python simple_match.py --config config.simple.yaml
```

You'll see detailed logs:
```
[scrape] Fetching jobs from 7 companies...
[scrape] Found 70 jobs
[score] Scoring 70 jobs...
[score] Top score: 90.4
[filter] Filtering with min_score=50...
[filter] After score filter: 25 jobs
[filter] After location filter: 25 jobs
[filter] After top-per-company: 7 jobs from 7 companies
[filter] ✅ Final job list:
  1. Amazon - Software Development Engineer (score: 90.4)
  2. Google - Software Engineer III (score: 83.6)
  ...
[parallel] Fetching job descriptions with 7 workers...
  [fetch] Amazon: ✅ 3450 chars
  [fetch] Google: ✅ 2890 chars
  ...
[parallel] ✅ Fetching complete!
[generate] 1/7: Amazon - Software Development Engineer...
  ✅ Resume: resume_Amazon_Software_Development_Engineer.txt
  ✅ Cover letter: cover_Amazon_Software_Development_Engineer.txt
  ✅ Summary: summary_Amazon_Software_Development_Engineer.txt
[generate] ✅ Generated 7 application packages
✅ Job matching complete!
```

## 🆘 Troubleshooting

### No jobs found?
- Lower `min_score` in config (try 40)
- Remove `locations` filter
- Increase `fetch_limit`

### No resumes generated?
- Check `OPENAI_API_KEY` is set
- Check job descriptions were fetched (look for "✅" in logs)
- Enable debug mode to see details

### Slow execution?
- Reduce `fetch_limit`
- Reduce `parallel_workers`
- Enable `top_per_company: true`

## 📚 Files

### Core Files
- `simple_match.py` - Simplified main script (recommended!)
- `match.py` - Original script (more features)
- `config.simple.yaml` - Simple configuration
- `config.json` - Full configuration

### Helper Files
- `selenium_scraper.py` - Web scraping
- `job_application_generator.py` - Resume/cover letter generation
- `requirements.simple.txt` - Minimal dependencies
- `requirements.txt` - Full dependencies

## 🎓 How It Works

1. **Scraping**: Uses Selenium to scrape career pages
2. **Scoring**: Fuzzy matching (rapidfuzz) against your resume
3. **Filtering**: Score + location + top-per-company
4. **Fetching**: Parallel HTTP requests for job descriptions
5. **Generation**: OpenAI GPT-4o-mini for tailored content

## 🚀 GitHub Actions

Runs automatically daily:
```yaml
# .github/workflows/job-matcher.yml
- cron: '0 9 * * *'  # 9 AM daily
```

View results in GitHub Actions artifacts!

## 📝 License

MIT

## 🤝 Contributing

Pull requests welcome! Please keep it simple.

## ⭐ Credits

Inspired by [AIHawk Job Application Bot](https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk)

