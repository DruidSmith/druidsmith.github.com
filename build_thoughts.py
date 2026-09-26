import html
import json
import re
import bleach
import markdown
import shutil
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import unicodedata
import urllib.request
import urllib.parse
import os

# Anchor paths to the script's directory
BASE_DIR = Path(__file__).resolve().parent
POSTS_FILE = BASE_DIR / "posts.json"
THOUGHTS_DIR = BASE_DIR / "thoughts"
DEFAULT_OG_IMAGE = "https://davidgsmith.net/images/og-default.jpg"

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
    "post": "https://unpkg.com/feather-icons/dist/icons/link.svg",
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

def parse_and_normalize_date(date_str):
    if not date_str:
        return datetime.now(timezone.utc)
    if not date_str.endswith("Z") and "+" not in date_str:
        date_str += "Z"
    return datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)

def load_posts():
    if not POSTS_FILE.exists(): return []
    with POSTS_FILE.open(encoding="utf-8") as posts_file:
        raw_posts = json.load(posts_file)
        
    seen_slugs = set()
    normalized_posts = []
    
    for post in raw_posts:
        # Standardize required & optional fields
        post.setdefault("type", "BlogPosting")
        if not post.get("url") or "davidgsmith.net" in post.get("url", ""):
            post["url"] = ""
            
        # Parse and anchor UTC dates
        dt = parse_and_normalize_date(post.get("date"))
        post["_dt"] = dt
        post["date"] = dt.isoformat()
        
        # Check slugs for collisions
        base_slug = slugify(post.get("title", "Untitled"))
        slug = base_slug
        counter = 1
        while slug in seen_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs.add(slug)
        post["_slug"] = slug
        
        normalized_posts.append(post)
        
    return sorted(normalized_posts, key=lambda p: p["_dt"], reverse=True)

def render_markdown(text):
    rendered = markdown.markdown(
        text, 
        extensions=["extra", "tables", "nl2br", "sane_lists"], 
        output_format="html"
    )
    
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union({
        "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
        "blockquote", "pre", "code", "ul", "ol", "li", "strong", "em", "img",
        "table", "thead", "tbody", "tfoot", "tr", "th", "td"
    })
    
    allowed_attributes = {
        "a": ["href", "title", "target", "rel"], 
        "code": ["class"],
        "img": ["src", "alt", "title", "class", "loading"],
        "th": ["align", "class"],
        "td": ["align", "class"]
    }
    
    cleaned = bleach.clean(
        rendered, 
        tags=allowed_tags, 
        attributes=allowed_attributes, 
        protocols=["http", "https", "mailto"], 
        strip=True
    )
    return re.sub(r'<a\b(?![^>]*\btarget=)', '<a target="_blank" rel="noopener noreferrer"', cleaned)

def calculate_reading_time(text):
    words = len(re.findall(r'\w+', text))
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"

def render_tag_badges(tags, size="normal"):
    if not tags: return ""
    size_classes = "text-xs px-2.5 py-1" if size == "normal" else "text-[11px] px-2 py-0.5"
    badges = []
    for t in tags:
        t_slug = slugify(t)
        badges.append(
            f'<a href="/thoughts-{t_slug}.html" '
            f'class="inline-block bg-sky-50 text-sky-950 font-semibold border border-sky-200/90 '
            f'{size_classes} rounded-md mr-1.5 mb-1.5 hover:bg-brand-accent hover:border-brand-accent '
            f'hover:text-white transition-all shadow-xs">{html.escape(t)}</a>'
        )
    return "".join(badges)

def render_breadcrumbs(post):
    title = html.escape(post.get("title", "Untitled"))
    return f"""
    <nav aria-label="Breadcrumb" class="mb-4 text-xs font-medium text-slate-500">
        <ol class="flex items-center flex-wrap gap-1.5">
            <li>
                <a href="/" class="hover:text-brand-accent text-slate-500 transition-colors">Home</a>
            </li>
            <li class="text-slate-400">/</li>
            <li>
                <a href="/thoughts.html" class="hover:text-brand-accent text-slate-500 transition-colors">Thoughts</a>
            </li>
            <li class="text-slate-400">/</li>
            <li class="text-slate-900 font-semibold truncate max-w-[240px] sm:max-w-md" aria-current="page">{title}</li>
        </ol>
    </nav>
    """

def render_share_bar(share_url, original_url):
    share_escaped = html.escape(share_url, quote=True)
    read_original_html = "<div></div>" 
    if original_url:
        orig_escaped = html.escape(original_url, quote=True)
        read_original_html = f"""
        <a href="{orig_escaped}" target="_blank" rel="noopener noreferrer"
           class="text-sm font-semibold text-brand-accent hover:text-amber-900 transition-colors inline-flex items-center gap-1">
           Read Original &rarr;
        </a>
        """

    return f"""
    <div class="mt-8 pt-4 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center gap-4">
        {read_original_html}
        <div class="flex items-center gap-3">
            <span class="text-xs font-medium uppercase tracking-wider text-slate-400">Share:</span>
            <a href="https://www.linkedin.com/sharing/share-offsite/?url={share_escaped}"
               target="_blank" class="hover:opacity-80 transition" aria-label="Share on LinkedIn">
                <img src="/images/InBug-Black.png" class="h-4 w-4" alt="LinkedIn icon">
            </a>
            <a href="https://twitter.com/intent/tweet?url={share_escaped}"
               target="_blank" class="hover:opacity-80 transition" aria-label="Share on X">
                <img src="https://unpkg.com/simple-icons/icons/x.svg" class="h-4 w-4" alt="X / Twitter icon">
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={share_escaped}"
               target="_blank" class="hover:opacity-80 transition" aria-label="Share on Facebook">
                <img src="https://unpkg.com/simple-icons/icons/facebook.svg" class="h-4 w-4" alt="Facebook icon">
            </a>
            <a href="https://bsky.app/intent/share?url={share_escaped}"
               target="_blank" class="hover:opacity-80 transition" aria-label="Share on Bluesky">
                <img src="https://unpkg.com/simple-icons/icons/bluesky.svg" class="h-4 w-4" alt="Bluesky icon">
            </a>
            <a href="https://mastodon.social/share?text={share_escaped}"
               target="_blank" class="hover:opacity-80 transition" aria-label="Share on Mastodon">
                <img src="https://unpkg.com/simple-icons/icons/mastodon.svg" class="h-4 w-4" alt="Mastodon icon">
            </a>
        </div>
    </div>
    """

def extract_post_image(post):
    if post.get("image"):
        img = post["image"]
        return img if img.startswith("http") else f"https://davidgsmith.net{img}"
    
    match = re.search(r'!\[.*?\]\((https?://[^\s\)]+|/[^\s\)]+)\)', post.get("body", ""))
    if match:
        img_url = match.group(1)
        return img_url if img_url.startswith("http") else f"https://davidgsmith.net{img_url}"
        
    return DEFAULT_OG_IMAGE

def create_text_excerpt(html_content, max_length=160):
    plain_text = bleach.clean(html_content, tags=[], strip=True)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    if len(plain_text) > max_length:
        return plain_text[:max_length].rsplit(' ', 1)[0] + '...'
    return plain_text

def get_related_posts(current_post, all_posts, limit=3):
    current_tags = set(current_post.get("tags", []))
    current_slug = current_post["_slug"]
    candidates = []
    
    for p in all_posts:
        if p["_slug"] == current_slug:
            continue
        p_tags = set(p.get("tags", []))
        shared = current_tags.intersection(p_tags)
        candidates.append({
            "post": p,
            "shared_count": len(shared),
            "date": p["_dt"]
        })
    
    candidates.sort(key=lambda x: (x["shared_count"], x["date"]), reverse=True)
    return [c["post"] for c in candidates[:limit]]

def render_related_posts_section(related_posts):
    if not related_posts: return ""
    cards = []
    for p in related_posts:
        slug = p["_slug"]
        title = html.escape(p.get("title", "Untitled"))
        date_str = p["_dt"].strftime("%b %d, %Y")
        body_html = render_markdown(p.get("body", ""))
        excerpt = html.escape(create_text_excerpt(body_html, max_length=120))
        reading_time = calculate_reading_time(p.get("body", ""))
        tags_html = render_tag_badges(p.get("tags", [])[:2], size="small")

        cards.append(f"""
        <div class="bg-white p-5 rounded-lg border border-slate-200/90 shadow-sm hover:shadow-md hover:border-amber-400 transition-all flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between text-xs font-medium text-slate-400 mb-2">
                    <span>{date_str}</span>
                    <span class="text-amber-900 bg-amber-50 px-2 py-0.5 rounded text-[11px] font-semibold">{reading_time}</span>
                </div>
                <a href="/thoughts/{slug}.html" class="block group mb-2">
                    <h3 class="text-base font-serif font-medium text-slate-900 group-hover:text-brand-accent transition-colors leading-snug line-clamp-2">
                        {title}
                    </h3>
                </a>
                <p class="text-xs text-slate-600 leading-relaxed mb-3 line-clamp-2">{excerpt}</p>
            </div>
            <div>
                <div class="flex flex-wrap">{tags_html}</div>
                <a href="/thoughts/{slug}.html" class="inline-flex items-center gap-1 text-xs font-semibold text-brand-accent hover:text-amber-900 transition-colors mt-2">
                    Read Thought &rarr;
                </a>
            </div>
        </div>
        """)

    return f"""
    <section class="mt-10 pt-8 border-t border-slate-200" aria-label="Related Thoughts">
        <div class="flex items-center justify-between mb-6">
            <div>
                <h2 class="text-xl sm:text-2xl font-serif font-medium text-slate-900">Related Thoughts</h2>
                <p class="text-xs text-slate-500 mt-0.5">Perspectives sharing related architectures, models, and domain context.</p>
            </div>
            <a href="/thoughts.html" class="text-xs font-semibold uppercase tracking-wider text-brand-accent hover:text-amber-900 transition-colors">
                All Thoughts &rarr;
            </a>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            {''.join(cards)}
        </div>
    </section>
    """

def get_json_ld(post=None):
    if post:
        title = post.get("title", "Untitled")
        slug = post["_slug"]
        canonical_url = f"https://davidgsmith.net/thoughts/{slug}.html"
        
        date_iso = post["_dt"].isoformat()
        modified_iso = post.get("last_modified", date_iso)
        
        tags = post.get("tags", [])
        body_text = post.get("body", "")
        description = create_text_excerpt(render_markdown(body_text), max_length=160)
        post_image = extract_post_image(post)
        word_count = len(re.findall(r'\w+', body_text))

        schema = [
            {
                "@context": "https://schema.org",
                "@type": post.get("type", "BlogPosting"),
                "@id": f"{canonical_url}#article",
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": canonical_url
                },
                "headline": title,
                "image": [post_image],
                "url": canonical_url,
                "datePublished": date_iso,
                "dateModified": modified_iso,
                "inLanguage": "en-US",
                "wordCount": word_count,
                "author": {
                    "@type": "Person",
                    "@id": "https://davidgsmith.net",
                    "name": "David G. Smith",
                    "url": "https://davidgsmith.net"
                },
                "publisher": {
                    "@type": "Person",
                    "@id": "https://davidgsmith.net",
                    "name": "David G. Smith",
                    "url": "https://davidgsmith.net"
                },
                "description": description,
                "keywords": ", ".join(tags) if tags else "",
                "articleSection": tags[0] if tags else "Technology"
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "@id": f"{canonical_url}#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": "https://davidgsmith.net"
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Thoughts",
                        "item": "https://davidgsmith.net/thoughts.html"
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": title,
                        "item": canonical_url
                    }
                ]
            }
        ]
    else:
        schema = {
            "@context": "https://schema.org",
            "@type": "Blog",
            "@id": "https://davidgsmith.net/thoughts.html#blog",
            "name": "Thoughts & Insights — David G. Smith",
            "url": "https://davidgsmith.net/thoughts.html",
            "description": "Latest perspectives on technical architecture, enterprise data, and critical thinking.",
            "author": {
                "@type": "Person",
                "@id": "https://davidgsmith.net",
                "name": "David G. Smith",
                "url": "https://davidgsmith.net"
            }
        }
    
    # Serialize safely to prevent breaking out of the script block
    serialized = json.dumps(schema, indent=2, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">\n{serialized}\n</script>'

def generate_nav_rail(posts, current_type=None, current_value=None):
    tag_counts = {}
    untagged_count = 0
    for post in posts:
        tags = post.get("tags", [])
        if not tags:
            untagged_count += 1
        for t in tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0].lower()))

    tags_html = ""
    for tag, count in sorted_tags:
        t_slug = slugify(tag)
        is_active = (current_type == "tag" and current_value == tag)
        if is_active:
            active_class = "border-brand-accent bg-brand-accent text-white font-semibold shadow-sm"
            badge_bg = "bg-amber-950/80 text-amber-200"
        else:
            active_class = "border-slate-700 bg-slate-800/90 text-slate-200 hover:border-brand-accent hover:text-white hover:bg-slate-700"
            badge_bg = "bg-slate-950 text-slate-400 group-hover:bg-slate-900"

        tags_html += f"""
        <a href="/thoughts-{t_slug}.html" class="inline-flex items-center justify-between px-2.5 py-1 rounded-md border text-xs transition-all {active_class}">
            <span>{html.escape(tag)}</span>
            <span class="ml-2 {badge_bg} px-1.5 py-0.5 rounded-full text-[10px] font-mono font-medium">{count}</span>
        </a>
        """

    if untagged_count > 0:
        is_active = (current_type == "tag" and current_value == "untagged")
        active_class = "border-brand-accent bg-brand-accent text-white font-semibold shadow-sm" if is_active else "border-slate-700 bg-slate-800/90 text-slate-200 hover:border-brand-accent hover:text-white hover:bg-slate-700"
        badge_bg = "bg-amber-950/80 text-amber-200" if is_active else "bg-slate-950 text-slate-400"
        tags_html += f"""
        <a href="/thoughts-untagged.html" class="inline-flex items-center justify-between px-2.5 py-1 rounded-md border text-xs transition-all {active_class}">
            <span>Untagged</span>
            <span class="ml-2 {badge_bg} px-1.5 py-0.5 rounded-full text-[10px] font-mono font-medium">{untagged_count}</span>
        </a>
        """

    year_months = {}
    for post in posts:
        year = post["_dt"].strftime("%Y")
        month_abbr = post["_dt"].strftime("%b").upper()
        if year not in year_months:
            year_months[year] = set()
        year_months[year].add(month_abbr)

    sorted_years = sorted(year_months.keys(), reverse=True)

    months_order = [
        ("JAN", "01"), ("FEB", "02"), ("MAR", "03"),
        ("APR", "04"), ("MAY", "05"), ("JUN", "06"),
        ("JUL", "07"), ("AUG", "08"), ("SEP", "09"),
        ("OCT", "10"), ("NOV", "11"), ("DEC", "12")
    ]

    months_tables_html = ""
    for year in sorted_years:
        present_months = year_months[year]
        grid_cells = ""
        for m_abbr, m_num in months_order:
            if m_abbr in present_months:
                is_active = (current_type == "month" and current_value == (year, m_abbr))
                if is_active:
                    active_style = "bg-brand-accent text-white shadow-sm ring-1 ring-amber-500 font-semibold"
                else:
                    active_style = "bg-slate-800 text-slate-200 hover:bg-brand-accent hover:text-white font-medium border border-slate-700"
                cell = f'<a href="/thoughts-{year}-{m_abbr.lower()}.html" class="block py-1.5 text-center text-xs rounded transition-all {active_style}">{m_abbr}</a>'
            else:
                cell = f'<span class="block py-1.5 text-center text-xs text-slate-500 bg-slate-950/60 border border-slate-800/80 rounded cursor-not-allowed select-none">{m_abbr}</span>'
            grid_cells += cell

        months_tables_html += f"""
        <div class="mb-4 last:mb-0">
            <div class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">{year}</div>
            <div class="grid grid-cols-4 gap-1.5">
                {grid_cells}
            </div>
        </div>
        """

    return f"""
    <aside aria-label="Sidebar Navigation" class="space-y-6">
        <div class="lg:hidden bg-slate-900 p-4 rounded-lg border border-slate-800 shadow-sm text-slate-100">
            <button id="nav-rail-toggle" class="w-full flex justify-between items-center text-slate-100 font-serif font-bold text-sm focus:outline-none">
                <span>Filter by Tag &amp; Archive</span>
                <svg id="nav-toggle-icon" class="w-5 h-5 transform transition-transform text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                </svg>
            </button>
        </div>

        <div id="nav-rail-content" class="space-y-6 hidden lg:block">
            <div class="bg-slate-900 p-6 rounded-lg border border-slate-800 shadow-lg text-slate-100">
                <div class="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                    <h3 class="text-sm sm:text-base font-bold uppercase tracking-wider text-slate-100 flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-brand-accent"></span>
                        Topics
                    </h3>
                    <span class="text-xs font-mono font-semibold text-amber-300 bg-amber-950/80 border border-amber-800/80 px-2 py-0.5 rounded-full">{len(sorted_tags)}</span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                    {tags_html}
                </div>
            </div>

            <div class="bg-slate-900 p-6 rounded-lg border border-slate-800 shadow-lg text-slate-100">
                <div class="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                    <h3 class="text-sm sm:text-base font-bold uppercase tracking-wider text-slate-100 flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-brand-accent"></span>
                        Archive
                    </h3>
                </div>
                {months_tables_html}
            </div>
        </div>
    </aside>
    """

def render_post(post, is_standalone=False, prev_post=None, next_post=None, related_posts=None):
    title = html.escape(post.get("title", "Untitled"))
    slug = post["_slug"]
    body = render_markdown(post.get("body", ""))
    url = post.get("url", "")
    canonical_url = f"https://davidgsmith.net/thoughts/{slug}.html"
    date = post["_dt"].strftime("%B %d, %Y")
    reading_time = calculate_reading_time(post.get("body", ""))
    
    platform = post.get("platform") or platform_for_url(url)
    icon = PLATFORM_ICONS.get(platform, PLATFORM_ICONS["post"])
    icon_alt = PLATFORM_ALT_TEXT.get(platform, PLATFORM_ALT_TEXT["post"])
    label = platform.title() if platform != "twitter" else "X / Twitter"
    
    tags = post.get("tags", [])
    if platform == "post":
        origin_text = "Published by David G. Smith"
    else:
        origin_text = f"Originally published on {html.escape(label)}"
        
    tags_html = render_tag_badges(tags, size="normal")

    if is_standalone:
        breadcrumbs_html = render_breadcrumbs(post)
        title_html = f'<h1 class="text-3xl sm:text-4xl font-serif font-medium text-slate-900 tracking-tight leading-tight mb-4">{title}</h1>'
    else:
        breadcrumbs_html = ""
        title_html = f'''
        <a href="/thoughts/{slug}.html" class="block group">
            <h2 class="text-2xl sm:text-3xl font-serif font-medium text-slate-900 group-hover:text-brand-accent transition-colors tracking-tight leading-snug mb-3">
                {title}
            </h2>
        </a>'''

    prev_next_html = ""
    if is_standalone and (prev_post or next_post):
        prev_link = f'''
        <a href="/thoughts/{prev_post["_slug"]}.html" class="flex-1 p-4 rounded-lg border border-slate-200 hover:border-brand-accent group transition-all">
            <span class="block text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">&larr; Older Thought</span>
            <span class="text-sm font-serif font-medium text-slate-900 group-hover:text-brand-accent transition-colors line-clamp-1">{html.escape(prev_post.get("title", ""))}</span>
        </a>
        ''' if prev_post else '<div class="flex-1"></div>'

        next_link = f'''
        <a href="/thoughts/{next_post["_slug"]}.html" class="flex-1 p-4 rounded-lg border border-slate-200 hover:border-brand-accent group transition-all text-right">
            <span class="block text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Newer Thought &rarr;</span>
            <span class="text-sm font-serif font-medium text-slate-900 group-hover:text-brand-accent transition-colors line-clamp-1">{html.escape(next_post.get("title", ""))}</span>
        </a>
        ''' if next_post else '<div class="flex-1"></div>'

        prev_next_html = f'''
        <nav aria-label="Adjacent Thoughts" class="mt-8 pt-6 border-t border-slate-100 flex flex-col sm:flex-row gap-4 justify-between">
            {prev_link}
            {next_link}
        </nav>
        '''

    related_posts_html = render_related_posts_section(related_posts) if is_standalone and related_posts else ""

    return f"""
        <article class="bg-white p-7 sm:p-9 border border-slate-200/90 rounded-lg shadow-md hover:shadow-xl hover:border-slate-300 transition-all">
            {breadcrumbs_html}
            <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-slate-400 font-medium mb-3">
                <img src="{icon}" alt="{icon_alt}" class="h-3.5 w-3.5 opacity-70" loading="lazy">
                <span>{date} &bull; <span class="text-amber-900 font-semibold">{reading_time}</span> &bull; {origin_text}</span>
            </div>
            {title_html}
            <div class="mb-6 flex flex-wrap items-center">{tags_html}</div>
            <div class="markdown-content text-slate-700 leading-relaxed text-[15px]">{body}</div>
            {render_share_bar(share_url=canonical_url, original_url=url)}
            {prev_next_html}
            {related_posts_html}
        </article>
    """

def render_aggregator_card(post):
    title = html.escape(post.get("title", "Untitled"))
    slug = post["_slug"]
    date = post["_dt"].strftime("%B %d, %Y")
    reading_time = calculate_reading_time(post.get("body", ""))
    
    body_html = render_markdown(post.get("body", ""))
    excerpt = create_text_excerpt(body_html, max_length=180)
    
    tags = post.get("tags", [])
    tags_html = render_tag_badges(tags, size="small")
    
    return f"""
    <article class="bg-white p-6 sm:p-7 border border-slate-200 rounded-lg shadow-md hover:shadow-xl hover:border-amber-300 transition-all flex flex-col justify-between">
        <div>
            <div class="flex items-center justify-between text-xs uppercase tracking-wider text-slate-400 font-medium mb-2">
                <span>{date}</span>
                <span class="text-amber-900 bg-amber-50 px-2 py-0.5 rounded font-semibold text-[11px]">{reading_time}</span>
            </div>
            <a href="/thoughts/{slug}.html" class="block group">
                <h3 class="text-xl font-serif font-medium text-slate-900 group-hover:text-brand-accent transition-colors leading-snug mb-2.5">
                    {title}
                </h3>
            </a>
            <div class="mb-3 flex flex-wrap">{tags_html}</div>
            <p class="text-slate-600 text-sm leading-relaxed mb-5">{html.escape(excerpt)}</p>
        </div>
        <div class="pt-3 border-t border-slate-100">
            <a href="/thoughts/{slug}.html" class="text-xs font-semibold uppercase tracking-wider text-brand-accent hover:text-amber-900 inline-flex items-center gap-1.5 transition-colors">
                Read Perspective &rarr;
            </a>
        </div>
    </article>
    """

def wrap_with_layout(title, main_content_html, nav_rail_html, json_ld="", canonical="", description="", og_meta=None, is_post=False, banner_title=None, banner_subtitle=None):
    canonical_escaped = html.escape(canonical, quote=True)
    canonical_tag = f'<link rel="canonical" href="{canonical_escaped}">' if canonical else ''
    meta_description = f'<meta name="description" content="{html.escape(description, quote=True)}">' if description else ''
    
    og_html = ""
    if og_meta:
        extra_article_tags = ""
        if og_meta.get("type") == "article":
            if og_meta.get("published_time"):
                extra_article_tags += f'\n<meta property="article:published_time" content="{html.escape(og_meta["published_time"], quote=True)}">'
            if og_meta.get("tags"):
                for tag in og_meta["tags"]:
                    extra_article_tags += f'\n<meta property="article:tag" content="{html.escape(tag, quote=True)}">'
            extra_article_tags += '\n<meta property="article:author" content="David G. Smith">'

        og_html = f"""
<meta property="og:site_name" content="David G. Smith">
<meta property="og:title" content="{html.escape(og_meta.get('title', title), quote=True)}">
<meta property="og:description" content="{html.escape(og_meta.get('description', description), quote=True)}">
<meta property="og:type" content="{html.escape(og_meta.get('type', 'website'), quote=True)}">
<meta property="og:url" content="{html.escape(og_meta.get('url', canonical), quote=True)}">
<meta property="og:image" content="{html.escape(og_meta.get('image', DEFAULT_OG_IMAGE), quote=True)}">{extra_article_tags}

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(og_meta.get('title', title), quote=True)}">
<meta name="twitter:description" content="{html.escape(og_meta.get('description', description), quote=True)}">
<meta name="twitter:image" content="{html.escape(og_meta.get('image', DEFAULT_OG_IMAGE), quote=True)}">
"""

    if is_post:
        header_content = """
        <div class="max-w-7xl mx-auto flex justify-between items-center text-sm">
            <a href="/thoughts.html" class="inline-flex items-center gap-1.5 text-slate-300 hover:text-brand-accent transition-colors font-medium">
                &larr; Back to all Thoughts
            </a>
            <a href="/rss.xml" target="_blank" class="inline-flex items-center gap-1.5 text-slate-400 hover:text-brand-accent transition-colors">
                <svg class="w-3.5 h-3.5 text-brand-accent" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M4 11a9 9 0 0 1 9 9H9c0-2.76-2.24-5-5-5v-4zm0-7a16 16 0 0 1 16 16h-4a12 12 0 0 0-12-12V4zm2 13a2 2 0 1 1-2 2c0-1.11.89-2 2-2z"></path>
                </svg>
                RSS Feed
            </a>
        </div>
        """
        header_classes = "pt-28 pb-6 px-4 w-full bg-slate-950 text-white border-b border-slate-800"
    else:
        h1_text = banner_title if banner_title else "Thoughts & Insights"
        sub_text = f'<p class="text-sm text-slate-400 max-w-xl mx-auto mt-2 mb-4">{html.escape(banner_subtitle)}</p>' if banner_subtitle else ''
        header_content = f"""
        <div class="max-w-7xl mx-auto text-center">
            <h1 class="text-4xl sm:text-5xl font-serif font-medium text-white mb-2">{html.escape(h1_text)}</h1>
            {sub_text}
            <div class="flex justify-center mb-2">
                <a href="/rss.xml" target="_blank" class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-slate-700 bg-slate-900/80 hover:bg-slate-800 text-sm font-medium text-slate-200 transition-all shadow-sm">
                    <svg class="w-4 h-4 text-brand-accent" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M4 11a9 9 0 0 1 9 9H9c0-2.76-2.24-5-5-5v-4zm0-7a16 16 0 0 1 16 16h-4a12 12 0 0 0-12-12V4zm2 13a2 2 0 1 1-2 2c0-1.11.89-2 2-2z"></path>
                    </svg>
                    Subscribe via RSS
                </a>
            </div>
        </div>
        """
        header_classes = "pt-32 pb-12 px-4 w-full bg-slate-950 text-white border-b border-slate-800"

    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4T0MRLF4V8"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-4T0MRLF4V8');
</script>
<title>{html.escape(title)}</title>
{meta_description}
{og_html}
<link rel="alternate" type="application/rss+xml" href="https://davidgsmith.net/rss.xml" title="Thoughts & Insights — David G. Smith" />
{canonical_tag}
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {{ 
        theme: {{ 
            extend: {{ 
                fontFamily: {{ 
                    sans: ['Inter', 'sans-serif'], 
                    serif: ['Lora', 'serif'] 
                }}, 
                colors: {{ 
                    brand: {{ 
                        dark: '#0f172a', 
                        muted: '#334155', 
                        accent: '#b45309',
                        light: '#f8fafc' 
                    }} 
                }} 
            }} 
        }} 
    }}
</script>
<style>
    body {{ background-color: #0a1128; }}
    .glass-nav {{ background: rgba(255, 255, 255, 0.96); backdrop-filter: blur(12px); }}
    .markdown-content p {{ margin-bottom: 1rem; }}
    .markdown-content p:empty {{ display: none; }}
    .markdown-content h1, .markdown-content h2, .markdown-content h3 {{ color: #0f172a; font-family: Lora, serif; font-weight: 500; margin: 1.25rem 0 0.5rem; }}
    .markdown-content a {{ color: #b45309; text-decoration: underline; }}
    .markdown-content a:hover {{ color: #78350f; }}
    .markdown-content ul {{ list-style-type: disc; margin-top: 0.75rem; margin-bottom: 1rem; padding-left: 1.5rem; }}
    .markdown-content ol {{ list-style-type: decimal; margin-top: 0.75rem; margin-bottom: 1rem; padding-left: 1.5rem; }}
    .markdown-content li {{ margin-bottom: 0.35rem; line-height: 1.6; }}
    .markdown-content li > ul {{ list-style-type: circle; margin-top: 0.25rem; margin-bottom: 0.25rem; padding-left: 1.25rem; }}
    .markdown-content li > ol {{ list-style-type: lower-alpha; margin-top: 0.25rem; margin-bottom: 0.25rem; padding-left: 1.25rem; }}
    .markdown-content table {{ display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 1.5rem 0; font-size: 0.875rem; line-height: 1.5; border: 1px solid #e2e8f0; border-radius: 6px; background-color: #ffffff; }}
    .markdown-content th {{ background-color: #f8fafc; color: #0f172a; font-weight: 600; text-align: left; padding: 0.75rem 1rem; border-bottom: 2px solid #cbd5e1; }}
    .markdown-content td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; color: #334155; }}
    .markdown-content tr:nth-child(even) {{ background-color: #fcfbf9; }}
    .markdown-content tr:last-child td {{ border-bottom: none; }}
</style>
{json_ld}
</head>
<body class="font-sans text-brand-muted antialiased selection:bg-brand-accent selection:text-white relative min-h-screen">
<div id="vanta-canvas" class="fixed inset-0 pointer-events-none -z-10" aria-hidden="true"></div>
<nav class="fixed w-full z-50 glass-nav border-b border-slate-200 transition-all duration-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-20">
            <div class="flex-shrink-0">
                <a href="/" class="text-xl font-serif font-semibold text-slate-900 tracking-tight">David G. Smith</a>
            </div>
            <div class="hidden md:flex space-x-8 items-center">
                <a href="https://davidgsmith.net/#about" class="text-slate-600 hover:text-brand-accent transition-colors text-sm font-medium">About</a>
                <a href="https://davidgsmith.net/#work" class="text-slate-600 hover:text-brand-accent transition-colors text-sm font-medium">Work</a>
                <a href="https://davidgsmith.net/thoughts.html" class="text-brand-accent transition-colors text-sm font-semibold">Thoughts</a>
                <a href="https://davidgsmith.net/books.html" class="text-slate-600 hover:text-brand-accent transition-colors text-sm font-medium">Books</a>
                <a href="https://davidgsmith.net/#advisory" class="text-slate-600 hover:text-brand-accent transition-colors text-sm font-medium">Advisory</a>
                <a href="https://davidgsmith.net/#contact" class="px-5 py-2 rounded border border-slate-300 text-slate-900 hover:border-brand-accent hover:text-brand-accent transition-all text-sm font-medium">Contact</a>
            </div>
            <div class="md:hidden flex items-center">
                <button id="mobile-menu-btn" class="text-slate-900 focus:outline-none" aria-label="Toggle menu">
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    <div id="mobile-menu" class="hidden md:hidden bg-white border-b border-gray-200 shadow-lg">
        <div class="px-4 pt-2 pb-4 space-y-1">
            <a href="https://davidgsmith.net/#about" class="mobile-link block py-2 text-base font-medium text-gray-600">About</a>
            <a href="https://davidgsmith.net/#work" class="mobile-link block py-2 text-base font-medium text-gray-600">Work</a>
            <a href="https://davidgsmith.net/thoughts.html" class="mobile-link block py-2 text-base font-medium text-gray-600">Thoughts</a>
            <a href="https://davidgsmith.net/books.html" class="mobile-link block py-2 text-base font-medium text-gray-600">Books</a>
            <a href="https://davidgsmith.net/#advisory" class="mobile-link block py-2 text-base font-medium text-gray-600">Advisory</a>
            <a href="https://davidgsmith.net/#contact" class="mobile-link block py-2 text-base font-medium text-brand-accent">Contact</a>
        </div>
    </div>
</nav>

<header class="{header_classes}">
    {header_content}
</header>

<main id="main-content" class="py-12 bg-transparent min-h-screen">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div class="lg:col-span-8 space-y-8">
                {main_content_html}
            </div>
            <div class="lg:col-span-4 lg:sticky lg:top-28">
                {nav_rail_html}
            </div>
        </div>
    </div>
</main>

<footer class="bg-slate-950 text-slate-400 py-12 border-t border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center">
        <div class="mb-4 md:mb-0">
            <span class="text-lg font-serif font-semibold text-white tracking-tight">David G. Smith</span>
        </div>
        <div class="mt-4 md:mt-0 text-sm">&copy; <span id="year"></span> David G. Smith. All rights reserved.</div>
    </div>
</footer>

<script>
    document.getElementById('year').textContent = new Date().getFullYear();
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    const mobileLinks = document.querySelectorAll('.mobile-link');
    if(btn && menu) {{
        btn.addEventListener('click', () => menu.classList.toggle('hidden'));
        mobileLinks.forEach(link => link.addEventListener('click', () => menu.classList.add('hidden')));
    }}
</script>

<button id="return-to-top" aria-label="Return to top" class="fixed bottom-6 right-6 z-40 bg-slate-900 border border-slate-700 text-white p-3 rounded-full shadow-lg hover:bg-brand-accent hover:border-brand-accent transition-all opacity-0 pointer-events-none focus:outline-none">
    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
    </svg>
</button>
<script>
    const returnToTopBtn = document.getElementById('return-to-top');
    window.addEventListener('scroll', () => {{
        if (window.scrollY > 300) {{
            returnToTopBtn.classList.remove('opacity-0', 'pointer-events-none');
            returnToTopBtn.classList.add('opacity-100', 'pointer-events-auto');
        }} else {{
            returnToTopBtn.classList.add('opacity-0', 'pointer-events-none');
            returnToTopBtn.classList.remove('opacity-100', 'pointer-events-auto');
        }}
    }});
    returnToTopBtn.addEventListener('click', () => window.scrollTo({{ top: 0, behavior: 'smooth' }}));

    const navToggle = document.getElementById('nav-rail-toggle');
    const navContent = document.getElementById('nav-rail-content');
    const navIcon = document.getElementById('nav-toggle-icon');
    if (navToggle && navContent) {{
        navToggle.addEventListener('click', () => {{
            navContent.classList.toggle('hidden');
            navIcon.classList.toggle('rotate-180');
        }});
    }}
</script>
<script src="/js/three.r134.min.js"></script>
<script src="/js/vanta.net.min.js"></script>
<script>
    function initVanta() {{
        if (window.VANTA && window.VANTA.NET) {{
            VANTA.NET({{
                el: "#vanta-canvas",
                mouseControls: true, touchControls: true, gyroControls: false,
                minHeight: 200.00, minWidth: 200.00, scale: 1.00, scaleMobile: 1.00,
                color: 0x38bdf8, backgroundColor: 0x0a1128, points: 10.00, maxDistance: 20.00, spacing: 18.00
            }});
        }}
    }}
    if (!window.THREE) {{
        const s1 = document.createElement('script');
        s1.src = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js";
        s1.onload = () => {{
            const s2 = document.createElement('script');
            s2.src = "https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.net.min.js";
            s2.onload = initVanta;
            document.body.appendChild(s2);
        }};
        document.body.appendChild(s1);
    }} else {{ initVanta(); }}
</script>
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

def generate_rss(posts):
    rss_items = []
    for post in posts:
        slug = post["_slug"]
        pub_date = post["_dt"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        html_body = render_markdown(post.get("body", ""))
        html_body = sanitize_feed_text(html_body)
        
        # Guard against breaking out of CDATA sequence
        html_body = html_body.replace("]]>", "]]]]><![CDATA[>")
        
        excerpt = html.escape(create_text_excerpt(html_body))
        safe_title = html.escape(sanitize_feed_text(post.get("title", "")))
        
        categories = "\n            ".join([
            f"<category>{html.escape(tag)}</category>\n            <dc:subject>{html.escape(tag)}</dc:subject>" 
            for tag in post.get("tags", [])
        ])

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
    <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <channel>
        <title>Thoughts &amp; Insights — David G. Smith</title>
        <link>https://davidgsmith.net/thoughts.html</link>
        <description>Latest perspectives on technical architecture, enterprise data, and critical thinking.</description>
        <atom:link href="https://davidgsmith.net/rss.xml" rel="self" type="application/rss+xml" />
        <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
        {''.join(rss_items)}
    </channel>
    </rss>"""
    
    with open(BASE_DIR / "rss.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed.strip())

def generate_sitemap(posts, tag_slugs, month_slugs):
    # Align structural assets precisely with the defined sitemap.xml rules
    entries = [
        """  <url>
    <loc>https://davidgsmith.net/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
    <image:image>
      <image:loc>https://davidgsmith.net/images/DaveSmithrPortrait.jpg</image:loc>
      <image:title>David G. Smith - Systems Architect and Author</image:title>
    </image:image>
  </url>""",
        """  <url>
    <loc>https://davidgsmith.net/books.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""",
        """  <url>
    <loc>https://davidgsmith.net/critical-thinking.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
    <image:image>
      <image:loc>https://davidgsmith.net/images/CriticalThinkingCover.jpg</image:loc>
      <image:title>Critical Thinking: A Practical Guide to Seeing Through Bias, Noise and Manipulation</image:title>
    </image:image>
  </url>""",
        """  <url>
    <loc>https://davidgsmith.net/thoughts.html</loc>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>""",
        """  <url>
    <loc>https://davidgsmith.net/rss.xml</loc>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>""",
        """  <url>
    <loc>https://davidgsmith.net/llms.txt</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""",
        """  <url>
    <loc>https://davidgsmith.net/book-manifest.json</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""",
        """  <url>
    <loc>https://davidgsmith.net/api/v1/book-manifest.json</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>"""
    ]
    
    # Do not set lastmod for dynamically generated pages without true modification dates
    for post in posts:
        slug = post["_slug"]
        entries.append(f"""  <url>
    <loc>https://davidgsmith.net/thoughts/{slug}.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")
        
    for t in sorted(tag_slugs):
        entries.append(f"""  <url>
    <loc>https://davidgsmith.net/thoughts-{t}.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>""")

    for m in sorted(month_slugs):
        entries.append(f"""  <url>
    <loc>https://davidgsmith.net/thoughts-{m}.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>""")

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{chr(10).join(entries)}
</urlset>"""
    
    with open(BASE_DIR / "sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml.strip())
    print("✓ Generated sitemap.xml for search and AI crawler indexing.")

def cleanup_stale_pages():
    # Remove thoughts directory completely and recreate it
    shutil.rmtree(THOUGHTS_DIR, ignore_errors=True)
    THOUGHTS_DIR.mkdir(exist_ok=True)
    
    # Remove dynamically generated taxonomy/date root HTML files
    for filepath in BASE_DIR.glob("thoughts-*.html"):
        filepath.unlink()

def generate_html():
    # Purge old generated pages to prevent stale records from surviving
    cleanup_stale_pages()
    
    posts = load_posts()
    all_tags = set()
    generated_urls = ["https://davidgsmith.net/thoughts.html", "https://davidgsmith.net/rss.xml"]
    
    for post in posts:
        for t in post.get("tags", []):
            all_tags.add(t)

    tag_slugs = [slugify(t) for t in all_tags]
    month_slugs = []

    # 1. Generate individual post pages
    total_posts = len(posts)
    for index, post in enumerate(posts):
        slug = post["_slug"]
        canonical = f"https://davidgsmith.net/thoughts/{slug}.html"
        generated_urls.append(canonical)

        prev_post = posts[index + 1] if index + 1 < total_posts else None
        next_post = posts[index - 1] if index > 0 else None
        related = get_related_posts(post, posts, limit=3)

        single_html = render_post(
            post, 
            is_standalone=True, 
            prev_post=prev_post, 
            next_post=next_post, 
            related_posts=related
        )
        json_ld_script = get_json_ld(post)
        description = create_text_excerpt(render_markdown(post.get("body", "")), max_length=160)
        nav_rail = generate_nav_rail(posts)
        post_img = extract_post_image(post)

        og_metadata = {
            "title": post.get("title", "Thoughts & Insights"),
            "description": description,
            "url": canonical,
            "image": post_img,
            "type": "article",
            "published_time": post["_dt"].isoformat(),
            "tags": post.get("tags", [])
        }
        
        page_html = wrap_with_layout(
            f"{post.get('title')} — David G. Smith",
            single_html,
            nav_rail,
            json_ld=json_ld_script,
            canonical=canonical,
            description=description,
            og_meta=og_metadata,
            is_post=True
        )
        with open(THOUGHTS_DIR / f"{slug}.html", "w", encoding="utf-8") as f:
            f.write(page_html)

    # 2. Generate Tag Aggregator Pages
    for tag in all_tags:
        t_slug = slugify(tag)
        tag_posts = [p for p in posts if tag in p.get("tags", [])]
        cards_html = "".join(render_aggregator_card(p) for p in tag_posts)
        main_content = f"""
        <div class="mb-6 bg-white p-6 rounded-lg border border-slate-200 shadow-md">
            <h2 class="text-2xl font-serif font-medium text-slate-900 mb-1">Posts Tagged: {html.escape(tag)}</h2>
            <p class="text-sm text-slate-500">Showing {len(tag_posts)} post(s) filed under this topic.</p>
        </div>
        <div class="grid grid-cols-1 gap-6">
            {cards_html}
        </div>
        """
        nav_rail = generate_nav_rail(posts, current_type="tag", current_value=tag)
        canonical = f"https://davidgsmith.net/thoughts-{t_slug}.html"
        generated_urls.append(canonical)
        description = f"Explore perspectives and technical insights on {tag} by David G. Smith."

        og_metadata = {
            "title": f"Posts tagged '{tag}' — David G. Smith",
            "description": description,
            "url": canonical,
            "image": DEFAULT_OG_IMAGE,
            "type": "website"
        }

        page_html = wrap_with_layout(
            f"Posts tagged '{tag}' — David G. Smith",
            main_content,
            nav_rail,
            canonical=canonical,
            description=description,
            og_meta=og_metadata,
            is_post=False,
            banner_title=f"Topic: {tag}",
            banner_subtitle=f"Perspectives and architecture notes relating to {tag}."
        )
        with open(BASE_DIR / f"thoughts-{t_slug}.html", "w", encoding="utf-8") as f:
            f.write(page_html)

    # Untagged aggregator page if untagged posts exist
    untagged_posts = [p for p in posts if not p.get("tags")]
    if untagged_posts:
        tag_slugs.append("untagged")
        cards_html = "".join(render_aggregator_card(p) for p in untagged_posts)
        main_content = f"""
        <div class="mb-6 bg-white p-6 rounded-lg border border-slate-200 shadow-md">
            <h2 class="text-2xl font-serif font-medium text-slate-900 mb-1">Untagged Posts</h2>
            <p class="text-sm text-slate-500">Showing {len(untagged_posts)} untagged post(s).</p>
        </div>
        <div class="grid grid-cols-1 gap-6">
            {cards_html}
        </div>
        """
        nav_rail = generate_nav_rail(posts, current_type="tag", current_value="untagged")
        canonical = "https://davidgsmith.net/thoughts-untagged.html"
        generated_urls.append(canonical)
        description = "Explore uncategorized thoughts and insights by David G. Smith."

        og_metadata = {
            "title": "Untagged Posts — David G. Smith",
            "description": description,
            "url": canonical,
            "image": DEFAULT_OG_IMAGE,
            "type": "website"
        }

        page_html = wrap_with_layout(
            "Untagged Posts — David G. Smith",
            main_content,
            nav_rail,
            canonical=canonical,
            description=description,
            og_meta=og_metadata,
            is_post=False,
            banner_title="Untagged Perspectives",
            banner_subtitle="Archived notes without specific category tags."
        )
        with open(BASE_DIR / "thoughts-untagged.html", "w", encoding="utf-8") as f:
            f.write(page_html)

    # 3. Generate Month Aggregator Pages
    year_month_posts = {}
    for post in posts:
        year = post["_dt"].strftime("%Y")
        m_abbr = post["_dt"].strftime("%b").upper()
        key = (year, m_abbr)
        if key not in year_month_posts:
            year_month_posts[key] = []
        year_month_posts[key].append(post)

    months_map = {
        "JAN": "January", "FEB": "February", "MAR": "March",
        "APR": "April", "MAY": "May", "JUN": "June",
        "JUL": "July", "AUG": "August", "SEP": "September",
        "OCT": "October", "NOV": "November", "DEC": "December"
    }

    for (year, m_abbr), m_posts in year_month_posts.items():
        m_full = months_map[m_abbr]
        m_slug_suffix = f"{year}-{m_abbr.lower()}"
        month_slugs.append(m_slug_suffix)
        cards_html = "".join(render_aggregator_card(p) for p in m_posts)
        main_content = f"""
        <div class="mb-6 bg-white p-6 rounded-lg border border-slate-200 shadow-md">
            <h2 class="text-2xl font-serif font-medium text-slate-900 mb-1">Posts from {m_full} {year}</h2>
            <p class="text-sm text-slate-500">Showing {len(m_posts)} post(s) published in {m_full} {year}.</p>
        </div>
        <div class="grid grid-cols-1 gap-6">
            {cards_html}
        </div>
        """
        nav_rail = generate_nav_rail(posts, current_type="month", current_value=(year, m_abbr))
        canonical = f"https://davidgsmith.net/thoughts-{m_slug_suffix}.html"
        generated_urls.append(canonical)
        description = f"Explore thoughts and insights published in {m_full} {year} by David G. Smith."

        og_metadata = {
            "title": f"Posts from {m_full} {year} — David G. Smith",
            "description": description,
            "url": canonical,
            "image": DEFAULT_OG_IMAGE,
            "type": "website"
        }

        page_html = wrap_with_layout(
            f"Posts from {m_full} {year} — David G. Smith",
            main_content,
            nav_rail,
            canonical=canonical,
            description=description,
            og_meta=og_metadata,
            is_post=False,
            banner_title=f"{m_full} {year} Archive",
            banner_subtitle=f"Published writings and analysis from {m_full} {year}."
        )
        with open(BASE_DIR / f"thoughts-{m_slug_suffix}.html", "w", encoding="utf-8") as f:
            f.write(page_html)

    # 4. Generate Main thoughts.html Index Page
    recent_posts = posts[:8]
    index_posts_html = "".join(render_post(p, is_standalone=False) for p in recent_posts)
    main_content_index = f"""
    <div class="mb-6 bg-white p-6 rounded-lg border border-slate-200 shadow-md flex justify-between items-center">
        <div>
            <h2 class="text-2xl font-serif font-medium text-slate-900">Recent Thoughts</h2>
            <p class="text-sm text-slate-500 mt-1">Showing the 8 most recent perspectives and notes.</p>
        </div>
    </div>
    <div class="space-y-8">
        {index_posts_html}
    </div>
    """
    nav_rail_index = generate_nav_rail(posts)
    json_ld_main = get_json_ld(None)
    main_description = "Latest perspectives on technical architecture, enterprise data, and critical thinking."
    
    og_metadata_index = {
        "title": "Thoughts & Insights — David G. Smith",
        "description": main_description,
        "url": "https://davidgsmith.net/thoughts.html",
        "image": DEFAULT_OG_IMAGE,
        "type": "website"
    }

    main_html = wrap_with_layout(
        "Thoughts & Insights — David G. Smith",
        main_content_index,
        nav_rail_index,
        json_ld=json_ld_main,
        canonical="https://davidgsmith.net/thoughts.html",
        description=main_description,
        og_meta=og_metadata_index,
        is_post=False
    )
    with open(BASE_DIR / "thoughts.html", "w", encoding="utf-8") as f:
        f.write(main_html)

    # Generate Feeds and Sitemaps
    generate_rss(posts)
    generate_sitemap(posts, tag_slugs, month_slugs)
    return generated_urls
        
def ping_websub_hub(feed_url="https://davidgsmith.net/rss.xml"):
    hub_url = "https://pubsubhubbub.appspot.com/publish"
    payload = {
        'hub.mode': 'publish',
        'hub.url': feed_url
    }
    try:
        encoded_data = urllib.parse.urlencode(payload).encode('utf-8')
        request_wrapper = urllib.request.Request(
            hub_url,
            data=encoded_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        print(f"Sending WebSub publish signal for {feed_url}...")
        with urllib.request.urlopen(request_wrapper) as response:
            if response.status in (200, 204):
                print("✓ Success! Google PubSubHubbub has been notified.")
            else:
                print(f"⚠ Hub responded with an unexpected status: {response.status}")
    except Exception as error:
        print(f"✗ Failed to complete publish notification: {error}")

def notify_indexnow(urls=None):
    key = os.environ.get("INDEXNOW_KEY")
    if not key or os.environ.get("INDEXNOW_NOTIFY", "true").lower() == "false":
        return

    url_list = urls if urls else [
        "https://davidgsmith.net/thoughts.html",
        "https://davidgsmith.net/rss.xml"
    ]

    payload = json.dumps({
        "host": "davidgsmith.net",
        "key": key,
        "keyLocation": f"https://davidgsmith.net/{key}.txt",
        "urlList": url_list[:10000]
    }).encode("utf-8")
    
    request_wrapper = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(request_wrapper, timeout=20) as response:
            if response.status not in (200, 202):
                print(f"IndexNow returned an unexpected status: {response.status}")
            else:
                print(f"IndexNow notified successfully for {len(url_list)} URLs.")
    except Exception as error:
        print(f"IndexNow notification failed: {error}")

if __name__ == "__main__":
    urls = generate_html()
    ping_websub_hub()
    notify_indexnow(urls)
    print("Successfully built thoughts, aggregators, sitemap.xml, and RSS feed.")