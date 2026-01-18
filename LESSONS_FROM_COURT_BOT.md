# Lessons from Federal Court Hearings Bot

What worked, what didn't, and how to apply these patterns to the regulatory comment bot.

## ✅ What Worked Brilliantly

### 1. SQLite Database in Git

**Pattern:**
```
database/
├── schema.sql          # Version-controlled schema
├── db.py              # Database utilities
└── hearings.db        # Actual data (committed to git)
```

**Why it worked:**
- GitHub Actions runs persist database between runs
- No external database needed (zero cost)
- Easy to inspect locally (`sqlite3 database/hearings.db`)
- Automatic backups via git history
- Simple queries, no ORM complexity

**Apply to comment bot:**
```
database/
├── schema.sql
├── db.py
└── comment_periods.db  # Commit this!
```

### 2. Idempotent Scraping

**Pattern:**
```python
def upsert_judge(court_id, name, phone, **kwargs):
    """Insert or update judge info"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO judges (court_id, name, phone, ...)
        VALUES (?, ?, ?, ...)
        ON CONFLICT(court_id, name) 
        DO UPDATE SET 
            phone=excluded.phone,
            last_updated=CURRENT_TIMESTAMP
    """, (court_id, name, phone, ...))
    
    conn.commit()
```

**Why it worked:**
- Safe to run scraper multiple times
- Handles updates gracefully
- UNIQUE constraints prevent duplicates
- ON CONFLICT updates changed data only

**Apply to comment bot:**
```python
def upsert_comment_period(document_id, **data):
    """Insert or update comment period"""
    # Same pattern - UNIQUE(document_id)
    # Update if already exists
```

### 3. GitHub Actions Daily Workflow

**Pattern:**
```yaml
name: Scrape and Post
on:
  schedule:
    - cron: '0 11 * * *'  # 6 AM ET / 11 AM UTC
  workflow_dispatch:        # Manual trigger

jobs:
  scrape-and-post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt --break-system-packages
      
      - name: Scrape courts
        run: |
          python -m scrapers.dc_district
          python -m scrapers.ndca_judges
          # ... more scrapers
      
      - name: Post to Bluesky
        run: python -m bot.post_daily
        env:
          BLUESKY_HANDLE: ${{ secrets.BLUESKY_HANDLE }}
          BLUESKY_APP_PASSWORD: ${{ secrets.BLUESKY_APP_PASSWORD }}
      
      - name: Commit database
        run: |
          git config user.name "Bot"
          git config user.email "bot@noreply"
          git add database/hearings.db
          git commit -m "Update data" || echo "No changes"
          git push
```

**Why it worked:**
- Fully automated (no server needed)
- Free (GitHub Actions generous free tier)
- Easy to debug (logs in GitHub UI)
- Manual trigger for testing
- Database persists via git push

**Apply to comment bot:**
- Same pattern, adjust cron time
- Add step for website generation
- Commit both database AND docs/ folder

### 4. Fuzzy String Matching for Names

**Pattern:**
```python
from fuzzywuzzy import fuzz

def find_matching_judge(hearing_judge_name, judges_list):
    """
    Match 'Chief Judge Beryl A. Howell' to 'Beryl A. Howell'
    """
    # Clean names
    clean_hearing = clean_judge_name(hearing_judge_name)
    
    best_match = None
    best_score = 0
    
    for judge in judges_list:
        clean_judge = clean_judge_name(judge['name'])
        score = fuzz.ratio(clean_hearing, clean_judge)
        
        if score > best_score and score >= 85:  # 85% match threshold
            best_score = score
            best_match = judge
    
    return best_match

def clean_judge_name(name):
    """Remove titles, normalize spacing"""
    # Remove common prefixes
    name = re.sub(r'^(Chief Judge|Judge|Magistrate Judge|Hon\.)\s+', '', name, flags=re.IGNORECASE)
    # Normalize whitespace
    name = ' '.join(name.split())
    return name.strip()
```

**Why it worked:**
- Court calendars inconsistent with judge spellings
- "Chief Judge John Doe" vs "John Doe" matched correctly
- Improved match rate from 80% → 100%

**Apply to comment bot:**
- Not directly applicable (document IDs are consistent)
- But same principle: normalize data before matching
- Useful for agency name matching between APIs

### 5. Simple Post Formatting

**Pattern:**
```python
def format_hearing_post(hearing, judge):
    """Keep it clean and scannable"""
    
    time_str = format_time(hearing['time'])
    
    post = f"""🏛️ {hearing['court_name']} - {hearing['date_display']}

{time_str} - {hearing['case_name'][:80]}

Judge {judge['name']}
📞 {judge['phone']}"""
    
    if judge['zoom_link']:
        post += f"\n🔗 {judge['zoom_link']}"
    
    post += f"\n\n#{hearing['court_id'].upper()}"
    
    return post
```

**Why it worked:**
- Emoji for scannability (🏛️ 📞 🔗)
- Clean structure (date, time, case, judge, access)
- Hashtags for filtering
- Under 300 chars (Bluesky limit)

**Apply to comment bot:**
```python
post = f"""🏛️ {agency_name} Proposes New Rule

Open for comment until {deadline}

What's changing:
{plain_english_summary}

Comment here:
{comment_url}

#{category_hashtag}"""
```

### 6. Static Website with GitHub Pages

**Pattern:**
```python
# web/build.py
def build_site():
    # 1. Read from database
    hearings = get_upcoming_hearings()
    
    # 2. Generate HTML from template
    html = render_template('index.html', hearings=hearings)
    
    # 3. Write to docs/ (GitHub Pages folder)
    with open('docs/index.html', 'w') as f:
        f.write(html)
    
    # 4. Generate RSS feed
    generate_rss_feed(hearings)
    
    # 5. Copy static assets
    shutil.copytree('web/static/', 'docs/')
```

**Why it worked:**
- No server needed
- Free hosting via GitHub Pages
- Auto-deploys on every commit
- Fast (static HTML)
- Easy to customize

**Apply to comment bot:**
- Exact same pattern
- Generate pages for:
  - Browse all open periods
  - Filter by topic/agency
  - Individual period pages
  - RSS feeds by topic

## ❌ What Didn't Work (Initially)

### 1. Match Rate Too Low

**Problem:**
- Initial: 82.9% match rate (37 hearings → 30 matched to judges)
- Caused by: prefix handling bug, strict matching

**Solution:**
- Better name cleaning
- Fuzzy matching with lower threshold
- Result: 100% match rate

**Lesson for comment bot:**
- Start with strict matching for document IDs
- Add fuzzy matching for agency names if needed
- Always log unmatched items for debugging

### 2. Duplicate Hearings

**Problem:**
- Same hearing appearing multiple times in database
- Caused by: scraper running multiple times, no UNIQUE constraint

**Solution:**
```sql
ALTER TABLE hearings 
ADD UNIQUE(court_id, case_number, hearing_date, hearing_time);
```

**Lesson for comment bot:**
```sql
-- CRITICAL: Add UNIQUE constraint on document_id
CREATE TABLE comment_periods (
    document_id TEXT NOT NULL UNIQUE,
    ...
);
```

### 3. Timezone Confusion

**Problem:**
- Mixed ET and PT times
- Hard to tell which timezone a hearing was in

**Solution:**
```python
def format_time(time_str, court_id):
    """Always show timezone"""
    tz = "ET" if court_id == "dcd" else "PT"
    return f"{time} {tz}"
```

**Lesson for comment bot:**
- Comment deadlines are always 11:59 PM ET
- Always display: "Closes March 15, 2026 at 11:59 PM ET"
- Store dates as DATE (not DATETIME) since time is always 11:59 PM

## 🎯 Architecture Patterns to Reuse

### 1. Modular Scraper Design

**Pattern:**
```
scrapers/
├── base.py              # BaseScraper class
├── dc_district.py       # DC District Court
├── ndca_judges.py       # NDCA judges
└── ca8_sessions.py      # 8th Circuit
```

**Each scraper:**
```python
class MyCourtScraper(BaseScraper):
    URL = "https://..."
    COURT_ID = "myct"
    
    def scrape(self, dry_run=False):
        soup = self.fetch_page(self.URL)
        data = self.parse(soup)
        if not dry_run:
            self.save(data)
        return data
```

**Apply to comment bot:**
```
scrapers/
├── base.py
├── regulations_gov.py   # Main scraper
├── federal_register.py  # Enrichment scraper
└── categorizer.py       # Topic categorization
```

### 2. Database Module with Utilities

**Pattern:**
```python
# database/db.py

def get_connection():
    """Return SQLite connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def upsert_judge(...):
    """Upsert judge data"""
    # SQL logic here
    
def get_upcoming_hearings(days=7):
    """Get hearings in next N days"""
    # Query logic here
    
def mark_hearing_posted(hearing_id):
    """Mark as posted to avoid duplicates"""
    # Update logic here
```

**Apply to comment bot:**
```python
# database/db.py

def upsert_comment_period(...)
def get_new_comment_periods()
def get_closing_soon(days=7)
def mark_posted(period_id, post_type)
```

### 3. Posting Module with Templates

**Pattern:**
```python
# bot/bluesky_poster.py

class BlueskyPoster:
    def __init__(self, handle, password):
        self.client = Client()
        self.login(handle, password)
    
    def post(self, text):
        """Post to Bluesky"""
        self.client.send_post(text=text)
    
# bot/post_daily.py

def post_hearings_for_today():
    hearings = get_todays_hearings()
    poster = BlueskyPoster(handle, password)
    
    for hearing in hearings:
        if not hearing['posted']:
            text = format_hearing_post(hearing)
            poster.post(text)
            mark_posted(hearing['id'])
```

**Apply to comment bot:**
```python
# bot/post_periods.py

def post_new_periods():
    periods = get_new_periods()
    for period in periods:
        if not period['posted_new']:
            text = format_new_period(period)
            poster.post(text)
            mark_posted(period['id'], 'new')

def post_deadline_reminders():
    # 7-day reminders
    periods_7day = get_closing_soon(days=7)
    for period in periods_7day:
        if not period['posted_7day_reminder']:
            text = format_reminder(period, days=7)
            poster.post(text)
            mark_posted(period['id'], '7day')
```

## 📋 Testing Strategies That Worked

### 1. Dry-Run Mode

**Pattern:**
```python
# In scraper
def scrape(self, dry_run=False):
    data = self.fetch_and_parse()
    
    if dry_run:
        print(f"Would save: {len(data)} items")
        print(json.dumps(data[0], indent=2))  # Show sample
        return data
    else:
        self.save_to_database(data)
        return data

# Usage
python -m scrapers.dc_district --dry-run
```

**Apply to comment bot:**
```bash
python -m scrapers.regulations_gov --dry-run
python -m bot.post_periods --dry-run
```

### 2. Manual GitHub Actions Trigger

**Pattern:**
```yaml
on:
  schedule:
    - cron: '0 11 * * *'
  workflow_dispatch:         # <-- This line!
    inputs:
      dry_run:
        description: 'Dry run (no posting)'
        required: false
        default: 'false'
      scrape_only:
        description: 'Only scrape, do not post'
        required: false
        default: 'false'
```

**Usage:**
- Go to Actions tab in GitHub
- Click "Run workflow"
- Choose branch and options
- Click "Run"

**Apply to comment bot:**
- Same pattern
- Add options for testing

### 3. Local Testing Before Deploy

**Pattern:**
```bash
# 1. Test scraper
python -m scrapers.regulations_gov --dry-run

# 2. Test with real database
python -m scrapers.regulations_gov

# 3. Inspect database
sqlite3 database/comment_periods.db
> SELECT * FROM comment_periods LIMIT 5;

# 4. Test posting (dry-run)
python -m bot.post_periods --dry-run

# 5. Build website locally
python -m web.build
open docs/index.html

# 6. Push to GitHub (triggers Actions)
git add .
git commit -m "Test changes"
git push
```

## 🚀 Deployment Strategy

### Phase 1: Local Development
1. Set up database schema
2. Build scrapers
3. Test with small dataset
4. Build posting logic
5. Test everything locally

### Phase 2: GitHub Actions Setup
1. Create `.github/workflows/daily.yml`
2. Add secrets (Bluesky credentials, API keys)
3. Test with manual trigger
4. Monitor logs
5. Fix issues

### Phase 3: Website Generation
1. Build static site generator
2. Test locally
3. Add to workflow
4. Enable GitHub Pages
5. Verify deployment

### Phase 4: Polish & Monitor
1. Watch for errors in logs
2. Improve post formatting based on engagement
3. Add features based on feedback
4. Iterate

## 💡 Key Insights

1. **Start simple** - MVP first, features later
2. **Use existing patterns** - Don't reinvent the wheel
3. **Test incrementally** - Don't deploy everything at once
4. **Monitor logs** - GitHub Actions logs are your friend
5. **Iterate quickly** - Easy to fix when it's all in git

## 🎁 Reusable Code

You can copy entire modules from court bot:
- `database/db.py` structure
- `bot/bluesky_poster.py` class
- `web/build.py` static site generator
- `.github/workflows/daily.yml` template

Just adapt the queries and data models!

---

**These patterns have been battle-tested. Use them with confidence.** 🚀
