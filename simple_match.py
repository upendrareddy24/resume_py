"""
Simplified Job Matcher - Core Logic
No embeddings, no complex dependencies, just reliable job matching and resume generation.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from rapidfuzz import fuzz

# Try to load optional dependencies
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

try:
    import openai_compat
except:
    pass


class SimpleJobMatcher:
    """Simplified job matching with minimal dependencies"""
    
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.resume_text = self.load_resume()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
    def load_config(self, path: str) -> Dict:
        """Load configuration from JSON or YAML"""
        with open(path) as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                import yaml
                return yaml.safe_load(f)
            return json.load(f)
    
    def load_resume(self) -> str:
        """Load resume text"""
        resume_path = self.config.get('resume', 'input/resume.txt')
        with open(resume_path) as f:
            return f.read()
    
    def scrape_jobs(self) -> List[Dict]:
        """Scrape jobs from configured companies"""
        from selenium_scraper import fetch_selenium_sites
        
        companies = self.config.get('companies', [])
        fetch_limit = self.config.get('fetch_limit', 10)
        
        print(f"[scrape] Fetching up to {fetch_limit} jobs from {len(companies)} companies...")
        
        jobs = fetch_selenium_sites(
            sites=self.get_selenium_config(),
            fetch_limit=fetch_limit
        )
        
        print(f"[scrape] Found {len(jobs)} jobs")
        return jobs
    
    def get_selenium_config(self) -> List[Dict]:
        """Get Selenium configuration for companies"""
        # This would read from config.json selenium_options.sites
        # Simplified for now
        return self.config.get('selenium_options', {}).get('sites', [])
    
    def score_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Score jobs based on resume match"""
        print(f"[score] Scoring {len(jobs)} jobs...")
        
        for job in jobs:
            title = job.get('title', '')
            description = job.get('description', '')
            combined = f"{title} {description}"
            
            # Fuzzy match against resume
            score = fuzz.token_set_ratio(self.resume_text, combined)
            job['score'] = score
        
        # Sort by score descending
        jobs.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        print(f"[score] Top score: {jobs[0]['score']:.1f}" if jobs else "[score] No jobs to score")
        return jobs
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs by score, location, and company"""
        min_score = self.config.get('min_score', 50)
        locations = self.config.get('target_locations', [])
        top_per_company = self.config.get('top_per_company', True)
        
        print(f"[filter] Filtering with min_score={min_score}, locations={locations}")
        
        # Filter by score
        filtered = [j for j in jobs if j.get('score', 0) >= min_score]
        print(f"[filter] After score filter: {len(filtered)} jobs")
        
        # Filter by location
        if locations:
            location_filtered = []
            for job in filtered:
                job_location = (job.get('location') or '').lower()
                if any(loc.lower() in job_location for loc in locations):
                    location_filtered.append(job)
            
            if location_filtered:
                filtered = location_filtered
                print(f"[filter] After location filter: {len(filtered)} jobs")
            else:
                print(f"[filter] No location matches, keeping all {len(filtered)} jobs")
        
        # Keep top per company
        if top_per_company and filtered:
            company_best = {}
            for job in filtered:
                company = self.extract_company(job)
                if not company:
                    continue
                
                if company not in company_best or job['score'] > company_best[company]['score']:
                    company_best[company] = job
            
            filtered = list(company_best.values())
            filtered.sort(key=lambda x: x.get('score', 0), reverse=True)
            print(f"[filter] After top-per-company: {len(filtered)} jobs from {len(company_best)} companies")
        
        # Show final list
        if filtered:
            print(f"[filter] ✅ Final job list:")
            for i, job in enumerate(filtered, 1):
                company = self.extract_company(job)
                title = job.get('title', 'Unknown')[:50]
                score = job.get('score', 0)
                print(f"  {i}. {company} - {title} (score: {score:.1f})")
        else:
            print(f"[filter] ❌ No jobs passed filters!")
        
        return filtered
    
    def extract_company(self, job: Dict) -> str:
        """Extract company name from job"""
        company = (job.get('company') or '').strip()
        
        # Fallback to source if not specified
        if not company or company.lower() in ['not specified', 'not specified.']:
            source = job.get('source', '')
            if ':' in source:
                company = source.split(':')[-1].strip().title()
        
        return company or 'Unknown'
    
    def fetch_descriptions_parallel(self, jobs: List[Dict]) -> List[Dict]:
        """Fetch job descriptions in parallel"""
        workers = min(self.config.get('parallel_workers', 5), len(jobs))
        
        print(f"[parallel] Fetching job descriptions with {workers} workers...")
        
        def fetch_one(job: Dict) -> Dict:
            url = job.get('url', '').strip()
            company = self.extract_company(job)
            
            if not url:
                return job
            
            print(f"  [fetch] {company}: {url[:60]}...")
            
            try:
                # Try to fetch description
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                resp = requests.get(url, timeout=30, headers=headers)
                resp.raise_for_status()
                
                # Extract text from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Remove script and style tags
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)
                
                if len(text) > 200:
                    job['description'] = text[:10000]  # Limit to 10k chars
                    print(f"  [fetch] {company}: ✅ {len(text)} chars")
                else:
                    print(f"  [fetch] {company}: ⚠️ Short result, using minimal")
                    job['description'] = f"Position: {job.get('title', '')} at {company}"
                
            except Exception as e:
                print(f"  [fetch] {company}: ❌ {e}")
                job['description'] = f"Position: {job.get('title', '')} at {company}. URL: {url}"
            
            return job
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(fetch_one, job): i for i, job in enumerate(jobs)}
            
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    jobs[idx] = future.result()
                except Exception as e:
                    print(f"  [fetch] Error: {e}")
        
        print(f"[parallel] ✅ Fetching complete!")
        return jobs
    
    def generate_applications(self, jobs: List[Dict]) -> Dict[str, Dict]:
        """Generate resumes and cover letters for jobs"""
        if not self.openai_key:
            print("[generate] ⚠️ No OpenAI API key, skipping generation")
            return {}
        
        try:
            from job_application_generator import JobApplicationGenerator
            generator = JobApplicationGenerator(self.openai_key)
            generator.set_resume(self.resume_text)
        except Exception as e:
            print(f"[generate] ❌ Failed to initialize generator: {e}")
            return {}
        
        output_dir = Path(self.config.get('output', {}).get('dir', 'output'))
        letters_dir = output_dir / 'cover_letters'
        resumes_dir = output_dir / 'tailored_resumes'
        summaries_dir = output_dir / 'job_summaries'
        
        letters_dir.mkdir(parents=True, exist_ok=True)
        resumes_dir.mkdir(parents=True, exist_ok=True)
        summaries_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for i, job in enumerate(jobs, 1):
            company = self.extract_company(job)
            title = job.get('title', 'Role')
            description = job.get('description', '')
            
            if not description or len(description) < 50:
                print(f"[generate] {i}/{len(jobs)}: {company} - ⚠️ No description, skipping")
                continue
            
            print(f"[generate] {i}/{len(jobs)}: {company} - {title[:40]}...")
            
            try:
                # Generate resume + cover letter + summary
                result = generator.generate_application_package(
                    description, company, title, parallel=True
                )
                
                # Save files
                base = re.sub(r'[^A-Za-z0-9_-]+', '_', f"{company}_{title}")[:80]
                
                if result.get('resume'):
                    resume_path = resumes_dir / f"resume_{base}.txt"
                    resume_path.write_text(result['resume'])
                    print(f"  ✅ Resume: {resume_path.name}")
                
                if result.get('cover_letter'):
                    letter_path = letters_dir / f"cover_{base}.txt"
                    letter_path.write_text(result['cover_letter'])
                    print(f"  ✅ Cover letter: {letter_path.name}")
                
                if result.get('job_summary'):
                    summary_path = summaries_dir / f"summary_{base}.txt"
                    summary_path.write_text(result['job_summary'])
                    print(f"  ✅ Summary: {summary_path.name}")
                
                results[job.get('url', base)] = {
                    'company': company,
                    'title': title,
                    'resume': str(resume_path) if result.get('resume') else None,
                    'cover_letter': str(letter_path) if result.get('cover_letter') else None,
                    'summary': str(summary_path) if result.get('job_summary') else None,
                }
                
            except Exception as e:
                print(f"  ❌ Generation failed: {e}")
        
        print(f"\n[generate] ✅ Generated {len(results)} application packages")
        return results
    
    def save_results(self, jobs: List[Dict], results: Dict):
        """Save job matches and results"""
        output_dir = Path(self.config.get('output', {}).get('dir', 'output'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefix = self.config.get('output', {}).get('prefix', 'matches')
        
        # Save JSON
        json_path = output_dir / f"{prefix}_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'jobs': jobs,
                'results': results,
                'total_jobs': len(jobs),
                'generated': len(results)
            }, f, indent=2)
        
        print(f"[save] ✅ Results saved to {json_path}")
    
    def run(self):
        """Main execution flow"""
        print("="*60)
        print("🚀 Simple Job Matcher")
        print("="*60)
        
        # 1. Scrape jobs
        jobs = self.scrape_jobs()
        
        # 2. Score jobs
        jobs = self.score_jobs(jobs)
        
        # 3. Filter jobs
        filtered_jobs = self.filter_jobs(jobs)
        
        if not filtered_jobs:
            print("\n❌ No jobs passed filters. Exiting.")
            return
        
        # 4. Fetch descriptions in parallel
        filtered_jobs = self.fetch_descriptions_parallel(filtered_jobs)
        
        # 5. Generate applications
        results = self.generate_applications(filtered_jobs)
        
        # 6. Save results
        self.save_results(filtered_jobs, results)
        
        print("\n" + "="*60)
        print("✅ Job matching complete!")
        print("="*60)


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='Simple Job Matcher')
    parser.add_argument('--config', default='config.json', help='Config file path')
    args = parser.parse_args()
    
    try:
        matcher = SimpleJobMatcher(args.config)
        matcher.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

