import html
import json
import re
import bleach
import markdown
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import unicodedata

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
    "post": "https://unpkg.com/feather-icons/dist/icons/link.svg", # Native post fallback
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
    "post": "Blog post icon",
}

def slugify(title):
    return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', title.lower())).strip('-')

def platform_for_url(url):
    if not url: return "post"
    hostname = urlparse(url).netloc.lower().removeprefix("www.")
    
    if "davidgsmith.net" in hostname: return "post"
    if "linkedin.com" in hostname: return "linkedin"
    if hostname in {"twitter.com", "x.com"}: return "twitter"
    if "bsky.app" in hostname: return "bluesky"
    if "mastodon" in hostname or hostname.endswith(".social") or hostname.endswith(".io"): return "mastodon"
    
    for platform in ("facebook", "instagram", "youtube", "tiktok", "threads", "medium", "github"):
        if platform in hostname: return platform
    return "post"

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

def render_share_bar(share_url, original_url):
    share_escaped = html.escape(share_url, quote=True)
    
    # Only show "Read Original" if an external URL is provided
    read_original_html = "<div></div>" # Spacer for flex layout
    if original_url and "davidgsmith.net" not in original_url:
        orig_escaped = html.escape(original_url, quote=True)
        read_original_html = f"""
        <a href="{orig_escaped}" target="_blank" rel="noopener noreferrer"
           class="text-sm font-medium text-brand-accent hover:text-brand-dark transition-colors">
           Read Original &rarr;
        </a>
        """

    return f"""
    <div class="mt-8 pt-4 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-4">
        {read_original_html}
        <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400">Share:</span>
            <a href="https://www.linkedin.com/sharing/share-offsite/?url={share_escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on LinkedIn">
                <img src="/images/InBug-Black.png" class="h-5 w-5" alt="LinkedIn icon">
            </a>
            <a href="https://twitter.com/intent/tweet?url={share_escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on X">
                <img src="https://unpkg.com/simple-icons/icons/x.svg" class="h-5 w-5" alt="X / Twitter icon">
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={share_escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on Facebook">
                <img src="https://unpkg.com/simple-icons/icons/facebook.svg" class="h-5 w-5" alt="Facebook icon">
            </a>
            <a href="https://bsky.app/intent/share?url={share_escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on Bluesky">
                <img src="https://unpkg.com/simple-icons/icons/bluesky.svg" class="h-5 w-5" alt="Bluesky icon">
            </a>
            <a href="https://mastodon.social/share?text={share_escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on Mastodon">
                <img src="https://unpkg.com/simple-icons/icons/mastodon.svg" class="h-5 w-5" alt="Mastodon icon">
            </a>
        </div>
    </div>
    """

def get_json_ld(post=None):
    """Generates Structured JSON-LD Data for AI Crawlers and Search Engines"""
    if post:
        title = post.get("title", "Untitled")
        slug = slugify(title)
        canonical_url = f"https://davidgsmith.net/thoughts/{slug}.html"
        date_iso = post.get("date", datetime.now(timezone.utc).isoformat())
        tags = post.get("tags", [])
        description = create_text_excerpt(render_markdown(post.get("body", "")))
        
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "url": canonical_url,
            "datePublished": date_iso,
            "author": {
                "@type": "Person",
                "name": "David G. Smith",
                "url": "https://davidgsmith.net"
            },
            "description": description,
            "keywords": ", ".join(tags) if tags else ""
        }
    else:
        # Schema for the main index page
        schema = {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "Thoughts & Insights — David G. Smith",
            "url": "https://davidgsmith.net/thoughts.html",
            "description": "Latest perspectives on technical architecture, enterprise data, and critical thinking.",
            "author": {
                "@type": "Person",
                "name": "David G. Smith",
                "url": "https://davidgsmith.net"
            }
        }
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'

def render_post(post, is_standalone=False):
    title = html.escape(post.get("title", "Untitled"))
    slug = slugify(title)
    body = render_markdown(post.get("body", ""))
    url = post.get("url", "")
    canonical_url = f"https://davidgsmith.net/thoughts/{slug}.html"
    date_iso = post["date"]
    date = datetime.fromisoformat(date_iso.replace("Z", "+00:00")).strftime("%B %d, %Y")
    
    platform = post.get("platform") or platform_for_url(url)
    icon = PLATFORM_ICONS.get(platform, PLATFORM_ICONS["post"])
    icon_alt = PLATFORM_ALT_TEXT.get(platform, PLATFORM_ALT_TEXT["post"])
    label = platform.title() if platform != "twitter" else "X / Twitter"
    
    tags = post.get("tags", [])
    tags_attr = ",".join(tags).lower()
    
    if platform == "post":
        origin_text = "Published by David G. Smith"
    else:
        origin_text = f"Originally on {html.escape(label)}"
        
    tags_html = "".join([f'<button onclick="filterByTag(\'{html.escape(t).lower()}\')" class="inline-block bg-gray-100 text-gray-500 text-xs px-2 py-1 rounded-full mr-2 mb-2 hover:bg-brand-accent hover:text-white transition-colors cursor-pointer">{html.escape(t)}</button>' for t in tags])

    title_html = f'<h2 itemprop="headline" class="text-xl font-serif font-medium text-brand-dark mb-3">{title}</h2>'
    if not is_standalone:
        title_html = f'<a href="/thoughts/{slug}.html"><h2 itemprop="headline" class="text-xl font-serif font-medium text-brand-dark group-hover:text-brand-accent transition-colors mb-3">{title}</h2></a>'

    return f"""
        <article data-tags="{html.escape(tags_attr)}" itemscope itemtype="https://schema.org/BlogPosting"
                 class="relative group bg-white p-8 border border-gray-200 rounded shadow-sm hover:shadow-lg transition-all post-card">
            <div class="flex items-center gap-2 text-sm text-gray-400 mb-4">
                <img src="{icon}" alt="{icon_alt}" class="h-4 w-4" loading="lazy">
                <span itemprop="datePublished">{date} &bull; {origin_text}</span>
            </div>
            {title_html}
            <div class="mb-4">{tags_html}</div>
            <div itemprop="articleBody" class="markdown-content text-gray-600 leading-relaxed text-sm">{body}</div>
            {render_share_bar(share_url=canonical_url, original_url=url)}
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

<!-- Navigation -->
<nav class="fixed w-full z-50 glass-nav border-b border-gray-200 transition-all duration-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-20">
            <div class="flex-shrink-0">
                <a href="/" class="text-xl font-serif font-semibold text-brand-dark tracking-tight">
                    David G. Smith
                </a>
            </div>
            
            <div class="hidden md:flex space-x-8 items-center">
                <a href="/#about" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">About</a>
                <a href="/#work" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">Work</a>
                <a href="/thoughts.html" class="text-brand-accent transition-colors text-sm font-medium">Thoughts</a>
                <a href="/#books" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">Books</a>
                <a href="/#advisory" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">Advisory</a>
                <a href="/#contact" class="px-5 py-2 rounded border border-gray-300 text-brand-dark hover:border-brand-dark transition-all text-sm font-medium">Contact</a>
            </div>

            <div class="md:hidden flex items-center">
                <button id="mobile-menu-btn" class="text-brand-dark focus:outline-none">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <div id="mobile-menu" class="hidden md:hidden bg-white border-b border-gray-200 shadow-lg">
        <div class="px-4 pt-2 pb-4 space-y-1">
            <a href="/#about" class="mobile-link block py-2 text-base font-medium text-gray-600">About</a>
            <a href="/#work" class="mobile-link block py-2 text-base font-medium text-gray-600">Work</a>
            <a href="/thoughts.html" class="mobile-link block py-2 text-base font-medium text-brand-accent">Thoughts</a>
            <a href="/#books" class="mobile-link block py-2 text-base font-medium text-gray-600">Books</a>
            <a href="/#advisory" class="mobile-link block py-2 text-base font-medium text-gray-600">Advisory</a>
            <a href="/#contact" class="mobile-link block py-2 text-base font-medium text-gray-600">Contact</a>
        </div>
    </div>
</nav>

<header class="pt-32 pb-16 px-4 max-w-5xl mx-auto text-center border-b border-gray-100">
    <h1 class="text-4xl sm:text-5xl font-serif font-medium text-brand-dark mb-4">Thoughts & Insights</h1>
    
    <div class="flex justify-center mb-6">
        <a href="/rss.xml" target="_blank" class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-200 bg-white hover:bg-gray-50 text-sm font-medium text-brand-accent hover:text-brand-dark transition-all shadow-sm">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M4 11a9 9 0 0 1 9 9H9c0-2.76-2.24-5-5-5v-4zm0-7a16 16 0 0 1 16 16h-4a12 12 0 0 0-12-12V4zm2 13a2 2 0 1 1-2 2c0-1.11.89-2 2-2z"></path>
            </svg>
            Subscribe via RSS
        </a>
    </div>
</header>

<main id="main-content" class="py-16 bg-brand-light min-h-screen">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {content}
    </div>
</main>

<!-- Footer -->
<footer class="bg-brand-dark text-gray-400 py-12 border-t border-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center">
        <div class="mb-4 md:mb-0">
            <span class="text-lg font-serif font-semibold text-white tracking-tight">
                David G. Smith
            </span>
        </div>
        <div class="mt-4 md:mt-0 text-sm">
            &copy; <span id="year"></span> David G. Smith. All rights reserved.
        </div>
    </div>
</footer>

<script>
    document.getElementById('year').textContent = new Date().getFullYear();

    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    const mobileLinks = document.querySelectorAll('.mobile-link');

    if(btn && menu) {{
        btn.addEventListener('click', () => {{
            menu.classList.toggle('hidden');
        }});

        mobileLinks.forEach(link => {{
            link.addEventListener('click', () => {{
                menu.classList.add('hidden');
            }});
        }});
    }}
</script>
{custom_js}
</body>
</html>"""

def sanitize_feed_text(text):
    if not text: return ""
    normalized = unicodedata.normalize('NFKD', text)
    replacements = {
        '‑': '-', '→': '->', '—': '--', 
        '“': '"', '”': '"', '‘': "'", '’': "'"
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized.encode('ascii', 'xmlcharrefreplace').decode('ascii')

def create_text_excerpt(html_content, max_length=250):
    plain_text = bleach.clean(html_content, tags=[], strip=True)
    if len(plain_text) > max_length:
        return plain_text[:max_length].rsplit(' ', 1)[0] + '...'
    return plain_text

def generate_rss(posts):
    rss_items = []
    for post in posts:
        slug = slugify(post.get("title", ""))
        pub_date = datetime.fromisoformat(post["date"].replace("Z", "+00:00")).strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        html_body = render_markdown(post.get("body", ""))
        html_body = sanitize_feed_text(html_body)
        excerpt = html.escape(create_text_excerpt(html_body))
        safe_title = html.escape(sanitize_feed_text(post.get("title", "")))
        
        # Add tags as <category> items for the RSS feed
        categories = "\n            ".join([f"<category>{html.escape(tag)}</category>" for tag in post.get("tags", [])])

        rss_items.append(f"""
        <item>
            <title>{safe_title}</title>
            <link>https://davidgsmith.net/thoughts/{slug}.html</link>
            <guid>https://davidgsmith.net/thoughts/{slug}.html</guid>
            <pubDate>{pub_date}</pubDate>
            <description>{excerpt}</description>
            {categories}
            <content:encoded><![CDATA[{html_body}]]></content:encoded>
        </item>""")

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
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
        json_ld_script = get_json_ld(post) # Fetch dynamic post JSON-LD
        
        page_html = get_base_html(f"{post.get('title')} - David G. Smith", single_html, json_ld=json_ld_script, canonical=canonical)
        
        with open(THOUGHTS_DIR / f"{slug}.html", "w", encoding="utf-8") as f:
            f.write(page_html)

    # 2. Generate the Main index page with filtering (showing latest 15)
    index_posts = "\n".join(render_post(post, is_standalone=False) for post in posts[:15])
    json_ld_script_main = get_json_ld(None) # Fetch generic site JSON-LD
    
    tag_options = "".join([f'<option value="{html.escape(t).lower()}">{html.escape(t)}</option>' for t in sorted(all_tags)])
    
    filter_ui = f"""
    <div class="mb-8 flex justify-end items-center gap-3">
        <label for="tag-filter" class="text-lg font-serif font-medium text-brand-dark whitespace-nowrap">Filter by topic</label>
        <select id="tag-filter" onchange="filterPosts()" class="rounded border border-gray-300 text-sm px-3 py-2 bg-white outline-none focus:border-brand-accent cursor-pointer max-w-xs">
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
            const tagsAttr = post.getAttribute('data-tags') || '';
            const tags = tagsAttr.split(',').map(t => t.trim());
            
            if (selected === 'all' || tags.includes(selected)) {
                post.style.display = 'block';
            } else {
                post.style.display = 'none';
            }
        });
    }

    function filterByTag(tag) {
        const filterDropdown = document.getElementById('tag-filter');
        if (filterDropdown) {
            filterDropdown.value = tag;
            filterPosts();
            document.getElementById('tag-filter').scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            window.location.href = '/thoughts.html?tag=' + encodeURIComponent(tag);
        }
    }

    window.addEventListener('DOMContentLoaded', (event) => {
        const urlParams = new URLSearchParams(window.location.search);
        const tagParam = urlParams.get('tag');
        if (tagParam) {
            const filterDropdown = document.getElementById('tag-filter');
            if (filterDropdown) {
                filterDropdown.value = tagParam;
                filterPosts();
            }
        }
    });
    </script>"""

    main_html = get_base_html("Thoughts & Insights — David G. Smith", filter_ui, json_ld=json_ld_script_main, custom_js=filter_js)
    with open("thoughts.html", "w", encoding="utf-8") as f:
        f.write(main_html)

    # 3. Generate RSS XML Feed
    generate_rss(posts)

if __name__ == "__main__":
    generate_html()
    print("Successfully generated files.")