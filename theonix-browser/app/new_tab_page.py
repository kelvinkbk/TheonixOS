"""
Theonix Browser — New Tab Page Generator.
Generates the modern Theonix Startpage with search, top bookmarks, and system telemetry.
"""

from typing import List, Dict, Any


def get_new_tab_html(bookmarks: List[Dict[str, Any]] = None, recent_history: List[Dict[str, Any]] = None, search_engine: str = "Google") -> str:
    """Generates the modern, lightweight Theonix New Tab startpage."""
    if bookmarks is None:
        bookmarks = [
            {"title": "⚡ Theonix OS", "url": "https://theonixos.xyz"},
            {"title": "📖 Arch Wiki", "url": "https://wiki.archlinux.org"},
            {"title": "🟣 Flathub", "url": "https://flathub.org"},
            {"title": "🐙 GitHub", "url": "https://github.com/kelvinkbk/TheonixOS"},
            {"title": "🔍 Google", "url": "https://google.com"},
        ]

    search_actions = {
        "Google": ("https://www.google.com/search", "Search Google or enter URL..."),
        "DuckDuckGo": ("https://duckduckgo.com/", "Search DuckDuckGo or enter URL..."),
        "Startpage": ("https://www.startpage.com/sp/search", "Search Startpage or enter URL..."),
        "Bing": ("https://www.bing.com/search", "Search Bing or enter URL..."),
    }

    action_url, placeholder = search_actions.get(search_engine, ("https://www.google.com/search", "Search Google or enter URL..."))

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
            title = h.get("title") or h.get("url", "Site")
            url = h.get("url", "#")
            history_items += f"""
            <a href="{url}" class="history-chip" title="{url}">{title[:28]}</a>
            """

    return f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>New Tab &mdash; Theonix Browser</title>
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            }}
            body {{
                background-color: #07090E;
                background-image: 
                    radial-gradient(circle at 50% 20%, rgba(108, 99, 255, 0.08) 0%, transparent 60%),
                    radial-gradient(circle at 80% 80%, rgba(0, 255, 170, 0.04) 0%, transparent 50%);
                color: #F8FAFC;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 40px 20px;
            }}
            .container {{
                width: 100%;
                max-width: 760px;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }}
            .brand-logo {{
                font-size: 42px;
                margin-bottom: 8px;
                filter: drop-shadow(0 0 16px rgba(0, 255, 170, 0.4));
            }}
            h1 {{
                font-size: 28px;
                font-weight: 800;
                letter-spacing: -0.5px;
                margin-bottom: 6px;
                background: linear-gradient(135deg, #FFFFFF 30%, #94A3B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .subtext {{
                color: #64748B;
                font-size: 13px;
                margin-bottom: 28px;
            }}
            .search-box {{
                width: 100%;
                max-width: 620px;
                position: relative;
                display: flex;
                align-items: center;
                background: rgba(14, 18, 28, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 28px;
                padding: 6px 8px 6px 20px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
                transition: all 0.25s ease;
                margin-bottom: 36px;
            }}
            .search-box:focus-within {{
                border-color: #00FFAA;
                box-shadow: 0 8px 30px rgba(0, 255, 170, 0.18);
            }}
            .search-input {{
                flex: 1;
                background: transparent;
                border: none;
                outline: none;
                color: #FFFFFF;
                font-size: 15px;
                padding: 8px 0;
            }}
            .search-input::placeholder {{
                color: #64748B;
            }}
            .search-btn {{
                background: linear-gradient(135deg, #6C63FF, #534BE8);
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            .search-btn:hover {{
                filter: brightness(1.15);
                transform: scale(1.02);
            }}
            .section-title {{
                width: 100%;
                text-align: left;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                color: #64748B;
                margin-bottom: 14px;
                padding-left: 6px;
            }}
            .bookmarks-grid {{
                width: 100%;
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
                gap: 12px;
                margin-bottom: 32px;
            }}
            .bookmark-tile {{
                background: rgba(14, 18, 28, 0.65);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 16px 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-decoration: none;
                color: #E2E8F0;
                transition: all 0.2s ease;
            }}
            .bookmark-tile:hover {{
                background: rgba(255, 255, 255, 0.06);
                border-color: rgba(0, 255, 170, 0.4);
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
            }}
            .tile-icon {{
                width: 38px;
                height: 38px;
                border-radius: 10px;
                background: rgba(108, 99, 255, 0.15);
                color: #00FFAA;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .tile-title {{
                font-size: 12px;
                font-weight: 500;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                width: 100%;
            }}
            .history-section {{
                width: 100%;
            }}
            .history-grid {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}
            .history-chip {{
                background: rgba(14, 18, 28, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
                padding: 6px 14px;
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

            <form action="{action_url}" method="GET" class="search-box">
                <input type="text" name="q" class="search-input" placeholder="{placeholder}" autofocus autocomplete="off" />
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
