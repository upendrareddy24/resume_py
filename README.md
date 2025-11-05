# Python Resume Tools

Python CLIs to tailor a resume to a job description (.docx) and fetch matched jobs.

## Setup

```bash
cd resume_py
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Tailor resume to JD (generate .docx)

```bash
# JD file (create one): ../resume/input/jd.txt
python tailor.py --jd ../resume/input/jd.txt \
  --resume ../resume/input/resume.txt \
  --out output/tailored.docx \
  --name "Bhavana Nare"
```

- Output: `resume_py/output/tailored.docx`

## Match jobs for resume (fuzzy scoring)

### Config-based (recommended)
Edit `resume_py/config.json`:
```json
{
  "resume": "../resume/input/resume.txt",
  "top": 15,
  "fetch": {
    "mode": "free",
    "source": "remoteok",
    "query": "Python MLOps Engineer",
    "location": null
  },
  "output": { "dir": "output", "prefix": "matches_daily" }
}
```
Run:
```bash
python match.py --config config.json
```
This will fetch the latest 15 jobs from the configured source/query and score them against your resume, saving to `output/matches_daily_<timestamp>.json`.

### Free sources (no API key)
```bash
python match.py --resume ../resume/input/resume.txt --free-source remotive --query "Python MLOps Engineer" --top 15
```

### SerpAPI (optional)
```bash
export SERPAPI_KEY=YOUR_KEY
python match.py --config config.json --query "Python MLOps Engineer site:linkedin.com/jobs"
```

## Schedule daily (macOS/Linux)
- Using cron (runs every day at 8am):
```bash
crontab -e
# add line (adjust path and venv):
0 8 * * * cd /Users/bhavananare/github/webapp/resume_py && /Users/bhavananare/github/webapp/resume_py/.venv/bin/python match.py --config /Users/bhavananare/github/webapp/resume_py/config.json >> /Users/bhavananare/github/webapp/resume_py/output/cron.log 2>&1
```

## Notes
- Config takes precedence unless CLI flags are provided for specific fields.
- Free sources are public boards; fields vary. Results are filtered by keywords client-side.
- Matching uses RapidFuzz token-set ratio + title boosts; tune by changing your query and resume content.


The workflow runs python resume_py/match.py with your config every 15 minutes.
match.py does:
Loads resume_py/config.json (e.g., top=15, source/query).
Fetches jobs from the selected source:
Free: Remotive/RemoteOK/Arbeitnow via public APIs.
Optional: SerpAPI Google Jobs if key+query provided.
Fallback: JSON file/URL if configured.
Scores each job against your resume using RapidFuzz token_set_ratio on concatenated job fields (title/company/location/description), with small boosts for titles containing Python/ML/MLOps/Data Engineer/Full‑Stack.
Sorts by score, keeps top N, writes JSON to resume_py/output/matches_*.json.
How you get the results
Each run uploads the JSON as a GitHub Actions artifact (named like job-matches-<run_id>).
The job summary also shows a short preview (last lines of the latest JSON).
Locally, you can run: python resume_py/match.py --config resume_py/config.json and open the file in resume_py/output/.

## Cover letter generator

Create a tailored cover letter (.docx) from your resume and a job description:

```bash
python cover_letter.py \
  --resume ../resume/input/resume.txt \
  --jd ../resume/input/jd.txt \
  --name "Bhavana Nare" \
  --company "Target Company" \
  --role "Senior ML Engineer" \
  --out output/cover_letter.docx
```

The generator extracts keywords from your resume and the JD, estimates an ATS overlap score, and writes a concise, keyword-rich letter.