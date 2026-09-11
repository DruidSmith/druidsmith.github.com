import html
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

POSTS_FILE = Path("posts.json")

PLATFORM_ICONS = {
    "linkedin": "/images/InBug-Black.png",  # local, reliable
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


def platform_for_url(url):
    hostname = urlparse(url).netloc.lower().removeprefix("www.")

    if "linkedin.com" in hostname:
        return "linkedin"
    if hostname in {"twitter.com", "x.com"}:
        return "twitter"
    if "bsky.app" in hostname:
        return "bluesky"
    if "mastodon" in hostname or hostname.endswith(".social") or hostname.endswith(".io"):
        return "mastodon"

    for platform in ("facebook", "instagram", "youtube", "tiktok", "threads", "medium", "github"):
        if platform in hostname:
            return platform

    return "other"



def load_posts():
    if not POSTS_FILE.exists():
        return []
    with POSTS_FILE.open(encoding="utf-8") as posts_file:
        posts = json.load(posts_file)
    return sorted(posts, key=lambda post: post.get("date", ""), reverse=True)


def render_share_bar(url):
    escaped = html.escape(url, quote=True)
    return f"""
    <div class="absolute bottom-4 right-4 text-right">
        <p class="text-xs text-gray-400 mb-2">Share this post</p>
        <div class="flex gap-3 justify-end">
            <a href="https://www.linkedin.com/sharing/share-offsite/?url={escaped}"
               target="_blank" class="hover:text-brand-accent transition">
               <img src="/images/InBug-Black.png" class="h-5 w-5" alt="LinkedIn">
            </a>
            <a href="https://twitter.com/intent/tweet?url={escaped}"
               target="_blank" class="hover:text-brand-accent transition">
               <img src="https://unpkg.com/simple-icons/icons/x.svg" class="h-5 w-5" alt="X">
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={escaped}"
               target="_blank" class="hover:text-brand-accent transition">
               <img src="https://unpkg.com/simple-icons/icons/facebook.svg" class="h-5 w-5" alt="Facebook">
            </a>
            <a href="https://bsky.app/intent/share?url={escaped}"
               target="_blank" class="hover:text-brand-accent transition">
               <img src="https://unpkg.com/simple-icons/icons/bluesky.svg" class="h-5 w-5" alt="Bluesky">
            </a>
            <a href="https://mastodon.social/share?text={escaped}"
               target="_blank" class="hover:text-brand-accent transition">
               <img src="https://unpkg.com/simple-icons/icons/mastodon.svg" class="h-5 w-5" alt="Mastodon">
            </a>
        </div>
    </div>
    """



def render_post(post):
    title = html.escape(post.get("title", "Untitled"))
    body = html.escape(post.get("body", ""))
    url = html.escape(post["url"], quote=True)
    date_iso = post["date"]
    date = datetime.fromisoformat(date_iso.replace("Z", "+00:00")).strftime("%B %d, %Y")
    platform = post.get("platform") or platform_for_url(post["url"])
    icon = PLATFORM_ICONS.get(platform, PLATFORM_ICONS["other"])
    label = platform.title() if platform != "twitter" else "X / Twitter"

    json_ld = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      "headline": "{title}",
      "datePublished": "{date_iso}",
      "author": {{
        "@type": "Person",
        "name": "David G. Smith"
      }},
      "url": "{url}",
      "articleBody": "{body}"
    }}
    </script>
    """

    return f"""
        <article itemscope itemtype="https://schema.org/BlogPosting"
                 class="relative group bg-white p-8 border border-gray-200 rounded shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all">

            <div class="flex items-center gap-2 text-sm text-gray-400 mb-4">
                <img src="{icon}" alt="" class="h-4 w-4" loading="lazy">
                <span itemprop="datePublished">{date} &bull; {html.escape(label)}</span>
            </div>

            <h2 itemprop="headline"
                class="text-xl font-serif font-medium text-brand-dark group-hover:text-brand-accent transition-colors mb-3">
                {title}
            </h2>

            <p itemprop="articleBody"
               class="text-gray-600 leading-loose text-sm whitespace-pre-wrap">{body}</p>

            <a href="{url}" target="_blank" rel="noopener noreferrer"
               class="mt-5 inline-block text-sm font-medium text-brand-dark border-b border-gray-300 hover:border-brand-dark transition-colors pb-1">
               Original post &rarr;
            </a>

            {render_share_bar(post["url"])}
        </article>
    """


def generate_html():
    posts_html = "\n".join(render_post(post) for post in load_posts())
    if not posts_html:
        posts_html = '<p class="text-gray-500 text-center py-12">New thoughts will appear here soon.</p>'

    json_ld_blog = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Blog",
      "name": "Thoughts & Insights — David G. Smith",
      "url": "https://druidsmith.github.com/thoughts.html",
      "author": {
        "@type": "Person",
        "name": "David G. Smith"
      }
    }
    </script>
    """

    html_template = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Thoughts & Insights — David G. Smith</title>
<meta name="description" content="Latest writing and insights on data science, technology modernization, and critical thinking from David G. Smith.">

<link rel="canonical" href="https://druidsmith.github.com/thoughts.html">

<!-- OpenGraph -->
<meta property="og:title" content="Thoughts & Insights — David G. Smith">
<meta property="og:description" content="Latest writing and insights on data science, technology modernization, and critical thinking.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://druidsmith.github.com/thoughts.html">
<meta property="og:image" content="https://druidsmith.github.com/assets/og-default.jpg">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Thoughts & Insights — David G. Smith">
<meta name="twitter:description" content="Latest writing and insights on data science, technology modernization, and critical thinking.">
<meta name="twitter:image" content="https://druidsmith.github.com/assets/og-default.jpg">

<!-- Fonts -->
<link rel="preload" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap" as="style">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">

<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {{
        theme: {{
            extend: {{
                fontFamily: {{ sans: ['Inter', 'sans-serif'], serif: ['Lora', 'serif'] }},
                colors: {{
                    brand: {{ dark: '#111827', muted: '#374151', accent: '#b45309', light: '#f9fafb' }}
                }}
            }}
        }}
    }}
</script>

<style>
    body {{
        background: linear-gradient(to bottom, #faf9f7, #f3f2ee);
    }}
    .glass-nav {{
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }}
</style>

{json_ld_blog}
</head>

<body class="font-sans text-brand-muted antialiased selection:bg-brand-accent selection:text-white">
<nav class="fixed w-full z-50 glass-nav border-b border-gray-200 transition-all duration-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-20">
            <div class="flex-shrink-0">
                <a href="/" class="text-xl font-serif font-semibold text-brand-dark tracking-tight">David G. Smith</a>
            </div>
            <div class="hidden md:flex space-x-8 items-center">
                <a href="/#about" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">About</a>
                <a href="/#work" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">Work</a>
                <a href="thoughts.html" class="text-brand-accent transition-colors text-sm font-medium">Thoughts</a>
                <a href="/#books" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">Books</a>
                <a href="/#consulting" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">Consulting</a>
                <a href="/#contact" class="px-5 py-2 rounded border border-gray-300 text-brand-dark hover:border-brand-dark transition-all text-sm font-medium">Contact</a>
            </div>
        </div>
    </div>
</nav>

<header class="pt-32 pb-16 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto text-center border-b border-gray-100">
    <h1 class="text-4xl sm:text-5xl font-serif font-medium text-brand-dark mb-6">Thoughts & Insights</h1>
    <p class="text-lg text-gray-500 max-w-2xl mx-auto">Latest perspectives on technical architecture, enterprise data, and critical thinking.</p>
</header>

<section class="py-16 bg-brand-light min-h-screen">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 gap-8">
            {posts_html}
        </div>
    </div>
</section>

<footer class="bg-brand-dark text-gray-400 py-12 border-t border-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
        &copy; {datetime.now().year} David G. Smith. All rights reserved.
    </div>
</footer>
</body>
</html>"""

    with open("thoughts2.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_html()
    print("Successfully generated thoughts2.html from posts.json")
