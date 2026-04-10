import feedparser
import os
import datetime
import google.generativeai as genai

# 1. SETUP GEMINI AI
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
    """Rewrites news to be completely original content."""
    if not model:
        return f"New reporting on {title}. Our team is following this development."
    
    try:
        prompt = f"Write an original 3-sentence news report based on this info. Do not copy the original text. Make it sound like exclusive reporting: {title}. {summary}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"New developments regarding {title} have been reported. Experts are monitoring the situation closely."

def get_image(entry):
    """Safely attempts to find an image in the RSS entry."""
    try:
        # Look in media:content with safety check for 'url' key
        if 'media_content' in entry and len(entry.media_content) > 0:
            return entry.media_content[0].get('url')
        
        # Look in enclosures/links
        if 'links' in entry:
            for link in entry.links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
    except:
        pass
    
    # Default fallback image
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"

def get_ticker_html():
    try:
        feed = feedparser.parse('https://www.businessdailyafrica.com/service/rss/539444/539444/rss.xml')
        headlines = [f" • {entry.title.upper()}" for entry in feed.entries[:10]]
        return "".join(headlines)
    except:
        return " • NSE MARKET WATCH: DATA REFRESHING..."

def generate_sections():
    html = ""
    for category, urls in FEEDS.items():
        html += f"<section id='{category.replace(' ', '')}'><h2>{category}</h2><div class='grid'>"
        all_entries = []
        for url in urls:
            feed = feedparser.parse(url)
            if hasattr(feed, 'entries'):
                all_entries.extend(feed.entries[:3])

        for entry in all_entries:
            raw_summary = getattr(entry, 'summary', '')
            rewritten = ai_rewrite(entry.title, raw_summary)
            img_url = get_image(entry) or "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"
            
            html += f"""
            <div class='card'>
                <img src='{img_url}' alt='News Image' onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80'">
                <h3>{entry.title}</h3>
                <p>{rewritten}</p>
                <a href='{entry.link}' target='_blank'>View Full Report</a>
            </div>"""
        html += "</div></section>"
    return html

# 3. CREATE THE FINAL HTML FILE
current_time = datetime.datetime.now().strftime("%Y")

full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Continent News</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {{ --red: #c0392b; --dark: #111; --light: #f4f4f4; --white: #ffffff; }}
        body {{ font-family: 'Georgia', serif; margin: 0; background: var(--light); color: var(--dark); padding-bottom: 80px; }}
        
        header {{ background: var(--white); color: var(--dark); padding: 20px 10px; text-align: center; border-bottom: 1px solid #ddd; }}
        header h1 {{ margin: 0; font-size: 1.5rem; letter-spacing: 2px; text-transform: uppercase; font-weight: 900; }}
        
        .social-icons {{ margin-top: 10px; }}
        .social-icons a {{ color: var(--dark); margin: 0 8px; font-size: 1.1rem; text-decoration: none; }}

        .ticker-wrap {{ background: var(--dark); color: white; padding: 10px 0; overflow: hidden; border-bottom: 3px solid var(--red); }}
        .ticker {{ display: inline-block; white-space: nowrap; animation: marquee 60s linear infinite; font-size: 0.8rem; font-family: monospace; }}
        @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}

        nav {{ background: var(--white); padding: 10px; text-align: center; border-bottom: 1px solid #ddd; position: sticky; top: 0; z-index: 100; }}
        nav a {{ color: #555; margin: 0 10px; text-decoration: none; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; }}

        .container {{ max-width: 1100px; margin: 20px auto; padding: 0 20px; }}
        h2 {{ border-bottom: 2px solid var(--dark); padding-bottom: 5px; text-transform: uppercase; font-size: 1.2rem; margin-top: 40px; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 40px; }}
        
        .card {{ background: var(--white); border: 1px solid #eee; padding-bottom: 15px; border-radius: 4px; overflow: hidden; }}
        .card img {{ width: 100%; height: 180px; object-fit: cover; background: #eee; border-bottom: 1px solid #eee; }}
        .card h3 {{ font-size: 1.1rem; line-height: 1.3; padding: 15px 15px 5px; margin: 0; }}
        .card p {{ font-size: 0.9rem; color: #444; line-height: 1.5; padding: 0 15px 15px; }}
        .card a {{ color: var(--red); text-decoration: none; font-size: 0.7rem; text-transform: uppercase; font-weight: bold; padding-left: 15px; }}

        #About {{ background: #eee; padding: 30px; margin-top: 50px; border-radius: 4px; border: 1px solid #ddd; }}
        #About h2 {{ margin-top: 0; }}

        footer {{ 
            position: fixed; 
            bottom: 0; 
            width: 100%; 
            background: var(--dark); 
            color: #999; 
            text-align: center; 
            padding: 15px 0; 
            font-size: 0.65rem; 
            text-transform: uppercase; 
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <header>
        <h1>The Continent News</h1>
        <div class="social-icons">
            <a href="#"><i class="fab fa-x-twitter"></i></a>
            <a href="#"><i class="fab fa-facebook-f"></i></a>
            <a href="#"><i class="fab fa-instagram"></i></a>
            <a href="#"><i class="fab fa-linkedin-in"></i></a>
            <a href="#"><i class="fab fa-youtube"></i></a>
        </div>
    </header>

    <div class="ticker-wrap">
        <div class="ticker">NSE MARKET WATCH: {get_ticker_html()}</div>
    </div>

    <nav>
        <a href="#LatestNews">Latest</a>
        <a href="#Africa">Africa</a>
        <a href="#International">World</a>
        <a href="#Sports">Sports</a>
        <a href="#Fashion">Fashion</a>
        <a href="#Tech&Biz">Business</a>
        <a href="#About">About</a>
    </nav>

    <div class="container">
        {generate_sections()}

        <section id="About">
            <h2>About & Disclaimer</h2>
            <p><strong>Disclaimer:</strong> We are not the rightful owners of the information created on this site. This is an AI powered tool. Alien environment!</p>
            <p>The Continent News uses automated technology to rewrite and aggregate global stories for a streamlined reading experience.</p>
        </section>
    </div>

    <footer>
        &copy; {current_time} The Continent News • Alien Environment • AI Powered Journalism
    </footer>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(full_html)
