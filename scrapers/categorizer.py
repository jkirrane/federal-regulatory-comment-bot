"""
Topic categorizer for Federal Regulatory Comment Bot

Categorizes comment periods by topic using keyword matching
"""

import json
from typing import List, Dict, Set


# Topic definitions with keywords
TOPICS = {
    'environment': {
        'name': 'Environment & Climate',
        'emoji': '🌍',
        'keywords': [
            'environment', 'environmental', 'climate', 'pollution', 'emissions',
            'air quality', 'water quality', 'clean air', 'clean water',
            'endangered species', 'wildlife', 'conservation', 'sustainability',
            'carbon', 'greenhouse gas', 'renewable', 'solar', 'wind energy',
            'toxic', 'hazardous waste', 'superfund', 'epa', 'pfas'
        ],
        'agencies': ['EPA', 'DOE', 'NOAA']
    },
    
    'healthcare': {
        'name': 'Healthcare',
        'emoji': '🏥',
        'keywords': [
            'health', 'healthcare', 'medical', 'medicine', 'drug', 'pharmaceutical',
            'hospital', 'patient', 'treatment', 'clinical', 'vaccine', 'disease',
            'medicaid', 'medicare', 'insurance', 'mental health', 'opioid',
            'fda', 'prescription', 'diagnostic', 'therapy', 'nursing'
        ],
        'agencies': ['FDA', 'HHS', 'CDC', 'CMS']
    },
    
    'privacy': {
        'name': 'Privacy & Security',
        'emoji': '🛡️',
        'keywords': [
            'privacy', 'data protection', 'personal information', 'cybersecurity',
            'data breach', 'encryption', 'surveillance', 'consumer data',
            'biometric', 'facial recognition', 'tracking', 'cookies',
            'identity theft', 'security breach', 'data security', 'gdpr'
        ],
        'agencies': ['FTC', 'FCC', 'DHS', 'CFPB']
    },
    
    'labor': {
        'name': 'Labor & Employment',
        'emoji': '💼',
        'keywords': [
            'labor', 'employment', 'worker', 'workplace', 'wage', 'salary',
            'minimum wage', 'overtime', 'union', 'collective bargaining',
            'discrimination', 'harassment', 'occupational safety', 'osha',
            'benefits', 'retirement', 'pension', 'unemployment', 'leave'
        ],
        'agencies': ['DOL', 'EEOC', 'NLRB', 'OSHA']
    },
    
    'transportation': {
        'name': 'Transportation',
        'emoji': '🚗',
        'keywords': [
            'transportation', 'highway', 'road', 'vehicle', 'car', 'truck',
            'aviation', 'aircraft', 'airline', 'airport', 'flight', 'pilot',
            'railroad', 'train', 'transit', 'shipping', 'maritime', 'port',
            'autonomous vehicle', 'self-driving', 'traffic safety', 'dot'
        ],
        'agencies': ['DOT', 'FAA', 'NHTSA', 'FRA', 'FMCSA']
    },
    
    'technology': {
        'name': 'Technology & Internet',
        'emoji': '💻',
        'keywords': [
            'internet', 'broadband', 'telecommunications', 'spectrum',
            'wireless', '5g', 'net neutrality', 'digital', 'online',
            'artificial intelligence', 'ai', 'algorithm', 'social media',
            'platform', 'content moderation', 'fcc', 'tech', 'software'
        ],
        'agencies': ['FCC', 'FTC', 'NTIA']
    },
    
    'finance': {
        'name': 'Finance & Banking',
        'emoji': '🏦',
        'keywords': [
            'financial', 'banking', 'bank', 'credit', 'loan', 'mortgage',
            'securities', 'investment', 'investor', 'stock', 'trading',
            'crypto', 'cryptocurrency', 'consumer protection', 'cfpb',
            'sec', 'money', 'payment', 'fintech', 'fraud'
        ],
        'agencies': ['SEC', 'CFPB', 'FDIC', 'FTC', 'CFTC']
    },
    
    'education': {
        'name': 'Education',
        'emoji': '🎓',
        'keywords': [
            'education', 'school', 'student', 'college', 'university',
            'higher education', 'k-12', 'elementary', 'secondary',
            'teacher', 'learning', 'curriculum', 'student loan',
            'title ix', 'special education', 'disability'
        ],
        'agencies': ['ED']
    },
    
    'housing': {
        'name': 'Housing',
        'emoji': '🏠',
        'keywords': [
            'housing', 'home', 'rent', 'rental', 'landlord', 'tenant',
            'affordable housing', 'homeless', 'mortgage', 'foreclosure',
            'fair housing', 'discrimination', 'hud', 'community development'
        ],
        'agencies': ['HUD', 'FHFA']
    },
    
    'agriculture': {
        'name': 'Agriculture & Food',
        'emoji': '🌾',
        'keywords': [
            'agriculture', 'farm', 'farmer', 'crop', 'livestock', 'cattle',
            'food safety', 'food labeling', 'nutrition', 'organic',
            'pesticide', 'fertilizer', 'rural', 'usda', 'agricultural'
        ],
        'agencies': ['USDA', 'FDA']
    }
}


def categorize(period: Dict) -> List[str]:
    """
    Categorize a comment period by topic
    
    Uses keyword matching on:
    - Title (lowercase)
    - Abstract (lowercase)
    - Agency ID
    
    Args:
        period: Comment period dict with 'title', 'abstract', 'agency_id'
    
    Returns:
        List of matching topic IDs (e.g., ['environment', 'healthcare'])
    """
    # Get text to search (handle None values)
    title = (period.get('title') or '').lower()
    abstract = (period.get('abstract') or '').lower()
    agency_id = period.get('agency_id', '')
    
    # Combine for searching
    search_text = f"{title} {abstract}"
    
    # Find matching topics
    matches = set()
    
    for topic_id, topic_data in TOPICS.items():
        # Check agency match
        if agency_id in topic_data['agencies']:
            matches.add(topic_id)
        
        # Check keyword match
        for keyword in topic_data['keywords']:
            if keyword.lower() in search_text:
                matches.add(topic_id)
                break  # One match per topic is enough
    
    return sorted(list(matches))


def categorize_with_metadata(period: Dict) -> Dict:
    """
    Categorize and return full metadata
    
    Args:
        period: Comment period dict
    
    Returns:
        Dict with topic IDs, names, and emojis
    """
    topic_ids = categorize(period)
    
    topics_metadata = []
    for topic_id in topic_ids:
        topic_data = TOPICS[topic_id]
        topics_metadata.append({
            'id': topic_id,
            'name': topic_data['name'],
            'emoji': topic_data['emoji']
        })
    
    return {
        'topic_ids': topic_ids,
        'topics': topics_metadata
    }


def get_hashtags(topic_ids: List[str]) -> List[str]:
    """
    Get hashtags for topics
    
    Args:
        topic_ids: List of topic IDs
    
    Returns:
        List of hashtags (e.g., ['#Environment', '#Climate'])
    """
    hashtags = set()
    
    for topic_id in topic_ids:
        if topic_id in TOPICS:
            name = TOPICS[topic_id]['name']
            # Split "Environment & Climate" into separate tags
            parts = name.replace('&', ',').split(',')
            for part in parts:
                # Clean and format
                tag = part.strip().replace(' ', '')
                if tag:
                    hashtags.add(f"#{tag}")
    
    return sorted(list(hashtags))


def get_all_topics() -> Dict[str, Dict]:
    """
    Get all available topics
    
    Returns:
        Dict of all topics with metadata
    """
    return TOPICS


def format_topics_json(topic_ids: List[str]) -> str:
    """
    Format topics as JSON string for database storage
    
    Args:
        topic_ids: List of topic IDs
    
    Returns:
        JSON string (e.g., '["environment", "healthcare"]')
    """
    return json.dumps(topic_ids)


def parse_topics_json(topics_json: str) -> List[str]:
    """
    Parse topics from JSON string
    
    Args:
        topics_json: JSON string from database
    
    Returns:
        List of topic IDs
    """
    try:
        return json.loads(topics_json)
    except (json.JSONDecodeError, TypeError):
        return []


def test_categorizer():
    """Test the categorizer with sample data"""
    
    print("Testing Topic Categorizer\n")
    print("="*60)
    
    test_cases = [
        {
            'title': 'EPA Proposes New Clean Water Standards',
            'abstract': 'New limits on PFAS chemicals in drinking water systems',
            'agency_id': 'EPA'
        },
        {
            'title': 'FDA Food Labeling Requirements',
            'abstract': 'Updates to nutrition facts labels on packaged foods',
            'agency_id': 'FDA'
        },
        {
            'title': 'FCC Net Neutrality Rules',
            'abstract': 'Proposed rules for internet service providers and broadband access',
            'agency_id': 'FCC'
        },
        {
            'title': 'DOL Overtime Wage Regulations',
            'abstract': 'New salary thresholds for overtime exemptions',
            'agency_id': 'DOL'
        },
        {
            'title': 'HUD Affordable Housing Program',
            'abstract': 'Fair housing rules and community development grants',
            'agency_id': 'HUD'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['title'][:50]}...")
        
        result = categorize_with_metadata(test_case)
        
        print(f"  Agency: {test_case['agency_id']}")
        print(f"  Topics: {result['topic_ids']}")
        
        for topic in result['topics']:
            print(f"    {topic['emoji']} {topic['name']}")
        
        hashtags = get_hashtags(result['topic_ids'])
        print(f"  Hashtags: {' '.join(hashtags)}")
    
    print("\n" + "="*60)
    print("✅ Categorizer test complete")


if __name__ == "__main__":
    test_categorizer()
