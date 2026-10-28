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
DEFAULT_OG_IMAGE = "https://davidgsmith.net/images/DaveSmithrPortrait.jpg"

# Central configuration for newsletter / waitlist signup endpoint
NEWSLETTER_FORM_ACTION = "https://webhook.davidgsmith.net/webhook/subscriber-capture"

GEOSPATIAL_CLUSTER_TAGS = {
    "Cloud-Native Geospatial", "DuckDB", "Geospatial", "Spatial SQL",
    "GeoAI", "Apache Sedona", "Open Source GIS", "3D Reality Capture",
    "Gaussian Splatting", "Cloud-Native", "Data Engineering", "Open Standards"
}

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
    seen_slugs = set()
    normalized_posts = []
    
    # Iterate over all yearly sharded files instead of a single posts.json
    for filepath in BASE_DIR.glob("posts-*.json"):
        with filepath.open(encoding="utf-8") as posts_file:
            try:
                raw_posts = json.load(posts_file)
            except json.JSONDecodeError:
                continue # Skip empty or malformed files
            
        for post in raw_posts:
            # Standardize required & optional fields
            post.setdefault("type", "BlogPosting")
            if not post.get("url") or "davidgsmith.net" in post.get("url", ""):
                post["url"] = ""
                
            # Parse and anchor UTC dates
            dt = parse_and_normalize_date(post.get("date"))
            post["_dt"] = dt
            
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
    <nav aria-label="Breadcrumb" class="no-print mb-4 text-xs font-medium text-slate-500">
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

def render_share_bar(share_url, original_url, post_title="Thought by David G. Smith", is_standalone=False):
    sep = "&" if "?" in share_url else "?"
    li_url = urllib.parse.quote(f"{share_url}{sep}utm_source=linkedin&utm_medium=social_share&utm_campaign=thoughts", safe="")
    tw_url = urllib.parse.quote(f"{share_url}{sep}utm_source=x_twitter&utm_medium=social_share&utm_campaign=thoughts", safe="")
    fb_url = urllib.parse.quote(f"{share_url}{sep}utm_source=facebook&utm_medium=social_share&utm_campaign=thoughts", safe="")
    bsky_url = urllib.parse.quote(f"{share_url}{sep}utm_source=bluesky&utm_medium=social_share&utm_campaign=thoughts", safe="")
    masto_url = urllib.parse.quote(f"{share_url}{sep}utm_source=mastodon&utm_medium=social_share&utm_campaign=thoughts", safe="")
    
    email_share_link = f"{share_url}{sep}utm_source=email_share&utm_medium=social_share&utm_campaign=thoughts"
    email_subject = urllib.parse.quote(f"{post_title} — David G. Smith", safe="")
    email_body = urllib.parse.quote(f"I thought you might find this article by David G. Smith interesting:\n\n{post_title}\n{email_share_link}", safe="")

    read_original_html = "<div></div>" 
    if original_url:
        orig_escaped = html.escape(original_url, quote=True)
        read_original_html = f"""
        <a href="{orig_escaped}" target="_blank" rel="noopener noreferrer"
           class="text-sm font-semibold text-brand-accent hover:text-amber-900 transition-colors inline-flex items-center gap-1">
           Read Original &rarr;
        </a>
        """

    if is_standalone:
        print_button_html = f"""
            <button type="button"
                    onclick="gtag('event', 'share', {{'method': 'Print', 'content_id': '{html.escape(share_url)}'}}); window.print();"
                    class="inline-flex items-center gap-1 text-slate-600 hover:text-brand-accent transition cursor-pointer ml-1 pl-2 border-l border-slate-200 text-xs font-medium"
                    title="Print clean article"
                    aria-label="Print clean article">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                <span class="hidden sm:inline">Print</span>
            </button>
        """
    else:
        print_arg = f"{share_url}{sep}print=1"
        print_button_html = f"""
            <a href="{html.escape(print_arg)}"
               target="_blank" rel="noopener noreferrer"
               onclick="gtag('event', 'share', {{'method': 'Print', 'content_id': '{html.escape(share_url)}'}});"
               class="inline-flex items-center gap-1 text-slate-600 hover:text-brand-accent transition ml-1 pl-2 border-l border-slate-200 text-xs font-medium"
               title="Print clean article"
               aria-label="Print clean article">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                <span class="hidden sm:inline">Print</span>
            </a>
        """

    return f"""
    <div class="no-print mt-8 pt-4 border-t border-slate-100 flex flex-col sm:flex-row justify-between items-center gap-4">
        {read_original_html}
        <div class="flex flex-wrap items-center gap-3">
            <span class="text-xs font-medium uppercase tracking-wider text-slate-400">Share:</span>
            <a href="https://www.linkedin.com/sharing/share-offsite/?url={li_url}"
               target="_blank" rel="noopener noreferrer" onclick="gtag('event', 'share', {{'method': 'LinkedIn', 'content_id': '{html.escape(share_url)}'}});" class="hover:opacity-80 transition" title="Share on LinkedIn" aria-label="Share on LinkedIn">
                <img src="/images/InBug-Black.png" class="h-4 w-4" alt="LinkedIn icon">
            </a>
            <a href="https://twitter.com/intent/tweet?url={tw_url}"
               target="_blank" rel="noopener noreferrer" onclick="gtag('event', 'share', {{'method': 'X', 'content_id': '{html.escape(share_url)}'}});" class="hover:opacity-80 transition" title="Share on X" aria-label="Share on X">
                <img src="https://unpkg.com/simple-icons/icons/x.svg" class="h-4 w-4" alt="X / Twitter icon">
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={fb_url}"
               target="_blank" rel="noopener noreferrer" onclick="gtag('event', 'share', {{'method': 'Facebook', 'content_id': '{html.escape(share_url)}'}});" class="hover:opacity-80 transition" title="Share on Facebook" aria-label="Share on Facebook">
                <img src="https://unpkg.com/simple-icons/icons/facebook.svg" class="h-4 w-4" alt="Facebook icon">
            </a>
            <a href="https://bsky.app/intent/compose?text={bsky_url}"
               target="_blank" rel="noopener noreferrer" onclick="gtag('event', 'share', {{'method': 'Bluesky', 'content_id': '{html.escape(share_url)}'}});" class="hover:opacity-80 transition" title="Share on Bluesky" aria-label="Share on Bluesky">
                <img src="https://unpkg.com/simple-icons/icons/bluesky.svg" class="h-4 w-4" alt="Bluesky icon">
            </a>
            <a href="https://mastodon.social/share?text={masto_url}"
               target="_blank" rel="noopener noreferrer" onclick="gtag('event', 'share', {{'method': 'Mastodon', 'content_id': '{html.escape(share_url)}'}});" class="hover:opacity-80 transition" title="Share on Mastodon" aria-label="Share on Mastodon">
                <img src="https://unpkg.com/simple-icons/icons/mastodon.svg" class="h-4 w-4" alt="Mastodon icon">
            </a>
            <a href="mailto:?subject={email_subject}&body={email_body}"
               onclick="gtag('event', 'share', {{'method': 'Email', 'content_id': '{html.escape(share_url)}'}});"
               class="inline-flex items-center gap-1 text-slate-600 hover:text-brand-accent transition ml-1 pl-2 border-l border-slate-200 text-xs font-medium"
               title="Send copy via Email"
               aria-label="Send copy via Email">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span class="hidden sm:inline">Email</span>
            </a>
            {print_button_html}
        </div>
    </div>
    """

def render_in_article_cta(post=None):
    slug = post.get("_slug", "thought-post") if isinstance(post, dict) else str(post or "geospatial-stack")
    safe_slug = html.escape(slug, quote=True)
    return f"""
    <div id="newsletter" class="no-print mt-14 bg-slate-900 border border-slate-800 rounded-2xl p-8 sm:p-10 shadow-2xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <div class="lg:col-span-7 space-y-3">
            <div class="flex flex-wrap items-center gap-2">
                <span class="px-2.5 py-0.5 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded text-[11px] font-bold uppercase tracking-widest">
                    Coming Soon &bull; Weekly Briefing &amp; Reference Hub
                </span>
                <a href="/cloud-native-geospatial-stack.html" class="text-xs font-semibold text-sky-400 hover:text-sky-300 underline">
                    New: The Cloud-Native Geospatial &amp; GeoAI Stack &rarr;
                </a>
            </div>
            <h3 class="text-2xl sm:text-3xl font-serif font-medium text-white leading-snug">
                Coming Soon: Get the Weekly Spatial, Data &amp; AI Architecture Digest
            </h3>
            <p class="text-sm text-gray-300 leading-relaxed">
                Launching soon: Every week, I will curate the top 5 cloud-native geospatial &amp; data engineering essays, key AI research papers, and my latest writing—plus early-access chapters from my forthcoming books.
            </p>
        </div>
        <div class="lg:col-span-5">
            <form data-newsletter-form data-source-page="thought_article_{safe_slug}" action="{NEWSLETTER_FORM_ACTION}" method="post"
                  class="flex flex-col sm:flex-row lg:flex-col gap-3">
                <input type="email" name="email" required placeholder="Enter your email address..."
                       aria-label="Email address"
                       class="w-full px-4 py-3 rounded-lg bg-slate-950 border border-slate-700 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-brand-accent">
                <input type="hidden" name="tag" value="thought-{safe_slug}">
                <button type="submit" data-submit-btn
                        class="w-full px-6 py-3 bg-brand-accent hover:bg-amber-700 disabled:opacity-50 text-white font-semibold text-sm rounded-lg transition-colors shadow-lg">
                    Join Waitlist (Coming Soon) &rarr;
                </button>
            </form>
            <p class="text-[11px] text-gray-400 mt-2 text-center lg:text-left">Coming soon &bull; 1x weekly synthesis &bull; Zero noise &bull; Unsubscribe anytime.</p>
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
    <section class="no-print mt-10 pt-8 border-t border-slate-200" aria-label="Related Thoughts">
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

def get_json_ld(post=None, collection_url=None, collection_name=None, collection_desc=None, topic_name=None):
    author_entity = {
        "@type": "Person",
        "@id": "https://davidgsmith.net/#person",
        "name": "David G. Smith",
        "url": "https://davidgsmith.net/"
    }

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
                "author": author_entity,
                "publisher": author_entity,
                "description": description,
                "keywords": ", ".join(tags) if tags else "",
                "articleSection": tags[0] if tags else "Technology"
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "@id": f"{canonical_url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://davidgsmith.net/"},
                    {"@type": "ListItem", "position": 2, "name": "Thoughts", "item": "https://davidgsmith.net/thoughts.html"},
                    {"@type": "ListItem", "position": 3, "name": title, "item": canonical_url}
                ]
            }
        ]
    elif collection_url:
        collection_schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "@id": f"{collection_url}#webpage",
            "url": collection_url,
            "name": collection_name,
            "description": collection_desc,
            "author": author_entity
        }
        if topic_name:
            collection_schema["about"] = {"@type": "Thing", "name": topic_name}
            
        schema = [
            collection_schema,
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "@id": f"{collection_url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://davidgsmith.net/"},
                    {"@type": "ListItem", "position": 2, "name": "Thoughts", "item": "https://davidgsmith.net/thoughts.html"},
                    {"@type": "ListItem", "position": 3, "name": collection_name, "item": collection_url}
                ]
            }
        ]
    else:
        blog_url = "https://davidgsmith.net/thoughts.html"
        schema = [
            {
                "@context": "https://schema.org",
                "@type": "Blog",
                "@id": f"{blog_url}#blog",
                "name": "Thoughts & Insights — David G. Smith",
                "url": blog_url,
                "description": "Latest perspectives on technical architecture, enterprise data, and critical thinking.",
                "author": author_entity
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "@id": f"{blog_url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://davidgsmith.net/"},
                    {"@type": "ListItem", "position": 2, "name": "Thoughts", "item": blog_url}
                ]
            }
        ]
    
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
    <aside aria-label="Sidebar Navigation" class="no-print space-y-6">
        <div class="bg-slate-900 p-6 rounded-lg border border-amber-500/40 shadow-xl text-slate-100">
            <span class="inline-block text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 mb-2">
                Coming Soon &bull; Weekly Digest
            </span>
            <h3 class="text-lg font-serif font-medium text-white leading-snug mb-2">
                Coming Soon: Newsletter on GeoAI, Cloud-Native Geo &amp; Innovative Data
            </h3>
            <p class="text-xs text-slate-300 leading-relaxed mb-4">
                Launching soon: Get my curated weekly synthesis of news, research, and articles on cloud-native geospatial, data pipelines, and serverless data stacks—plus early book chapters.
            </p>
            <form data-newsletter-form data-source-page="thoughts_sidebar" action="{NEWSLETTER_FORM_ACTION}" method="post"
                  class="space-y-2.5">
                <input type="email" name="email" required placeholder="Your email address..."
                       aria-label="Email address"
                       class="w-full px-3.5 py-2 rounded bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-brand-accent">
                <input type="hidden" name="tag" value="thoughts-sidebar-digest">
                <button type="submit" data-submit-btn
                        class="w-full py-2 bg-brand-accent hover:bg-amber-700 disabled:opacity-50 text-white font-semibold text-xs rounded transition-colors shadow">
                    Join Waitlist (Coming Soon) &rarr;
                </button>
            </form>
            <p class="text-[10px] text-slate-400 mt-2">Coming soon &bull; Weekly synthesis &bull; Zero spam.</p>
            <div class="mt-4 pt-3 border-t border-slate-800 flex flex-col gap-1.5 text-xs">
                <a href="/cloud-native-geospatial-stack.html" class="text-amber-400 hover:text-amber-300 font-semibold flex items-center justify-between">
                    <span>Cloud-Native Geospatial Hub</span>
                    <span>&rarr;</span>
                </a>
                <a href="/books.html" data-book-funnel="sidebar_books_link" class="text-slate-300 hover:text-white font-medium flex items-center justify-between">
                    <span>Explore Books &amp; Publications</span>
                    <span>&rarr;</span>
                </a>
            </div>
        </div>

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
    raw_title = post.get("title", "Untitled")
    title = html.escape(raw_title)
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
        content_html = f'<div class="markdown-content text-slate-700 leading-relaxed text-[15px]">{body}</div>'
        cta_html = render_in_article_cta(post)
        print_footer_html = f"""
        <div class="hidden print-only mt-8 pt-4 border-t border-slate-300 text-xs text-slate-600">
            <p><strong>Author:</strong> David G. Smith &bull; <strong>Source:</strong> {html.escape(canonical_url)}</p>
        </div>
        """
    else:
        breadcrumbs_html = ""
        title_html = f'''
        <a href="/thoughts/{slug}.html" class="block group">
            <h2 class="text-2xl sm:text-3xl font-serif font-medium text-slate-900 group-hover:text-brand-accent transition-colors tracking-tight leading-snug mb-3">
                {title}
            </h2>
        </a>'''
        excerpt_text = html.escape(create_text_excerpt(body, max_length=340))
        content_html = f'''
        <p class="text-slate-600 leading-relaxed text-[15px] mb-4">{excerpt_text}</p>
        <a href="/thoughts/{slug}.html" class="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-accent hover:text-amber-900 transition-colors">
            Read Full Essay ({reading_time}) &rarr;
        </a>
        '''
        cta_html = ""
        print_footer_html = ""

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
        <nav aria-label="Adjacent Thoughts" class="no-print mt-8 pt-6 border-t border-slate-100 flex flex-col sm:flex-row gap-4 justify-between">
            {prev_link}
            {next_link}
        </nav>
        '''

    related_posts_html = render_related_posts_section(related_posts) if is_standalone and related_posts else ""

    return f"""
        <article class="print-article bg-white p-7 sm:p-9 border border-slate-200/90 rounded-lg shadow-md hover:shadow-xl hover:border-slate-300 transition-all">
            {breadcrumbs_html}
            <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-slate-400 font-medium mb-3">
                <img src="{icon}" alt="{icon_alt}" class="no-print h-3.5 w-3.5 opacity-70" loading="lazy">
                <span>{date} &bull; <span class="text-amber-900 font-semibold">{reading_time}</span> &bull; {origin_text}</span>
            </div>
            {title_html}
            <div class="no-print mb-6 flex flex-wrap items-center">{tags_html}</div>
            {content_html}
            {print_footer_html}
            {cta_html}
            {render_share_bar(share_url=canonical_url, original_url=url, post_title=raw_title, is_standalone=is_standalone)}
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
            <a href="/thoughts.html" class="inline-flex items-center gap-1.5 text-slate-300 hover:text-amber-400 transition-colors font-medium">
                &larr; Back to all Thoughts
            </a>
            <a href="/rss.xml" target="_blank" class="inline-flex items-center gap-1.5 text-slate-400 hover:text-amber-400 transition-colors">
                <svg class="w-3.5 h-3.5 text-brand-accent" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M4 11a9 9 0 0 1 9 9H9c0-2.76-2.24-5-5-5v-4zm0-7a16 16 0 0 1 16 16h-4a12 12 0 0 0-12-12V4zm2 13a2 2 0 1 1-2 2c0-1.11.89-2 2-2z"></path>
                </svg>
                RSS Feed
            </a>
        </div>
        """
        header_classes = "no-print pt-28 pb-6 px-4 w-full bg-slate-950 text-white border-b border-slate-800"
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
        header_classes = "no-print pt-32 pb-12 px-4 w-full bg-slate-950 text-white border-b border-slate-800"

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
    gtag('config', 'G-4T0MRLF4V8', {{ send_page_view: true }});
</script>
<!-- Microsoft Clarity -->
<script>
    (function(c,l,a,r,i,t,y){{
        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i+"?ref=bwt";
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    }})(window, document, "clarity", "script", "yolwcmk37v");
</script>
<title>{html.escape(title)}</title>
{meta_description}
<meta name="theme-color" content="#0f172a">
{og_html}
<link rel="alternate" type="application/rss+xml" href="https://davidgsmith.net/rss.xml" title="Thoughts & Insights — David G. Smith" />
{canonical_tag}
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
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
    .glass-nav {{ background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px); }}
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

    @media print {{
        body {{ background: #ffffff !important; color: #000000 !important; }}
        .no-print, #vanta-canvas, header, nav, footer, aside, #return-to-top, #sub-toast, #sub-modal {{ display: none !important; }}
        .print-only {{ display: block !important; }}
        #main-content {{ padding: 0 !important; margin: 0 !important; min-height: auto !important; }}
        #main-content .grid {{ display: block !important; }}
        .print-article {{ border: none !important; box-shadow: none !important; padding: 0 !important; margin: 0 !important; width: 100% !important; max-width: 100% !important; }}
        .markdown-content {{ color: #000000 !important; font-size: 11pt !important; line-height: 1.55 !important; }}
        .markdown-content a {{ color: #000000 !important; text-decoration: underline !important; }}
    }}
</style>
{json_ld}
<script src="/js/site-core.js" defer></script>
</head>
<body class="font-sans text-brand-muted antialiased selection:bg-brand-accent selection:text-white relative min-h-screen flex flex-col justify-between">
<div id="vanta-canvas" class="no-print fixed inset-0 pointer-events-none -z-10" aria-hidden="true"></div>

<!-- Standardized High-Contrast Dark Glass Header -->
<header class="no-print">
    <nav aria-label="Main Navigation" class="fixed top-0 left-0 right-0 w-full z-50 glass-nav border-b border-slate-800 transition-all duration-300">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-20">
                <div class="flex-shrink-0">
                    <a href="/" class="text-xl font-serif font-semibold text-white tracking-tight">David G. Smith</a>
                </div>
                <div class="hidden md:flex space-x-7 items-center">
                    <a href="/#about" class="text-slate-200 hover:text-amber-400 transition-colors text-sm font-medium">About</a>
                    <a href="/#work" class="text-slate-200 hover:text-amber-400 transition-colors text-sm font-medium">Work</a>
                    <a href="/cloud-native-geospatial-stack.html" class="text-slate-200 hover:text-amber-400 transition-colors text-sm font-medium">Geo &amp; DuckDB Hub</a>
                    <a href="/thoughts.html" class="text-amber-400 transition-colors text-sm font-semibold" aria-current="page">Thoughts</a>
                    <a href="/books.html" data-book-funnel="thoughts_nav_books" class="text-slate-200 hover:text-amber-400 transition-colors text-sm font-medium">Books</a>
                    <a href="/#advisory" class="text-slate-200 hover:text-amber-400 transition-colors text-sm font-medium">Advisory</a>
                    <a href="/#contact" class="px-5 py-2 rounded border border-slate-600 text-white hover:border-amber-400 hover:text-amber-400 transition-all text-sm font-medium">Contact</a>
                </div>
                <div class="md:hidden flex items-center">
                    <button id="mobile-menu-btn" type="button" class="text-white focus:outline-none p-2" aria-label="Toggle Navigation" aria-expanded="false" aria-controls="mobile-menu">
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        <div id="mobile-menu" class="hidden md:hidden bg-slate-900/98 border-b border-slate-800 shadow-xl">
            <div class="px-4 pt-2 pb-5 space-y-1.5">
                <a href="/#about" class="mobile-link block py-2 text-base font-medium text-slate-200 hover:text-amber-400">About</a>
                <a href="/#work" class="mobile-link block py-2 text-base font-medium text-slate-200 hover:text-amber-400">Work</a>
                <a href="/cloud-native-geospatial-stack.html" class="mobile-link block py-2 text-base font-medium text-slate-200 hover:text-amber-400">Geo &amp; DuckDB Hub</a>
                <a href="/thoughts.html" class="mobile-link block py-2 text-base font-semibold text-amber-400" aria-current="page">Thoughts</a>
                <a href="/books.html" data-book-funnel="thoughts_mobile_nav_books" class="mobile-link block py-2 text-base font-medium text-slate-200 hover:text-amber-400">Books</a>
                <a href="/#advisory" class="mobile-link block py-2 text-base font-medium text-slate-200 hover:text-amber-400">Advisory</a>
                <a href="/#contact" class="mobile-link block py-2 text-base font-medium text-amber-400 font-semibold">Contact</a>
            </div>
        </div>
    </nav>
</header>

<div class="{header_classes}">
    {header_content}
</div>

<main id="main-content" class="py-12 bg-transparent min-h-screen flex-grow">
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

<!-- Dismissible Subscription Feedback Toast & Modal -->
<div id="sub-toast" role="status" aria-live="polite" class="no-print fixed bottom-20 right-6 z-50 hidden max-w-sm bg-slate-900 border border-slate-700 text-white px-5 py-4 rounded-xl shadow-2xl flex items-start gap-3 transition-all duration-300">
    <span id="sub-toast-icon" class="mt-0.5 text-emerald-400 shrink-0"></span>
    <div class="text-xs sm:text-sm flex-1">
        <p id="sub-toast-title" class="font-semibold text-white">Subscription Update</p>
        <p id="sub-toast-msg" class="text-slate-300 mt-0.5"></p>
    </div>
    <button type="button" onclick="closeSubFeedback()" class="text-slate-400 hover:text-white p-1" aria-label="Close notification">&times;</button>
</div>

<div id="sub-modal" role="dialog" aria-modal="true" aria-labelledby="sub-modal-title" class="no-print fixed inset-0 z-50 hidden flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 sm:p-8 shadow-2xl text-center space-y-4 relative">
        <button type="button" onclick="closeSubFeedback()" class="absolute top-4 right-4 text-slate-400 hover:text-white p-1" aria-label="Dismiss modal">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
        <div id="sub-modal-badge" class="w-12 h-12 rounded-full mx-auto flex items-center justify-center bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"></div>
        <h3 id="sub-modal-title" class="text-xl font-serif font-semibold text-white"></h3>
        <p id="sub-modal-message" class="text-sm text-slate-300 leading-relaxed"></p>
        <p class="text-xs text-amber-400/90 font-medium">The Spatial, Data &amp; AI Architecture Digest is coming soon — you are locked in for the inaugural issue.</p>
        <div class="pt-2">
            <button type="button" onclick="closeSubFeedback()" class="w-full py-2.5 px-5 bg-brand-accent hover:bg-amber-700 text-white font-semibold rounded-lg text-xs sm:text-sm transition-colors">
                Got It
            </button>
        </div>
    </div>
</div>

<!-- Standardized Footer -->
<footer class="no-print bg-slate-950 text-slate-400 py-12 border-t border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div class="flex flex-col md:flex-row justify-between items-center gap-6">
            <div>
                <a href="/" class="text-lg font-serif font-semibold text-white tracking-tight">David G. Smith</a>
                <p class="text-xs text-slate-500 mt-1">Data Scientist, Technical Architect &amp; Author &bull; Washington, DC</p>
            </div>
            <div class="flex flex-wrap justify-center gap-6 text-xs font-medium text-slate-300">
                <a href="/#about" class="hover:text-amber-400 transition-colors">About</a>
                <a href="/#work" class="hover:text-amber-400 transition-colors">Work</a>
                <a href="/cloud-native-geospatial-stack.html" class="hover:text-amber-400 transition-colors">Geo &amp; DuckDB Hub</a>
                <a href="/thoughts.html" class="hover:text-amber-400 transition-colors">Thoughts</a>
                <a href="/books.html" data-book-funnel="thoughts_footer_books" class="hover:text-amber-400 transition-colors">Books</a>
                <a href="/critical-thinking.html" data-book-funnel="thoughts_footer_ct" class="hover:text-amber-400 transition-colors">Critical Thinking</a>
                <a href="/rss.xml" class="hover:text-amber-400 transition-colors">RSS</a>
                <a href="/#contact" class="hover:text-amber-400 transition-colors">Contact</a>
            </div>
        </div>
        <div class="pt-6 border-t border-slate-900 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
            <div>&copy; <span id="year"></span> David G. Smith. All rights reserved.</div>
            <div class="flex flex-wrap justify-center gap-4">
                <a href="https://www.linkedin.com/in/davidgsmith" target="_blank" rel="noopener noreferrer" class="hover:text-slate-300 transition-colors">LinkedIn</a>
                <a href="https://www.amazon.com/stores/David-G-Smith/author/B0HH5CQD2F" target="_blank" rel="noopener noreferrer" class="hover:text-slate-300 transition-colors">Amazon Author</a>
                <a href="https://www.goodreads.com/author/show/72277946.David_G_Smith" target="_blank" rel="noopener noreferrer" class="hover:text-slate-300 transition-colors">Goodreads</a>
                <a href="https://www.bookbub.com/authors/david-g-smith-fa581830-75e6-4711-99c6-5a145a2ec887" target="_blank" rel="noopener noreferrer" class="hover:text-slate-300 transition-colors">BookBub</a>
            </div>
        </div>
    </div>
</footer>

<button id="return-to-top" aria-label="Return to top" class="no-print fixed bottom-6 right-6 z-40 bg-slate-900 border border-slate-700 text-white p-3 rounded-full shadow-lg hover:bg-brand-accent hover:border-brand-accent transition-all opacity-0 pointer-events-none focus:outline-none">
    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
    </svg>
</button>

<script>
    document.getElementById('year').textContent = new Date().getFullYear();
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');
    const mobileLinks = document.querySelectorAll('.mobile-link');
    if (btn && menu && !btn.dataset.navBound) {{
        btn.dataset.navBound = 'true';
        btn.addEventListener('click', () => {{
            const isHidden = menu.classList.toggle('hidden');
            btn.setAttribute('aria-expanded', String(!isHidden));
        }});
        mobileLinks.forEach(link => link.addEventListener('click', () => {{
            menu.classList.add('hidden');
            btn.setAttribute('aria-expanded', 'false');
        }}));
    }}

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

    // Auto-trigger clean print dialog if opened from the feed with ?print=1
    if (new URLSearchParams(window.location.search).get('print') === '1') {{
        window.addEventListener('load', () => setTimeout(() => window.print(), 350));
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
            s2.src = "https://cdn.jsdelivr.net/npm/vanta@0.5.24/dist/vanta.net.min.js";
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

def generate_image_index():
    images_dir = THOUGHTS_DIR / "images"
    if not images_dir.exists():
        return
    
    images = []
    # Sort files by modified time (newest first)
    for filepath in sorted(images_dir.glob("*.*"), key=os.path.getmtime, reverse=True):
        if filepath.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif']:
            images.append({
                "name": filepath.name,
                "url": f"https://davidgsmith.net/thoughts/images/{urllib.parse.quote(filepath.name)}"
            })
            
    with open(BASE_DIR / "images-index.json", "w", encoding="utf-8") as f:
        json.dump(images, f)


def generate_rss(posts):
    last_build_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    rss_items = []
    
    for post in posts:
            slug = post["_slug"]
            pub_date = post["_dt"].strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            html_body = render_markdown(post.get("body", ""))
            html_body = sanitize_feed_text(html_body)
            html_body = html_body.replace("]]>", "]]]]><![CDATA[>")
            
            excerpt = html.escape(create_text_excerpt(html_body))
            safe_title = html.escape(sanitize_feed_text(post.get("title", "")))
            
            # Identify true post image to avoid using the OG default portrait in the RSS feed
            media_tag = ""
            img_src = post.get("image")
            if not img_src:
                match = re.search(r'!\[.*?\]\((https?://[^\s\)]+|/[^\s\)]+)\)', post.get("body", ""))
                if match:
                    img_src = match.group(1)
                    
            if img_src:
                full_img_url = img_src if img_src.startswith("http") else f"https://davidgsmith.net{img_src}"
                # Use media:thumbnail instead of media:content to prevent inline duplication
                media_tag = f'\n            <media:thumbnail url="{html.escape(full_img_url)}" />'
            
            categories = "\n            ".join([
                f"<category>{html.escape(tag)}</category>" 
                for tag in post.get("tags", [])
            ])

            rss_items.append(f"""
            <item>
                <title>{safe_title}</title>
                <link>https://davidgsmith.net/thoughts/{slug}.html</link>
                <guid>https://davidgsmith.net/thoughts/{slug}.html</guid>
                <pubDate>{pub_date}</pubDate>
                <dc:creator>David G. Smith</dc:creator>
                <description>{excerpt}</description>
                {categories}{media_tag}
                <content:encoded><![CDATA[{html_body}]]></content:encoded>
            </item>""")
        
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/">
        <channel>
            <title>Thoughts &amp; Insights — David G. Smith</title>
            <link>https://davidgsmith.net/thoughts.html</link>
            <description>Latest perspectives on technical architecture, enterprise data, and critical thinking.</description>
            <language>en-US</language>
            <lastBuildDate>{last_build_date}</lastBuildDate>
            <managingEditor>d.smith.publishing@gmail.com (David G. Smith)</managingEditor>
            <webMaster>d.smith.publishing@gmail.com (David G. Smith)</webMaster>
            <atom:author>
                <atom:name>David G. Smith</atom:name>
                <atom:email>d.smith.publishing@gmail.com</atom:email>
                <atom:uri>https://davidgsmith.net/</atom:uri>
            </atom:author>
            <atom:link href="https://davidgsmith.net/rss.xml" rel="self" type="application/rss+xml" />
            <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
            {''.join(rss_items)}
        </channel>
        </rss>"""
    
    with open(BASE_DIR / "rss.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed.strip())

def generate_sitemap(posts, tag_slugs, month_slugs):
    # Only indexable HTML endpoints
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
    <loc>https://davidgsmith.net/cloud-native-geospatial-stack.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.95</priority>
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
  </url>"""
    ]
    
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

def cleanup_stale_pages():
    THOUGHTS_DIR.mkdir(exist_ok=True)
    
    # Safely remove ONLY generated HTML files, preserving thoughts/images/
    for filepath in THOUGHTS_DIR.glob("*.html"):
        filepath.unlink()
        
    # Remove dynamically generated taxonomy/date root HTML files
    for filepath in BASE_DIR.glob("thoughts-*.html"):
        filepath.unlink()

def generate_post_index(posts):
    index_data = []
    for post in posts:
        index_data.append({
            "title": post.get("title", "Untitled"),
            "date": post.get("date"),
            "tags": post.get("tags", []),
            "type": post.get("type"),
            "url": post.get("url", "")
            # Body is intentionally excluded to keep the index tiny
        })
    with open(BASE_DIR / "post-index.json", "w", encoding="utf-8") as f:
        json.dump(index_data, f)


def inject_geospatial_pillar_posts(posts):
    pillar_path = BASE_DIR / "cloud-native-geospatial-stack.html"
    if not pillar_path.exists():
        return

    geo_posts = [
        p for p in posts
        if set(p.get("tags", [])).intersection(GEOSPATIAL_CLUSTER_TAGS)
    ][:9]

    cards_html = ""
    for p in geo_posts:
        slug = p["_slug"]
        title = html.escape(p.get("title", "Untitled"))
        date_str = p["_dt"].strftime("%b %d, %Y")
        body_html = render_markdown(p.get("body", ""))
        excerpt = html.escape(create_text_excerpt(body_html, max_length=220))
        reading_time = calculate_reading_time(p.get("body", ""))

        tags_html = ""
        for tag in p.get("tags", [])[:3]:
            t_slug = slugify(tag)
            tags_html += f'<a href="/thoughts-{t_slug}.html" class="inline-block px-2 py-0.5 mr-1.5 mb-2 text-[10px] font-semibold text-sky-300 bg-slate-800 border border-slate-700 rounded hover:text-white hover:border-brand-accent transition-colors">{html.escape(tag)}</a>'

        cards_html += f"""
                <article class="bg-slate-900/90 border border-slate-800 rounded-xl p-6 flex flex-col shadow-xl hover:border-amber-500/50 transition-all">
                    <div class="flex items-center justify-between text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        <span>{date_str}</span>
                        <span class="text-amber-400 font-mono">{reading_time}</span>
                    </div>
                    <h3 class="text-lg font-serif font-medium text-white mb-2 leading-snug">
                        <a href="/thoughts/{slug}.html" class="hover:text-amber-400 transition-colors">{title}</a>
                    </h3>
                    <div class="flex flex-wrap mb-2">{tags_html}</div>
                    <p class="text-sm text-slate-300 mb-5 flex-grow line-clamp-3">{excerpt}</p>
                    <a href="/thoughts/{slug}.html" class="text-xs font-semibold text-amber-400 hover:text-amber-300 mt-auto uppercase tracking-wide">Read Architecture Note &rarr;</a>
                </article>"""

    with open(pillar_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!-- GEOSPATIAL_POSTS_INJECT_START -->).*?(<!-- GEOSPATIAL_POSTS_INJECT_END -->)"
    if re.search(pattern, content, flags=re.DOTALL):
        updated_content = re.sub(
            pattern,
            lambda match: f"{match.group(1)}\n{cards_html}\n                {match.group(2)}",
            content,
            flags=re.DOTALL
        )
        with open(pillar_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"✓ Successfully injected {len(geo_posts)} geospatial/DuckDB posts into {pillar_path.name}")

def generate_html():
    # Purge old generated pages to prevent stale records from surviving
    cleanup_stale_pages()
    
    posts = load_posts()
    inject_homepage_posts(posts)
    inject_geospatial_pillar_posts(posts)
    
    # Generate the new static post index for the editor
    generate_post_index(posts)
    
    all_tags = set()
    # Ensure the root homepage is included since latest posts are injected into it
    generated_urls = [
        "https://davidgsmith.net/",
        "https://davidgsmith.net/thoughts.html",
        "https://davidgsmith.net/rss.xml"
    ]
    
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

        json_ld_script = get_json_ld(
            collection_url=canonical,
            collection_name=f"Articles on {tag} — David G. Smith",
            collection_desc=description,
            topic_name=tag
        )

        page_html = wrap_with_layout(
            f"Posts tagged '{tag}' — David G. Smith",
            main_content,
            nav_rail,
            json_ld=json_ld_script,
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

        json_ld_script = get_json_ld(
            collection_url=canonical,
            collection_name="Untagged Posts — David G. Smith",
            collection_desc=description
        )

        page_html = wrap_with_layout(
            "Untagged Posts — David G. Smith",
            main_content,
            nav_rail,
            json_ld=json_ld_script,
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

        json_ld_script = get_json_ld(
            collection_url=canonical,
            collection_name=f"Posts from {m_full} {year} — David G. Smith",
            collection_desc=description
        )

        page_html = wrap_with_layout(
            f"Posts from {m_full} {year} — David G. Smith",
            main_content,
            nav_rail,
            json_ld=json_ld_script,
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
    # Submit only recently changed/injected pages to IndexNow instead of the entire archive
    recent_slugs = [p["_slug"] for p in posts[:3]]
    targeted_urls = [
        "https://davidgsmith.net/",
        "https://davidgsmith.net/thoughts.html",
        "https://davidgsmith.net/rss.xml",
    ] + [f"https://davidgsmith.net/thoughts/{s}.html" for s in recent_slugs]

    return targeted_urls
            
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

def inject_homepage_posts(posts):
    # Auto-detect index.html or alternative filenames in root
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        alt_path = BASE_DIR / "index_2.html"
        if alt_path.exists():
            index_path = alt_path
        else:
            print(f"⚠ Warning: Neither 'index.html' nor 'index_2.html' was found in {BASE_DIR}.")
            return
        
    recent_posts = posts[:3]
    cards_html = ""
    
    for p in recent_posts:
        slug = p["_slug"]
        title = html.escape(p.get("title", "Untitled"))
        date_str = p["_dt"].strftime("%b %d, %Y")
        body_html = render_markdown(p.get("body", ""))
        excerpt = html.escape(create_text_excerpt(body_html, max_length=350))
        
        tags_html = ""
        for tag in p.get("tags", [])[:2]:
            t_slug = slugify(tag)
            tags_html += f'<a href="/thoughts-{t_slug}.html" class="inline-block px-2 py-0.5 mr-1.5 mb-3 text-[10px] font-semibold text-slate-300 bg-slate-800 border border-slate-700 rounded hover:text-white hover:border-brand-accent transition-colors">{html.escape(tag)}</a>'
        
        tags_container = f'<div class="flex flex-wrap">{tags_html}</div>' if tags_html else ""
        
        cards_html += f"""
                <article class="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col shadow-xl hover:border-slate-700 transition-colors">
                    <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">{date_str}</span>
                    <h3 class="text-lg font-serif font-medium text-white mb-2 leading-snug">
                        <a href="thoughts/{slug}.html" class="hover:text-brand-accent transition-colors">{title}</a>
                    </h3>
                    {tags_container}
                    <p class="text-sm text-gray-400 mb-5 flex-grow line-clamp-4">{excerpt}</p>
                    <a href="thoughts/{slug}.html" class="text-xs font-semibold text-brand-accent hover:text-amber-500 mt-auto uppercase tracking-wide">Read More &rarr;</a>
                </article>"""

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!-- LATEST_POSTS_INJECT_START -->).*?(<!-- LATEST_POSTS_INJECT_END -->)"
    
    if not re.search(pattern, content, flags=re.DOTALL):
        print("⚠ Warning: Could not find the <!-- LATEST_POSTS_INJECT_START --> markers in the HTML.")
        return
        
    updated_content = re.sub(
        pattern, 
        lambda match: f"{match.group(1)}\n{cards_html}\n                {match.group(2)}", 
        content, 
        flags=re.DOTALL
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
        
    print(f"✓ Successfully injected {len(recent_posts)} recent posts with tags into {index_path.name}")


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
    generate_image_index()
    ping_websub_hub()
    notify_indexnow(urls)
    print("Successfully built thoughts, aggregators, sitemap.xml, and RSS feed.")