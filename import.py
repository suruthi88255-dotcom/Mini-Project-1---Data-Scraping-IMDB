import re
import time
import pandas as pd
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========================
# CONFIG
# ========================
# Updated URL with higher count parameter and sorted by popularity
URL = "https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-12-31"
OUT_CSV = r"C:\Users\surut\OneDrive\Desktop\IMDB\outcsv.csv" # Changed for Colab compatibility
TARGET_MOVIES = 5000                      # Target number of movies
MAX_LOAD_MORE_CLICKS = 100                # Increased significantly
SCROLL_PAUSE = 2.0                        
MAX_SCROLL_ATTEMPTS = 20                  
WAIT_TIMEOUT = 30                         

# ========================
# HELPERS
# ========================
def create_chrome_driver():
    """Create a Chrome driver with simplified configuration to avoid session issues"""
    options = Options()
    
    # Essential options for stability - NO user-data-dir
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # Window and display options
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    
    # Random user agent to avoid detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Additional experimental options
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Headless mode (comment out if you want to see the browser)
    options.add_argument("--headless=new")
    
    # Memory and performance
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=4096")
    
    try:
        # Kill any existing Chrome processes first
        try:
            os.system("pkill -f chrome")  # Linux/Mac
            os.system("taskkill /f /im chrome.exe")  # Windows (will fail silently on Linux)
            time.sleep(2)
        except:
            pass
        
        # Create the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute script to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome driver created successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to create Chrome driver: {e}")
        # Try with even more basic options
        try:
            logger.info("Trying with minimal Chrome options...")
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--headless=new")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome driver created with minimal options")
            return driver
        except Exception as e2:
            logger.error(f"Failed with minimal options too: {e2}")
            raise e2

def parse_votes_to_int(v):
    """Convert '3.1M' -> 3100000, '946K' -> 946000, '2,345' -> 2345."""
    if not v or v == "N/A":
        return None
    v = v.strip().replace(",", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KM]?)", v, flags=re.IGNORECASE)
    if not m:
        return None
    num = float(m.group(1))
    suffix = m.group(2).upper()
    if suffix == "K":
        num *= 1_000
    elif suffix == "M":
        num *= 1_000_000
    return int(num)

def safe_find_elements(driver_or_element, by, selector):
    """Safely find elements"""
    try:
        return driver_or_element.find_elements(by, selector)
    except:
        return []

def gentle_text(el, selector=None, by_css=True):
    try:
        if selector:
            if by_css:
                element = el.find_element(By.CSS_SELECTOR, selector)
            else:
                element = el.find_element(By.XPATH, selector)
            return element.text.strip() if element else ""
        return el.text.strip()
    except:
        return ""

def gentle_attr(el, selector, attr="href"):
    try:
        element = el.find_element(By.CSS_SELECTOR, selector)
        return element.get_attribute(attr) if element else ""
    except:
        return ""

def extract_year(meta_text):
    m_year = re.search(r"(?<!\d)((?:19|20)\d{2})", meta_text)
    return m_year.group(1) if m_year else "N/A"

def extract_runtime(meta_text):
    m_runtime = re.search(r"(?<!\d)(\d+h\s*\d+m|\d+h|\d+m)", meta_text)
    return m_runtime.group(1) if m_runtime else "N/A"

def extract_rating_votes(block_text):
    if not block_text:
        return "N/A", "N/A"
    m = re.search(r"(?P<rating>\d+\.\d)\s*\((?P<votes>[\d.,KM]+)\)", block_text)
    rating = m.group("rating") if m else "N/A"
    votes = m.group("votes") if m else "N/A"
    return rating, votes

def normalize_title_and_rank(h3_text):
    if not h3_text:
        return None, "N/A"
    m = re.match(r"^(\d+)\.\s*(.*)$", h3_text)
    if m:
        return int(m.group(1)), m.group(2).strip()
    return None, h3_text.strip()

def click_load_more_if_any(driver):
    """Try clicking load more buttons"""
    # Comprehensive selectors
    selectors = [
        (By.CSS_SELECTOR, '[data-testid="adv-search-load-more"] button'),
        (By.CSS_SELECTOR, 'button[aria-label*="Load more"]'),
        (By.CSS_SELECTOR, 'button.ipc-see-more__button'),
        (By.CSS_SELECTOR, '.ipc-see-more__button'),
        (By.XPATH, "//button[contains(text(), 'Load more')]"),
        (By.XPATH, "//button[contains(text(), 'load more')]"),
        (By.XPATH, "//button[contains(@aria-label, 'Load more')]"),
        (By.CSS_SELECTOR, 'button[class*="load"]'),
    ]
    
    for by_type, selector in selectors:
        try:
            time.sleep(1)
            btns = safe_find_elements(driver, by_type, selector)
            
            for b in btns:
                try:
                    if b.is_displayed() and b.is_enabled():
                        # Count items before
                        items_before = len(safe_find_elements(driver, By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item"))
                        
                        # Scroll to and click button
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                        time.sleep(0.5)
                        
                        try:
                            b.click()
                        except:
                            driver.execute_script("arguments[0].click();", b)
                        
                        # Wait and check
                        time.sleep(3)
                        items_after = len(safe_find_elements(driver, By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item"))
                        
                        if items_after > items_before:
                            logger.info(f"Load more successful: {items_before} -> {items_after}")
                            return True
                        return True  # Button was clicked even if no new items
                        
                except Exception as e:
                    continue
        except Exception:
            continue
    
    return False

def aggressive_scroll_to_bottom(driver, pause=SCROLL_PAUSE, max_tries=MAX_SCROLL_ATTEMPTS):
    """Scroll to load more content"""
    logger.info("Scrolling to bottom...")
    
    for attempt in range(max_tries):
        try:
            # Get current scroll position
            last_position = driver.execute_script("return window.pageYOffset;")
            
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            
            # Check if we've scrolled
            new_position = driver.execute_script("return window.pageYOffset;")
            
            if new_position == last_position:
                logger.info(f"Reached bottom after {attempt + 1} attempts")
                break
                
        except Exception as e:
            logger.warning(f"Scroll attempt {attempt + 1} failed: {e}")

def scrape_imdb_page(url):
    driver = None
    rows = []  # Initialize rows here to avoid variable scope issues
    
    try:
        driver = create_chrome_driver()
        seen_urls = set()

        logger.info(f"Loading URL: {url}")
        driver.get(url)
        
        # Wait for page load
        time.sleep(5)
        
        # Wait for content with multiple selectors
        selectors_to_wait = [
            "li.ipc-metadata-list-summary-item",
            ".ipc-metadata-list-summary-item", 
            "[data-testid='tm-box-content']",
            "body"
        ]
        
        content_loaded = False
        for selector in selectors_to_wait:
            try:
                WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                content_loaded = True
                logger.info(f"Content loaded with selector: {selector}")
                break
            except TimeoutException:
                continue
        
        if not content_loaded:
            logger.error("Failed to load initial content")
            return pd.DataFrame()
        
        # Initial scroll
        aggressive_scroll_to_bottom(driver, max_tries=5)
        
        # Load more content
        clicks = 0
        consecutive_failures = 0
        
        while clicks < MAX_LOAD_MORE_CLICKS and consecutive_failures < 5:
            current_items = safe_find_elements(driver, By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
            current_count = len(current_items)
            
            logger.info(f"Items loaded: {current_count}, Target: {TARGET_MOVIES}")
            
            if current_count >= TARGET_MOVIES:
                logger.info(f"Reached target!")
                break
            
            if click_load_more_if_any(driver):
                clicks += 1
                consecutive_failures = 0
                aggressive_scroll_to_bottom(driver, max_tries=3)
                time.sleep(2)
            else:
                consecutive_failures += 1
                aggressive_scroll_to_bottom(driver, max_tries=5)
                time.sleep(3)
        
        logger.info(f"Loading complete. Clicks: {clicks}")
        
        # Final scroll
        aggressive_scroll_to_bottom(driver, max_tries=10)
        
        # Collect items
        items = safe_find_elements(driver, By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
        
        if not items:
            logger.warning("Trying fallback selectors...")
            fallback_selectors = [
                ".ipc-metadata-list-summary-item",
                "[data-testid='tm-box-content'] article",
                "div.ipc-poster-card"
            ]
            
            for fallback in fallback_selectors:
                items = safe_find_elements(driver, By.CSS_SELECTOR, fallback)
                if items:
                    logger.info(f"Found {len(items)} items with: {fallback}")
                    break
        
        logger.info(f"Processing {len(items)} items...")

        # Process items
        for idx, item in enumerate(items):
            if idx % 50 == 0:
                logger.info(f"Processing {idx + 1}/{len(items)}")
            
            try:
                # Get title and rank
                h3_text = (gentle_text(item, "h3.ipc-title__text") or 
                          gentle_text(item, "h3"))
                rank, title = normalize_title_and_rank(h3_text)

                # Get URL
                href = (gentle_attr(item, "a.ipc-title-link-wrapper", "href") or
                       gentle_attr(item, "a", "href"))
                
                if href and href.startswith("/"):
                    href = "https://www.imdb.com" + href

                # Skip if no basic info
                if not title and not href:
                    continue

                # Deduplicate
                key = href or f"{title}_{rank}"
                if key in seen_urls:
                    continue
                seen_urls.add(key)

                # Extract metadata
                meta_text = gentle_text(item)
                year = extract_year(meta_text)
                runtime = extract_runtime(meta_text)

                # Get rating and votes
                rating_block = (gentle_text(item, '[data-testid="ratingGroup--imdb-rating"]') or
                               gentle_text(item, '.ratingGroup--imdb-rating'))
                
                rating, votes_str = extract_rating_votes(rating_block)
                votes_num = parse_votes_to_int(votes_str)

                rows.append({
                    "Rank": rank,
                    "Title": title or "N/A",
                    "Year": year,
                    "Runtime": runtime,
                    "IMDb Rating": rating,
                    "Votes": votes_str or "N/A",
                    "Votes_Numeric": votes_num,
                    "URL": href or "N/A",
                })

            except Exception as e:
                logger.warning(f"Error processing item {idx}: {e}")
                continue

    except Exception as e:
        logger.error(f"Major error during scraping: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Remove duplicates and sort
    if not df.empty:
        df = df.drop_duplicates(subset=['URL'], keep='first')
        logger.info(f"Unique movies after deduplication: {len(df)}")
        
        # Sort by rank if available
        if "Rank" in df.columns and df["Rank"].notna().any():
            df = df.sort_values(by="Rank", na_position="last").reset_index(drop=True)

    return df

# ========================
# MAIN EXECUTION
# ========================
if __name__ == "__main__":
    logger.info("Starting IMDb scraper...")
    logger.info(f"Target: {TARGET_MOVIES} movies")
    
    try:
        df = scrape_imdb_page(URL)
        
        if not df.empty:
            # Save to CSV
            df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
            logger.info(f"✅ Successfully saved {len(df)} movies to {OUT_CSV}")
            
            print(f"\n✅ Successfully scraped {len(df)} movies!")
            print(f"📁 Saved to: {OUT_CSV}")
            
            print("\n📊 Summary:")
            print(f"Total movies: {len(df)}")
            print(f"With ratings: {df['IMDb Rating'].notna().sum()}")
            print(f"With years: {df['Year'].notna().sum()}")
            
            if not df['Year'].isna().all():
                years = df['Year'][df['Year'] != 'N/A']
                if len(years) > 0:
                    print(f"Year range: {years.min()} - {years.max()}")
            
            print("\n🎬 First 10 movies:")
            print(df[['Rank', 'Title', 'Year', 'IMDb Rating']].head(10).to_string(index=False))
            
        else:
            print("❌ No movies were scraped!")
            logger.error("No data collected")
            
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        print(f"❌ Script failed: {e}")
        print("Try running the script again or check your internet connection.")