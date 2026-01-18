"""
Static site generator for Federal Regulatory Comment Bot

Generates:
- HTML pages (docs/index.html)
- RSS feed (docs/feed.xml)
- JSON API (docs/data.json)
- Copies static assets
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from feedgen.feed import FeedGenerator

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_all_open_periods, get_stats
from scrapers.categorizer import categorize_with_metadata, get_all_topics


# Paths
WEB_DIR = Path(__file__).parent
DOCS_DIR = WEB_DIR.parent / 'docs'
TEMPLATES_DIR = WEB_DIR / 'templates'
STATIC_DIR = WEB_DIR / 'static'


def ensure_docs_dir():
    """Create docs directory if it doesn't exist"""
    DOCS_DIR.mkdir(exist_ok=True)
    print(f"Docs directory: {DOCS_DIR}")


def build_index_page(periods: List[Dict[str, Any]], stats: Dict[str, int]) -> str:
    """
    Generate index.html from template
    
    Args:
        periods: List of comment period dicts
        stats: Database statistics
    
    Returns:
        HTML string
    """
    # Enhance periods with categorization
    enhanced_periods = []
    for period in periods:
        enhanced = period.copy()
        
        # Add categorization
        cat_data = categorize_with_metadata(period)
        enhanced['topics_data'] = cat_data['topics']
        enhanced['topic_ids'] = cat_data['topic_ids']
        
        # Format dates
        try:
            end_date = datetime.fromisoformat(period['comment_end_date'].replace('Z', '+00:00'))
            enhanced['formatted_end_date'] = end_date.strftime('%B %d, %Y')
            
            # Days until deadline
            days_until = (end_date - datetime.now()).days
            if days_until < 0:
                enhanced['urgency'] = 'closed'
                enhanced['days_label'] = 'Closed'
            elif days_until == 0:
                enhanced['urgency'] = 'urgent'
                enhanced['days_label'] = 'Today!'
            elif days_until <= 3:
                enhanced['urgency'] = 'urgent'
                enhanced['days_label'] = f'{days_until} days'
            elif days_until <= 7:
                enhanced['urgency'] = 'soon'
                enhanced['days_label'] = f'{days_until} days'
            else:
                enhanced['urgency'] = 'normal'
                enhanced['days_label'] = f'{days_until} days'
        except:
            enhanced['formatted_end_date'] = period['comment_end_date']
            enhanced['urgency'] = 'normal'
            enhanced['days_label'] = ''
        
        enhanced_periods.append(enhanced)
    
    # Sort by deadline (soonest first)
    enhanced_periods.sort(key=lambda x: x.get('comment_end_date', ''))
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Federal Regulatory Comment Periods - Open for Public Comment</title>
    <meta name="description" content="Track federal regulatory comment periods. Browse {stats['open_periods']} open comment periods from EPA, FDA, FCC, and more. Make your voice heard in democracy.">
    <link rel="stylesheet" href="styles.css">
    <link rel="alternate" type="application/rss+xml" title="All Comment Periods" href="feed.xml">
</head>
<body>
    <header>
        <div class="container">
            <h1>🏛️ Federal Regulatory Comment Periods</h1>
            <p class="tagline">Make your voice heard in democracy</p>
        </div>
    </header>
    
    <main class="container">
        <section class="stats">
            <div class="stat">
                <span class="stat-number">{stats['open_periods']}</span>
                <span class="stat-label">Open Periods</span>
            </div>
            <div class="stat">
                <span class="stat-number">{len(set(p['agency_id'] for p in periods))}</span>
                <span class="stat-label">Agencies</span>
            </div>
            <div class="stat">
                <span class="stat-number">{len([p for p in enhanced_periods if p['urgency'] in ['urgent', 'soon']])}</span>
                <span class="stat-label">Closing Soon</span>
            </div>
        </section>
        
        <section class="filters">
            <h2>Filter by Topic</h2>
            <div class="filter-buttons" id="topicFilters">
                <button class="filter-btn active" data-topic="all">All</button>
"""
    
    # Add topic filter buttons
    topics = get_all_topics()
    for topic_id, topic_data in sorted(topics.items(), key=lambda x: x[1]['name']):
        html += f'                <button class="filter-btn" data-topic="{topic_id}">{topic_data["emoji"]} {topic_data["name"]}</button>\n'
    
    html += """            </div>
        </section>
        
        <section class="periods" id="periodsContainer">
"""
    
    # Add period cards
    for period in enhanced_periods:
        urgency_class = period['urgency']
        topics_json = json.dumps(period['topic_ids'])
        
        # Build topics HTML
        topics_html = ''
        for topic in period.get('topics_data', []):
            topics_html += f'<span class="topic-tag">{topic["emoji"]} {topic["name"]}</span> '
        
        # Truncate abstract
        abstract = period.get('abstract') or 'No description available'
        if len(abstract) > 250:
            abstract = abstract[:247] + '...'
        
        html += f"""            <div class="period-card {urgency_class}" data-topics='{topics_json}'>
                <div class="period-header">
                    <h3>{period['title']}</h3>
                    <span class="agency-badge">{period['agency_id']}</span>
                </div>
                
                <div class="period-meta">
                    <span class="deadline">📅 Closes: {period['formatted_end_date']}</span>
                    <span class="urgency-badge urgency-{urgency_class}">{period['days_label']}</span>
                </div>
                
                <p class="period-abstract">{abstract}</p>
                
                <div class="period-topics">
                    {topics_html}
                </div>
                
                <div class="period-actions">
                    <a href="{period['regulations_url']}" target="_blank" rel="noopener" class="btn btn-primary">
                        💬 Submit Comment
                    </a>
                    <a href="{period.get('details_url', period['regulations_url'])}" target="_blank" rel="noopener" class="btn btn-secondary">
                        📄 View Details
                    </a>
                </div>
            </div>
            
"""
    
    html += """        </section>
    </main>
    
    <footer>
        <div class="container">
            <p>Updated: """ + datetime.now().strftime('%B %d, %Y at %I:%M %p ET') + """</p>
            <p>
                <a href="feed.xml">RSS Feed</a> | 
                <a href="data.json">JSON API</a> | 
                <a href="https://github.com/your-username/federal-regulatory-comment-bot">GitHub</a>
            </p>
            <p class="about">
                This site tracks federal regulatory comment periods to make civic participation accessible.
                Data from <a href="https://www.regulations.gov">Regulations.gov</a>.
            </p>
        </div>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
"""
    
    return html


def build_rss_feed(periods: List[Dict[str, Any]]) -> None:
    """
    Generate RSS feed
    
    Args:
        periods: List of comment period dicts
    """
    fg = FeedGenerator()
    fg.title('Federal Regulatory Comment Periods')
    fg.description('Open comment periods for federal regulations')
    fg.link(href='https://your-username.github.io/federal-regulatory-comment-bot/')
    fg.language('en')
    
    # Add items (most recent first)
    sorted_periods = sorted(periods, key=lambda x: x.get('posted_date', ''), reverse=True)
    
    for period in sorted_periods[:50]:  # Limit to 50 most recent
        fe = fg.add_entry()
        fe.id(period['document_id'])
        fe.title(f"{period['agency_id']}: {period['title']}")
        fe.link(href=period['regulations_url'])
        
        # Description
        abstract = period.get('abstract', 'No description available')
        end_date = period.get('comment_end_date', '')
        
        description = f"""
        <p><strong>Comment Deadline:</strong> {end_date}</p>
        <p>{abstract}</p>
        <p><a href="{period['regulations_url']}">Submit Comment →</a></p>
        """
        fe.description(description)
        
        # Published date
        try:
            posted_date = datetime.fromisoformat(period['posted_date'])
            fe.published(posted_date)
        except:
            pass
    
    # Write to file
    rss_path = DOCS_DIR / 'feed.xml'
    fg.rss_file(str(rss_path))
    print(f"RSS feed generated: {rss_path}")


def build_json_api(periods: List[Dict[str, Any]], stats: Dict[str, int]) -> None:
    """
    Generate JSON API
    
    Args:
        periods: List of comment period dicts
        stats: Database statistics
    """
    # Enhance periods with categorization
    api_periods = []
    for period in periods:
        api_period = {
            'document_id': period['document_id'],
            'docket_id': period['docket_id'],
            'title': period['title'],
            'agency_id': period['agency_id'],
            'agency_name': period['agency_name'],
            'document_type': period.get('document_type'),
            'posted_date': period['posted_date'],
            'comment_end_date': period['comment_end_date'],
            'comment_start_date': period.get('comment_start_date'),
            'abstract': period.get('abstract'),
            'regulations_url': period['regulations_url'],
            'federal_register_url': period.get('federal_register_url'),
            'details_url': period.get('details_url'),
        }
        
        # Add categorization
        cat_data = categorize_with_metadata(period)
        api_period['topics'] = cat_data['topics']
        api_period['topic_ids'] = cat_data['topic_ids']
        
        api_periods.append(api_period)
    
    # Build API response
    api_data = {
        'meta': {
            'generated_at': datetime.now().isoformat(),
            'total_periods': len(api_periods),
            'stats': stats
        },
        'data': api_periods
    }
    
    # Write to file
    json_path = DOCS_DIR / 'data.json'
    with open(json_path, 'w') as f:
        json.dump(api_data, f, indent=2)
    
    print(f"JSON API generated: {json_path}")


def copy_static_files() -> None:
    """Copy static CSS/JS files to docs directory"""
    if STATIC_DIR.exists():
        for file in STATIC_DIR.glob('*'):
            if file.is_file():
                dest = DOCS_DIR / file.name
                shutil.copy2(file, dest)
                print(f"Copied: {file.name}")
    else:
        print(f"Warning: Static directory not found: {STATIC_DIR}")


def build_site():
    """Main build function"""
    print("="*60)
    print("Building Federal Regulatory Comment Bot Website")
    print("="*60)
    
    # Ensure docs directory exists
    ensure_docs_dir()
    
    # Get data
    print("\nFetching data from database...")
    periods = get_all_open_periods()
    stats = get_stats()
    
    print(f"  Found {len(periods)} open comment periods")
    print(f"  Total in database: {stats['total_periods']}")
    
    # Build index page
    print("\nGenerating index.html...")
    html = build_index_page(periods, stats)
    index_path = DOCS_DIR / 'index.html'
    with open(index_path, 'w') as f:
        f.write(html)
    print(f"  Created: {index_path}")
    
    # Build RSS feed
    print("\nGenerating RSS feed...")
    build_rss_feed(periods)
    
    # Build JSON API
    print("\nGenerating JSON API...")
    build_json_api(periods, stats)
    
    # Copy static files
    print("\nCopying static assets...")
    copy_static_files()
    
    print("\n" + "="*60)
    print("✅ Website built successfully!")
    print("="*60)
    print(f"\nOpen in browser: file://{index_path.absolute()}")


if __name__ == "__main__":
    build_site()
