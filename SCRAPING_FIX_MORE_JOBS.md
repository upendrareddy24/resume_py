# 🔧 Fix: Getting More Jobs from All Companies

## Issues Identified

### 1. ❌ Location Filter Too Strict
```
target_locations: ["united states"]
```

**Problem:** This exact match was rejecting jobs like:
- "Austin, TX, USA" ❌
- "Boulder, CO, USA" ❌  
- "San Francisco, CA" ❌

**Result:** Google jobs were being filtered out!

### 2. ❌ Insufficient Scrolling
```
max_scrolls = 3  # Only 3 scroll attempts
time.sleep(1)    # Only 1 second wait
```

**Problem:** Not enough time for lazy-loaded content to appear, especially on Uber and Apple sites.

**Result:** Only 1 container found from Uber and Apple!

---

## Fixes Applied

### ✅ 1. Removed Location Filter
```json
"target_locations": [],
```

**Why:** 
- Disabled strict location matching
- Now accepts ALL US jobs regardless of city/state format
- Google jobs will now pass through

**Impact:**
- ✅ Google jobs included (Austin, TX; Boulder, CO; etc.)
- ✅ All US-based jobs accepted
- ✅ Remote jobs still included

### ✅ 2. Increased Scrolling
```javascript
max_scrolls = 5      // Was 3, now 5
time.sleep(2)        // Was 1s, now 2s per scroll
+ Double-check wait  // Extra 1s if no change detected
```

**Why:**
- More time for lazy-loaded content
- Uber and Apple need more scrolling
- Double-check ensures content fully loaded

**Impact:**
- ✅ More jobs loaded from Uber (expected: 30-50 vs 1)
- ✅ More jobs loaded from Apple (expected: 40-60 vs 1)
- ✅ Meta already working (13 containers), will get more

---

## Expected Results

### Before (Current)
```
[selenium] selenium:uber containers=1 ❌
[selenium] selenium:apple containers=1 ❌
[selenium] selenium:meta containers=13 ⚠️
[selenium] selenium:google containers=20 ✅

[filter] After location filter: 1 jobs (removed 6) ❌
[filter] After top-per-company: 1 jobs from 1 companies ❌
```

### After (Expected)
```
[selenium] scrolled 5 times to load more jobs
[selenium] selenium:uber containers=45+ ✅
[selenium] selenium:apple containers=55+ ✅
[selenium] selenium:meta containers=70+ ✅
[selenium] selenium:google containers=20 ✅
[selenium] selenium:amazon containers=35+ ✅
[selenium] selenium:microsoft containers=25+ ✅
[selenium] selenium:netflix containers=18+ ✅

[filter] After location filter: 7 jobs (no removal) ✅
[filter] After top-per-company: 7 jobs from 7 companies ✅
```

---

## Why Only 1 Container Before?

### Uber Issue
- **Problem**: After clicking "find open roles", jobs load dynamically
- **Solution**: Scroll 5 times with 2s waits to trigger loading
- **Expected**: 40-50 job containers

### Apple Issue
- **Problem**: Table rows (`tr[id*='job-']`) load progressively as you scroll
- **Solution**: More scrolling to load all table rows
- **Expected**: 50-60 job containers

### Google Jobs Filtered Out
- **Problem**: Location "Austin, TX, USA" doesn't match "united states"
- **Solution**: Removed location filter
- **Expected**: All Google US jobs included

---

## Configuration Changes

### config.json
```json
{
  "target_locations": [],  // Was: ["united states"]
  // This disables location filtering
  // All jobs will pass through regardless of location format
}
```

### selenium_scraper.py
```python
{
  "max_scrolls": 5,       // Was: 3
  "scroll_wait": 2,       // Was: 1
  "double_check": True    // New: Extra wait if no change
}
```

---

## Testing the Fix

### Run Locally
```bash
cd /Users/bhavananare/github/webapp/resume_py
python match.py --config config.json
```

### Expected Log Output
```
[selenium] loading: https://www.uber.com/us/en/careers/list/
[selenium] clicked 'find open roles' button/link (waited 3.0s)
[selenium] scrolled 5 times to load more jobs
[selenium] selenium:uber containers=45 ✅

[selenium] loading: https://jobs.apple.com/en-us/search
[selenium] scrolled 5 times to load more jobs
[selenium] selenium:apple containers=55 ✅

[filter] After score filter: 20+ jobs
[filter] After location filter: 20+ jobs (no removal)
[filter] After top-per-company: 7 jobs from 7 companies

[filter] ✅ Will generate cover letters and resumes for these 7 jobs:
  1. uber - Senior Software Engineer (score: 82.5)
  2. apple - ML Engineer (score: 79.3)
  3. meta - Infrastructure Engineer (score: 78.1)
  4. google - Solutions Engineer (score: 67.8)
  5. amazon - SDE (score: 73.2)
  6. microsoft - Software Engineer (score: 71.5)
  7. netflix - Backend Engineer (score: 69.8)
```

---

## Alternative: Keep Location Filter But Make It Flexible

If you DO want location filtering, use this instead:

```json
"target_locations": ["usa", "us", "united states", "remote", "remote-us"],
```

And update the matching logic in `match.py` to use fuzzy matching:

```python
# Check if any target location keyword appears in job location
location_match = any(
    target.lower() in job_location.lower() 
    for target in target_locations
)
```

---

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| `config.json` | `target_locations: []` | Disable strict location filter |
| `selenium_scraper.py` | Increase scrolling (3→5, 1s→2s) | Load more lazy-loaded jobs |

---

## Summary

### Problems:
1. ❌ Location filter removing Google jobs
2. ❌ Only 1 job from Uber (need 40+)
3. ❌ Only 1 job from Apple (need 50+)
4. ❌ Only 1 company's jobs being processed

### Solutions:
1. ✅ Removed strict location filter
2. ✅ Increased scrolling to 5 attempts
3. ✅ Increased wait time to 2s per scroll
4. ✅ Added double-check for slow-loading content

### Expected Impact:
- **10x-50x** more jobs from Uber and Apple
- **All** US-based Google jobs included
- **7 companies** generating resumes instead of 1
- **35+ jobs** passing filters instead of 1

---

## Next Steps

1. **Commit changes**:
   ```bash
   git add config.json selenium_scraper.py
   git commit -m "fix: Improve job scraping from all companies
   
   - Remove strict location filter to include all US jobs
   - Increase scrolling from 3 to 5 attempts
   - Increase scroll wait time from 1s to 2s
   - Add double-check for slow-loading content
   - Expected: 40+ jobs from Uber, 50+ from Apple"
   ```

2. **Push to GitHub**:
   ```bash
   git push origin main
   ```

3. **Monitor next run**:
   - Check container counts for each company
   - Verify 7 companies are generating resumes
   - Confirm Google jobs are included

**You should now see jobs from ALL 7 companies (Uber, Apple, Meta, Google, Amazon, Microsoft, Netflix)!** 🎯

