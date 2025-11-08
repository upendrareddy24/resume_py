# GitHub Actions Pipeline Setup

## 🚀 Quick Start

Your Job Application Agent can now run automatically in GitHub Actions!

### Prerequisites

1. **GitHub Repository** with this code
2. **GitHub Secrets** configured:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `SERPAPI_KEY` - (Optional) For job search APIs

### Setup Steps

#### 1. Add GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
```
Name: OPENAI_API_KEY
Value: sk-...your-key...

Name: SERPAPI_KEY  (optional)
Value: ...your-serpapi-key...
```

#### 2. Commit the Workflow

The workflow file is already created at:
```
.github/workflows/agent-pipeline.yml
```

Commit and push it to your repository.

#### 3. Run the Agent

**Option A: Manual Trigger**

1. Go to Actions tab in GitHub
2. Click "Job Application Agent Pipeline"
3. Click "Run workflow"
4. Configure options:
   - **Mode**: `agent` (recommended) or `legacy`
   - **Max Jobs**: Number of applications to generate (default: 10)
   - **Min Score**: Minimum match score 0-100 (default: 60)
   - **Dry Run**: `true` (safe, no submissions) or `false` (submit applications)
   - **Config Path**: Path to your config.json

5. Click "Run workflow"

**Option B: Scheduled Run**

The agent runs automatically every day at 9 AM UTC.

To change the schedule, edit `.github/workflows/agent-pipeline.yml`:
```yaml
schedule:
  - cron: '0 9 * * *'  # Daily at 9 AM UTC
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 0 * * 1'  # Every Monday
```

## 📊 Workflow Options

### Agent Mode (Recommended)

Uses the new intelligent agent:
```yaml
mode: agent
max_jobs: 10
min_score: 60
dry_run: true
```

Features:
- Auto-detecting job scraper
- LLM-powered extraction
- Parallel generation
- Smart fallbacks
- Comprehensive statistics

### Legacy Mode

Uses the original match.py:
```yaml
mode: legacy
```

Features:
- Original matching logic
- Backward compatible
- All config.json options

## 📁 Artifacts

After each run, download artifacts from the Actions page:

- **agent-results-XXX**: JSON results with statistics
- **resumes-XXX**: All generated tailored resumes
- **cover-letters-XXX**: All generated cover letters
- **job-matches-XXX**: Job listings and matches

Artifacts are kept for 30 days.

## 📈 GitHub Summary

Each run creates a summary showing:
- Jobs discovered, analyzed, above threshold
- Resumes and cover letters generated
- Applications submitted
- Top 10 matches with scores
- List of generated files

View it in: Actions → Your workflow run → Summary

## 🔧 Configuration

### Environment Variables

Set in the workflow or in your config:

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  OPENAI_EMBED_MODEL: "text-embedding-3-small"
  SERPAPI_KEY: ${{ secrets.SERPAPI_KEY }}
```

### Config File

Edit `config.json` in your repository:

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
      }
    ]
  }
}
```

## 🎯 Example Workflow Runs

### Daily Discovery

Schedule it to run every morning and review matches:

```yaml
# In agent-pipeline.yml
schedule:
  - cron: '0 9 * * *'  # 9 AM UTC daily
```

### Targeted Blitz

Run manually with specific settings:

```
Mode: agent
Max Jobs: 20
Min Score: 75
Dry Run: false  # Actually submit!
```

### Weekend Job Hunt

Run on weekends when you have time to review:

```yaml
schedule:
  - cron: '0 10 * * 6'  # Saturdays at 10 AM
  - cron: '0 10 * * 0'  # Sundays at 10 AM
```

## 🔒 Security

### Secrets Protection

- Never commit API keys to the repository
- Use GitHub Secrets for all sensitive data
- Keys are masked in logs automatically

### Dry Run by Default

- Workflow defaults to `dry_run: true`
- Review generated materials before enabling submissions
- Confirmation required for actual submissions

### Rate Limiting

The agent respects rate limits:
- 2-second delay between LLM calls
- Configurable wait times
- Max jobs limit prevents runaway costs

## 🐛 Troubleshooting

### Workflow Fails to Start

**Problem**: Workflow doesn't appear in Actions tab

**Solution**:
1. Ensure `.github/workflows/agent-pipeline.yml` is in main branch
2. Check YAML syntax: `yamllint agent-pipeline.yml`
3. Verify file permissions

### No Jobs Found

**Problem**: "Jobs discovered: 0"

**Solution**:
1. Check career URLs in `config.json` are accessible
2. Verify Selenium is working (check Chrome installation in logs)
3. Increase `sleep_seconds` in site configs

### LLM Errors

**Problem**: "Failed to initialize LLM"

**Solution**:
1. Verify `OPENAI_API_KEY` secret is set correctly
2. Check API key has credits/quota
3. Review logs for specific error messages

### Empty Job Descriptions

**Problem**: "Job description too short or empty"

**Solution**:
1. The agent now automatically fetches from URLs
2. Enable LLM extraction (automatic in new mode)
3. Check job URLs are valid and accessible

### Artifact Upload Fails

**Problem**: "No files found" in artifacts

**Solution**:
1. Check `output/` directory is created
2. Verify files are generated (check logs)
3. Review artifact path patterns in workflow

## 📊 Monitoring

### Check Run Status

```bash
# View recent runs
gh run list --workflow=agent-pipeline.yml

# View specific run logs
gh run view RUN_ID --log

# Download artifacts
gh run download RUN_ID
```

### Email Notifications

GitHub sends notifications for:
- Workflow failures
- Scheduled run results
- Manual run completion

Configure in: Settings → Notifications

### Slack/Discord Integration

Add notification steps to the workflow:

```yaml
- name: Notify Slack
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Job Agent completed: ${{ job.status }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## 🎉 Success Metrics

Track your pipeline success:

1. **Discovery Rate**: Jobs found vs. expected
2. **Match Rate**: Jobs above threshold / Total jobs
3. **Generation Rate**: Materials generated / Matched jobs
4. **Submission Rate**: Submitted / Generated (if enabled)
5. **Error Rate**: Failures / Total runs

View these in the GitHub Summary after each run.

## 🔄 Updates

### Update Dependencies

```yaml
# Add to workflow
- name: Update dependencies
  run: |
    pip install --upgrade pip
    pip list --outdated
```

### Update Agent Code

Push changes to main branch:
```bash
git add agent_cli.py job_application_agent.py
git commit -m "Improve agent logic"
git push
```

Workflow automatically uses latest code.

### Update Config

Edit and push `config.json`:
```bash
git add config.json
git commit -m "Update target companies"
git push
```

Changes apply to next run.

## 💡 Pro Tips

1. **Start with dry run**: Always test with `dry_run: true` first
2. **Review artifacts**: Download and check quality before enabling auto-submit
3. **Use notifications**: Set up Slack/email for important runs
4. **Monitor costs**: Track OpenAI API usage in their dashboard
5. **Iterate config**: Adjust `min_score` and `max_jobs` based on results
6. **Schedule wisely**: Run when job postings are fresh (mornings, weekdays)
7. **Backup artifacts**: Download important applications locally
8. **Check logs**: Review full logs for debugging and optimization

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AGENT_README.md](AGENT_README.md) - Complete agent guide
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details
- [CAREER_PAGE_PATTERNS.md](CAREER_PAGE_PATTERNS.md) - Scraping patterns

---

**Your automated job search is now running! 🚀**

Check the Actions tab to see your first run.

