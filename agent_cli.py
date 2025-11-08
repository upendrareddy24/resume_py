#!/usr/bin/env python3
"""
CLI for running the Job Application Agent
"""
import argparse
import json
from pathlib import Path
from job_application_agent import JobApplicationAgent, AgentConfig


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Job Application Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python agent_cli.py
  
  # Specify custom config
  python agent_cli.py --config my_config.json
  
  # Dry run (no submissions)
  python agent_cli.py --dry-run
  
  # Enable auto-submit (careful!)
  python agent_cli.py --auto-submit
  
  # Search specific companies
  python agent_cli.py --companies uber apple meta
  
  # Search specific roles
  python agent_cli.py --roles "software engineer" "ml engineer"
        """
    )
    
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    parser.add_argument(
        "--companies",
        nargs="+",
        help="Target companies to search"
    )
    parser.add_argument(
        "--roles",
        nargs="+",
        help="Target roles to search for"
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        help="Maximum jobs to apply to"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        help="Minimum match score (0-100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually submit applications"
    )
    parser.add_argument(
        "--auto-submit",
        action="store_true",
        help="Automatically submit applications"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for generated materials"
    )
    
    args = parser.parse_args()
    
    # Load base config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1
    
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    
    # Build agent configuration
    agent_config = AgentConfig(
        resume_path=config_dict.get("resume", "input/resume.txt"),
        candidate_name=config_dict.get("cover_letter", {}).get("name", "Candidate"),
        target_roles=args.roles or config_dict.get("companies", ["software engineer"]),
        target_companies=args.companies or config_dict.get("companies", []),
        max_jobs_to_fetch=config_dict.get("fetch_limit", 500),
        max_jobs_to_apply=args.max_jobs or config_dict.get("top", 15),
        min_match_score=args.min_score or 60.0,
        auto_generate_resume=config_dict.get("auto_tailor_resume", True),
        auto_generate_cover_letter=True,
        auto_submit=args.auto_submit or config_dict.get("autofill", {}).get("enabled", False),
        dry_run=args.dry_run,
        output_dir=args.output_dir or config_dict.get("output", {}).get("dir", "output"),
        verbose=True
    )
    
    # Build job sources from config
    sources = []
    
    # Add selenium sites
    selenium_sites = config_dict.get("selenium_options", {}).get("sites", [])
    for site in selenium_sites:
        if isinstance(site, dict) and site.get("url"):
            sources.append(site)
        elif isinstance(site, str):
            sources.append({"url": site})
    
    # Add default career pages if no sources
    if not sources and agent_config.target_companies:
        # Map common companies to their career URLs
        career_urls = {
            "uber": "https://www.uber.com/us/en/careers/list/",
            "apple": "https://jobs.apple.com/en-us/search?location=united-states-USA",
            "meta": "https://www.metacareers.com/jobs",
            "google": "https://careers.google.com/jobs/results/",
            "amazon": "https://www.amazon.jobs/en/search",
            "microsoft": "https://careers.microsoft.com/us/en/search-results",
            "openai": "https://openai.com/careers/search/"
        }
        
        for company in agent_config.target_companies:
            company_lower = company.lower()
            if company_lower in career_urls:
                sources.append({
                    "url": career_urls[company_lower],
                    "company": company
                })
    
    if not sources:
        print("Error: No job sources configured. Add 'selenium_options.sites' to config.json")
        return 1
    
    print(f"\nJob Application Agent")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Resume: {agent_config.resume_path}")
    print(f"  Target roles: {', '.join(agent_config.target_roles)}")
    print(f"  Target companies: {', '.join(agent_config.target_companies) if agent_config.target_companies else 'Any'}")
    print(f"  Max applications: {agent_config.max_jobs_to_apply}")
    print(f"  Min score: {agent_config.min_match_score}")
    print(f"  Auto-submit: {agent_config.auto_submit} (dry_run={agent_config.dry_run})")
    print(f"  Output: {agent_config.output_dir}")
    print(f"  Sources: {len(sources)} configured")
    print("=" * 60)
    
    if agent_config.auto_submit and not agent_config.dry_run:
        response = input("\n⚠️  Auto-submit is ENABLED. Applications will be submitted automatically. Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return 0
    
    # Create and run agent
    try:
        agent = JobApplicationAgent(agent_config)
        results = agent.run(sources)
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✓ Jobs discovered: {results['jobs_discovered']}")
        print(f"✓ Jobs analyzed: {results['jobs_analyzed']}")
        print(f"✓ Jobs above threshold: {results['jobs_above_threshold']}")
        print(f"✓ Resumes generated: {results['resumes_generated']}")
        print(f"✓ Cover letters generated: {results['cover_letters_generated']}")
        print(f"✓ Applications submitted: {results['applications_submitted']}")
        if results['failures'] > 0:
            print(f"⚠ Failures: {results['failures']}")
        print(f"⏱  Time: {results['elapsed_seconds']:.1f}s")
        print("=" * 60)
        
        # Save results
        results_path = Path(agent_config.output_dir) / "agent_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_path}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nAgent interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n\nAgent failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

