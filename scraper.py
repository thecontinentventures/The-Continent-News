import feedparser
import os
import datetime
import time
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
    """Generates a long-form rewrite using Gemini."""
    if not model:
        return f"Full report on {title} is being processed."
    
    try:
        prompt = (f"Act as a lead investigative journalist for The Continent News. "
                  f"Based on this headline: '{title}' and summary: '{summary}', "
                  f"write a detailed, standalone 6-sentence news report. "
                  f"Do not mention other news outlets. Write it as an exclusive, definitive account.")
        response = model.generate_content(prompt)
        return response.text.strip().replace('"', '&quot;').replace("'", "\\'")
    except:
        return f"Developments regarding {title} continue to emerge."

def get_image(entry):
    try:
        if 'media_content' in entry and len(entry.media_content) > 0:
            return entry.media_content[0].get('url')
        if 'links' in entry:
            for link in entry.links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
    except: pass
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"

def generate_sections():
    html = ""
    for category, urls in FEEDS.items():
        cat_id = category.replace(' ', '').replace('&', '')
        html += f"<section id='{cat_id}' class='news-section'><h2>{category}</h2><div class='grid'>"
        all_entries = []
        for url in urls:
            feed = feedparser.parse(url)
            if hasattr(feed, 'entries'):
                all_entries.extend(feed.entries[:6])

        for entry in all_entries:
            full_story = ai_rewrite(entry.title, getattr(entry, 'summary', ''))
            preview = full_story[:120] + "..."
            img_url = get_image(entry)
            
            html += f"""
            <div class='card'>
                <img src='{img_url}' alt='News Image' onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80'">
                <div class="card-content">
                    <h3>{entry.title}</h3>
                    <p>{preview}</p>
                    <div class="meta">
                        <button class="read-more-btn" onclick="openStory('{entry.title.replace("'", "\\'")}', '{full_story}', '{img_url}')">Continue Reading</button>
                        <span class="exclusive-tag">Exclusive</span>
                    </div>
                </div>
            </div>"""
        html += "</div></section>"
    return html

def update_website():
    """Main function to update index.html."""
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Refreshing news database...")
    current_time = datetime.datetime.now().strftime("%Y")
    last_sync = datetime.datetime.now().strftime("%H:%M:%S")
    
    sections_content = generate_sections()

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
        body {{ font-family: 'Georgia', serif; margin: 0; background: var(--light); color: var(--dark); padding-bottom: 80px; overflow-x: hidden; }}
        header {{ background: var(--white); padding: 20px 10px; text-align: center; border-bottom: 1px solid #ddd; cursor: pointer; }}
        header h1 {{ margin: 0; font-size: 1.5rem; letter-spacing: 2px; text-transform: uppercase; font-weight: 900; }}
        
        .tradingview-widget-container {{ width: 100%; background: var(--dark); border-bottom: 3px solid var(--red); }}
        
        nav {{ background: var(--white); padding: 10px; text-align: center; border-bottom: 1px solid #ddd; position: sticky; top: 0; z-index: 100; }}
        nav a {{ color: #555; margin: 0 10px; text-decoration: none; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; cursor: pointer; padding: 5px 0; }}
        nav a.active {{ color: var(--red); border-bottom: 2px solid var(--red); }}

        .container {{ max-width: 1100px; margin: 20px auto; padding: 0 20px; min-height: 80vh; }}
        
        .news-section {{ display: none; }}
        .news-section.active {{ display: block; animation: fadeIn 0.4s ease-in-out; }}

        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 40px; }}
        .card {{ background: var(--white); border: 1px solid #eee; border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-5px); }}
        .card img {{ width: 100%; height: 200px; object-fit: cover; }}
        .card-content {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
        .card h3 {{ font-size: 1.1rem; margin: 0 0 10px 0; line-height: 1.3; font-weight: 900; }}
        .card p {{ font-size: 0.9rem; color: #444; line-height: 1.5; margin-bottom: 15px; }}

        .meta {{ display: flex; justify-content: space-between; align-items: center; margin-top: auto; }}
        .read-more-btn {{ background: none; border: none; color: var(--red); font-weight: bold; text-transform: uppercase; font-size: 0.7rem; cursor: pointer; padding: 0; }}
        .exclusive-tag {{ font-size: 0.6rem; color: #999; text-transform: uppercase; border: 1px solid #ccc; padding: 2px 5px; }}

        #storyModal {{ display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); overflow-y: auto; }}
        .modal-body {{ background: var(--white); margin: 3% auto; padding: 40px; width: 90%; max-width: 750px; border-radius: 4px; position: relative; }}
        .close {{ position: absolute; right: 20px; top: 10px; font-size: 35px; cursor: pointer; }}
        .modal-img {{ width: 100%; height: 400px; object-fit: cover; margin-bottom: 25px; }}
        .modal-body h2 {{ font-size: 2.2rem; margin-bottom: 20px; line-height: 1.1; font-weight: 900; }}
        .modal-body p {{ font-size: 1.2rem; line-height: 1.8; color: #111; }}

        #sync-info {{ position: fixed; bottom: 70px; right: 20px; background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 20px; font-size: 10px; font-family: monospace; z-index: 500; }}
        footer {{ position: fixed; bottom: 0; width: 100%; background: var(--dark); color: #999; text-align: center; padding: 15px 0; font-size: 0.65rem; z-index: 1000; }}
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
        {{ "description": "Safaricom", "proName": "NSE:SCOM" }},
        {{ "description": "Equity Group", "proName": "NSE:EQTY" }},
        {{ "description": "KCB Group", "proName": "NSE:KCB" }},
        {{ "description": "East African Breweries", "proName": "NSE:EABL" }}
      ],
      "showSymbolLogo": true,
      "colorTheme": "dark",
      "isTransparent": true,
      "displayMode": "adaptive",
      "locale": "en"
    }}
      </script>
    </div>

    <nav id="mainNav">
        <a onclick="switchPage('LatestNews')" id="btn-LatestNews" class="nav-link">Latest</a>
        <a onclick="switchPage('Africa')" id="btn-Africa" class="nav-link">Africa</a>
        <a onclick="switchPage('International')" id="btn-International" class="nav-link">World</a>
        <a onclick="switchPage('Sports')" id="btn-Sports" class="nav-link">Sports</a>
        <a onclick="switchPage('Fashion')" id="btn-Fashion" class="nav-link">Fashion</a>
        <a onclick="switchPage('TechBiz')" id="btn-TechBiz" class="nav-link">Business</a>
    </nav>

    <div id="sync-info">LAST UPDATED: {last_sync}</div>

    <div class="container" id="news-container">
        {sections_content}
    </div>

    <div id="storyModal">
        <div class="modal-body">
            <span class="close" onclick="closeStory()">&times;</span>
            <img id="modalImg" class="modal-img" src="">
            <h2 id="modalTitle"></h2>
            <p id="modalText"></p>
        </div>
    </div>

    <footer>&copy; {current_time} The Continent News • AI JOURNALISM • NO FLICKER SYNC ACTIVE</footer>

    <script>
        let currentActiveSection = 'LatestNews';

        function switchPage(sectionId) {{
            currentActiveSection = sectionId;
            const sections = document.querySelectorAll('.news-section');
            sections.forEach(sec => sec.classList.remove('active'));

            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.remove('active'));

            const target = document.getElementById(sectionId);
            if (target) {{
                target.classList.add('active');
            }}

            const activeBtn = document.getElementById('btn-' + sectionId);
            if (activeBtn) activeBtn.classList.add('active');
        }}

        function openStory(title, text, img) {{
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('modalText').innerText = text;
            document.getElementById('modalImg').src = img;
            document.getElementById('storyModal').style.display = "block";
            document.body.style.overflow = "hidden";
        }}

        function closeStory() {{
            document.getElementById('storyModal').style.display = "none";
            document.body.style.overflow = "auto";
        }}

        // SILENT REFRESH LOGIC (Every 5 minutes)
        setInterval(function() {{
            console.log("Checking for updates...");
            fetch('index.html')
                .then(response => response.text())
                .then(htmlText => {{
                    const parser = new DOMParser();
                    const newDoc = parser.parseFromString(htmlText, 'text/html');
                    
                    // Update only the news container
                    const newContainer = newDoc.getElementById('news-container').innerHTML;
                    document.getElementById('news-container').innerHTML = newContainer;
                    
                    // Update the timestamp
                    const newSync = newDoc.getElementById('sync-info').innerText;
                    document.getElementById('sync-info').innerText = newSync;

                    // Re-apply visibility for the current section
                    switchPage(currentActiveSection);
                    console.log("News updated silently.");
                }})
                .catch(err => console.log("Refresh failed: ", err));
        }}, 300000); 

        window.onclick = function(event) {{
            if (event.target == document.getElementById('storyModal')) {{ closeStory(); }}
        }}

        window.onload = () => switchPage('LatestNews');
    </script>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Success: index.html generated.")

# CONTINUOUS EXECUTION LOOP
if __name__ == "__main__":
    while True:
        try:
            update_website()
        except Exception as e:
            print(f"Loop error: {e}")
        
        print("Waiting 5 minutes for next crawl...")
        time.sleep(300)
