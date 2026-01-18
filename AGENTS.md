# Working with AI Agents on Regulatory Comment Bot

Guide for using VS Code Claude (or other AI coding assistants) to build this project efficiently.

## 🎯 Quick Start for AI Assistants

When starting a new coding session, provide this context:

```
I'm building a Bluesky bot that tracks federal regulatory comment periods.

Key docs in this project:
- REGULATORY_COMMENT_BOT_SPEC.md - Full project specification
- API_DOCUMENTATION.md - Regulations.gov and Federal Register API reference
- IMPLEMENTATION_GUIDE.md - Step-by-step build plan
- LESSONS_FROM_COURT_BOT.md - Proven architectural patterns

Current phase: [tell Claude which phase you're on]
Working on: [specific component]
```

## 📋 Recommended Workflow

### Phase 1: Foundation (Session 1)

**Context to provide:**
- REGULATORY_COMMENT_BOT_SPEC.md (database schema section)
- LESSONS_FROM_COURT_BOT.md (SQLite patterns)

**Tasks:**
1. Create database schema
```
Create database/schema.sql based on REGULATORY_COMMENT_BOT_SPEC.md section "Database Schema"

Include:
- comment_periods table with all fields
- bot_posts table
- agencies table
- All indexes
- Proper constraints (UNIQUE on document_id, CHECK constraints)
```

2. Create database utilities
```
Create database/db.py with these functions:
- get_connection() - Return SQLite connection with row_factory
- initialize_database() - Create tables from schema.sql
- upsert_comment_period(document_id, **kwargs) - Insert/update period
- get_new_comment_periods(days=1) - Get recent periods not yet posted
- get_closing_soon(days=7) - Get periods closing in N days
- mark_posted(period_id, post_type) - Mark as posted to avoid duplicates
- get_period_by_document_id(document_id) - Fetch single period

Use ON CONFLICT pattern from LESSONS_FROM_COURT_BOT.md
```

3. Test database
```bash
python -m database.db
sqlite3 database/comment_periods.db ".schema"
```

### Phase 2: Scraper (Sessions 2-3)

**Context to provide:**
- API_DOCUMENTATION.md (entire file)
- IMPLEMENTATION_GUIDE.md (Phase 2 section)

**Task 1: Base scraper**
```
Create scrapers/base.py

Include BaseScraper class with:
- fetch_page(url, params=None) - Requests with user-agent
- Rate limiting (1 second between requests using time.sleep)
- Error handling (retry on timeout, handle 429)
- Logging

Reference LESSONS_FROM_COURT_BOT.md for error handling patterns.
```

**Task 2: Regulations.gov scraper**
```
Create scrapers/regulations_gov.py

Use API_DOCUMENTATION.md "Regulations.gov API (v4)" section.

Class: RegulationsGovScraper(BaseScraper)

Methods:
- __init__(api_key)
- get_new_comment_periods(days_back=1) - Query for new periods
- get_document_details(doc_id) - Get full details
- scrape(dry_run=False) - Main scraper logic

Query parameters:
- filter[openForComment]=true
- filter[commentEndDate][ge]=today
- filter[postedDate][ge]=yesterday
- page[size]=250

Return list of dicts with:
- document_id
- title
- agency_id, agency_name
- comment_end_date
- abstract/summary
- regulations_url (construct from document_id)

If not dry_run, save to database using upsert_comment_period()
```

**Task 3: Federal Register enrichment**
```
Create scrapers/federal_register.py

Use API_DOCUMENTATION.md "Federal Register API (v1)" section.

Function: enrich_with_federal_register(document_id, fr_doc_num)

If fr_doc_num exists:
- Query Federal Register API
- Get better abstract
- Get topics
- Get federal_register_url
- Return enriched dict

This scraper supplements Regulations.gov data with better summaries.
```

**Task 4: Topic categorization**
```
Create scrapers/categorizer.py

Function: categorize(period_dict) -> List[str]

Categories (from REGULATORY_COMMENT_BOT_SPEC.md):
- Environment & Climate
- Healthcare
- Privacy & Security
- Labor & Employment
- Transportation
- Technology & Internet
- Finance & Banking
- Education
- Housing
- Agriculture & Food

Use keyword matching on:
- title (lowercase)
- abstract (lowercase)
- agency_id

Return list of matching categories.

Example:
period = {'title': 'EPA Clean Water Rule', 'agency_id': 'EPA'}
-> ['Environment & Climate']
```

### Phase 3: Bluesky Bot (Sessions 4-5)

**Context to provide:**
- REGULATORY_COMMENT_BOT_SPEC.md (Bot Behavior section)
- LESSONS_FROM_COURT_BOT.md (Posting patterns)

**Task 1: Bluesky poster**
```
Create bot/bluesky_poster.py

Requirements:
- pip install atproto

Class: BlueskyPoster
- __init__(handle, app_password)
- login()
- post(text) - Post to Bluesky, return URI
- Error handling

Simple wrapper around atproto Client.
```

**Task 2: Post formatting**
```
Create bot/post_periods.py

Functions:
- format_new_period(period) - Initial announcement post
- format_reminder(period, days) - Deadline reminder (7, 3, or 1 day)
- post_new_periods() - Query DB, post new periods, mark as posted
- post_deadline_reminders() - Check closing soon, post reminders

Use post templates from REGULATORY_COMMENT_BOT_SPEC.md "Post Types"

Keep posts under 300 characters (Bluesky limit)
Include:
- Emoji (🛖, ⏰, 🚨, 📢)
- Agency and topic
- Comment link
- Hashtags
```

**Test:**
```bash
python -m bot.post_periods --dry-run
```

### Phase 4: GitHub Actions (Session 6)

**Context to provide:**
- LESSONS_FROM_COURT_BOT.md (GitHub Actions workflow)
- IMPLEMENTATION_GUIDE.md (Phase 4)

**Task:**
```
Create .github/workflows/daily.yml

Schedule: Daily at 9 AM ET (2 PM UTC)
Manual trigger: workflow_dispatch with dry_run option

Steps:
1. Checkout code
2. Setup Python 3.11
3. Install dependencies (requirements.txt)
4. Run scrapers (regulations_gov.py)
5. Post to Bluesky (post_periods.py)
6. Build website (web/build.py)
7. Commit database and docs/
8. Push to repo

Use secrets:
- BLUESKY_HANDLE
- BLUESKY_APP_PASSWORD
- REGULATIONS_API_KEY

Use exact pattern from LESSONS_FROM_COURT_BOT.md
```

### Phase 5: Website (Sessions 7-8)

**Context to provide:**
- REGULATORY_COMMENT_BOT_SPEC.md (Website Features section)
- LESSONS_FROM_COURT_BOT.md (Static site generator)

**Task 1: Site generator**
```
Create web/build.py

Functions:
- build_index_page() - Generate docs/index.html
- build_rss_feed() - Generate docs/feed.xml
- build_json_api() - Generate docs/data.json
- copy_static_files() - Copy CSS/JS to docs/

Query database for all open comment periods
Render using templates
Write to docs/ folder (GitHub Pages)
```

**Task 2: Templates and styling**
```
Create web/templates/index.html.template

Features:
- Header with stats (X open periods)
- Filter buttons (by topic, agency)
- Cards for each comment period
- Responsive grid layout
- Mobile-friendly

Create web/static/styles.css
- Clean, professional design
- Card-based layout
- Filter button styling

Create web/static/script.js
- Client-side filtering
- Hide/show cards based on selection
```

## 🎨 Effective Prompting Patterns

### ✅ Good Prompts

**Specific with context:**
```
Create database/db.py based on schema.sql

Include:
- get_connection() returning sqlite3.Connection with row_factory=sqlite3.Row
- upsert_comment_period() using ON CONFLICT pattern from LESSONS_FROM_COURT_BOT.md
- Error handling with try/except

Reference LESSONS_FROM_COURT_BOT.md for the upsert pattern.
```

**Break down complex tasks:**
```
Create scrapers/regulations_gov.py in 3 steps:

Step 1: Write get_new_comment_periods() method that queries the API
Step 2: Write get_document_details() for individual documents
Step 3: Write scrape() method that orchestrates both

Use API_DOCUMENTATION.md for endpoint details.
```

**Provide error messages:**
```
I'm getting this error when scraping:

[paste error]

Here's my code in scrapers/regulations_gov.py:

[paste relevant code]

The API docs say: [paste relevant API documentation]

How do I fix this?
```

### ❌ Avoid Vague Prompts

**Too vague:**
```
Make a scraper
```

**Too broad:**
```
Build the whole bot
```

**Without context:**
```
Why isn't this working? [paste code with no context]
```

## 🔧 Common Development Patterns

### Testing Individual Components

**Always test incrementally:**
```bash
# Test database
python -m database.db
sqlite3 database/comment_periods.db "SELECT * FROM comment_periods LIMIT 5;"

# Test scraper with dry-run
python -m scrapers.regulations_gov --dry-run

# Test posting with dry-run
python -m bot.post_periods --dry-run

# Test website locally
python -m web.build
open docs/index.html
```

### Debugging with Claude

**Provide full context:**
```
I'm trying to scrape Regulations.gov but getting 403 errors.

Error:
[paste full traceback]

Code (scrapers/regulations_gov.py):
[paste relevant function]

API key is set in .env:
REGULATIONS_API_KEY=DEMO_KEY

According to API_DOCUMENTATION.md, the endpoint is:
https://api.regulations.gov/v4/documents

What am I doing wrong?
```

### Iterating on Features

**Start simple, then enhance:**
```
# First iteration
"Create a basic scraper that gets document IDs and titles"

# Test it
python -m scrapers.regulations_gov --dry-run

# Second iteration
"Now add enrichment from Federal Register API to get better abstracts"

# Test again
python -m scrapers.regulations_gov --dry-run

# Third iteration
"Add categorization using scrapers/categorizer.py"
```

## 📚 Key Reference Points

### When Working on Database
- Reference: REGULATORY_COMMENT_BOT_SPEC.md (Database Schema)
- Pattern: LESSONS_FROM_COURT_BOT.md (SQLite in Git, Upsert pattern)
- Example: Court bot's database/db.py

### When Working on Scrapers
- Reference: API_DOCUMENTATION.md (complete API reference)
- Pattern: LESSONS_FROM_COURT_BOT.md (BaseScraper class)
- Example: Court bot's scrapers/

### When Working on Bluesky Bot
- Reference: REGULATORY_COMMENT_BOT_SPEC.md (Post Types)
- Pattern: LESSONS_FROM_COURT_BOT.md (Post formatting)
- Example: Court bot's bot/bluesky_poster.py

### When Working on GitHub Actions
- Reference: IMPLEMENTATION_GUIDE.md (Phase 4)
- Pattern: LESSONS_FROM_COURT_BOT.md (Daily workflow)
- Example: Court bot's .github/workflows/daily.yml

### When Working on Website
- Reference: REGULATORY_COMMENT_BOT_SPEC.md (Website Features)
- Pattern: LESSONS_FROM_COURT_BOT.md (Static site generator)
- Example: Court bot's web/build.py

## 🎯 Session Planning

### Session 1: Database Foundation (1-2 hours)
- Create schema.sql
- Create db.py
- Test database creation
- Verify queries work

### Session 2: Basic Scraper (2 hours)
- Create base.py
- Create regulations_gov.py
- Test with DEMO_KEY
- Get API key if needed

### Session 3: Enrichment & Categorization (1-2 hours)
- Create federal_register.py
- Create categorizer.py
- Test full scraping pipeline

### Session 4: Bluesky Integration (1-2 hours)
- Create bluesky_poster.py
- Create post_periods.py
- Test dry-run posting

### Session 5: GitHub Actions (1 hour)
- Create workflow file
- Set up secrets
- Test manual trigger

### Session 6: Website (2-3 hours)
- Create build.py
- Create templates
- Create static files
- Enable GitHub Pages

### Session 7: Testing & Refinement (1-2 hours)
- End-to-end testing
- Fix bugs
- Improve filtering
- Polish UI

## 🚀 Launch Checklist

Before going live:
- [ ] Database schema created
- [ ] Scraper finds new periods
- [ ] Data saves to database correctly
- [ ] Bot posts to Bluesky (dry-run works)
- [ ] GitHub Actions runs without errors
- [ ] Website generates and deploys
- [ ] RSS feed validates
- [ ] Mobile-responsive design tested
- [ ] Bot profile complete with bio and link

## 💡 Pro Tips for Working with Claude

1. **One component at a time** - Don't ask for everything at once
2. **Reference the docs** - Always point to relevant spec sections
3. **Test before moving on** - Verify each component works
4. **Iterate** - Start simple, add complexity gradually
5. **Show errors** - Include full tracebacks when debugging
6. **Use dry-run mode** - Test logic without side effects
7. **Commit often** - Easy to roll back if something breaks

## 🆘 Troubleshooting Guide

### "Module not found" errors
```
Make sure you're in the project root and running as a module:
python -m scrapers.regulations_gov
```

### API rate limits
```
Use DEMO_KEY for testing (50 requests/hour)
Request real key from: https://open.gsa.gov/api/regulationsgov/
```

### Database locked
```
Make sure only one process is writing at a time
Close any open sqlite3 connections
```

### GitHub Actions failing
```
Check:
1. Python version (must be 3.11)
2. Secrets are set correctly
3. requirements.txt is complete
4. Database file is committed
```

---

**Built with VS Code Claude Sonnet 4.5. Let's make government accessible!** 🛖✨
