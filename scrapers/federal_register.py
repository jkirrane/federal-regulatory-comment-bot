"""
Federal Register scraper for enriching comment period data

Provides better abstracts and additional metadata
"""

import requests
from typing import Optional, Dict, Any
from .base import BaseScraper


class FederalRegisterScraper(BaseScraper):
    """
    Scraper for Federal Register API (v1)
    
    Used to enrich Regulations.gov data with:
    - Better abstracts/summaries
    - Topics
    - Action descriptions
    """
    
    BASE_URL = "https://www.federalregister.gov/api/v1"
    
    def __init__(self):
        """Initialize Federal Register scraper"""
        super().__init__(name="FederalRegisterScraper", rate_limit=0.5)  # Be nice, no rate limit but still slow
    
    def get_document(self, fr_doc_num: str) -> Optional[Dict[str, Any]]:
        """
        Get document from Federal Register by document number
        
        Args:
            fr_doc_num: Federal Register document number (e.g., '2026-00783')
        
        Returns:
            Document dict or None if not found
        """
        url = f"{self.BASE_URL}/documents/{fr_doc_num}.json"
        
        response = self.fetch_page(url)
        if not response:
            return None
        
        try:
            return response.json()
        except ValueError as e:
            self.logger.error(f"Failed to parse Federal Register document: {e}")
            return None
    
    def enrich_period(self, period: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a comment period with Federal Register data
        
        Args:
            period: Comment period dict with optional 'federal_register_url' or fr doc num
        
        Returns:
            Enhanced period dict
        """
        # Extract FR doc number from URL or direct field
        fr_doc_num = None
        
        if period.get('federal_register_url'):
            # Extract from URL like: https://www.federalregister.gov/documents/2026-00783
            url = period['federal_register_url']
            parts = url.rstrip('/').split('/')
            if len(parts) > 0:
                fr_doc_num = parts[-1]
        
        if not fr_doc_num:
            self.logger.debug(f"No Federal Register document number for {period.get('document_id')}")
            return period
        
        # Fetch from Federal Register
        self.logger.debug(f"Enriching with Federal Register document {fr_doc_num}")
        fr_doc = self.get_document(fr_doc_num)
        
        if not fr_doc:
            return period
        
        # Enhance period with FR data
        enhanced = period.copy()
        
        # Use better abstract if available and current one is empty
        if fr_doc.get('abstract') and not period.get('abstract'):
            enhanced['abstract'] = fr_doc.get('abstract')
        
        # Add topics if available
        if fr_doc.get('topics'):
            # Join existing and new topics
            existing_topics = period.get('keywords', '').split(', ') if period.get('keywords') else []
            fr_topics = fr_doc.get('topics', [])
            all_topics = set(existing_topics + fr_topics)
            enhanced['keywords'] = ', '.join(sorted(all_topics))
        
        # Add action description if available
        if fr_doc.get('action') and not period.get('document_type'):
            enhanced['document_type'] = fr_doc.get('action')
        
        self.logger.debug(f"Enriched {period.get('document_id')} with Federal Register data")
        
        return enhanced


def enrich_with_federal_register(period: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to enrich a single period
    
    Args:
        period: Comment period dict
    
    Returns:
        Enhanced period dict
    """
    scraper = FederalRegisterScraper()
    return scraper.enrich_period(period)
