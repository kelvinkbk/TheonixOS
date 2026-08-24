"""
Theonix Browser — New Tab Page Generator.
Generates the modern Theonix Startpage with search, top bookmarks, and system telemetry.
"""

from typing import List, Dict, Any


def get_new_tab_html(bookmarks: List[Dict[str, Any]] = None, recent_history: List[Dict[str, Any]] = None) -> str:
    """Generates the modern, lightweight Theonix New Tab startpage."""
    if bookmarks is None:
        bookmarks = [
            {"title": "⚡ Theonix OS", "url": "https://theonixos.xyz"},
            {"title": "📖 Arch Wiki", "url": "https://wiki.archlinux.org"},
            {"title": "🟣 Flathub", "url": "https://flathub.org"},
            {"title": "🐙 GitHub", "url": "https://github.com/kelvinkbk/TheonixOS"},
            {"title": "🔍 DuckDuckGo", "url": "https://duckduckgo.com"},
        ]

    bookmark_tiles = ""
    for b in bookmarks[:8]:
        title = b.get("title", "Link")
        url = b.get("url", "#")
        initial = title[0] if title else "⚡"
        bookmark_tiles += f"""
        <a href="{url}" class="bookmark-tile">
            <div class="tile-icon">{initial}</div>
            <div class="tile-title">{title}</div>
        </a>
        """

    history_items = ""
    if recent_history:
        for h in recent_history[:6]:
            h_title = h.get("title", h.get("url", "Page"))
            h_url = h.get("url", "#")
            history_items += f"""
            <a href="{h_url}" class="history-chip">
                <span style="color:#00FFAA;">•</span> {h_title[:32]}
            </a>
            """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>New Tab &mdash; Theonix Browser</title>
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                background-color: #07090E;
                color: #F8FAFC;
                font-family: 'Segoe UI', -apple-system, system-ui, sans-serif;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 40px 20px;
                background-image: 
                    radial-gradient(circle at 50% 20%, rgba(108, 99, 255, 0.12) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(0, 255, 170, 0.08) 0%, transparent 40%);
            }}
            .container {{
                width: 100%;
                max-width: 780px;
                text-align: center;
            }}
            .brand-logo {{
                width: 64px;
                height: 64px;
                margin: 0 auto 16px;
                border-radius: 18px;
                background: linear-gradient(135deg, #00FFAA, #6C63FF);
                display: grid;
                place-items: center;
                font-size: 30px;
                font-weight: 800;
                color: #04121A;
                box-shadow: 0 0 30px rgba(0, 255, 170, 0.3);
            }}
            h1 {{
                font-size: 30px;
                font-weight: 800;
                color: #FFFFFF;
                letter-spacing: -0.5px;
                margin-bottom: 6px;
            }}
            p.subtext {{
                color: #94A3B8;
                font-size: 14px;
                margin-bottom: 30px;
            }}
            .search-box {{
                display: flex;
                background: rgba(18, 24, 38, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 14px;
                padding: 8px 16px;
                margin-bottom: 36px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
                transition: border-color 0.2s;
            }}
            .search-box:focus-within {{
                border-color: #00FFAA;
                box-shadow: 0 0 20px rgba(0, 255, 170, 0.2);
            }}
            .search-input {{
                flex: 1;
                background: transparent;
                border: none;
                outline: none;
                color: #FFFFFF;
                font-size: 15px;
                padding: 8px 12px;
            }}
            .search-btn {{
                background: linear-gradient(135deg, #6C63FF, #00D4FF);
                color: #0B0E14;
                border: none;
                border-radius: 10px;
                padding: 8px 20px;
                font-weight: 700;
                font-size: 13px;
                cursor: pointer;
            }}
            .section-title {{
                color: #94A3B8;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 16px;
                text-align: left;
            }}
            .bookmarks-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
                gap: 14px;
                margin-bottom: 36px;
            }}
            .bookmark-tile {{
                background: rgba(18, 24, 38, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 16px 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-decoration: none;
                transition: all 0.2s ease;
            }}
            .bookmark-tile:hover {{
                background: rgba(26, 34, 52, 0.9);
                border-color: rgba(0, 255, 170, 0.4);
                transform: translateY(-2px);
            }}
            .tile-icon {{
                width: 40px;
                height: 40px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
                display: grid;
                place-items: center;
                font-size: 18px;
                color: #00FFAA;
                margin-bottom: 8px;
            }}
            .tile-title {{
                color: #F8FAFC;
                font-size: 12.5px;
                font-weight: 600;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 100%;
            }}
            .history-section {{
                background: rgba(14, 18, 28, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 12px;
                padding: 16px;
                text-align: left;
            }}
            .history-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}
            .history-chip {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 6px;
                padding: 6px 12px;
                color: #94A3B8;
                text-decoration: none;
                font-size: 12px;
            }}
            .history-chip:hover {{
                background: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
                border-color: #00FFAA;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="brand-logo">⚡</div>
            <h1>Theonix Browser</h1>
            <p class="subtext">AI-Augmented &middot; Privacy First &middot; High Performance</p>

            <form action="https://duckduckgo.com/" method="GET" class="search-box">
                <input type="text" name="q" class="search-input" placeholder="Search the web with DuckDuckGo or enter URL..." autofocus autocomplete="off" />
                <button type="submit" class="search-btn">Search</button>
            </form>

            <div class="section-title">Quick Access</div>
            <div class="bookmarks-grid">
                {bookmark_tiles}
            </div>

            {f'''
            <div class="history-section">
                <div class="section-title" style="margin-bottom:10px;">Recent Sites</div>
                <div class="history-grid">
                    {history_items}
                </div>
            </div>
            ''' if history_items else ''}
        </div>
    </body>
    </html>
    """
