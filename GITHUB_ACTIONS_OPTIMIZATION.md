# GitHub Actions Optimization Guide

## Problem
Your GitHub Actions workflow was timing out after **60 minutes** when running `match.py` due to:
- Scraping 25+ company websites with Selenium
- LLM rate limits causing retries
- Slow job description fetching

## Solutions Implemented

### 1. **Optimized Workflow Configuration** ✅
- **Reduced timeout**: 60min → **30min**
- **Uses `config.ci.json`** by default (optimized for CI)
- Better error messages for debugging

### 2. **Created `config.ci.json` for Fast CI Runs** ✅
Key optimizations:
- **Companies**: 25 → **5** (Meta, Google, Apple, Microsoft, Amazon)
- **Fetch limit**: 200 → **50** jobs
- **Top per company**: 10 → **3** jobs
- **Parallel workers**: 5 → **10** (faster processing)
- **Fast discovery**: `true` (skips slow LLM parsing)
- **Extract job descriptions**: `false` (saves time)
- **Selenium sleep**: 3s → **2s**

### 3. **LLM Retry Logic with Exponential Backoff** ✅
Added to `llm_manager.py`:
- Automatically retries **3 times** on rate limit errors
- **Exponential backoff**: 2s → 4s → 8s delays
- Detects: `429`, `quota`, `rate limit`, `resource_exhausted`
- **Automatic fallback**: Gemini → Ollama → OpenAI

### 4. **Job Quality Filters** ✅
Added to `match.py`:
- **Invalid title filter**: Removes UI elements ("Apply Now", "Job at X")
- **Non-technical filter**: Removes retail/admin positions
- **Min score enforcement**: Actually filters jobs below threshold
- **Full-time filter**: Only shows full-time positions
- **Keyword extraction**: Excludes stopwords like "in", "of", "with"

## Expected Results

### Before:
- ❌ 60+ minute timeout failures
- ❌ Rate limit errors stopping runs
- ❌ 100+ low-quality jobs cluttering results
- ❌ UI elements scraped as jobs

### After:
- ✅ Completes in **15-20 minutes**
- ✅ Automatic retry on rate limits
- ✅ Only relevant, high-quality technical jobs
- ✅ Clean results (no UI elements)

## Usage

### For GitHub Actions (Default)
The workflow now automatically uses `config.ci.json`:
```bash
# Triggered via workflow_dispatch or scheduled runs
# No changes needed - it's automatic!
```

### For Local Development
Use the full `config.json` for comprehensive searches:
```bash
python match.py --config config.json
```

### Custom Config Override
Override in workflow:
```yaml
uses: ./.github/workflows/job-matcher.yml
with:
  config_path: config.custom.json
```

## Monitoring

Check workflow runs at:
- **Old repo**: https://github.com/Bhavana5N/resume_py/actions
- **New repo**: https://github.com/BNTiyan/resume_py/actions

Look for:
- ✅ Green checkmarks (success)
- ⏱️ Run time < 30 minutes
- 📊 Generated artifacts (resumes, cover letters)

## Troubleshooting

**Still timing out?**
- Reduce companies further (try 3 instead of 5)
- Increase `min_score` to 40+ to filter more aggressively
- Disable Selenium entirely: `"selenium_only": false`

**LLM rate limits?**
- Install Ollama for unlimited local generation (see `OLLAMA_SETUP.md`)
- The retry logic will automatically use it

**Too few results?**
- Lower `min_score` to 25
- Increase `fetch_limit` to 100
- Add more companies to `config.ci.json`

---

**Next Steps**: Your GitHub Actions should now complete successfully in under 30 minutes with high-quality job matches!
