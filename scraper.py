import feedparser
import os
import datetime
import google.generativeai as genai

# 1. SETUP GEMINI AI
# Ensure you've added GEMINI_API_KEY to your GitHub Repository Secrets
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# 2. CONFIGURATION: RSS FEEDS
FEEDS = {
    'Latest News': [
        'https://www.standardmedia.co.ke/rss/headlines.php',
        'https://nation.africa/service/rss/622/622/rss.xml'
    ],
    'Africa': ['https://www.africanews.com/feed/'],
    'International': [
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'https://www.aljazeera.com/xml/rss/all.xml'
    ],
    'Sports': ['https://www.skysports.com/rss/12040'],
    'Fashion': ['https://www.vogue.com/feed/rss'],
    'Tech & Biz': [
        'https://www.businessdailyafrica.com/service/rss/539444/539444/rss.xml',
        'https://itweb.africa/feed'
    ]
}

def ai_rewrite(title, summary):
    """Uses Gemini to rewrite news into a fresh 2-sentence summary."""
    if not model:
        return summary[:200] + "..." if summary else "No details available."
    
    try:
        prompt = f"Rewrite this news headline and snippet into a professional, engaging 2-sentence summary for a news portal: {title}. {summary}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return summary[:200] + "..."

def get_ticker_html():
    """Pulls market-related headlines for the scrolling ticker."""
    try:
        feed = feedparser.parse('https://www.businessdailyafrica.com/service/rss/539444/539444/rss.xml')
        headlines = [f" • {entry.title.upper()}" for entry in feed.entries[:8]]
        return "".join(headlines)
    except:
        return " • THE CONTINENT NEWS: GLOBAL UPDATES DELIVERED DAILY"

def generate_sections():
    """Loops through categories, fetches news, and builds HTML cards."""
    html = ""
    for category, urls in FEEDS.items():
        html += f"<section id='{category.replace(' ', '')}'><h2>{category}</h2><div class='grid'>"
        
        # Collect entries from all URLs in this category
        all_entries = []
        for url in urls:
            feed = feedparser.parse(url)
            all_entries.extend(feed.entries[:3]) # Get top 3 from each source

        for entry in all_entries:
            raw_summary = getattr(entry, 'summary', '')
            rewritten = ai_rewrite(entry.title, raw_summary)
            
            html += f"""
            <div class='card'>
                <h3>{entry.title}</h3>
                <p>{rewritten}</p>
                <a href='{entry.link}' target='_blank'>Source: {category}</a>
            </div>"""
        
        html += "</div></section>"
    return html

# 3. CREATE THE FINAL HTML FILE
current_time = datetime.datetime.now().strftime("%B %d, %Y | %H:%M GMT")

full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Continent News</title>
    <style>
        :root {{ --red: #c0392b; --dark: #1a1a1a; --light: #f4f4f4; --white: #ffffff; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 0; background: var(--light); color: var(--dark); line-height: 1.6; }}
        
        header {{ background: var(--dark); color: var(--white); padding: 30px 10px; text-align: center; border-bottom: 5px solid var(--red); }}
        header h1 {{ margin: 0; font-size: 2.5rem; letter-spacing: -1px; }}
        header p {{ margin: 5px 0 0; opacity: 0.7; font-size: 0.9rem; }}

        /* Ticker Styling */
        .ticker-wrap {{ background: var(--red); color: white; padding: 12px 0; overflow: hidden; position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .ticker {{ display: inline-block; white-space: nowrap; animation: marquee 40s linear infinite; font-weight: bold; font-size: 0.9rem; }}
        @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        nav {{ background: #222; padding: 12px; text-align: center; }}
        nav a {{ color: white; margin: 0 12px; text-decoration: none; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; transition: 0.3s; }}
        nav a:hover {{ color: var(--red); }}

        .container {{ max-width: 1200px; margin: 30px auto; padding: 0 20px; }}
        
        h2 {{ border-left: 6px solid var(--red); padding-left: 15px; text-transform: uppercase; font-size: 1.5rem; margin-top: 40px; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; }}
        
        .card {{ background: var(--white); padding: 25px; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-5px); }}
        .card h3 {{ margin-top: 0; font-size: 1.25rem; line-height: 1.3; color: #000; }}
        .card p {{ color: #444; font-size: 0.95rem; margin: 15px 0; }}
        .card a {{ color: var(--red); text-decoration: none; font-weight: bold; font-size: 0.8rem; border: 1px solid var(--red); padding: 5px 10px; border-radius: 3px; }}
        .card a:hover {{ background: var(--red); color: white; }}

        .about-section {{ background: var(--dark); color: white; padding: 40px; border-radius: 4px; margin-top: 60px; }}
        
        footer {{ text-align: center; padding: 40px; font-size: 0.8rem; color: #666; border-top: 1px solid #ddd; margin-top: 50px; }}
    </style>
</head>
<body>
    <header>
        <h1>THE CONTINENT NEWS</h1>
        <p>Intelligent News Aggregation • {current_time}</p>
    </header>

    <div class="ticker-wrap">
        <div class="ticker">MARKET TICKER: {get_ticker_html()}</div>
    </div>

    <nav>
        <a href="#LatestNews">Latest</a>
        <a href="#Africa">Africa</a>
        <a href="#International">World</a>
        <a href="#Sports">Sports</a>
        <a href="#Fashion">Fashion</a>
        <a href="#Tech&Biz">Tech & Biz</a>
        <a href="#About">About</a>
    </nav>

    <div class="container">
        {generate_sections()}

        <section id="About" class="about-section">
            <h2>About The Continent News</h2>
            <p>Welcome to <strong>The Continent News</strong>, your automated portal for Kenyan and global perspectives. Our system scans trusted sources like <em>The Nation, BBC, and Business Daily</em>, using Google Gemini AI to summarize complex stories into digestible updates.</p>
            <p>Built for efficiency. Powered by AI.</p>
        </section>
    </div>

    <footer>
        &copy; 2026 The Continent News. All content is rewritten from original sources. <br>
        Published via GitHub Actions.
    </footer>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(full_html)

print("Website updated successfully!")