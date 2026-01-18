"""Test Federal Register enrichment"""

from scrapers.regulations_gov import RegulationsGovScraper
from scrapers.federal_register import enrich_with_federal_register

# Test with just a couple documents
scraper = RegulationsGovScraper()
documents = scraper.get_new_comment_periods(days_back=1)

print(f'Found {len(documents)} documents\n')

# Test enrichment on first 3
for i, doc in enumerate(documents[:3]):
    doc_id = doc.get('id')
    print(f'{i+1}. {doc_id}')
    
    # Parse it
    parsed = scraper.parse_document(doc)
    
    # Fetch details
    details = scraper.get_document_details(doc_id)
    if details:
        detail_attrs = details.get('attributes', {})
        if detail_attrs.get('frDocNum'):
            fr_num = detail_attrs.get('frDocNum')
            parsed['federal_register_url'] = f'https://www.federalregister.gov/documents/{fr_num}'
            print(f'   FR Doc: {fr_num}')
    
    # Show before enrichment
    abstract_before = parsed.get('abstract') or 'None'
    print(f'   Abstract (before): {abstract_before[:100]}...')
    
    # Enrich with Federal Register
    if parsed.get('federal_register_url'):
        parsed = enrich_with_federal_register(parsed)
        abstract_after = parsed.get('abstract') or 'None'
        print(f'   Abstract (after):  {abstract_after[:100]}...')
    else:
        print('   No Federal Register doc - skipping enrichment')
    
    print()
