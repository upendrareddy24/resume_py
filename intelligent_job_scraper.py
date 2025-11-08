"""
Intelligent job scraper that auto-detects career page patterns and extracts jobs.
Works with various ATS systems and custom career pages.
"""
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class IntelligentJobScraper:
    """
    Auto-detects career page patterns and extracts job listings.
    """
    
    # Common ATS patterns
    ATS_PATTERNS = {
        "greenhouse": {
            "domain_match": "greenhouse.io",
            "list_selector": "div.opening, div[class*='opening']",
            "title_selector": "a",
            "location_selector": "span.location, .location",
            "link_selector": "a"
        },
        "lever": {
            "domain_match": "lever.co",
            "list_selector": "div.posting, div[class*='posting']",
            "title_selector": "h5, a.posting-title",
            "location_selector": "span.location, .location",
            "link_selector": "a.posting-title, a"
        },
        "workday": {
            "domain_match": "myworkdayjobs.com",
            "list_selector": "li[class*='job'], ul[class*='job'] > li",
            "title_selector": "h3, a[data-automation-id='jobTitle']",
            "location_selector": "dd[class*='location']",
            "link_selector": "a"
        },
        "smartrecruiters": {
            "domain_match": "smartrecruiters.com",
            "list_selector": "li[class*='opening']",
            "title_selector": "h4, a[class*='link']",
            "location_selector": "span[class*='location']",
            "link_selector": "a"
        },
        "ashby": {
            "domain_match": "ashbyhq.com",
            "list_selector": "a[class*='job-posting'], div[class*='job']",
            "title_selector": "h3, span[class*='title']",
            "location_selector": "span[class*='location']",
            "link_selector": "a"
        }
    }
    
    # Generic fallback selectors (try in order)
    GENERIC_SELECTORS = {
        "list": [
            "div[class*='job']",
            "li[class*='job']",
            "a[href*='/jobs/']",
            "div[class*='posting']",
            "div[class*='opening']",
            "div[class*='position']",
            "article",
            "tr[class*='job']"
        ],
        "title": [
            "h3",
            "h4",
            "h2",
            "a[class*='title']",
            "span[class*='title']",
            ".job-title",
            ".title",
            "a"
        ],
        "location": [
            "span[class*='location']",
            "div[class*='location']",
            ".location",
            "span[class*='city']",
            "[data-location]"
        ]
    }
    
    # Common trigger patterns for navigation
    TRIGGER_PATTERNS = [
        "find open roles",
        "start job search",
        "view all jobs",
        "see all openings",
        "search jobs",
        "search roles",
        "current openings",
        "explore opportunities",
        "browse jobs"
    ]
    
    def __init__(self, driver_factory=None, verbose: bool = True):
        """
        Initialize the intelligent scraper.
        
        Args:
            driver_factory: Function that returns a Selenium WebDriver
            verbose: Whether to print debug information
        """
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium not available")
        
        self.driver_factory = driver_factory
        self.driver = None
        self.verbose = verbose
    
    def _log(self, message: str):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[intelligent_scraper] {message}")
    
    def _detect_ats(self, url: str, page_source: str) -> Optional[str]:
        """
        Detect which ATS system is being used.
        
        Args:
            url: The page URL
            page_source: The page HTML source
            
        Returns:
            ATS name if detected, None otherwise
        """
        # Check URL for ATS domains
        for ats_name, patterns in self.ATS_PATTERNS.items():
            if patterns["domain_match"] in url.lower():
                self._log(f"Detected {ats_name} from URL")
                return ats_name
        
        # Check page source for ATS signatures
        page_lower = page_source.lower()
        if "greenhouse" in page_lower or "grnhse" in page_lower:
            return "greenhouse"
        elif "lever" in page_lower and "postings" in page_lower:
            return "lever"
        elif "workday" in page_lower:
            return "workday"
        elif "smartrecruiters" in page_lower:
            return "smartrecruiters"
        elif "ashby" in page_lower:
            return "ashby"
        
        return None
    
    def _try_click_triggers(self, driver):
        """
        Try to find and click common trigger buttons/links.
        
        Args:
            driver: Selenium WebDriver instance
        """
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for pattern in self.TRIGGER_PATTERNS:
                if pattern.lower() in page_text:
                    # Try multiple strategies to find clickable elements
                    selectors = [
                        (By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"),
                        (By.CSS_SELECTOR, f"button:contains('{pattern}')"),
                        (By.CSS_SELECTOR, f"a:contains('{pattern}')"),
                        (By.XPATH, f"//button[contains(., '{pattern}')]"),
                        (By.XPATH, f"//a[contains(., '{pattern}')]"),
                    ]
                    
                    for by, selector in selectors:
                        try:
                            elements = driver.find_elements(by, selector)
                            if elements:
                                elem = elements[0]
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                time.sleep(0.5)
                                elem.click()
                                time.sleep(2)
                                self._log(f"Clicked trigger: '{pattern}'")
                                return True
                        except Exception:
                            continue
        except Exception as e:
            self._log(f"Trigger click failed: {e}")
        
        return False
    
    def _find_best_selector(self, driver, selectors: List[str]) -> Optional[str]:
        """
        Find the selector that returns the most elements.
        
        Args:
            driver: Selenium WebDriver instance
            selectors: List of CSS selectors to try
            
        Returns:
            Best selector or None
        """
        best_selector = None
        max_count = 0
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                count = len(elements)
                if count > max_count:
                    max_count = count
                    best_selector = selector
            except Exception:
                continue
        
        if best_selector and max_count > 0:
            self._log(f"Best selector '{best_selector}' found {max_count} elements")
            return best_selector
        
        return None
    
    def scrape_jobs(
        self,
        url: str,
        company: str = "",
        max_jobs: int = 100,
        wait_seconds: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Intelligently scrape jobs from a career page.
        
        Args:
            url: Career page URL
            company: Company name (optional)
            max_jobs: Maximum number of jobs to extract
            wait_seconds: Seconds to wait for page load
            
        Returns:
            List of job dictionaries with title, location, url, company
        """
        if not self.driver_factory:
            raise ValueError("No driver factory provided")
        
        self.driver = self.driver_factory()
        jobs = []
        
        try:
            self._log(f"Loading {url}")
            self.driver.get(url)
            time.sleep(wait_seconds)
            
            # Try to click navigation triggers
            self._try_click_triggers(self.driver)
            time.sleep(2)
            
            # Detect ATS
            page_source = self.driver.page_source
            ats_type = self._detect_ats(url, page_source)
            
            # Get selectors based on ATS or use generic
            if ats_type and ats_type in self.ATS_PATTERNS:
                patterns = self.ATS_PATTERNS[ats_type]
                list_selector = patterns["list_selector"]
                title_selector = patterns["title_selector"]
                location_selector = patterns["location_selector"]
                link_selector = patterns["link_selector"]
                self._log(f"Using {ats_type} selectors")
            else:
                # Use generic selectors
                self._log("Using generic selectors")
                list_selector = self._find_best_selector(self.driver, self.GENERIC_SELECTORS["list"])
                if not list_selector:
                    self._log("No job listings found")
                    return jobs
                
                title_selector = self.GENERIC_SELECTORS["title"][0]
                location_selector = self.GENERIC_SELECTORS["location"][0]
                link_selector = "a"
            
            # Extract job listings
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, list_selector)
            self._log(f"Found {len(job_elements)} potential job elements")
            
            for idx, elem in enumerate(job_elements[:max_jobs]):
                try:
                    job = {
                        "title": "",
                        "location": "",
                        "url": "",
                        "company": company,
                        "description": "",
                        "source": f"intelligent_scraper:{company or 'unknown'}"
                    }
                    
                    # Extract title
                    try:
                        title_elem = elem.find_element(By.CSS_SELECTOR, title_selector)
                        job["title"] = title_elem.text.strip()
                    except Exception:
                        job["title"] = elem.text.strip()[:100]
                    
                    # Extract location
                    try:
                        loc_elem = elem.find_element(By.CSS_SELECTOR, location_selector)
                        job["location"] = loc_elem.text.strip()
                    except Exception:
                        pass
                    
                    # Extract URL
                    try:
                        link_elem = elem.find_element(By.CSS_SELECTOR, link_selector)
                        href = link_elem.get_attribute("href")
                        if href:
                            if href.startswith("http"):
                                job["url"] = href
                            else:
                                job["url"] = urljoin(base_url, href)
                    except Exception:
                        # Try to get href from elem itself if it's an anchor
                        href = elem.get_attribute("href")
                        if href:
                            job["url"] = urljoin(base_url, href) if not href.startswith("http") else href
                    
                    # Only add jobs with at least a title
                    if job["title"]:
                        jobs.append(job)
                        if self.verbose and idx < 5:  # Log first 5 jobs
                            self._log(f"  Job {idx+1}: {job['title'][:50]}... @ {job['location']}")
                
                except Exception as e:
                    self._log(f"Error extracting job {idx}: {e}")
                    continue
            
            self._log(f"Successfully extracted {len(jobs)} jobs")
            
        except Exception as e:
            self._log(f"Scraping failed: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return jobs


def scrape_jobs_from_url(
    url: str,
    company: str = "",
    driver_factory=None,
    max_jobs: int = 100,
    wait_seconds: int = 5,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape jobs from a URL.
    
    Args:
        url: Career page URL
        company: Company name
        driver_factory: Function that returns a Selenium WebDriver
        max_jobs: Maximum jobs to extract
        wait_seconds: Wait time for page load
        verbose: Print debug info
        
    Returns:
        List of job dictionaries
    """
    scraper = IntelligentJobScraper(driver_factory, verbose)
    return scraper.scrape_jobs(url, company, max_jobs, wait_seconds)

