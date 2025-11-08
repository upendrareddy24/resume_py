# Career Page Patterns Guide

This document describes common patterns for scraping job listings from company career pages.

## Common Career Page Architectures

### 1. **Direct Job Listing Pages**
Companies that show jobs immediately on the careers page.
- **Example**: LinkedIn, Indeed, RemoteOK
- **Pattern**: Jobs are visible in the HTML on page load
- **Selectors**: `div[class*='job']`, `a[href*='/jobs/']`

### 2. **Search-First Pages**
Companies that require clicking a "Search Jobs" or "Find Roles" button first.
- **Examples**: Uber, Google, Amazon
- **Pattern**: Landing page → Click search → Job listings
- **Trigger Text**: "find open roles", "search jobs", "start job search"
- **Selectors**: Look for buttons/links with search-related text

### 3. **Filter-Based Pages**
Companies with location/team filters that must be applied.
- **Examples**: Apple, Meta, Microsoft
- **Pattern**: Filters → Apply filters → Job listings
- **Default Filters**: Often default to showing jobs or need location selection
- **Wait Strategy**: Wait for results to load after filter application

### 4. **Infinite Scroll Pages**
Companies that load jobs as you scroll.
- **Examples**: Netflix, Spotify
- **Pattern**: Initial load → Scroll → More jobs load
- **Strategy**: Scroll to bottom, wait, repeat

### 5. **ATS (Applicant Tracking System) Hosted**
Companies using third-party job boards.
- **Examples**: Greenhouse, Lever, Workday, SmartRecruiters
- **Pattern**: Standardized layouts per ATS provider
- **Advantage**: Consistent selectors across companies using same ATS

## Configuration Parameters

### Essential Fields

```json
{
  "url": "https://company.com/careers",
  "company": "company_name",
  "list_selector": "CSS selector for job listing containers",
  "title_selector": "CSS selector for job title",
  "location_selector": "CSS selector for location",
  "link_selector": "CSS selector for job detail link",
  "source": "selenium:company_name",
  "absolute_base": "https://company.com"
}
```

### Optional Enhancement Fields

```json
{
  "wait_selector": "CSS selector to wait for before scraping",
  "sleep_seconds": 3,
  "open_roles_text": ["find open roles", "view all jobs"],
  "search_patterns": ["search roles", "search jobs"],
  "scroll_to_load": true,
  "max_scrolls": 5,
  "domain_filter": "company.com",
  "require_path_contains": "/jobs/"
}
```

## Common Button/Link Patterns

### Search Triggers
- "search jobs"
- "search roles"
- "find jobs"
- "find open roles"
- "job search"
- "explore opportunities"

### View All Triggers
- "view all jobs"
- "see all openings"
- "see all roles"
- "current openings"
- "open positions"
- "browse jobs"

### Application Triggers
- "apply now"
- "apply for this job"
- "submit application"
- "easy apply"

## Common Selectors by ATS

### Greenhouse
```
list_selector: "div[class*='opening']"
title_selector: "a[class*='opening-title']"
link_selector: "a[href*='/jobs/']"
```

### Lever
```
list_selector: "div[class*='posting']"
title_selector: "h5[class*='posting-title']"
link_selector: "a[class*='posting-title']"
```

### Workday
```
list_selector: "li[class*='job']"
title_selector: "h3[class*='title']"
link_selector: "a[data-automation-id='jobTitle']"
```

### SmartRecruiters
```
list_selector: "li[class*='opening']"
title_selector: "h4[class*='link']"
link_selector: "a[class*='job-link']"
```

### Ashby
```
list_selector: "a[class*='job-posting']"
title_selector: "h3[class*='title']"
link_selector: "a"
```

## Job Description Extraction Patterns

### Section Headers to Look For
1. **Responsibilities**
   - "What You'll Do"
   - "Responsibilities"
   - "Job Duties"
   - "Your Role"
   - "Key Responsibilities"

2. **Minimum Qualifications**
   - "Minimum Qualifications"
   - "Required Qualifications"
   - "Requirements"
   - "Must Have"
   - "Basic Qualifications"
   - "You Have"

3. **Preferred Qualifications**
   - "Preferred Qualifications"
   - "Nice to Have"
   - "Bonus Points"
   - "Preferred Skills"
   - "Ideal Candidate"
   - "We'd Love If You"

4. **About the Role**
   - "About the Role"
   - "Job Overview"
   - "Position Summary"
   - "Role Description"

5. **About the Company**
   - "About Us"
   - "About [Company]"
   - "Who We Are"
   - "Company Overview"

## Debugging Tips

### 1. Check for Dynamic Content
If jobs aren't showing:
- Increase `sleep_seconds`
- Add `wait_selector` for a specific element
- Check if page uses infinite scroll

### 2. Verify Selectors
Use browser DevTools:
```javascript
// Test in browser console
document.querySelectorAll('your-selector-here')
```

### 3. Check for Auth Requirements
Some career pages require:
- Cookie acceptance
- Location selection
- Login (for internal positions)

### 4. Monitor for Changes
Career page structures change frequently. Monitor logs for:
- "0 jobs found" warnings
- Empty description warnings
- Selector mismatch errors

## Adding a New Company

1. **Find the careers page URL**
2. **Identify the architecture pattern** (see above)
3. **Use DevTools to find selectors**
   - Right-click on job title → Inspect
   - Find unique class/id patterns
   - Test selector in console
4. **Add to config.json**
5. **Test with small fetch_limit first**
6. **Monitor output and refine selectors**

## Example Configurations

### Tech Giant (Apple-style)
```json
{
  "url": "https://jobs.apple.com/en-us/search?location=united-states-USA",
  "company": "apple",
  "list_selector": "div[id*='job-']",
  "title_selector": "a[id*='job-title']",
  "location_selector": ".location",
  "link_selector": "a[href*='/details/']",
  "wait_selector": "div[id*='job-']",
  "sleep_seconds": 4,
  "absolute_base": "https://jobs.apple.com"
}
```

### Startup (Greenhouse-hosted)
```json
{
  "url": "https://boards.greenhouse.io/company",
  "company": "company",
  "list_selector": "div.opening",
  "title_selector": "a",
  "location_selector": "span.location",
  "link_selector": "a",
  "absolute_base": "https://boards.greenhouse.io"
}
```

### Search-First (Uber-style)
```json
{
  "url": "https://www.uber.com/us/en/careers/list/",
  "company": "uber",
  "list_selector": "div[data-testid='job-card']",
  "title_selector": "h3",
  "link_selector": "a",
  "open_roles_text": ["find open roles"],
  "search_patterns": ["search jobs"],
  "sleep_seconds": 3,
  "absolute_base": "https://www.uber.com"
}
```

## Troubleshooting Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| No jobs found | Wrong selectors | Use DevTools to find correct selectors |
| Empty descriptions | Jobs load dynamically | Increase sleep_seconds, add wait_selector |
| Duplicate jobs | Multiple selectors match same job | Make selectors more specific |
| Missing URLs | Relative URLs not resolved | Check absolute_base is correct |
| Jobs not clickable | Button click needed first | Add to open_roles_text or search_patterns |

## Future Enhancements

- [ ] Auto-detect ATS type from page HTML
- [ ] Smart selector fallback chain
- [ ] Auto-retry with different selectors
- [ ] Machine learning-based selector prediction
- [ ] Screenshot on failure for debugging
- [ ] A/B test different wait strategies

