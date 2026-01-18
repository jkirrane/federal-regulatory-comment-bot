# Federal Regulatory Comment Bot

**Make civic participation accessible.**

A Bluesky bot and website that tracks federal regulatory comment periods, translates them into plain English, and helps people participate in democracy.

## 🎯 What This Does

- **Discovers** new federal comment periods daily
- **Posts** to Bluesky with plain-language summaries
- **Reminds** followers of upcoming deadlines
- **Categorizes** by topic (environment, healthcare, privacy, etc.)
- **Provides** direct links to submit comments

## 🌐 Website

**Browse open comment periods:** [Your GitHub Pages URL here]

- Filter by topic or agency
- Sort by deadline
- RSS feeds available
- JSON API for developers

## 🤖 Follow the Bot

[@fedcomments.bsky.social](https://bsky.app/profile/fedcomments.bsky.social) *(update with your handle)*

## 💡 Why This Matters

Federal agencies propose new regulations almost every day. The public has a right to comment, but discovering these opportunities is nearly impossible:

- No central "what's open now?" view
- Dense legal language in Federal Register
- Scattered across dozens of agency websites
- Only lobbyists and nonprofits monitor effectively

**This bot makes the regulatory process accessible to everyone.**

## 🏗️ How It Works

```
Regulations.gov API → Daily Scraper → SQLite Database
                                           ↓
                    ┌──────────────────────┴──────────────────────┐
                    ↓                                              ↓
              Bluesky Posts                                 Static Website
            (new periods + reminders)                    (GitHub Pages)
```

## 📊 Coverage

Currently tracking comment periods from:
- EPA (Environmental Protection Agency)
- FDA (Food and Drug Administration)
- FCC (Federal Communications Commission)
- FTC (Federal Trade Commission)
- DOL (Department of Labor)
- *[Add more as you expand]*

## 🛠️ Tech Stack

- **Language:** Python 3.11
- **Database:** SQLite (committed to git)
- **APIs:** Regulations.gov, Federal Register, Bluesky (atproto)
- **Hosting:** GitHub Actions + GitHub Pages
- **Cost:** $0/month

## 📁 Project Structure

```
regulatory-comment-bot/
├── database/
│   ├── schema.sql              # Database schema
│   ├── db.py                   # Database utilities
│   └── comment_periods.db      # SQLite database (committed)
├── scrapers/
│   ├── base.py                 # Base scraper class
│   ├── regulations_gov.py      # Main scraper
│   ├── federal_register.py     # Enrichment scraper
│   └── categorizer.py          # Topic categorization
├── bot/
│   ├── bluesky_poster.py       # Bluesky API wrapper
│   └── post_periods.py         # Posting logic
├── web/
│   ├── build.py                # Static site generator
│   ├── templates/              # HTML templates
│   └── static/                 # CSS, JS, images
├── docs/                       # Generated website (GitHub Pages)
├── .github/
│   └── workflows/
│       └── daily.yml           # Automated scraping & posting
├── AGENTS.md                   # Guide for AI-assisted development
├── API_DOCUMENTATION.md        # API reference
├── IMPLEMENTATION_GUIDE.md     # Step-by-step build guide
├── REGULATORY_COMMENT_BOT_SPEC.md
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Bluesky account for the bot
- Regulations.gov API key ([get one here](https://open.gsa.gov/api/regulationsgov/))

### Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/regulatory-comment-bot.git
   cd regulatory-comment-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Initialize database**
   ```bash
   python -m database.db
   ```

5. **Test scraper**
   ```bash
   python -m scrapers.regulations_gov --dry-run
   ```

6. **Run locally**
   ```bash
   # Scrape new periods
   python -m scrapers.regulations_gov
   
   # Post to Bluesky (dry-run first)
   python -m bot.post_periods --dry-run
   
   # Build website
   python -m web.build
   ```

### Deploy

1. **Set up GitHub secrets** (in repo Settings → Secrets)
   - `BLUESKY_HANDLE`
   - `BLUESKY_APP_PASSWORD`
   - `REGULATIONS_API_KEY`

2. **Enable GitHub Pages**
   - Settings → Pages
   - Source: Deploy from branch `main`, folder `/docs`

3. **Run workflow**
   - Actions tab → "Daily Scrape and Post"
   - Click "Run workflow"

The bot will now run automatically every day at 9 AM ET!

## 📖 Documentation

- **[AGENTS.md](AGENTS.md)** - Guide for AI-assisted development
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Step-by-step build guide
- **[REGULATORY_COMMENT_BOT_SPEC.md](REGULATORY_COMMENT_BOT_SPEC.md)** - Full specification

## 🤝 Contributing

This is a civic tech project! Contributions welcome:

- **Add agencies** - Expand coverage to more federal agencies
- **Improve categorization** - Better topic detection
- **Better summaries** - Help translate legalese
- **State regulations** - Expand beyond federal
- **Bug fixes** - Always appreciated

See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for development workflow.

## 📊 Stats

*[Update these as your bot grows]*

- **Comment periods tracked:** 0
- **Bluesky followers:** 0
- **Comments facilitated:** 0
- **Days running:** 0

## 🎯 Roadmap

- [x] Phase 1: Database & scraper
- [x] Phase 2: Bluesky bot
- [x] Phase 3: Website
- [ ] Phase 4: AI summaries
- [ ] Phase 5: Email digest
- [ ] Phase 6: Mobile app
- [ ] Phase 7: State regulations

## 📜 License

MIT License - feel free to fork and adapt!

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://anthropic.com)
- Inspired by [@courtlistener](https://bsky.app/profile/courtlistener.bsky.social)
- Data from [Regulations.gov](https://www.regulations.gov/) and [Federal Register](https://www.federalregister.gov/)

## 📧 Contact

Questions? Suggestions? Reach out:
- Bluesky: [@fedcomments.bsky.social](https://bsky.app/profile/fedcomments.bsky.social)
- GitHub Issues: [Report a bug](https://github.com/yourusername/regulatory-comment-bot/issues)

---

**Built with civic duty.** 🛖✨

*Help make government accessible to everyone.*
