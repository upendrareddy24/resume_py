import time
import requests
from typing import Any
from urllib.parse import urljoin, urlparse

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False


def create_chrome_driver(headless: bool = True, window_size: str = "1920,1080") -> Any:
    if not SELENIUM_AVAILABLE:
        return None
    chrome_options = ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    if window_size:
        chrome_options.add_argument(f"--window-size={window_size}")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(5)
    return driver


def create_headless_driver() -> Any:
    return create_chrome_driver(headless=True)


def fetch_selenium_sites(sites: list[Any], fetch_limit: int) -> list[dict[str, Any]]:
    if not SELENIUM_AVAILABLE:
        return []
    driver = create_headless_driver()
    if driver is None:
        return []
    results: list[dict[str, Any]] = []
    # Normalize sites to dict entries even if provided as plain URLs
    normalized: list[dict[str, Any]] = []
    for site in sites or []:
        if isinstance(site, str):
            try:
                p = urlparse(site)
                absolute_base = f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else site
                normalized.append({
                    "url": site,
                    "list_selector": "a[href*='job'], a[href*='/jobs/'], a[href*='/careers/']",
                    "title_selector": "",
                    "location_selector": "",
                    "link_selector": "a",
                    "company": "",
                    "source": f"selenium:{p.netloc or 'site'}",
                    "careers_url": site,
                    "domain_filter": "",
                    "require_path_contains": "",
                    "absolute_base": absolute_base,
                    "open_roles_text": ["open roles", "view all jobs", "see all openings", "current openings", "job openings", "find open roles"],
                    "search_patterns": ["search for open roles", "search roles", "search jobs", "find jobs", "job search", "search openings", "start job search"]
                })
            except Exception:
                continue
        elif isinstance(site, dict):
            normalized.append(site)
    sites = normalized
    try:
        for site in sites or []:
            url = site.get("url")
            if not url:
                continue
            list_sel = site.get("list_selector") or ""
            item_sel = site.get("item_selector") or ""
            title_sel = site.get("title_selector") or ""
            loc_sel = site.get("location_selector") or ""
            link_sel = site.get("link_selector") or "a"
            desc_sel = site.get("description_selector") or ""
            source = site.get("source") or f"selenium:{url.split('/')[2]}"
            careers_url = site.get("careers_url") or url
            domain_filter = site.get("domain_filter") or ""
            require_path_contains = site.get("require_path_contains") or ""
            absolute_base = site.get("absolute_base") or url

            try:
                print(f"[selenium] loading: {url} source={source} company={site.get('company')}")
            except Exception:
                pass
            driver.get(url)

            # Optional explicit wait for dynamic pages
            wait_sel = site.get("wait_selector")
            try:
                if wait_sel:
                    WebDriverWait(driver, 12).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_sel))
                    )
            except Exception:
                pass

            # Optional sleep for heavy JS pages
            try:
                sleep_seconds = float(site.get("sleep_seconds") or 0)
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
            except Exception:
                pass
            
            # Try to find "open roles" or similar text and click it
            open_roles_patterns = site.get("open_roles_text") or []
            search_patterns = site.get("search_patterns") or []
            all_patterns = open_roles_patterns + search_patterns
            
            if all_patterns:
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                    
                    # First try to find and click search-related buttons
                    for pattern in all_patterns:
                        if pattern.lower() in page_text:
                            # Try multiple ways to find clickable elements
                            clickable_selectors = [
                                # XPath for text content
                                (By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"),
                                # Common button/link classes and IDs for search
                                (By.CSS_SELECTOR, "button[class*='search'], a[class*='search']"),
                                (By.CSS_SELECTOR, "button[id*='search'], a[id*='search']"),
                                (By.CSS_SELECTOR, "a[href*='search'], a[href*='jobs']"),
                                # Generic buttons/links near search text
                                (By.XPATH, f"//button[contains(., '{pattern}')]"),
                                (By.XPATH, f"//a[contains(., '{pattern}')]"),
                            ]
                            
                            for by, selector in clickable_selectors:
                                try:
                                    elements = driver.find_elements(by, selector)
                                    if elements:
                                        # Try to click the first matching element
                                        elem = elements[0]
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                        time.sleep(0.5)
                                        elem.click()
                                        # Wait longer after clicking for content to load
                                        wait_after_click = max(sleep_seconds, 3)  # At least 3 seconds
                                        time.sleep(wait_after_click)
                                        print(f"[selenium] clicked '{pattern}' button/link (waited {wait_after_click}s)")
                                        break
                                except Exception:
                                    continue
                            else:
                                # Continue to next pattern if click failed
                                continue
                            # Break out of pattern loop if we successfully clicked
                            break
                            
                except Exception as e:
                    print(f"[selenium] open roles/search button click failed: {e}")
            
            # Scroll down to load more jobs (many sites lazy-load)
            try:
                last_height = driver.execute_script("return document.body.scrollHeight")
                scroll_attempts = 0
                max_scrolls = 3  # Scroll down 3 times to load more jobs
                
                while scroll_attempts < max_scrolls:
                    # Scroll to bottom
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)  # Wait for content to load
                    
                    # Calculate new height and compare
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # No more content loaded
                        break
                    last_height = new_height
                    scroll_attempts += 1
                
                # Scroll back to top
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.5)
                
                if scroll_attempts > 0:
                    print(f"[selenium] scrolled {scroll_attempts} times to load more jobs")
            except Exception as scroll_err:
                print(f"[selenium] scroll error: {scroll_err}")
            
            items = []
            if list_sel:
                items = driver.find_elements(By.CSS_SELECTOR, list_sel)
            elif item_sel:
                items = driver.find_elements(By.CSS_SELECTOR, item_sel)
            # Fallback to page-level if no container selector
            if not items:
                items = [driver]

            # Debug: counts per site
            try:
                print(f"[selenium] {source} containers={len(items)} url={url}")
            except Exception:
                pass

            for idx, elem in enumerate(items):
                try:
                    title = ""
                    location = ""
                    link = ""
                    description = ""
                    # Title
                    if title_sel:
                        t_nodes = elem.find_elements(By.CSS_SELECTOR, title_sel)
                        if t_nodes:
                            title = t_nodes[0].text.strip()
                    else:
                        txt = getattr(elem, 'text', '') or ''
                        title = txt.strip()
                    # Location
                    if loc_sel:
                        l_nodes = elem.find_elements(By.CSS_SELECTOR, loc_sel)
                        if l_nodes:
                            location = l_nodes[0].text.strip()
                    # Description
                    if desc_sel:
                        d_nodes = elem.find_elements(By.CSS_SELECTOR, desc_sel)
                        if d_nodes:
                            description = d_nodes[0].text.strip()
                    # Link
                    l_nodes = elem.find_elements(By.CSS_SELECTOR, link_sel) if link_sel else []
                    if l_nodes:
                        link = l_nodes[0].get_attribute("href") or ""
                    if not link and hasattr(elem, 'get_attribute'):
                        link = elem.get_attribute('href') or ""
                    # Normalize relative links
                    if link and absolute_base and link.startswith('/'):
                        link = urljoin(absolute_base, link)
                    # Domain/path filters
                    if domain_filter:
                        try:
                            netloc = urlparse(link).netloc
                            if domain_filter not in netloc:
                                continue
                        except Exception:
                            pass
                    if require_path_contains and (require_path_contains not in (link or '')):
                        continue
                    # Skip if no title
                    if not title:
                        continue
                    
                    # If no description from list page, try to fetch from job detail page
                    if not description and link and site.get("fetch_description_from_link"):
                        try:
                            driver.get(link)
                            time.sleep(2)  # Wait for page load
                            detail_desc_sel = site.get("detail_description_selector") or "body"
                            desc_nodes = driver.find_elements(By.CSS_SELECTOR, detail_desc_sel)
                            if desc_nodes:
                                description = desc_nodes[0].text.strip()[:2000]  # Limit to 2000 chars
                            driver.back()
                            time.sleep(1)
                        except Exception as e:
                            print(f"  [selenium] failed to fetch description from {link}: {e}")
                    
                    results.append({
                        "title": title,
                        "company": site.get("company") or "",
                        "location": location,
                        "description": description,
                        "url": link or url,
                        "careers_url": careers_url,
                        "source": source,
                    })
                    if len(results) >= fetch_limit:
                        return results
                except Exception:
                    continue
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return results


def build_selenium_sites_from_company_opts(company_opts: dict[str, Any]) -> list[dict[str, Any]]:
    print(company_opts, "hello")
    sites: list[dict[str, Any]] = []
    if not company_opts:
        return sites
    companies = company_opts or []
    print(companies)
    
    def discover_careers_url(company_slug: str) -> str | None:
        slug = company_slug.lower().strip()
        if not slug:
            return None
        candidates = [
            f"https://www.{slug}.com/careers",
            f"https://{slug}.com/careers",
            f"https://www.{slug}.com/jobs",
            f"https://{slug}.com/jobs",
            f"https://careers.{slug}.com/",
            f"https://jobs.{slug}.com/",
        ]
        headers = {"User-Agent": "Mozilla/5.0 (compatible; JobMatcher/1.0)"}
        for c in candidates:
            try:
                r = requests.get(c, headers=headers, timeout=10, allow_redirects=True)
                if r.status_code == 200 and ("career" in r.text.lower() or "job" in r.text.lower()):
                    return r.url
            except Exception:
                continue
        return None

    for slug in companies:
        s = (slug or "").strip()
        if not s:
            continue
        base = discover_careers_url(s)
        if not base:
            # last-resort guess
            base = f"https://{s}.com/careers"
        try:
            print(f"[selenium] discovered careers url for {s}: {base}")
        except Exception:
            pass
        parsed = urlparse(base)
        print(base)
        domain = parsed.netloc
        sites.append({
            "url": base,
            "list_selector": "a[href*='job'], a[href*='/jobs/'], a[href*='/careers/']",
            "title_selector": "",
            "location_selector": "",
            "link_selector": "a",
            "company": s,
            "source": f"selenium:{domain}",
            "careers_url": base,
            "domain_filter": domain,
            "require_path_contains": "",
            "absolute_base": f"{parsed.scheme}://{parsed.netloc}"
        })
    return sites

