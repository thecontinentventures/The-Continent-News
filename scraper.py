import feedparser
import os
import datetime
import time
import json
import re
import base64
from google import genai

# 1. SETUP GEMINI AI
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
    model_id = "gemini-1.5-flash"
else:
    client = None

# DATABASE FILE FOR PERSISTENCE
DB_FILE = "news_database.json"

# 2. CONFIGURATION: RSS FEEDS
FEEDS = {
    'Latest News': [
        'https://www.standardmedia.co.ke/rss/headlines.php',
        'https://nation.africa/service/rss/622/622/rss.xml',
        'https://kenyanews.go.ke/feed/',
        'https://www.kenyans.co.ke/feeds/news',
        'https://www.capitalfm.co.ke/news/feed/',
        'https://www.the-star.co.ke/rss/'
    ],
    'Africa': [
        'https://www.africanews.com/feed/',
        'https://allafrica.com/tools/headlines/rdf/africa/main.rdf',
        'https://africa.com/feed/',
        'https://newafricanmagazine.com/feed/',
        'https://mg.co.za/feed/',
        'https://www.premiumtimesng.com/feed'
    ],
    'International': [
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'https://www.aljazeera.com/xml/rss/all.xml',
        'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
        'https://www.france24.com/en/rss',
        'https://news.un.org/en/rss/all/rss.xml',
        'https://www.dw.com/en/top-stories/s-9097'
    ],
    'Sports': [
        'https://www.skysports.com/rss/12040',
        'https://www.espn.com/espn/rss/news',
        'https://www.goal.com/en/feeds/news',
        'https://bc.ctvnews.ca/rss/sports-1.822340',
        'https://feeds.feedburner.com/daily-sun-sports'
    ],
    'Fashion': [
        'https://www.vogue.com/feed/rss',
        'https://www.businessoffashion.com/feed',
        'https://wwd.com/fashion-news/feed/',
        'https://www.harpersbazaar.com/rss/fashion.xml',
        'https://hypebeast.com/fashion/feed',
        'https://www.elle.com/rss/fashion.xml'
    ],
    'Tech & Biz': [
        'https://www.businessdailyafrica.com/service/rss/539444/539444/rss.xml',
        'https://itnewsafrica.com/feed/',
        'https://techcabal.com/feed/',
        'https://african.business/feed/',
        'https://www.ft.com/?format=rss',
        'https://feeds.bloomberg.com/business/news.rss'
    ]
}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def ai_rewrite(title, summary, source_url):
    backlink_html = f'<br><br><a href="{source_url}" target="_blank" style="color:#c0392b; font-weight:bold; text-decoration:none; font-size:0.9rem;">[Read the original full report on the source site →]</a>'
    
    if not client:
        return f"Full report on {title} is being processed.{backlink_html}"
    
    try:
        prompt = (f"Act as a lead investigative journalist for The Continent News. "
                  f"Headline: '{title}' | Summary: '{summary}' "
                  f"Task: Write a detailed 4-paragraph news report. "
                  f"Paragraph 1 (The Hook): Core facts and immediate impact. "
                  f"Paragraph 2 (The Context): Historical background and contributing factors. "
                  f"Paragraph 3 (The Stakes): Socio-economic impact and stakeholder reactions. "
                  f"Paragraph 4 (The Outlook): Future projections and concluding analysis. "
                  f"Strict Rules: No mention of other news sources. Exclusive tone. Output paragraphs separated by double newlines.")
        
        response = client.models.generate_content(model=model_id, contents=prompt)
        paragraphs = response.text.strip().split('\n\n')
        
        formatted_paragraphs = []
        for p in paragraphs:
            if len(p.strip()) > 10:
                clean_p = p.strip().replace('"', '&quot;')
                formatted_paragraphs.append(f"{clean_p}")
        
        return '<br><br>'.join(formatted_paragraphs) + backlink_html

    except Exception:
        fallback = [
            f"Developments regarding {title} continue to emerge as our correspondents track the situation.",
            f"Historical data suggests this trend follows a pattern of regional shifts observed over the last decade.",
            f"Local stakeholders and community leaders are currently being consulted to gauge the full breadth of the impact.",
            f"As the situation evolves, our analysts expect a formal policy response within the coming business cycle."
        ]
        return '<br><br>'.join(fallback) + backlink_html

def get_image(entry):
    try:
        if 'media_content' in entry and len(entry.media_content) > 0:
            return entry.media_content[0].get('url')
        if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
            return entry.media_thumbnail[0].get('url')
        if 'enclosures' in entry and len(entry.enclosures) > 0:
            return entry.enclosures[0].get('url')
        if 'links' in entry:
            for link in entry.links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
        if 'summary' in entry:
            img_match = re.search(r'<img.+?src=["\'](.+?)["\']', entry.summary)
            if img_match:
                return img_match.group(1)
    except: pass
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"

def get_telegram_data():
    try:
        tg_feed = feedparser.parse("https://rss.rssforever.com/telegram/channel/sputnik_africa")
        if tg_feed.entries:
            latest = tg_feed.entries[0]
            clean_summary = re.sub('<[^<]+?>', '', latest.summary)
            clean_summary = clean_summary[:120].replace("'", "").replace('"', "") + "..."
            return {
                "title": latest.title.replace("'", "").replace('"', "")[:60] + "...",
                "summary": clean_summary
            }
    except: pass
    return {"title": "Live: Regional Updates", "summary": "New developments emerging. Stay tuned for live coverage."}

def generate_sections(all_posts):
    html = ""
    for category in FEEDS.keys():
        cat_id = category.replace(' ', '').replace('&', '')
        html += f"<section id='{cat_id}' class='news-section'><h2>{category}</h2><div class='grid'>"
        
        cat_posts = [p for p in all_posts if p['category'] == category]
        cat_posts.sort(key=lambda x: x['timestamp'], reverse=True)

        for entry in cat_posts:
            b64_content = base64.b64encode(entry['content'].encode('utf-8')).decode('utf-8')
            preview = re.sub('<[^<]+?>', '', entry['content'])[:140] + "..."
            img_url = entry['image']
            js_safe_title = entry['title'].replace("'", "\\'").replace('"', '&quot;')
            
            html += f"""
            <div class='card'>
                <div class="img-container">
                    <img src='{img_url}' alt='News' loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80'">
                </div>
                <div class="card-content">
                    <h3>{entry['title']}</h3>
                    <p>{preview}</p>
                    <div class="meta">
                        <button class="read-more-btn" onclick="openStory('{js_safe_title}', '{b64_content}', '{img_url}')">Full Report</button>
                        <span class="exclusive-tag">Exclusive</span>
                    </div>
                </div>
            </div>"""
        html += "</div></section>"
    return html

def update_website():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting Hourly Sync...")
    
    db_posts = load_db()
    existing_links = {p['link'] for p in db_posts}
    
    new_found = False
    for category, urls in FEEDS.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                # Processing top 3 from each feed to ensure freshness
                for entry in feed.entries[:3]:
                    link = getattr(entry, 'link', '#')
                    if link not in existing_links:
                        print(f"Processing New Story: {entry.title}")
                        report = ai_rewrite(entry.title, getattr(entry, 'summary', ''), link)
                        db_posts.append({
                            "title": entry.title,
                            "content": report,
                            "image": get_image(entry),
                            "link": link,
                            "category": category,
                            "timestamp": time.time()
                        })
                        existing_links.add(link)
                        new_found = True
            except: continue
    
    if new_found:
        save_db(db_posts)

    current_time = datetime.datetime.now().strftime("%Y")
    last_sync = datetime.datetime.now().strftime("%H:%M:%S")
    GA_ID = "G-ZH9DSKC65T"
    
    sections_content = generate_sections(db_posts)
    tg_news = get_telegram_data()
    tg_json = json.dumps(tg_news)

    full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_ID}');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Continent News | Global Intelligence</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {{ --red: #c0392b; --dark: #111; --light: #f4f4f4; --white: #ffffff; --tg-blue: #0088cc; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 0; background: var(--light); color: var(--dark); padding-bottom: 80px; overflow-x: hidden; }}
        header {{ background: var(--white); padding: 30px 10px; text-align: center; border-bottom: 4px solid var(--dark); cursor: pointer; }}
        header h1 {{ margin: 0; font-size: 2.5rem; letter-spacing: -1px; text-transform: uppercase; font-weight: 900; }}
        .tradingview-widget-container {{ width: 100%; background: var(--dark); border-bottom: 3px solid var(--red); height: 46px; }}
        nav {{ background: var(--white); padding: 12px; text-align: center; border-bottom: 1px solid #ddd; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        nav a {{ color: #444; margin: 0 15px; text-decoration: none; font-size: 0.8rem; text-transform: uppercase; font-weight: 800; cursor: pointer; padding: 5px 0; transition: 0.2s; }}
        nav a:hover, nav a.active {{ color: var(--red); border-bottom: 2px solid var(--red); }}
        .container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; min-height: 80vh; }}
        .news-section {{ display: none; }}
        .news-section.active {{ display: block; animation: fadeIn 0.5s ease; }}
        .news-section h2 {{ border-left: 5px solid var(--red); padding-left: 15px; text-transform: uppercase; font-size: 1.2rem; margin-bottom: 25px; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px; }}
        .card {{ background: var(--white); border: 1px solid #ddd; overflow: hidden; display: flex; flex-direction: column; transition: 0.3s; }}
        .card:hover {{ box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
        .img-container {{ width: 100%; height: 220px; background: #222; overflow: hidden; }}
        .card img {{ width: 100%; height: 100%; object-fit: cover; display: block; transition: 0.5s; }}
        .card:hover img {{ transform: scale(1.05); }}
        .card-content {{ padding: 20px; flex-grow: 1; }}
        .card h3 {{ font-size: 1.1rem; margin: 0 0 12px 0; line-height: 1.3; font-weight: 800; }}
        .card p {{ font-size: 0.9rem; color: #555; line-height: 1.6; }}
        .meta {{ display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid #eee; }}
        .read-more-btn {{ background: var(--dark); color: white; border: none; padding: 8px 15px; font-weight: bold; text-transform: uppercase; font-size: 0.7rem; cursor: pointer; }}
        .exclusive-tag {{ font-size: 0.6rem; color: var(--red); font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }}
        .x-sidebar-container {{ position: fixed; left: -320px; top: 50%; transform: translateY(-50%); width: 360px; height: 500px; background: #fff; display: flex; z-index: 4500; transition: 0.4s; box-shadow: 5px 0 25px rgba(0,0,0,0.3); border-radius: 0 12px 12px 0; overflow: hidden; }}
        .x-sidebar-container:hover {{ left: 0; }}
        .x-preview-window {{ width: 320px; height: 100%; background: #000; overflow-y: auto; }}
        .x-handle {{ width: 40px; height: 100%; background: #000; color: #fff; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; }}
        #tg-popup {{ position: fixed; bottom: 100px; right: 20px; width: 300px; background: white; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); z-index: 4000; display: none; flex-direction: column; overflow: hidden; border-left: 6px solid var(--tg-blue); }}
        #storyModal {{ display: none; position: fixed; z-index: 5000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); overflow-y: auto; }}
        .modal-body {{ background: var(--white); margin: 2% auto; padding: 0; width: 95%; max-width: 800px; position: relative; }}
        .close {{ position: absolute; right: 20px; top: 15px; font-size: 40px; color: white; cursor: pointer; z-index: 10; }}
        .modal-img-container {{ width: 100%; height: 450px; background: #000; }}
        .modal-img {{ width: 100%; height: 100%; object-fit: cover; }}
        .modal-inner-padding {{ padding: 40px; }}
        .story-content {{ font-family: 'Georgia', serif; font-size: 1.25rem; line-height: 1.8; color: #222; }}
        #sync-info {{ position: fixed; bottom: 85px; right: 20px; background: var(--red); color: white; padding: 4px 12px; border-radius: 2px; font-size: 10px; font-weight: bold; z-index: 500; }}
        footer {{ position: fixed; bottom: 0; width: 100%; background: var(--dark); color: #777; text-align: center; padding: 20px 0; font-size: 0.7rem; z-index: 1000; }}
    </style>
</head>
<body>
    <header onclick="switchPage('LatestNews')"><h1>The Continent News</h1></header>

    <div class="x-sidebar-container">
        <div class="x-preview-window">
            <a class="twitter-timeline" data-width="320" data-height="500" data-theme="dark" href="https://twitter.com/sputnik_africa">Latest from @sputnik_africa</a> 
            <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        </div>
        <div class="x-handle"><i class="fab fa-x-twitter"></i><span>UPDATES</span></div>
    </div>

    <nav id="mainNav">
        <a onclick="switchPage('LatestNews')" id="btn-LatestNews" class="nav-link">Latest</a>
        <a onclick="switchPage('Africa')" id="btn-Africa" class="nav-link">Africa</a>
        <a onclick="switchPage('International')" id="btn-International" class="nav-link">World</a>
        <a onclick="switchPage('Sports')" id="btn-Sports" class="nav-link">Sports</a>
        <a onclick="switchPage('Fashion')" id="btn-Fashion" class="nav-link">Fashion</a>
        <a onclick="switchPage('TechBiz')" id="btn-TechBiz" class="nav-link">Tech & Business</a>
    </nav>

    <div id="sync-info">LIVE UPDATE: {last_sync}</div>
    <div class="container" id="news-container">{sections_content}</div>

    <div id="tg-popup">
        <div class="tg-head"><span><i class="fab fa-telegram"></i> @SPUTNIK_AFRICA FLASH</span></div>
        <div class="tg-body"><h4 id="tg-title"></h4><p id="tg-desc"></p></div>
        <a href="https://t.me/sputnik_africa" target="_blank" class="tg-btn">READ ON TELEGRAM</a>
    </div>

    <div id="storyModal">
        <span class="close" onclick="closeStory()">&times;</span>
        <div class="modal-body">
            <div class="modal-img-container"><img id="modalImg" class="modal-img" src=""></div>
            <div class="modal-inner-padding"><h2 id="modalTitle"></h2><div id="modalText" class="story-content"></div></div>
        </div>
    </div>

    <footer>&copy; {current_time} THE CONTINENT NEWS • GLOBAL INTELLIGENCE NETWORK</footer>

    <script>
        let currentActiveSection = 'LatestNews';
        const tgData = {tg_json};

        function switchPage(sectionId) {{
            const sections = document.querySelectorAll('.news-section');
            sections.forEach(sec => sec.classList.toggle('active', sec.id === sectionId));
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.toggle('active', link.id === 'btn-' + sectionId));
        }}

        function openStory(title, b64Content, img) {{
            const htmlContent = decodeURIComponent(escape(window.atob(b64Content)));
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('modalText').innerHTML = htmlContent;
            document.getElementById('modalImg').src = img;
            document.getElementById('storyModal').style.display = "block";
            document.body.style.overflow = "hidden";
        }}

        function closeStory() {{
            document.getElementById('storyModal').style.display = "none";
            document.body.style.overflow = "auto";
        }}

        window.onload = () => {{
            switchPage('LatestNews');
            if(tgData && tgData.title) {{
                document.getElementById('tg-title').innerText = tgData.title;
                document.getElementById('tg-desc').innerText = tgData.summary;
                setTimeout(() => {{ document.getElementById('tg-popup').style.display = 'flex'; }}, 4000);
            }}
        }};
    </script>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Build Complete.")

if __name__ == "__main__":
    while True:
        try:
            update_website()
            print(f"Next sync in 1 hour...")
            time.sleep(3600)  # Updated to 1 hour (3600 seconds)
        except Exception as e:
            print(f"Update failed: {e}")
            time.sleep(60)  # Wait 1 minute before retrying on crash
