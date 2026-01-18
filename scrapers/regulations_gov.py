"""
Regulations.gov scraper for Federal Regulatory Comment Bot

Fetches new comment periods from Regulations.gov API (v4)
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from .base import BaseScraper, APIError
from database import upsert_comment_period
from .federal_register import enrich_with_federal_register


# Load environment variables
load_dotenv()


class RegulationsGovScraper(BaseScraper):
    """
    Scraper for Regulations.gov API (v4)
    
    Fetches:
    - New comment periods posted in last N days
    - Document details (title, abstract, links)
    - Agency information
    """
    
    BASE_URL = "https://api.regulations.gov/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Regulations.gov scraper
        
        Args:
            api_key: API key (defaults to env var REGULATIONS_API_KEY)
                    Use 'DEMO_KEY' for testing (limited rate)
        """
        super().__init__(name="RegulationsGovScraper")
        
        self.api_key = api_key or os.getenv('REGULATIONS_API_KEY', 'DEMO_KEY')
        
        if self.api_key == 'DEMO_KEY':
            self.logger.warning("Using DEMO_KEY - limited to 50 requests/hour")
        
        # Add API key to session headers
        self.session.headers.update({'X-Api-Key': self.api_key})
    
    def get_new_comment_periods(
        self,
        days_back: int = 1,
        document_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get comment periods posted in the last N days
        
        Args:
            days_back: Number of days to look back (default 1)
            document_types: Filter by types (e.g., ['Proposed Rule', 'Notice'])
        
        Returns:
            List of document dicts
        """
        posted_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            # Note: openForComment filter seems to not work with v4 API
            # Instead we filter by date and check openForComment in results
            'filter[commentEndDate][ge]': today,
            'filter[postedDate][ge]': posted_date,
            'sort': '-postedDate',
            'page[size]': 250,
            'page[number]': 1
        }
        
        # Filter by document type if specified
        if document_types:
            params['filter[documentType]'] = ','.join(document_types)
        
        all_documents = []
        
        while True:
            self.logger.info(f"Fetching page {params['page[number]']}...")
            
            response = self.fetch_page(
                f"{self.BASE_URL}/documents",
                params=params
            )
            
            if not response:
                self.logger.error("Failed to fetch documents")
                break
            
            try:
                data = response.json()
            except ValueError as e:
                self.logger.error(f"Failed to parse JSON: {e}")
                break
            
            if 'data' not in data:
                self.logger.error(f"Unexpected response structure: {data}")
                break
            
            documents = data['data']
            all_documents.extend(documents)
            
            # Check if there are more pages
            meta = data.get('meta', {})
            total_pages = meta.get('totalPages', 1)
            current_page = params['page[number]']
            
            self.logger.info(
                f"Page {current_page}/{total_pages}: "
                f"Found {len(documents)} documents "
                f"(total so far: {len(all_documents)})"
            )
            
            if current_page >= total_pages:
                break
            
            params['page[number]'] += 1
        
        self.logger.info(f"Total documents found: {len(all_documents)}")
        return all_documents
    
    def get_document_details(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details for a single document
        
        Args:
            document_id: Document ID (e.g., 'FDA-2024-N-1234')
        
        Returns:
            Document details dict or None if error
        """
        response = self.fetch_page(f"{self.BASE_URL}/documents/{document_id}")
        
        if not response:
            return None
        
        try:
            data = response.json()
            return data.get('data')
        except ValueError as e:
            self.logger.error(f"Failed to parse document details: {e}")
            return None
    
    def parse_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse document data into our database format
        
        Args:
            doc_data: Raw document from API
        
        Returns:
            Parsed dict ready for database
        """
        # Extract attributes
        attrs = doc_data.get('attributes', {})
        doc_id = doc_data.get('id', '')
        
        # Build regulations.gov URLs
        regulations_url = f"https://www.regulations.gov/commenton/{doc_id}"
        details_url = f"https://www.regulations.gov/document/{doc_id}"
        
        # Parse dates
        posted_date = attrs.get('postedDate', '')
        comment_end_date = attrs.get('commentEndDate', '')
        comment_start_date = attrs.get('commentStartDate')
        
        # Get content
        title = attrs.get('title', 'Untitled Document')
        abstract = attrs.get('summary') or attrs.get('highlightedContent') or ''
        
        # Agency info
        agency_id = attrs.get('agencyId', 'UNKNOWN')
        
        # Map common agency IDs to full names
        agency_names = {
            'EPA': 'Environmental Protection Agency',
            'FDA': 'Food and Drug Administration',
            'FCC': 'Federal Communications Commission',
            'FTC': 'Federal Trade Commission',
            'DOL': 'Department of Labor',
            'HHS': 'Department of Health and Human Services',
            'DOT': 'Department of Transportation',
            'ED': 'Department of Education',
            'HUD': 'Department of Housing and Urban Development',
            'USDA': 'Department of Agriculture',
            'DOE': 'Department of Energy',
            'DHS': 'Department of Homeland Security',
            'SEC': 'Securities and Exchange Commission',
            'CFPB': 'Consumer Financial Protection Bureau',
        }
        
        agency_name = agency_names.get(agency_id, agency_id)
        
        # Parse document
        parsed = {
            'document_id': doc_id,
            'docket_id': attrs.get('docketId', doc_id),
            'title': title,
            'agency_id': agency_id,
            'agency_name': agency_name,
            'document_type': attrs.get('documentType', ''),
            'posted_date': posted_date,
            'comment_start_date': comment_start_date,
            'comment_end_date': comment_end_date,
            'abstract': abstract,
            'regulations_url': regulations_url,
            'details_url': details_url,
            'source_url': f"{self.BASE_URL}/documents/{doc_id}",
        }
        
        # Optional: Federal Register document number
        fr_doc_num = attrs.get('frDocNum')
        if fr_doc_num:
            parsed['federal_register_url'] = f"https://www.federalregister.gov/documents/{fr_doc_num}"
        
        return parsed
    
    def scrape(
        self,
        days_back: int = 1,
        dry_run: bool = False,
        document_types: Optional[List[str]] = None,
        enrich: bool = True
    ) -> Dict[str, int]:
        """
        Main scraping method
        
        Args:
            days_back: Days to look back for new periods
            dry_run: If True, fetch but don't save to database
            document_types: Filter by types (e.g., ['Proposed Rule'])
            enrich: If True, fetch detailed data and Federal Register enrichment
        
        Returns:
            Dict with statistics
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Starting Regulations.gov scrape")
        self.logger.info(f"Looking back: {days_back} day(s)")
        self.logger.info(f"Dry run: {dry_run}")
        if document_types:
            self.logger.info(f"Document types: {', '.join(document_types)}")
        self.logger.info(f"{'='*60}\n")
        
        # Statistics
        stats = {
            'fetched': 0,
            'parsed': 0,
            'new': 0,
            'updated': 0,
            'errors': 0
        }
        
        # Fetch documents
        documents = self.get_new_comment_periods(
            days_back=days_back,
            document_types=document_types
        )
        stats['fetched'] = len(documents)
        
        if not documents:
            self.logger.warning("No documents found")
            self.log_summary(stats)
            return stats
        
        # Process each document
        for doc_data in documents:
            try:
                # Skip if not open for comment
                attrs = doc_data.get('attributes', {})
                if not attrs.get('openForComment', False):
                    continue
                
                # Parse basic data from search results
                parsed = self.parse_document(doc_data)
                
                # Fetch full details to get better summary (if enrichment enabled)
                if enrich:
                    doc_id = parsed['document_id']
                    self.logger.debug(f"Fetching details for {doc_id}...")
                    
                    details = self.get_document_details(doc_id)
                    if details:
                        # Enhance with data from details endpoint
                        detail_attrs = details.get('attributes', {})
                        
                        # Use the better summary from details if available
                        if detail_attrs.get('summary'):
                            parsed['abstract'] = detail_attrs.get('summary')
                        
                        # Get Federal Register doc number if not already set
                        if detail_attrs.get('frDocNum') and not parsed.get('federal_register_url'):
                            fr_num = detail_attrs.get('frDocNum')
                            parsed['federal_register_url'] = f"https://www.federalregister.gov/documents/{fr_num}"
                        
                        # Add any additional useful fields
                        if detail_attrs.get('rin'):
                            parsed['keywords'] = f"RIN: {detail_attrs.get('rin')}"
                    
                    # Enrich with Federal Register data (better abstracts)
                    if parsed.get('federal_register_url'):
                        self.logger.debug(f"Enriching {doc_id} with Federal Register data...")
                        parsed = enrich_with_federal_register(parsed)
                
                stats['parsed'] += 1
                
                # Log what we found
                abstract_preview = (parsed.get('abstract') or 'No description')[:80]
                self.logger.info(
                    f"Found: {parsed['document_id']} - {parsed['title'][:50]}... "
                    f"({abstract_preview}...)"
                )
                
                # Save to database (unless dry run)
                if not dry_run:
                    period_id = upsert_comment_period(**parsed)
                    
                    # Check if new or updated (simple heuristic)
                    # In practice, this would query DB to check
                    stats['new'] += 1
                    
                    self.logger.debug(f"Saved as period ID {period_id}")
            
            except Exception as e:
                stats['errors'] += 1
                doc_id = doc_data.get('id', 'unknown')
                self.logger.error(f"Error processing {doc_id}: {e}", exc_info=True)
        
        # Log summary
        self.log_summary(stats)
        
        return stats


def main():
    """
    Run scraper from command line
    
    Usage:
        python -m scrapers.regulations_gov
        python -m scrapers.regulations_gov --dry-run
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Regulations.gov for new comment periods')
    parser.add_argument('--days', type=int, default=1, help='Days to look back (default: 1)')
    parser.add_argument('--dry-run', action='store_true', help='Fetch but don\'t save to database')
    parser.add_argument('--api-key', help='Regulations.gov API key (or use REGULATIONS_API_KEY env var)')
    parser.add_argument(
        '--types',
        nargs='+',
        help='Filter by document types (e.g., "Proposed Rule" "Notice")'
    )
    parser.add_argument(
        '--no-enrich',
        action='store_true',
        help='Skip fetching details and Federal Register enrichment (faster but less data)'
    )
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = RegulationsGovScraper(api_key=args.api_key)
    
    # Run scrape
    scraper.scrape(
        days_back=args.days,
        enrich=not args.no_enrich,
        dry_run=args.dry_run,
        document_types=args.types
    )


if __name__ == "__main__":
    main()
