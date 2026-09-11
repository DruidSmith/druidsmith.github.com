import html
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

POSTS_FILE = Path("posts.json")

PLATFORM_ICONS = {
    "linkedin": "https://cdn.simpleicons.org/linkedin/0A66C2",
    "twitter": "https://cdn.simpleicons.org/x/111827",
    "facebook": "https://cdn.simpleicons.org/facebook/1877F2",
    "instagram": "https://cdn.simpleicons.org/instagram/E4405F",
    "youtube": "https://cdn.simpleicons.org/youtube/FF0000",
    "tiktok": "https://cdn.simpleicons.org/tiktok/111827",
    "threads": "https://cdn.simpleicons.org/threads/111827",
    "medium": "https://cdn.simpleicons.org/medium/111827",
    "github": "https://cdn.simpleicons.org/github/111827",
    "other": "https://cdn.simpleicons.org/link/6B7280",
}


def platform_for_url(url):
    hostname = urlparse(url).netloc.lower().removeprefix("www.")
    if "linkedin.com" in hostname:
        return "linkedin"
    if hostname in {"twitter.com", "x.com"}:
        return "twitter"
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


def render_post(post):
    title = html.escape(post.get("title", "Untitled"))
    body = html.escape(post.get("body", ""))
    url = html.escape(post["url"], quote=True)
    date = datetime.fromisoformat(post["date"].replace("Z", "+00:00")).strftime("%B %d, %Y")
    platform = post.get("platform") or platform_for_url(post["url"])
    icon = PLATFORM_ICONS.get(platform, PLATFORM_ICONS["other"])
    label = platform.title() if platform != "twitter" else "X / Twitter"
    return f"""
        <article class="group bg-white p-8 border border-gray-200 rounded shadow-sm hover:shadow-md transition-shadow">
            <div class="flex items-center gap-2 text-sm text-gray-400 mb-4">
                <img src="{icon}" alt="" class="h-4 w-4" loading="lazy">
                <span>{date} &bull; {html.escape(label)}</span>
            </div>
            <h2 class="text-xl font-serif font-medium text-brand-dark group-hover:text-brand-accent transition-colors mb-3">{title}</h2>
            <p class="text-gray-600 leading-relaxed text-sm whitespace-pre-wrap">{body}</p>
            <a href="{url}" target="_blank" rel="noopener noreferrer" class="mt-5 inline-block text-sm font-medium text-brand-dark border-b border-gray-300 hover:border-brand-dark transition-colors pb-1">Original post &rarr;</a>
        </article>
        """


def generate_html():
    posts_html = "\n".join(render_post(post) for post in load_posts())
    if not posts_html:
        posts_html = '<p class="text-gray-500 text-center py-12">New thoughts will appear here soon.</p>'

    html_template = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Thoughts & Insights — David G. Smith</title>
<meta name="description" content="Latest writing and insights on data science, technology modernization, and critical thinking from David G. Smith.">
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
    body {{ background-color: #fcfcfc; }}
    .glass-nav {{ background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }}
</style>
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