# 🐛 Current Issues & Solutions

## Issues Found in Latest Run

### 1. ❌ `auto_tailor: False` - Resume Generation Disabled

**Symptom:**
```
[jobgen] ⚠️  Skipping Not specified. - auto_tailor is disabled
```

**Root Cause:**
The config being used in GitHub Actions has `auto_tailor_resume: false` or the setting is missing.

**Solution:**
Make sure your config has:
```json
{
  "auto_tailor_resume": true,
  "tailor_threshold": 50
}
```

**Quick Fix:**
The code now prints a warning if `auto_tailor_resume` is false:
```
[config] ⚠️  WARNING: auto_tailor_resume is FALSE in config!
[config] Resumes and cover letters will NOT be generated!
[config] Set 'auto_tailor_resume': true in your config.json
```

---

### 2. ⚠️  Company Name Shows "Not specified."

**Symptom:**
```
[debug] Job processing for Not specified.:
```

**Root Cause:**
Google jobs don't have the company field populated during scraping.

**Solution:**
The code now extracts company from source field:
```python
# Fix company name if not specified
if not company or company.lower() in ["not specified", "not specified."]:
    source = j.get("source", "")  # e.g., "selenium:google"
    if ":" in source:
        company = source.split(":")[-1].strip().title()  # "Google"
        j["company"] = company  # Update job object
```

**Status:** ✅ FIXED (but needs to be in GitHub repo)

---

## 🔧 How to Fix

### Option 1: Update Config (GitHub Secrets)

If using GitHub Actions, make sure the config file committed to the repo has:

```json
{
  "auto_tailor_resume": true,
  "tailor_threshold": 50,
  "min_score": 50,
  "companies": ["uber", "apple", "meta", "google", "amazon", "microsoft", "netflix"]
}
```

### Option 2: Force Enable in Workflow

Add this to `.github/workflows/job-matcher.yml`:

```yaml
- name: Enable auto-tailor
  run: |
    # Force enable auto_tailor in config
    python3 << 'EOF'
    import json
    with open('config.json', 'r+') as f:
        config = json.load(f)
        config['auto_tailor_resume'] = True
        config['tailor_threshold'] = 50
        f.seek(0)
        json.dump(config, f, indent=2)
        f.truncate()
    EOF
```

### Option 3: Use Simple Version

The simple version (`simple/match.py`) has these fixes built-in and is more reliable:

```bash
cd simple/
python match.py --config config.yaml
```

---

## 📊 What Should Happen

### ✅ Correct Output:
```
[config] auto_tailor_resume: True
[config] tailor_threshold: 50

[filter] ✅ Final job list:
  1. Google - Customer Solutions Engineer (score: 67.8)
  2. Google - Product Technology Manager (score: 63.0)

[parallel] Fetching job descriptions with 7 workers...
  [fetch] Google: ✅ 12000 chars

[debug] Job processing for Google:
  - use_job_app_gen: True
  - auto_tailor: True  ← SHOULD BE TRUE!
  - jd_len: 12000
  - job_url: https://...

[jobgen] Generating application package for Google...
  ✅ Resume: resume_Google_Customer_Solutions_Engineer.txt
  ✅ Cover letter: cover_Google_Customer_Solutions_Engineer.txt
```

### ❌ Current (Wrong) Output:
```
[debug] Job processing for Not specified.:
  - auto_tailor: False  ← WRONG!
  - jd_len: 12000

[jobgen] ⚠️  Skipping Not specified. - auto_tailor is disabled
```

---

## 🚀 Quick Action Items

1. **Check your config.json**:
   ```bash
   grep "auto_tailor_resume" config.json
   ```
   Should return: `"auto_tailor_resume": true,`

2. **Commit and push the updated files**:
   ```bash
   git add config.json config.fast.json match.py
   git commit -m "Fix: Enable auto_tailor and company name extraction"
   git push
   ```

3. **Re-run the workflow**

4. **Verify the output** shows:
   - `[config] auto_tailor_resume: True`
   - Company names (not "Not specified.")
   - `[jobgen] Generating application package...`
   - `✅ Resume saved`
   - `✅ Cover letter saved`

---

## 💡 Why This Happened

1. **Config not synced**: Local config.json might have `auto_tailor_resume: true`, but GitHub repo has old version
2. **Company extraction timing**: The fix exists but wasn't deployed yet
3. **Testing vs Production**: Works locally but not in GitHub Actions

---

## ✅ Verification Checklist

After fixing, you should see:

- [ ] `[config] auto_tailor_resume: True` in logs
- [ ] Company names instead of "Not specified."
- [ ] `[jobgen] Generating application package for Google...`
- [ ] Files in `output/cover_letters/`
- [ ] Files in `output/tailored_resumes/`
- [ ] Artifact uploads succeed

---

## 🆘 Still Not Working?

1. **Check the actual config being used**:
   Add this to the workflow before running match.py:
   ```yaml
   - name: Show config
     run: cat config.json | grep -A 2 "auto_tailor"
   ```

2. **Use the simple version** (recommended):
   ```yaml
   - name: Run simple matcher
     run: cd simple && python match.py --config config.yaml
   ```

3. **Enable debug mode**:
   ```yaml
   env:
     DEBUG: "1"
   ```

The new debug output will tell you exactly what's wrong! 🎯

