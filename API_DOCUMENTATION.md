# API Documentation - Regulatory Comment Bot

Complete technical reference for the APIs used in this project.

## Table of Contents
1. [Regulations.gov API (v4)](#regulationsgov-api-v4)
2. [Federal Register API (v1)](#federal-register-api-v1)
3. [Data Flow](#data-flow)
4. [Common Patterns](#common-patterns)
5. [Error Handling](#error-handling)
6. [Rate Limits](#rate-limits)

---

## Regulations.gov API (v4)

### Overview

**Base URL:** `https://api.regulations.gov/v4`  
**Authentication:** API key in `X-Api-Key` header  
**Format:** JSON  
**Rate Limit:** 1000 requests/hour (can request increase)  

### Getting an API Key

1. Visit: https://open.gsa.gov/api/regulationsgov/
2. Fill out registration form
3. Receive key via email
4. Store in `.env` file: `REGULATIONS_API_KEY=your-key-here`

**Demo Key:** Use `DEMO_KEY` for testing (limited rate)

### Key Endpoints

#### 1. Search Documents Open for Comment

**Purpose:** Find all proposed rules and notices currently accepting comments

**Endpoint:** `GET /v4/documents`

**Query Parameters:**
```python
params = {
    'filter[openForComment]': 'true',           # Only open periods
    'filter[commentEndDate][ge]': '2026-01-18', # Closing today or later
    'filter[documentType]': 'Proposed Rule',    # Optional: filter by type
    'filter[postedDate][ge]': '2026-01-17',     # Posted yesterday or today
    'sort': '-postedDate',                      # Newest first
    'page[size]': 250,                          # Max 250 per page
    'page[number]': 1
}
```

**Example Request:**
```python
import requests

API_KEY = 'your-api-key'
BASE_URL = 'https://api.regulations.gov/v4'

headers = {'X-Api-Key': API_KEY}

params = {
    'filter[openForComment]': 'true',
    'filter[commentEndDate][ge]': '2026-01-18',
    'page[size]': 250
}

response = requests.get(
    f'{BASE_URL}/documents',
    headers=headers,
    params=params
)

data = response.json()
```

**Response Structure:**
```json
{
  "data": [
    {
      "id": "FDA-2024-N-1234",
      "type": "documents",
      "attributes": {
        "agencyId": "FDA",
        "documentType": "Proposed Rule",
        "title": "Food Labeling: Nutrition and Supplement Facts Labels",
        "postedDate": "2026-01-15",
        "commentEndDate": "2026-03-15",
        "commentStartDate": "2026-01-15",
        "openForComment": true,
        "objectId": "0900006483a1b2c3",
        "highlightedContent": "Summary of the proposed rule...",
        "docketId": "FDA-2024-N-1234"
      },
      "links": {
        "self": "https://api.regulations.gov/v4/documents/FDA-2024-N-1234"
      }
    }
  ],
  "meta": {
    "numberOfElements": 25,
    "totalElements": 247,
    "totalPages": 10
  }
}
```

#### 2. Get Document Details

**Purpose:** Get full details including abstract, links to comment form

**Endpoint:** `GET /v4/documents/{documentId}`

**Example:**
```python
doc_id = 'FDA-2024-N-1234'

response = requests.get(
    f'{BASE_URL}/documents/{doc_id}',
    headers=headers
)

details = response.json()
```

**Response Structure:**
```json
{
  "data": {
    "id": "FDA-2024-N-1234",
    "attributes": {
      "agencyId": "FDA",
      "title": "Food Labeling: Nutrition and Supplement Facts Labels",
      "documentType": "Proposed Rule",
      "subtype": "Proposed Rule",
      "postedDate": "2026-01-15",
      "commentEndDate": "2026-03-15",
      "commentStartDate": "2026-01-15",
      "openForComment": true,
      "withdrawn": false,
      "docketId": "FDA-2024-N-1234",
      "objectId": "0900006483a1b2c3",
      "frDocNum": "2026-00123",
      "summary": "FDA proposes to update the Nutrition Facts label...",
      "topics": ["Food Safety", "Nutrition"],
      "rin": "0910-AI23"
    }
  }
}
```

**Important Fields:**
- `commentEndDate` - When comment period closes (YYYY-MM-DD)
- `objectId` - Needed for some queries
- `frDocNum` - Federal Register document number
- `rin` - Regulation Identifier Number (for tracking)
- `summary` - Official abstract (often technical)

#### 3. Search by Agency

**Endpoint:** `GET /v4/documents?filter[agencyId]=EPA,FDA`

**Common Agency IDs:**
- `EPA` - Environmental Protection Agency
- `FDA` - Food and Drug Administration
- `FCC` - Federal Communications Commission
- `FTC` - Federal Trade Commission
- `DOL` - Department of Labor
- `HHS` - Health and Human Services
- `DOT` - Department of Transportation
- `USDA` - Agriculture
- `DHS` - Homeland Security
- `DOE` - Energy

#### 4. Get Docket Information

**Purpose:** Get parent docket details (contains multiple documents)

**Endpoint:** `GET /v4/dockets/{docketId}`

**Example:**
```python
docket_id = 'EPA-HQ-OAR-2024-0123'

response = requests.get(
    f'{BASE_URL}/dockets/{docket_id}',
    headers=headers
)

docket = response.json()
```

### Building Comment URLs

**Direct comment link:**
```
https://www.regulations.gov/commenton/{documentId}
```

Example: `https://www.regulations.gov/commenton/FDA-2024-N-1234`

**View document:**
```
https://www.regulations.gov/document/{documentId}
```

### Filtering Best Practices

**Get today's new comment periods:**
```python
from datetime import date

params = {
    'filter[openForComment]': 'true',
    'filter[postedDate]': str(date.today()),
    'sort': '-postedDate',
    'page[size]': 250
}
```

**Get closing soon (next 7 days):**
```python
from datetime import date, timedelta

end_date = date.today() + timedelta(days=7)

params = {
    'filter[openForComment]': 'true',
    'filter[commentEndDate][le]': str(end_date),
    'filter[commentEndDate][ge]': str(date.today()),
    'sort': 'commentEndDate',  # Soonest first
    'page[size]': 250
}
```

---

## Federal Register API (v1)

### Overview

**Base URL:** `https://www.federalregister.gov/api/v1`  
**Authentication:** None required  
**Format:** JSON  
**Rate Limit:** None (respectful use expected)

### Key Endpoints

#### 1. Search Documents

**Purpose:** Get Federal Register documents with better summaries

**Endpoint:** `GET /api/v1/documents.json`

**Query Parameters:**
```python
params = {
    'conditions[type][]': 'PRORULE',           # Proposed Rules
    'conditions[agencies][]': 'food-and-drug-administration',
    'conditions[comment_date][gte]': '2026-01-18',  # Open for comment
    'per_page': 100,
    'page': 1
}
```

**Example Request:**
```python
response = requests.get(
    'https://www.federalregister.gov/api/v1/documents.json',
    params=params
)

data = response.json()
```

**Response Structure:**
```json
{
  "count": 45,
  "results": [
    {
      "abstract": "Full abstract text here...",
      "action": "Proposed rule.",
      "agencies": [
        {
          "name": "Food and Drug Administration",
          "raw_name": "DEPARTMENT OF HEALTH AND HUMAN SERVICES"
        }
      ],
      "comment_date": "2026-03-15",
      "document_number": "2026-00123",
      "html_url": "https://www.federalregister.gov/documents/2026/01/15/2026-00123/food-labeling",
      "publication_date": "2026-01-15",
      "title": "Food Labeling: Nutrition and Supplement Facts Labels",
      "type": "Proposed Rule",
      "topics": ["Food", "Nutrition"]
    }
  ]
}
```

#### 2. Get Single Document

**Endpoint:** `GET /api/v1/documents/{document_number}.json`

**Example:**
```python
doc_number = '2026-00123'

response = requests.get(
    f'https://www.federalregister.gov/api/v1/documents/{doc_number}.json'
)

doc = response.json()
```

**Useful Fields:**
- `abstract` - Usually better than Regulations.gov summary
- `full_text_xml_url` - Full text of rule
- `raw_text_url` - Plain text version
- `topics` - Pre-categorized topics

#### 3. Public Inspection Documents

**Purpose:** Get documents before they're officially published

**Endpoint:** `GET /api/v1/public-inspection-documents.json`

```python
params = {
    'conditions[available_on]': '2026-01-18',
    'conditions[type][]': 'Proposed Rule'
}
```

### Document Types

**Federal Register Types:**
- `PRORULE` - Proposed Rule (most important for comments)
- `RULE` - Final Rule (usually closed for comment)
- `NOTICE` - Notice (sometimes open for comment)
- `PRESDOCU` - Presidential Document

### Agency Slugs

**Federal Register uses slugs (lowercase-with-dashes):**
- `environmental-protection-agency`
- `food-and-drug-administration`
- `federal-communications-commission`
- `securities-and-exchange-commission`

**Convert from Regulations.gov:**
```python
AGENCY_SLUG_MAP = {
    'EPA': 'environmental-protection-agency',
    'FDA': 'food-and-drug-administration',
    'FCC': 'federal-communications-commission',
    'SEC': 'securities-and-exchange-commission',
    'DOL': 'labor-department'
}
```

---

## Data Flow

### Daily Scraping Workflow

```python
# 1. Get new comment periods from Regulations.gov
new_periods = get_new_comment_periods_regs_gov()

# 2. For each new period, get Federal Register details
for period in new_periods:
    fr_details = get_federal_register_details(period['frDocNum'])
    
    # Merge data
    period['abstract'] = fr_details.get('abstract', period['summary'])
    period['topics'] = fr_details.get('topics', [])
    
    # Categorize
    period['categories'] = categorize_by_keywords(period)
    
    # Store in database
    upsert_comment_period(period)

# 3. Check for closing deadlines
check_deadline_reminders()

# 4. Post to Bluesky
post_new_periods()
post_reminders()
```

### Combining Both APIs

**Best practice:** Use Regulations.gov as primary, Federal Register for enrichment

```python
def get_enriched_comment_period(doc_id):
    # Get from Regulations.gov
    regs_data = get_regs_gov_document(doc_id)
    
    # Get FR document number
    fr_doc_num = regs_data['attributes'].get('frDocNum')
    
    if fr_doc_num:
        # Get better abstract from Federal Register
        fr_data = get_federal_register_document(fr_doc_num)
        
        return {
            'document_id': doc_id,
            'title': regs_data['attributes']['title'],
            'agency': regs_data['attributes']['agencyId'],
            'comment_end_date': regs_data['attributes']['commentEndDate'],
            'abstract': fr_data.get('abstract', regs_data['attributes'].get('summary')),
            'topics': fr_data.get('topics', []),
            'comment_url': f'https://www.regulations.gov/commenton/{doc_id}',
            'federal_register_url': fr_data.get('html_url')
        }
    
    return regs_data
```

---

## Common Patterns

### Pagination

**Regulations.gov:**
```python
def get_all_pages(endpoint, params):
    all_data = []
    page = 1
    
    while True:
        params['page[number]'] = page
        response = requests.get(endpoint, headers=headers, params=params)
        data = response.json()
        
        all_data.extend(data['data'])
        
        if page >= data['meta']['totalPages']:
            break
        
        page += 1
    
    return all_data
```

**Federal Register:**
```python
def get_all_pages_fr(endpoint, params):
    all_results = []
    page = 1
    
    while True:
        params['page'] = page
        response = requests.get(endpoint, params=params)
        data = response.json()
        
        all_results.extend(data['results'])
        
        if len(data['results']) < params.get('per_page', 20):
            break
        
        page += 1
    
    return all_results
```

### Date Filtering

**Both APIs use ISO 8601 dates (YYYY-MM-DD):**

```python
from datetime import date, timedelta

today = date.today()
yesterday = today - timedelta(days=1)
next_week = today + timedelta(days=7)

# Get periods posted yesterday or today
params = {
    'filter[postedDate][ge]': str(yesterday),
    'filter[postedDate][le]': str(today)
}

# Get periods closing in next 7 days
params = {
    'filter[commentEndDate][ge]': str(today),
    'filter[commentEndDate][le]': str(next_week)
}
```

---

## Error Handling

### Common Errors

**Regulations.gov:**
```python
def safe_api_call(url, headers, params):
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Rate limit hit, waiting...")
            time.sleep(3600)  # Wait 1 hour
            return safe_api_call(url, headers, params)
        elif e.response.status_code == 404:
            print(f"Document not found: {url}")
            return None
        else:
            print(f"HTTP error: {e}")
            raise
    except requests.exceptions.Timeout:
        print("Request timed out, retrying...")
        return safe_api_call(url, headers, params)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
```

**Federal Register:**
```python
# Usually just need basic error handling
try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()
except Exception as e:
    print(f"Federal Register API error: {e}")
    return None
```

---

## Rate Limits

### Regulations.gov

**Default limits:**
- 1000 requests per hour per API key
- Resets on the hour

**Requesting increase:**
1. Email `eRulemaking@gsa.gov`
2. Explain public service use case
3. Estimate needed rate (e.g., 5000/hour)
4. Usually approved for legitimate civic tech

**Best practices:**
- Cache responses in database
- Batch requests
- Use `page[size]=250` to minimize requests
- Track remaining quota in headers

**Check rate limit:**
```python
response = requests.get(url, headers=headers)
print(f"Remaining: {response.headers.get('X-RateLimit-Remaining')}")
print(f"Resets at: {response.headers.get('X-RateLimit-Reset')}")
```

### Federal Register

**No official rate limit** but be respectful:
- 1-2 requests per second max
- Use caching
- Don't hammer the API

```python
import time

def rate_limited_get(url, params):
    time.sleep(1)  # 1 second between requests
    return requests.get(url, params=params)
```

---

## Testing

### Test with DEMO_KEY

```python
# Regulations.gov
headers = {'X-Api-Key': 'DEMO_KEY'}

# Get a few documents
params = {
    'filter[openForComment]': 'true',
    'page[size]': 5
}

response = requests.get(
    'https://api.regulations.gov/v4/documents',
    headers=headers,
    params=params
)

print(json.dumps(response.json(), indent=2))
```

### Staging Environment

**Regulations.gov has staging API:**
```
https://api-staging.regulations.gov/v4/documents
```

Use for testing without hitting production rate limits.

---

## Quick Reference

### URLs to Remember

**Regulations.gov:**
- API Docs: https://open.gsa.gov/api/regulationsgov/
- Web interface: https://www.regulations.gov/
- Comment on document: `https://www.regulations.gov/commenton/{docId}`

**Federal Register:**
- API Docs: https://www.federalregister.gov/developers/documentation/api/v1
- Web interface: https://www.federalregister.gov/
- Document page: `https://www.federalregister.gov/documents/{year}/{month}/{day}/{docNum}/{slug}`

### Key Fields Mapping

| Field | Regulations.gov | Federal Register |
|-------|----------------|------------------|
| Document ID | `id` | `document_number` |
| Title | `attributes.title` | `title` |
| Agency | `attributes.agencyId` | `agencies[0].name` |
| Comment End | `attributes.commentEndDate` | `comment_date` |
| Summary | `attributes.summary` | `abstract` |
| Topics | `attributes.topics` | `topics` |

---

**Ready to start building!** See QUICKSTART.md for implementation steps.
