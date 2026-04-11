import feedparser
import os
import datetime
import time
import google.generativeai as genai
import re

# 1. SETUP GEMINI AI
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# 2. CONFIGURATION: EXPANDED RSS FEEDS
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

def ai_rewrite(title, summary):
    """Generates a strictly structured 4-paragraph investigative report."""
    if not model:
        return f"Full report on {title} is being processed."
    
    try:
        prompt = (f"Act as a lead investigative journalist for The Continent News. "
                  f"Headline: '{title}' | Summary: '{summary}' "
                  f"Task: Write a detailed 4-paragraph news report. "
                  f"Paragraph 1 (The Hook): Core facts and immediate impact. "
                  f"Paragraph 2 (The Context): Historical background and contributing factors. "
                  f"Paragraph 3 (The Stakes): Socio-economic impact and stakeholder reactions. "
                  f"Paragraph 4 (The Outlook): Future projections and concluding analysis. "
                  f"Strict Rules: No mention of other news sources. Exclusive tone. Format with 4 clear paragraphs.")
        
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('"', '&quot;').replace("'", "\\'")
        return clean_text.replace('\n\n', '<br><br>')
    except:
        return (f"Developments regarding {title} continue to emerge.<br><br>"
                f"Historical patterns suggest regional shifts observed over the last decade.<br><br>"
                f"Local stakeholders are currently being consulted to gauge impact.<br><br>"
                f"Our analysts expect a formal response within the coming cycle.")

def get_image(entry):
    try:
        if 'media_content' in entry and len(entry.media_content) > 0:
            return entry.media_content[0].get('url')
        if 'enclosures' in entry and len(entry.enclosures) > 0:
            return entry.enclosures[0].get('url')
        if 'links' in entry:
            for link in entry.links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
    except: pass
    return "https://images.unsplash.com/photo-1495020689067-958852a7765e?auto=format&fit=crop&w=1200&q=80"

def get_telegram_data():
    try:
        tg_feed = feedparser.parse("https://rss.rssforever.com/telegram/channel/sputnik_africa")
        if tg_feed.entries:
            latest = tg_feed.entries[0]
            clean_summary = re.sub('<[^<]+?>', '', latest.summary)
            clean_summary = clean_summary[:130].replace("'", "").replace('"', "") + "..."
            return {
                "title": latest.title.replace("'", "").replace('"', "")[:55] + "...",
                "summary": clean_summary
            }
    except:
        return {"title": "Live: Sputnik Africa Updates", "summary": "New developments emerging from the region. Stay tuned for live coverage."}
    return None

def generate_sections():
    html = ""
    for category, urls in FEEDS.items():
        cat_id = category.replace(' ', '').replace('&', '')
        html += f"<section id='{cat_id}' class='news-section'><h2>{category}</h2><div class='grid'>"
        all_entries = []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                if hasattr(feed, 'entries'):
                    all_entries.extend(feed.entries[:3]) 
            except: continue

        for entry in all_entries:
            full_story = ai_rewrite(entry.title, getattr(entry, 'summary', ''))
            preview = full_story.replace('<br><br>', ' ')[:140] + "..."
            img_url = get_image(entry)
            js_safe_title = entry.title.replace("'", "\\'")
            
            html += f"""
            <div class='card'>
                <div class="img-container">
                    <img src='{img_url}' alt='News' loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80'">
                </div>
                <div class="card-content">
                    <h3>{entry.title}</h3>
                    <p>{preview}</p>
                    <div class="meta">
                        <button class="read-more-btn" onclick="openStory('{js_safe_title}', '{full_story}', '{img_url}')">Full Report</button>
                        <span class="exclusive-tag">Exclusive</span>
                    </div>
                </div>
            </div>"""
        html += "</div></section>"
    return html

def update_website():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Syncing Global Feeds...")
    current_year = datetime.datetime.now().strftime("%Y")
    last_sync = datetime.datetime.now().strftime("%H:%M:%S")
    
    sections_content = generate_sections()
    tg_news = get_telegram_data()
    # Fixed JSON formatting for JS injection
    tg_json = f'{{ "title": "{tg_news["title"]}", "summary": "{tg_news["summary"]}" }}' if tg_news else "null"

    full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
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
        
        nav {{ background: var(--white); padding: 12px; text-align: center; border-bottom: 1px solid #ddd; position: sticky; top: 0; z-index: 100; }}
        nav a {{ color: #444; margin: 0 15px; text-decoration: none; font-size: 0.8rem; text-transform: uppercase; font-weight: 800; cursor: pointer; padding: 5px 0; transition: 0.2s; }}
        nav a:hover, nav a.active {{ color: var(--red); border-bottom: 2px solid var(--red); }}

        .container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; min-height: 80vh; }}
        .news-section {{ display: none; }}
        .news-section.active {{ display: block; animation: fadeIn 0.5s ease; }}
        .news-section h2 {{ border-left: 5px solid var(--red); padding-left: 15px; text-transform: uppercase; font-size: 1.2rem; margin-bottom: 25px; }}

        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px; }}
        .card {{ background: var(--white); border: 1px solid #ddd; overflow: hidden; display: flex; flex-direction: column; }}
        .img-container {{ width: 100%; height: 220px; background: #222; }}
        .card img {{ width: 100%; height: 100%; object-fit: cover; transition: 0.5s; }}
        .card:hover img {{ transform: scale(1.05); }}
        .card-content {{ padding: 20px; flex-grow: 1; }}

        /* FLOATING TELEGRAM WINDOW STYLES */
        #tg-floating-window {{
            position: fixed; bottom: 100px; right: 20px; width: 320px; 
            background: white; border-radius: 12px; box-shadow: 0 15px 45px rgba(0,0,0,0.3);
            z-index: 9999; display: none; flex-direction: column; overflow: hidden;
            border: 1px solid #ddd; touch-action: none;
        }}
        .tg-header {{ 
            background: var(--tg-blue); color: white; padding: 12px 15px; 
            display: flex; justify-content: space-between; align-items: center; 
            cursor: move; user-select: none;
        }}
        .tg-header h5 {{ margin: 0; font-size: 0.75rem; letter-spacing: 1px; }}
        .tg-body {{ padding: 18px; }}
        .tg-body h4 {{ margin: 0 0 10px 0; font-size: 1rem; line-height: 1.3; color: var(--dark); }}
        .tg-body p {{ margin: 0; font-size: 0.85rem; color: #555; line-height: 1.5; }}
        .tg-footer {{ padding: 0 18px 18px; }}
        .tg-link {{ 
            display: block; background: var(--tg-blue); color: white; text-align: center; 
            padding: 10px; text-decoration: none; font-size: 0.8rem; font-weight: bold; border-radius: 6px;
        }}

        #storyModal {{ display: none; position: fixed; z-index: 10000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); overflow-y: auto; }}
        .modal-body {{ background: var(--white); margin: 2% auto; width: 95%; max-width: 800px; position: relative; }}
        .close {{ position: absolute; right: 20px; top: 15px; font-size: 40px; color: white; cursor: pointer; z-index: 11; }}
        .modal-img {{ width: 100%; height: 400px; object-fit: cover; }}
        .modal-inner {{ padding: 40px; }}

        #sync-info {{ position: fixed; bottom: 85px; right: 20px; background: var(--red); color: white; padding: 4px 12px; font-size: 10px; font-weight: bold; z-index: 500; }}
        footer {{ position: fixed; bottom: 0; width: 100%; background: var(--dark); color: #777; text-align: center; padding: 20px 0; font-size: 0.7rem; z-index: 1000; }}
    </style>
</head>
<body>
    <header onclick="switchPage('LatestNews')"><h1>The Continent News</h1></header>

    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {{
      "symbols": [
        {{ "proName": "FX_IDC:USDKES", "title": "USD/KES" }},
        {{ "proName": "OANDA:XAUUSD", "title": "Gold" }},
        {{ "proName": "INDEX:DXY", "title": "US Dollar Index" }},
        {{ "proName": "BITSTAMP:BTCUSD", "title": "Bitcoin" }}
      ],
      "colorTheme": "dark", "isTransparent": true, "displayMode": "adaptive", "locale": "en"
      }}
      </script>
    </div>

    <nav id="mainNav">
        <a onclick="switchPage('LatestNews')" id="btn-LatestNews" class="nav-link">Latest</a>
        <a onclick="switchPage('Africa')" id="btn-Africa" class="nav-link">Africa</a>
        <a onclick="switchPage('International')" id="btn-International" class="nav-link">World</a>
        <a onclick="switchPage('Sports')" id="btn-Sports" class="nav-link">Sports</a>
        <a onclick="switchPage('Fashion')" id="btn-Fashion" class="nav-link">Fashion</a>
        <a onclick="switchPage('TechBiz')" id="btn-TechBiz" class="nav-link">Tech & Biz</a>
    </nav>

    <div id="sync-info">LIVE UPDATE: {last_sync}</div>

    <div class="container" id="news-container">
        {sections_content}
    </div>

    <div id="tg-floating-window">
        <div class="tg-header" id="tg-drag-handle">
            <h5><i class="fab fa-telegram"></i> SPUTNIK AFRICA FLASH</h5>
            <span onclick="document.getElementById('tg-floating-window').style.display='none'" style="cursor:pointer">&times;</span>
        </div>
        <div class="tg-body">
            <h4 id="tg-title"></h4>
            <p id="tg-desc"></p>
        </div>
        <div class="tg-footer">
            <a href="https://t.me/sputnik_africa" target="_blank" class="tg-link">OPEN IN TELEGRAM</a>
        </div>
    </div>

    <div id="storyModal">
        <span class="close" onclick="closeStory()">&times;</span>
        <div class="modal-body">
            <img id="modalImg" class="modal-img" src="">
            <div class="modal-inner">
                <h2 id="modalTitle"></h2>
                <div id="modalText" class="story-content"></div>
            </div>
        </div>
    </div>

    <footer>&copy; {current_year} THE CONTINENT NEWS • GLOBAL INTELLIGENCE • POWERED BY AI</footer>

    <script>
        let currentActiveSection = 'LatestNews';
        const tgData = {tg_json};

        function switchPage(sectionId) {{
            currentActiveSection = sectionId;
            document.querySelectorAll('.news-section').forEach(sec => sec.classList.toggle('active', sec.id === sectionId));
            document.querySelectorAll('.nav-link').forEach(link => link.classList.toggle('active', link.id === 'btn-' + sectionId));
            window.scrollTo(0,0);
        }}

        function openStory(title, html, img) {{
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('modalText').innerHTML = html;
            document.getElementById('modalImg').src = img;
            document.getElementById('storyModal').style.display = "block";
            document.body.style.overflow = "hidden";
        }}

        function closeStory() {{
            document.getElementById('storyModal').style.display = "none";
            document.body.style.overflow = "auto";
        }}

        // DRAGGABLE LOGIC FOR TELEGRAM WINDOW
        const tgWindow = document.getElementById("tg-floating-window");
        const dragHandle = document.getElementById("tg-drag-handle");
        let isDragging = false, offsetX, offsetY;

        dragHandle.addEventListener("mousedown", (e) => {{
            isDragging = true;
            offsetX = e.clientX - tgWindow.offsetLeft;
            offsetY = e.clientY - tgWindow.offsetTop;
        }});

        document.addEventListener("mousemove", (e) => {{
            if (!isDragging) return;
            tgWindow.style.left = (e.clientX - offsetX) + "px";
            tgWindow.style.top = (e.clientY - offsetY) + "px";
            tgWindow.style.bottom = "auto";
            tgWindow.style.right = "auto";
        }});

        document.addEventListener("mouseup", () => isDragging = false);

        window.onload = () => {{
            switchPage('LatestNews');
            if(tgData) {{
                document.getElementById('tg-title').innerText = tgData.title;
                document.getElementById('tg-desc').innerText = tgData.summary;
                setTimeout(() => {{ tgWindow.style.display = 'flex'; }}, 3000);
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
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(300)
