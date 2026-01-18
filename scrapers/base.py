"""
Base scraper class for Federal Regulatory Comment Bot

Provides common functionality:
- HTTP requests with user-agent
- Rate limiting
- Error handling and retries
- Logging
"""

import requests
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseScraper:
    """
    Base class for all scrapers
    
    Handles:
    - Rate limiting (1 second between requests)
    - Retry logic for transient errors
    - User agent management
    - Error logging
    """
    
    def __init__(self, name: str = "BaseScraper", rate_limit: float = 1.0):
        """
        Initialize base scraper
        
        Args:
            name: Name for logging
            rate_limit: Seconds to wait between requests (default 1.0)
        """
        self.name = name
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.logger = logging.getLogger(name)
        
        # User agent (identify ourselves)
        self.user_agent = (
            'Federal-Regulatory-Comment-Bot/1.0 '
            '(+https://github.com/your-username/federal-regulatory-comment-bot)'
        )
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def _rate_limit(self):
        """
        Enforce rate limiting between requests
        
        Waits if not enough time has passed since last request
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_page(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        timeout: int = 30
    ) -> Optional[requests.Response]:
        """
        Fetch a page with rate limiting and retry logic
        
        Args:
            url: URL to fetch
            params: Query parameters
            headers: Additional headers (merged with defaults)
            max_retries: Number of retry attempts for transient errors
            timeout: Request timeout in seconds
        
        Returns:
            Response object or None if all retries failed
        """
        # Apply rate limiting
        self._rate_limit()
        
        # Merge headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Retry logic
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Fetching: {url} (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=request_headers,
                    timeout=timeout
                )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited (429). Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Handle server errors (5xx) - retry
                if 500 <= response.status_code < 600:
                    self.logger.warning(f"Server error {response.status_code}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                # Handle client errors (4xx) - don't retry
                if 400 <= response.status_code < 500:
                    self.logger.error(f"Client error {response.status_code}: {url}")
                    self.logger.error(f"Response: {response.text[:500]}")
                    return None
                
                # Success
                response.raise_for_status()
                return response
            
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
                time.sleep(2 ** attempt)
            
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}: {e}")
                time.sleep(2 ** attempt)
            
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed: {e}")
                return None
        
        self.logger.error(f"All {max_retries} attempts failed for: {url}")
        return None
    
    def scrape(self, dry_run: bool = False):
        """
        Main scraping method - should be overridden by subclasses
        
        Args:
            dry_run: If True, fetch data but don't save to database
        
        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement scrape() method")
    
    def log_summary(self, stats: Dict[str, int]):
        """
        Log a summary of scraping results
        
        Args:
            stats: Dictionary of counts (e.g., {'fetched': 10, 'new': 3, 'updated': 2})
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Scraping Summary - {self.name}")
        self.logger.info(f"{'='*60}")
        for key, value in stats.items():
            self.logger.info(f"  {key.capitalize()}: {value}")
        self.logger.info(f"{'='*60}\n")


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass


def format_date(date_str: str) -> str:
    """
    Format date string consistently
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        Formatted date string (e.g., "January 17, 2026")
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d, %Y')
    except ValueError:
        return date_str


def days_until(date_str: str) -> int:
    """
    Calculate days until a date
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        Number of days (negative if past)
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.now()
        delta = date_obj - today
        return delta.days
    except ValueError:
        return 0
