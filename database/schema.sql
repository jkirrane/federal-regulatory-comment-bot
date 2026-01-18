-- Federal Regulatory Comment Bot Database Schema

-- Main table: comment_periods
-- Stores all federal regulatory comment periods
CREATE TABLE IF NOT EXISTS comment_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identifiers
    document_id TEXT NOT NULL UNIQUE,    -- FDA-2024-N-1234
    docket_id TEXT,                      -- FDA-2024-N-1234 (parent) - optional as some documents don't have one
    
    -- Basic info
    title TEXT NOT NULL,
    agency_id TEXT NOT NULL,             -- FDA, EPA, FCC, etc.
    agency_name TEXT NOT NULL,
    document_type TEXT,                  -- Proposed Rule, Notice, etc.
    
    -- Dates
    posted_date DATE NOT NULL,
    comment_start_date DATE,
    comment_end_date DATE NOT NULL,
    
    -- Content
    abstract TEXT,                       -- Brief summary
    summary TEXT,                        -- AI-generated plain English
    
    -- Links
    regulations_url TEXT NOT NULL,       -- Direct comment link
    federal_register_url TEXT,
    details_url TEXT,
    
    -- Categorization
    topics TEXT,                         -- JSON array: ["healthcare", "privacy"]
    keywords TEXT,                       -- Comma-separated
    
    -- Status tracking (avoid duplicate posts)
    posted_new BOOLEAN DEFAULT 0,
    posted_7day_reminder BOOLEAN DEFAULT 0,
    posted_3day_reminder BOOLEAN DEFAULT 0,
    posted_last_day BOOLEAN DEFAULT 0,
    
    -- Metadata
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (comment_end_date >= comment_start_date OR comment_start_date IS NULL)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_comment_end_date ON comment_periods(comment_end_date);
CREATE INDEX IF NOT EXISTS idx_posted_date ON comment_periods(posted_date);
CREATE INDEX IF NOT EXISTS idx_agency_id ON comment_periods(agency_id);
CREATE INDEX IF NOT EXISTS idx_posted_status ON comment_periods(posted_new, posted_7day_reminder, posted_3day_reminder, posted_last_day);
CREATE INDEX IF NOT EXISTS idx_document_id ON comment_periods(document_id);

-- Table: bot_posts
-- Track all posts made by the bot (for analytics)
CREATE TABLE IF NOT EXISTS bot_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_period_id INTEGER NOT NULL,
    post_type TEXT NOT NULL,             -- 'new', '7day', '3day', 'last_day'
    post_uri TEXT NOT NULL,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comment_period_id) REFERENCES comment_periods(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bot_posts_period ON bot_posts(comment_period_id);
CREATE INDEX IF NOT EXISTS idx_bot_posts_type ON bot_posts(post_type);

-- Table: agencies
-- Reference data for federal agencies
CREATE TABLE IF NOT EXISTS agencies (
    id TEXT PRIMARY KEY,                 -- EPA, FDA, etc.
    name TEXT NOT NULL,
    description TEXT,
    website TEXT,
    topics TEXT                          -- JSON array of common topics
);

-- Insert common agencies
INSERT OR IGNORE INTO agencies (id, name, website, topics) VALUES
('EPA', 'Environmental Protection Agency', 'https://www.epa.gov', '["environment", "climate"]'),
('FDA', 'Food and Drug Administration', 'https://www.fda.gov', '["healthcare", "food"]'),
('FCC', 'Federal Communications Commission', 'https://www.fcc.gov', '["technology", "internet"]'),
('FTC', 'Federal Trade Commission', 'https://www.ftc.gov', '["privacy", "security", "finance"]'),
('DOL', 'Department of Labor', 'https://www.dol.gov', '["labor", "employment"]'),
('HHS', 'Department of Health and Human Services', 'https://www.hhs.gov', '["healthcare"]'),
('DOT', 'Department of Transportation', 'https://www.transportation.gov', '["transportation"]'),
('ED', 'Department of Education', 'https://www.ed.gov', '["education"]'),
('HUD', 'Department of Housing and Urban Development', 'https://www.hud.gov', '["housing"]'),
('USDA', 'Department of Agriculture', 'https://www.usda.gov', '["agriculture", "food"]'),
('DOE', 'Department of Energy', 'https://www.energy.gov', '["environment", "climate"]'),
('DHS', 'Department of Homeland Security', 'https://www.dhs.gov', '["security"]'),
('SEC', 'Securities and Exchange Commission', 'https://www.sec.gov', '["finance", "banking"]'),
('CFPB', 'Consumer Financial Protection Bureau', 'https://www.consumerfinance.gov', '["finance", "banking"]');
