# Federal Regulatory Comment Period Bot

## 🎯 Mission

**Make civic participation accessible by broadcasting federal regulatory comment periods to the public.**

Help people discover and participate in the regulatory process by posting about open comment periods on Bluesky in plain language, explaining what's at stake, and providing direct links to comment.

## 🔍 The Problem

### Current State (Broken)

**Discovery is impossible:**
- No central "what's open now?" view
- Must know specific agency/docket to search
- Technical jargon (RIN numbers, docket IDs, CFR citations)
- Scattered across dozens of agency websites

**Comment periods are hidden:**
- Dense Federal Register notices
- Buried in Regulations.gov
- Only industry lobbyists and nonprofits monitor effectively
- Public has no idea they can participate

**Result:** Policy gets made without public input because people don't know how to participate.

### Gap Analysis

**What EXISTS:**
- ✅ Regulations.gov API (v4) - all the data
- ✅ Federal Register API - daily publications
- ✅ Email alerts - but require custom searches per topic
- ✅ @FedRegister Twitter - dry, technical, not comment-focused

**What DOESN'T exist:**
- ❌ User-friendly comment period tracker
- ❌ Social media bot explaining what's at stake
- ❌ Plain-language translations of rules
- ❌ Discovery mechanism ("browse what's open")
- ❌ Topic-based filtering for non-experts

## 🚀 The Solution

### What We're Building

**Bluesky Bot + Website** that:
1. **Discovers** new comment periods daily
2. **Translates** Federal Register legalese into plain English
3. **Posts** to Bluesky with context and deadlines
4. **Links** directly to comment submission
5. **Categorizes** by topic (environment, healthcare, immigration, tech, etc.)

### Architecture

```
┌──────────────────────┐
│  Regulations.gov API │
│  Federal Register API│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Daily Scraper       │
│  - New comment       │
│    periods           │
│  - Closing deadlines │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐       ┌──────────────────┐
│  comment_periods.db  │──────▶│  Post to Bluesky │
│  (SQLite)            │       │  - New periods   │
└──────────────────────┘       │  - Deadlines     │
           │                   │  - Categories    │
           │                   └──────────────────┘
           │
           ▼
┌──────────────────────┐
│  Static Website      │
│  - Browse all open   │
│  - Filter by topic   │
│  - RSS feed          │
│  - JSON API          │
└──────────────────────┘
```

### Core Features

**1. Daily Scraping**
- Check Regulations.gov for new proposed rules/notices
- Parse Federal Register for comment deadlines
- Categorize by agency and topic
- Store in SQLite database

**2. Bluesky Posts**
- **New comment periods** (when opened)
- **Deadline reminders** (7 days, 3 days, last day)
- **Plain language summary** of what's being proposed
- **Direct comment link**
- **Hashtags by topic** (#EPA #Healthcare #Privacy)

**3. Website**
- Browse all open comment periods
- Filter by agency, topic, deadline
- Calendar view
- RSS feed by topic
- JSON API for developers

**4. Topic Categorization**
Auto-tag by keywords and agency:
- 🌍 Environment & Climate
- 🏥 Healthcare
- 🛡️ Privacy & Security
- 💼 Labor & Employment
- 🚗 Transportation
- 💻 Technology & Internet
- 🏦 Finance & Banking
- 🎓 Education
- 🏠 Housing
- 🌾 Agriculture & Food

## 📊 Database Schema

### Table: `comment_periods`

```sql
CREATE TABLE comment_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identifiers
    document_id TEXT NOT NULL UNIQUE,    -- FDA-2024-N-1234
    docket_id TEXT NOT NULL,             -- FDA-2024-N-1234 (parent)
    
    -- Basic info
    title TEXT NOT NULL,
    agency_id TEXT NOT NULL,              -- FDA, EPA, FCC, etc.
    agency_name TEXT NOT NULL,
    document_type TEXT,                   -- Proposed Rule, Notice, etc.
    
    -- Dates
    posted_date DATE NOT NULL,
    comment_start_date DATE,
    comment_end_date DATE NOT NULL,
    
    -- Content
    abstract TEXT,                        -- Brief summary
    summary TEXT,                         -- AI-generated plain English
    
    -- Links
    regulations_url TEXT NOT NULL,        -- Direct comment link
    federal_register_url TEXT,
    details_url TEXT,
    
    -- Categorization
    topics TEXT,                          -- JSON array: ["healthcare", "privacy"]
    keywords TEXT,                        -- Comma-separated
    
    -- Status
    posted_new BOOLEAN DEFAULT 0,
    posted_7day_reminder BOOLEAN DEFAULT 0,
    posted_3day_reminder BOOLEAN DEFAULT 0,
    posted_last_day BOOLEAN DEFAULT 0,
    
    -- Metadata
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (comment_end_date >= comment_start_date)
);

CREATE INDEX idx_comment_end_date ON comment_periods(comment_end_date);
CREATE INDEX idx_posted_date ON comment_periods(posted_date);
CREATE INDEX idx_agency_id ON comment_periods(agency_id);
CREATE INDEX idx_posted_status ON comment_periods(posted_new, posted_7day_reminder, posted_3day_reminder, posted_last_day);
```

### Table: `bot_posts`

```sql
CREATE TABLE bot_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_period_id INTEGER NOT NULL,
    post_type TEXT NOT NULL,              -- 'new', '7day', '3day', 'last_day'
    post_uri TEXT NOT NULL,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comment_period_id) REFERENCES comment_periods(id)
);
```

### Table: `agencies`

```sql
CREATE TABLE agencies (
    id TEXT PRIMARY KEY,                  -- EPA, FDA, etc.
    name TEXT NOT NULL,
    description TEXT,
    website TEXT,
    topics TEXT                           -- JSON array of common topics
);
```

## 🔌 Data Sources

### 1. Regulations.gov API (Primary)

**Endpoint:** `https://api.regulations.gov/v4/documents`

**What we need:**
- New proposed rules and notices open for comment
- Comment period start/end dates
- Direct links to comment forms

**Query Example:**
```
GET /v4/documents?filter[commentEndDate][ge]=2026-01-18&filter[openForComment]=true
```

**Rate Limits:**
- Standard: 1000 requests/hour
- Can request increase for public service

### 2. Federal Register API (Secondary)

**Endpoint:** `https://www.federalregister.gov/api/v1/documents`

**What we need:**
- Additional metadata
- Better text summaries
- RIN numbers for tracking

**Query Example:**
```
GET /api/v1/documents.json?conditions[type][]=PRORULE&conditions[comment_date][gte]=2026-01-18
```

**No rate limit** - free public API

## 🤖 Bot Behavior

### Post Types

**1. New Comment Period (Posted immediately)**
```
🏛️ EPA Proposes New Clean Water Standards

Public comment period now open until March 15

What's changing:
New limits on PFAS chemicals in drinking water. Would affect 
200+ water systems nationwide.

Your voice matters! Comment here:
regulations.gov/commenton/EPA-HQ-OW-2024-0123

#EPA #CleanWater #Environment
```

**2. 7-Day Reminder**
```
⏰ 7 Days Left to Comment

EPA Clean Water Standards close March 15

18,543 comments received so far

Comment: regulations.gov/commenton/EPA-HQ-OW-2024-0123

#EPA #CleanWater
```

**3. 3-Day Reminder**
```
🚨 3 Days Left!

EPA Clean Water Standards close March 15

Last chance to make your voice heard

Comment: regulations.gov/commenton/EPA-HQ-OW-2024-0123
```

**4. Last Day**
```
📢 LAST DAY to Comment!

EPA Clean Water Standards close TODAY at 11:59pm ET

Comment now: regulations.gov/commenton/EPA-HQ-OW-2024-0123

#EPA #CleanWater
```

### Posting Strategy

**Volume Management:**
- ~100-300 new comment periods per day across all agencies
- **FILTER** to highest-impact rules:
  - Proposed Rules (not Notices)
  - Major agencies (EPA, FDA, FCC, FTC, DOL, etc.)
  - Rules with significant public interest
  - Cross-reference with news coverage

**Post Frequency:**
- **New periods:** 5-10 per day
- **Reminders:** As needed
- **Total:** 15-30 posts/day

**Topic Distribution:**
- Rotate through topics daily
- Prioritize based on follower engagement
- Special attention to breaking/controversial rules

## 🌐 Website Features

### Homepage

**"Open for Comment Right Now"**
- Cards for each open comment period
- Sort by: Deadline (soonest first), Most commented, Recently opened
- Filter by: Topic, Agency, Deadline range
- Search box

### Individual Comment Period Page

Shows:
- Title and summary
- What's being proposed (plain English)
- Who's affected
- Comment deadline (with countdown)
- Number of comments submitted so far
- Direct "Submit Comment" button
- Link to full Federal Register notice

### RSS Feeds

- All comment periods: `/feed.xml`
- By topic: `/feed/environment.xml`
- By agency: `/feed/epa.xml`

### JSON API

```
GET /api/periods/open           # All open periods
GET /api/periods/closing        # Closing in 7 days
GET /api/periods/{document_id}  # Single period
GET /api/topics                 # List all topics
```

## 🎨 User Experience

### For Regular People

**Problem:** "I care about clean air but don't know how to participate"

**Solution:**
1. Follow bot on Bluesky
2. See post about new EPA air quality rule
3. Read plain-English summary
4. Click link
5. Submit comment in 5 minutes

**Impact:** Empowers citizens to participate in democracy

### For Journalists

**Problem:** "I miss important regulatory developments"

**Solution:**
1. Subscribe to RSS feed for their beat (healthcare, tech, etc.)
2. Get alerts when relevant rules drop
3. Story ideas delivered automatically

**Impact:** Better regulatory coverage

### For Nonprofits

**Problem:** "We can't monitor 50+ federal agencies"

**Solution:**
1. Check website for open periods
2. Filter by relevant topics
3. Mobilize members to comment
4. Track engagement via comment counts

**Impact:** More effective advocacy

## 🚢 Implementation Phases

### Phase 1: MVP (Week 1-2)
- ✅ Database schema
- ✅ Regulations.gov scraper
- ✅ Basic Bluesky posting (new periods only)
- ✅ Filter to EPA + FDA only
- ✅ Manual AI summaries

### Phase 2: Automation (Week 3-4)
- ✅ Deadline reminders (7-day, 3-day, last day)
- ✅ Auto-categorization by keywords
- ✅ Add more agencies (FCC, FTC, DOL, HHS)
- ✅ Improve filtering logic

### Phase 3: Website (Week 5-6)
- ✅ Static site generator
- ✅ Browse/filter interface
- ✅ RSS feeds
- ✅ JSON API
- ✅ Deploy to GitHub Pages

### Phase 4: Intelligence (Week 7-8)
- ✅ AI-generated summaries (Claude API)
- ✅ Impact assessment
- ✅ News correlation
- ✅ Comment volume tracking

## 📈 Success Metrics

**After 1 month:**
- Bot has 500+ followers
- 10+ people mention using it to submit comments
- Journalists reference it
- Website gets 1000+ visits

**After 6 months:**
- Bot has 5,000+ followers
- Website is primary source for comment period tracking
- Cited in news articles
- Nonprofits use it for advocacy campaigns

## 🔮 Future Enhancements

**Phase 5+:**
1. **Email Digest** - Weekly summary by topic
2. **Comment Templates** - Help people write better comments
3. **Impact Tracking** - "Your comment was cited in final rule!"
4. **Mobile App** - Push notifications for deadlines
5. **Comment Analysis** - Visualize public sentiment
6. **Historical Archive** - Track regulatory trends over time
7. **State-Level** - Expand to state regulatory agencies

## 🛠️ Tech Stack

Same as court bot (proven):
- **Language:** Python 3.11+
- **Database:** SQLite (committed to git)
- **APIs:** Regulations.gov, Federal Register, atproto (Bluesky)
- **Scraping:** requests, beautifulsoup4
- **Website:** Static HTML/CSS/JS
- **Hosting:** GitHub Pages + GitHub Actions
- **Cost:** $0/month

## 🎓 Lessons from Court Bot

**What worked:**
- SQLite in git (persistence across Actions runs)
- Static site deployment to GitHub Pages
- Daily scraping + posting workflow
- Simple, focused MVP first
- Clear post formatting

**What to improve:**
- Better duplicate detection
- More sophisticated filtering
- AI summaries from day 1
- Mobile-responsive design

**What to keep:**
- Same GitHub Actions pattern
- Same database approach
- Same posting logic
- Same website generator pattern

## 🚀 Getting Started

See **QUICKSTART.md** for step-by-step implementation guide.

See **API_DOCUMENTATION.md** for detailed API reference.

See **LESSONS_FROM_COURT_BOT.md** for architectural patterns.

---

**Built with civic duty and Claude. Let's make government accessible.** 🏛️📢
