# Implementation Guide - Regulatory Comment Bot

Step-by-step implementation guide for building this with VS Code Claude.

## 📋 Prerequisites

Before starting:
- GitHub account
- Bluesky account (create bot account: e.g., `@fedcomments.bsky.social`)
- VS Code with Claude extension installed
- Basic familiarity with Python and GitHub

## 🎯 Implementation Strategy

**Total time:** 8-12 hours over 1-2 weeks

**Approach:** Incremental development
- Build each component
- Test thoroughly
- Deploy when working
- Add features iteratively

## Phase 1: Foundation (2-3 hours)

### Step 1.1: Create GitHub Repository

```bash
# On GitHub
1. Create new repo: "regulatory-comment-bot"
2. Initialize with README
3. Clone locally
```

### Step 1.2: Project Structure

Create this structure:
```
regulatory-comment-bot/
├── .github/
│   └── workflows/
│       └── daily.yml
├── database/
│   ├── schema.sql
│   ├── db.py
│   └── comment_periods.db (created by db.py)
├── scrapers/
│   ├── __init__.py
│   ├── base.py
│   └── regulations_gov.py
├── bot/
│   ├── __init__.py
│   ├── bluesky_poster.py
│   └── post_periods.py
├── web/
│   ├── build.py
│   ├── templates/
│   │   └── index.html.template
│   └── static/
│       ├── styles.css
│       └── script.js
├── docs/ (generated)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Step 1.3: Set Up Database

**In VS Code Claude, provide:**

```
Create database/schema.sql based on REGULATORY_COMMENT_BOT_SPEC.md

Include:
- comment_periods table
- bot_posts table  
- agencies table
- All indexes
```

**Then create `database/db.py`:**

```
Create database/db.py with:
- get_connection()
- initialize_database()
- upsert_comment_period()
- get_new_comment_periods()
- get_closing_soon(days)
- mark_posted(period_id, post_type)
```

**Test it:**
```bash
python -m database.db  # Should create comment_periods.db
sqlite3 database/comment_periods.db ".schema"  # Verify schema
```

### Step 1.4: Requirements File

**Create `requirements.txt`:**
```
requests>=2.31.0
beautifulsoup4>=4.12.0
atproto>=0.0.50
feedgen>=1.0.0
lxml>=4.9.0
python-dotenv>=1.0.0
```

**Install:**
```bash
pip install -r requirements.txt
```

### Step 1.5: Environment Variables

**Create `.env.example`:**
```
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=your-app-password
REGULATIONS_API_KEY=your-api-key
```

**Create `.env` (don't commit!):**
```bash
cp .env.example .env
# Edit .env with real credentials
```

**Update `.gitignore`:**
```
.env
__pycache__/
*.pyc
.DS_Store
venv/
```

## Phase 2: Scraper (3-4 hours)

### Step 2.1: Base Scraper Class

**In VS Code Claude:**

```
Create scrapers/base.py with BaseScraper class

Include:
- fetch_page(url) method with user-agent
- Rate limiting (1 second between requests)
- Error handling
- Logging
```

### Step 2.2: Regulations.gov Scraper

**In VS Code Claude, provide the API_DOCUMENTATION.md file and ask:**

```
Create scrapers/regulations_gov.py

Scrape Regulations.gov API for:
- New comment periods (posted in last 24 hours)
- Document details
- Build comment URLs

Use API_DOCUMENTATION.md for reference.

Should have:
- get_new_comment_periods(days_back=1)
- get_document_details(doc_id)
- Main scrape() method
- --dry-run flag for testing
```

**Test it:**
```bash
# Get API key from https://open.gsa.gov/api/regulationsgov/
# Add to .env

python -m scrapers.regulations_gov --dry-run
```

### Step 2.3: Topic Categorization

**In VS Code Claude:**

```
Create scrapers/categorizer.py

Auto-categorize comment periods by keywords:

Categories:
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

Use title, abstract, agency to categorize.
Return list of matching categories.
```

**Test:**
```python
from scrapers.categorizer import categorize

period = {
    'title': 'EPA Clean Water Standards',
    'abstract': 'Proposes limits on PFAS in drinking water',
    'agency': 'EPA'
}

categories = categorize(period)
# Should return: ['Environment & Climate', 'Healthcare']
```

## Phase 3: Bluesky Bot (2 hours)

### Step 3.1: Bluesky Poster Class

**In VS Code Claude:**

```
Create bot/bluesky_poster.py

Wrapper for atproto Bluesky client:
- __init__(handle, password)
- login()
- post(text)
- Error handling
```

**Test connection:**
```python
from bot.bluesky_poster import BlueskyPoster

poster = BlueskyPoster(handle, password)
poster.post("Test post from regulatory comment bot!")
```

### Step 3.2: Post Formatting

**In VS Code Claude:**

```
Create bot/post_periods.py

Include functions:
- format_new_period(period) - Initial announcement
- format_reminder(period, days) - Deadline reminder
- post_new_periods() - Post today's new periods
- post_deadline_reminders() - Post 7-day, 3-day, last-day reminders

Use post templates from REGULATORY_COMMENT_BOT_SPEC.md
```

**Test dry-run:**
```bash
python -m bot.post_periods --dry-run
```

## Phase 4: GitHub Actions (1 hour)

### Step 4.1: Create Workflow

**In VS Code Claude:**

```
Create .github/workflows/daily.yml

Schedule:
- Run daily at 9 AM ET (2 PM UTC)
- Manual trigger option

Steps:
1. Checkout code
2. Set up Python 3.11
3. Install dependencies
4. Scrape Regulations.gov
5. Post to Bluesky
6. Commit database
7. (Later) Build website

Use LESSONS_FROM_COURT_BOT.md for workflow template.
```

### Step 4.2: Add GitHub Secrets

1. Go to repo Settings → Secrets and variables → Actions
2. Add:
   - `BLUESKY_HANDLE`
   - `BLUESKY_APP_PASSWORD`
   - `REGULATIONS_API_KEY`

### Step 4.3: Test Workflow

1. Push to GitHub
2. Go to Actions tab
3. Click "Run workflow" (manual trigger)
4. Select "dry_run: true"
5. Monitor logs

**Debug issues:**
- Check Python version
- Verify dependencies installed
- Check secrets are available
- Review error messages in logs

## Phase 5: Website (2-3 hours)

### Step 5.1: Static Site Generator

**In VS Code Claude, provide WEB_INTERFACE_SPEC.md:**

```
Create web/build.py based on WEB_INTERFACE_SPEC.md

Generate:
- index.html (browse all open periods)
- feed.xml (RSS feed)
- data.json (JSON API)

Features:
- Filter by topic/agency
- Sort by deadline
- Responsive design
```

### Step 5.2: Templates & Static Files

**In VS Code Claude:**

```
Create web/templates/index.html.template

Include:
- Header with stats
- Filter buttons (by topic/agency)
- Cards for each comment period
- Responsive grid layout
```

```
Create web/static/styles.css

Clean, professional design:
- Color palette from court bot
- Card-based layout
- Mobile-responsive
```

```
Create web/static/script.js

Client-side filtering:
- Filter by topic
- Filter by agency
- Hide/show based on selection
```

### Step 5.3: Test Locally

```bash
# Build site
python -m web.build

# Open in browser
open docs/index.html

# Check RSS feed
open docs/feed.xml

# Check JSON API
cat docs/data.json | jq .
```

### Step 5.4: Enable GitHub Pages

1. Go to repo Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main`, Folder: `/docs`
4. Save
5. Wait 2-3 minutes for deployment

**Site will be live at:**
`https://yourusername.github.io/regulatory-comment-bot/`

## Phase 6: Integration & Testing (1-2 hours)

### Step 6.1: End-to-End Test

**Full workflow:**
```bash
# 1. Scrape
python -m scrapers.regulations_gov

# 2. Check database
sqlite3 database/comment_periods.db "SELECT COUNT(*) FROM comment_periods;"

# 3. Test posting (dry-run)
python -m bot.post_periods --dry-run

# 4. Build website
python -m web.build

# 5. Push to GitHub
git add .
git commit -m "Full integration test"
git push

# 6. Watch GitHub Actions
# Go to Actions tab and monitor workflow

# 7. Check website
# Visit https://yourusername.github.io/regulatory-comment-bot/
```

### Step 6.2: Update Workflow

**Add website build step to `.github/workflows/daily.yml`:**

```yaml
- name: Build Website
  run: python -m web.build

- name: Commit Changes
  run: |
    git config user.name "Comment Bot"
    git config user.email "bot@noreply.github.com"
    git add database/comment_periods.db docs/
    git commit -m "Update data - $(date)" || echo "No changes"
    git push
```

## Phase 7: Refinement (Ongoing)

### Improve Filtering

**Only post high-impact rules:**
```python
def should_post(period):
    """Filter to important rules"""
    
    # Always post these agencies
    priority_agencies = ['EPA', 'FDA', 'FCC', 'FTC', 'DOL']
    if period['agency'] in priority_agencies:
        return True
    
    # Post if Proposed Rule (not Notice)
    if period['document_type'] == 'Proposed Rule':
        return True
    
    # Post if lots of comments already (viral)
    if period.get('comment_count', 0) > 100:
        return True
    
    # Otherwise skip
    return False
```

### Add AI Summaries

**Optional: Use Claude API for better summaries:**
```python
from anthropic import Anthropic

def generate_summary(abstract):
    """Generate plain-English summary"""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = f"""Summarize this proposed regulation in 2-3 sentences that a regular person can understand. Focus on:
- What's changing
- Who's affected
- Why it matters

Regulation abstract:
{abstract}

Plain English summary:"""
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text
```

## 🎯 Success Checklist

After implementation, verify:

- [ ] Database creates successfully
- [ ] Scraper finds new comment periods
- [ ] Scraper stores data correctly
- [ ] Bot posts to Bluesky (dry-run works)
- [ ] GitHub Actions runs without errors
- [ ] Website generates and deploys
- [ ] RSS feed validates
- [ ] Filtering works on website
- [ ] Mobile-responsive design
- [ ] Bot account has profile info + link to website

## 🐛 Troubleshooting

### "Module not found" Error
```bash
# Make sure you're in project root
pwd
# Should show: .../regulatory-comment-bot

# Try running as module
python -m scrapers.regulations_gov
```

### GitHub Actions Fails
- Check Python version (should be 3.11)
- Verify secrets are set correctly
- Look at error message in logs
- Test locally first

### No Comment Periods Found
- Check API key is valid
- Verify date range (might be no new periods today)
- Try expanding date range
- Check API rate limit

### Website Not Updating
- Verify docs/ folder is committed
- Check GitHub Pages is enabled
- Wait 2-3 minutes for deployment
- Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)

## 📚 Using VS Code Claude Effectively

### Good Prompts

**✅ Specific and contextual:**
```
Create database/db.py based on schema.sql

Include these functions:
- upsert_comment_period(document_id, **data)
- get_new_comment_periods(days=1)
- mark_posted(period_id, post_type)

Use sqlite3, return dicts, handle errors gracefully.
```

**❌ Too vague:**
```
Make a database file
```

### Provide Context

**Always give Claude:**
- Relevant spec docs (REGULATORY_COMMENT_BOT_SPEC.md, API_DOCUMENTATION.md)
- Example code from court bot
- Error messages if debugging
- What you've tried already

**Example:**
```
I'm getting this error when scraping:

[paste error]

Here's my code:

[paste code]

And here's the API docs:

[paste relevant section]

How do I fix this?
```

### Iterate

**Don't expect perfection first try:**
1. Get working version
2. Test it
3. Ask for improvements
4. Test again
5. Repeat

### Ask for Explanations

```
Can you explain how this categorization logic works?
What does this SQL query do?
Why did you use ON CONFLICT here?
```

## 🎉 Launch Checklist

Before announcing the bot:

- [ ] Bot has run successfully for 3+ days
- [ ] Website is live and looks good
- [ ] RSS feed works in feed reader
- [ ] Bot profile is complete (bio, avatar, link)
- [ ] README has clear description
- [ ] Post about it from your main account
- [ ] Share in relevant communities (civic tech, transparency, journalism)

## 🚀 Expansion Ideas

Once working well:

1. **More agencies** - Add SEC, HUD, ED, USDA
2. **Better categorization** - Machine learning
3. **Email alerts** - Weekly digest by topic
4. **Mobile app** - Push notifications
5. **Comment templates** - Help people write better comments
6. **State regulations** - Expand beyond federal

## 💡 Pro Tips

1. **Start small** - Get EPA working, then add more
2. **Test locally first** - Don't debug in GitHub Actions
3. **Use dry-run mode** - Test posting logic without actually posting
4. **Monitor logs** - GitHub Actions logs show everything
5. **Git commit often** - Easy to roll back if something breaks
6. **Ask for help** - Civic tech community is supportive!

---

**You've got this! Build something that helps democracy.** 🏛️✨

**Estimated timeline:**
- Weekend 1: Phases 1-3 (foundation, scraper, bot)
- Weekend 2: Phases 4-6 (GitHub Actions, website, testing)
- Weeknights: Refinement and polish

**Then: Launch and make civic participation accessible!** 🚀
