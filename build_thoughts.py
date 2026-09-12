import html
import json
import re
import bleach
import markdown
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse

POSTS_FILE = Path("posts.json")
THOUGHTS_DIR = Path("thoughts")

PLATFORM_ICONS = {
    "linkedin": "/images/InBug-Black.png",
    "twitter": "https://unpkg.com/simple-icons/icons/x.svg",
    "facebook": "https://unpkg.com/simple-icons/icons/facebook.svg",
    "instagram": "https://unpkg.com/simple-icons/icons/instagram.svg",
    "youtube": "https://unpkg.com/simple-icons/icons/youtube.svg",
    "tiktok": "https://unpkg.com/simple-icons/icons/tiktok.svg",
    "threads": "https://unpkg.com/simple-icons/icons/threads.svg",
    "medium": "https://unpkg.com/simple-icons/icons/medium.svg",
    "github": "https://unpkg.com/simple-icons/icons/github.svg",
    "bluesky": "https://unpkg.com/simple-icons/icons/bluesky.svg",
    "mastodon": "https://unpkg.com/simple-icons/icons/mastodon.svg",
    "other": "https://unpkg.com/simple-icons/icons/link.svg",
}

PLATFORM_ALT_TEXT = {
    "linkedin": "LinkedIn icon",
    "twitter": "X / Twitter icon",
    "facebook": "Facebook icon",
    "instagram": "Instagram icon",
    "youtube": "YouTube icon",
    "tiktok": "TikTok icon",
    "threads": "Threads icon",
    "medium": "Medium icon",
    "github": "GitHub icon",
    "bluesky": "Bluesky icon",
    "mastodon": "Mastodon icon",
    "other": "Blog post image",
}

def slugify(title):
    return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', title.lower())).strip('-')

def platform_for_url(url):
    hostname = urlparse(url).netloc.lower().removeprefix("www.")
    if "linkedin.com" in hostname: return "linkedin"
    if hostname in {"twitter.com", "x.com"}: return "twitter"
    if "bsky.app" in hostname: return "bluesky"
    if "mastodon" in hostname or hostname.endswith(".social") or hostname.endswith(".io"): return "mastodon"
    for platform in ("facebook", "instagram", "youtube", "tiktok", "threads", "medium", "github"):
        if platform in hostname: return platform
    return "other"

def load_posts():
    if not POSTS_FILE.exists(): return []
    with POSTS_FILE.open(encoding="utf-8") as posts_file:
        posts = json.load(posts_file)
    return sorted(posts, key=lambda post: post.get("date", ""), reverse=True)

def render_markdown(text):
    rendered = markdown.markdown(text, extensions=["extra", "nl2br", "sane_lists"], output_format="html")
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union({
        "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
        "blockquote", "pre", "code", "ul", "ol", "li", "strong", "em", "img"
    })
    allowed_attributes = {
        "a": ["href", "title", "target", "rel"], 
        "code": ["class"],
        "img": ["src", "alt", "title", "class", "loading"]
    }
    cleaned = bleach.clean(rendered, tags=allowed_tags, attributes=allowed_attributes, protocols=["http", "https", "mailto"], strip=True)
    return re.sub(r'<a\b(?![^>]*\btarget=)', '<a target="_blank" rel="noopener noreferrer"', cleaned)

def render_share_bar(url):
    escaped = html.escape(url, quote=True)
    return f"""
    <div class="mt-8 pt-4 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-4">
        <a href="{escaped}" target="_blank" rel="noopener noreferrer"
           class="text-sm font-medium text-brand-accent hover:text-brand-dark transition-colors">
           Read Syndicated Post &rarr;
        </a>
        <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400">Share:</span>
            <a href="https://www.linkedin.com/sharing/share-offsite/?url={escaped}" target="_blank" class="hover:text-brand-accent transition"><img src="/images/InBug-Black.png" class="h-5 w-5" alt="LinkedIn icon"></a>
            <a href="https://twitter.com/intent/tweet?url={escaped}" target="_blank" class="hover:text-brand-accent transition"><img src="https://unpkg.com/simple-icons/icons/x.svg" class="h-5 w-5" alt="X icon"></a>
        </div>
    </div>
    """

def render_post(post, is_standalone=False):
    title = html.escape(post.get("title", "Untitled"))
    slug = slugify(title)
    body = render_markdown(post.get("body", ""))
    url = html.escape(post["url"], quote=True)
    canonical_url = f"https://davidgsmith.net/thoughts/{slug}.html"
    date_iso = post["date"]
    date = datetime.fromisoformat(date_iso.replace("Z", "+00:00")).strftime("%B %d, %Y")
    
    platform = post.get("platform") or platform_for_url(post["url"])
    icon = PLATFORM_ICONS.get(platform, PLATFORM_ICONS["other"])
    icon_alt = PLATFORM_ALT_TEXT.get(platform, PLATFORM_ALT_TEXT["other"])
    label = platform.title() if platform != "twitter" else "X / Twitter"
    
    tags = post.get("tags", [])
    tags_attr = ",".join(tags).lower()
    
    tags_html = "".join([f'<span class="inline-block bg-gray-100 text-gray-500 text-xs px-2 py-1 rounded-full mr-2 mb-2">{html.escape(t)}</span>' for t in tags])

    # If on index page, link title to individual page. If on standalone, just text.
    title_html = f'<h2 itemprop="headline" class="text-xl font-serif font-medium text-brand-dark mb-3">{title}</h2>'
    if not is_standalone:
        title_html = f'<a href="/thoughts/{slug}.html"><h2 itemprop="headline" class="text-xl font-serif font-medium text-brand-dark group-hover:text-brand-accent transition-colors mb-3">{title}</h2></a>'

    return f"""
        <article data-tags="{html.escape(tags_attr)}" itemscope itemtype="https://schema.org/BlogPosting"
                 class="relative group bg-white p-8 border border-gray-200 rounded shadow-sm hover:shadow-lg transition-all post-card">
            <div class="flex items-center gap-2 text-sm text-gray-400 mb-4">
                <img src="{icon}" alt="{icon_alt}" class="h-4 w-4" loading="lazy">
                <span itemprop="datePublished">{date} &bull; Originally on {html.escape(label)}</span>
            </div>
            {title_html}
            <div class="mb-4">{tags_html}</div>
            <div itemprop="articleBody" class="markdown-content text-gray-600 leading-relaxed text-sm">{body}</div>
            {render_share_bar(canonical_url)}
        </article>
    """

def get_base_html(title, content, json_ld="", canonical="", custom_js=""):
    canonical_tag = f'<link rel="canonical" href="{canonical}">' if canonical else ''
    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="alternate" type="application/rss+xml" href="https://davidgsmith.net/rss.xml" title="Thoughts & Insights — David G. Smith" />
{canonical_tag}
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {{ theme: {{ extend: {{ fontFamily: {{ sans: ['Inter', 'sans-serif'], serif: ['Lora', 'serif'] }}, colors: {{ brand: {{ dark: '#111827', muted: '#374151', accent: '#b45309', light: '#f9fafb' }} }} }} }} }}
</script>
<style>
    body {{ background: linear-gradient(to bottom, #faf9f7, #f3f2ee); }}
    .glass-nav {{ background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }}
    .markdown-content p {{ margin-bottom: 1rem; }}
    .markdown-content p:empty {{ display: none; }}
    .markdown-content h1, .markdown-content h2, .markdown-content h3 {{ color: #111827; font-family: Lora, serif; font-weight: 500; margin: 1.25rem 0 0.5rem; }}
    .markdown-content a {{ color: #92400e; text-decoration: underline; }}
</style>
{json_ld}
</head>
<body class="font-sans text-brand-muted antialiased selection:bg-brand-accent selection:text-white">

<nav class="fixed w-full z-50 glass-nav border-b border-gray-200 transition-all duration-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-20">
            <div class="flex-shrink-0"><a href="/" class="text-xl font-serif font-semibold text-brand-dark tracking-tight">David G. Smith</a></div>
            <div class="hidden md:flex space-x-8 items-center">
                <a href="/thoughts.html" class="text-brand-accent transition-colors text-sm font-medium">Thoughts</a>
            </div>
        </div>
    </div>
</nav>

<header class="pt-32 pb-16 px-4 max-w-5xl mx-auto text-center border-b border-gray-100">
    <h1 class="text-4xl sm:text-5xl font-serif font-medium text-brand-dark mb-6">Thoughts & Insights</h1>
</header>

<main id="main-content" class="py-16 bg-brand-light min-h-screen">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {content}
    </div>
</main>
{custom_js}
</body>
</html>"""

def generate_rss(posts):
    rss_items = []
    for post in posts:
        slug = slugify(post.get("title", ""))
        # RSS requires RFC 822 dates
        pub_date = datetime.fromisoformat(post["date"].replace("Z", "+00:00")).strftime("%a, %d %b %Y %H:%M:%S +0000")
        rss_items.append(f"""
        <item>
            <title>{html.escape(post.get("title", ""))}</title>
            <link>https://davidgsmith.net/thoughts/{slug}.html</link>
            <guid>https://davidgsmith.net/thoughts/{slug}.html</guid>
            <pubDate>{pub_date}</pubDate>
            <description><![CDATA[{render_markdown(post.get("body", ""))}]]></description>
        </item>""")

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>Thoughts &amp; Insights — David G. Smith</title>
        <link>https://davidgsmith.net/thoughts.html</link>
        <description>Latest perspectives on technical architecture, enterprise data, and critical thinking.</description>
        <atom:link href="https://davidgsmith.net/rss.xml" rel="self" type="application/rss+xml" />
        {''.join(rss_items)}
    </channel>
    </rss>"""
    with open("rss.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed.strip())

def generate_html():
    posts = load_posts()
    THOUGHTS_DIR.mkdir(exist_ok=True)
    all_tags = set()
    
    # 1. Generate Individual Standalone Pages
    for post in posts:
        slug = slugify(post.get("title", "Untitled"))
        for t in post.get("tags", []):
            all_tags.add(t)
            
        single_html = render_post(post, is_standalone=True)
        canonical = f"https://davidgsmith.net/thoughts/{slug}.html"
        page_html = get_base_html(f"{post.get('title')} - David G. Smith", single_html, canonical=canonical)
        
        with open(THOUGHTS_DIR / f"{slug}.html", "w", encoding="utf-8") as f:
            f.write(page_html)

    # 2. Generate the Main index page with filtering (showing latest 15)
    index_posts = "\n".join(render_post(post, is_standalone=False) for post in posts[:15])
    
    tag_options = "".join([f'<option value="{html.escape(t).lower()}">{html.escape(t)}</option>' for t in sorted(all_tags)])
    
    filter_ui = f"""
    <div class="mb-8 flex justify-between items-center">
        <h3 class="text-lg font-serif font-medium text-brand-dark">Filter by topic</h3>
        <select id="tag-filter" onchange="filterPosts()" class="rounded border border-gray-300 text-sm px-3 py-2 bg-white outline-none focus:border-brand-accent">
            <option value="all">All Thoughts</option>
            {tag_options}
        </select>
    </div>
    <div class="grid grid-cols-1 gap-8" id="post-list">
        {index_posts}
    </div>
    """

    filter_js = """<script>
    function filterPosts() {
        const selected = document.getElementById('tag-filter').value;
        const posts = document.querySelectorAll('.post-card');
        posts.forEach(post => {
            const tags = post.getAttribute('data-tags') || '';
            if (selected === 'all' || tags.includes(selected)) {
                post.style.display = 'block';
            } else {
                post.style.display = 'none';
            }
        });
    }
    </script>"""

    main_html = get_base_html("Thoughts & Insights — David G. Smith", filter_ui, custom_js=filter_js)
    with open("thoughts.html", "w", encoding="utf-8") as f:
        f.write(main_html)

    # 3. Generate RSS XML Feed
    generate_rss(posts)

if __name__ == "__main__":
    generate_html()
    print("Successfully generated files.")