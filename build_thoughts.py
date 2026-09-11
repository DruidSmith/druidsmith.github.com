import html
import json
import re
import bleach
import markdown
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

POSTS_FILE = Path("posts.json")

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


def render_markdown(text):
    rendered = markdown.markdown(
        text,
        extensions=["extra", "nl2br", "sane_lists"],
        output_format="html",
    )
    # Added img to the allowed tags to ensure markdown images render properly
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union({
        "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
        "blockquote", "pre", "code", "ul", "ol", "li", "strong", "em", "img"
    })
    # Safelisted img attributes for proper rendering
    allowed_attributes = {
        "a": ["href", "title", "target", "rel"], 
        "code": ["class"],
        "img": ["src", "alt", "title", "class", "loading"]
    }
    cleaned = bleach.clean(
        rendered,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    return re.sub(
        r'<a\b(?![^>]*\btarget=)',
        '<a target="_blank" rel="noopener noreferrer"',
        cleaned,
    )


def render_share_bar(url):
    escaped = html.escape(url, quote=True)
    # Refactored to a flex row to avoid absolute overlap issues and added aria-labels
    return f"""
    <div class="mt-8 pt-4 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-4">
        <a href="{escaped}" target="_blank" rel="noopener noreferrer"
           class="text-sm font-medium text-brand-accent hover:text-brand-dark transition-colors">
           Read Original &rarr;
        </a>
        <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400">Share:</span>
            <a href="https://www.linkedin.com/sharing/share-offsite/?url={escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on LinkedIn">
               <img src="/images/InBug-Black.png" class="h-5 w-5" alt="" aria-hidden="true">
            </a>
            <a href="https://twitter.com/intent/tweet?url={escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on X">
               <img src="https://unpkg.com/simple-icons/icons/x.svg" class="h-5 w-5" alt="" aria-hidden="true">
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on Facebook">
               <img src="https://unpkg.com/simple-icons/icons/facebook.svg" class="h-5 w-5" alt="" aria-hidden="true">
            </a>
            <a href="https://bsky.app/intent/share?url={escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on Bluesky">
               <img src="https://unpkg.com/simple-icons/icons/bluesky.svg" class="h-5 w-5" alt="" aria-hidden="true">
            </a>
            <a href="https://mastodon.social/share?text={escaped}"
               target="_blank" class="hover:text-brand-accent transition" aria-label="Share on Mastodon">
               <img src="https://unpkg.com/simple-icons/icons/mastodon.svg" class="h-5 w-5" alt="" aria-hidden="true">
            </a>
        </div>
    </div>
    """


def render_post(post):
    title = html.escape(post.get("title", "Untitled"))
    body_source = post.get("body", "")
    body = render_markdown(body_source)
    url = html.escape(post["url"], quote=True)
    date_iso = post["date"]
    date = datetime.fromisoformat(date_iso.replace("Z", "+00:00")).strftime("%B %d, %Y")
    platform = post.get("platform") or platform_for_url(post["url"])
    icon = PLATFORM_ICONS.get(platform, PLATFORM_ICONS["other"])
    label = platform.title() if platform != "twitter" else "X / Twitter"

    return f"""
        <article itemscope itemtype="https://schema.org/BlogPosting"
                 class="relative group bg-white p-8 border border-gray-200 rounded shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all">

            <div class="flex items-center gap-2 text-sm text-gray-400 mb-4">
                <img src="{icon}" alt="" aria-hidden="true" class="h-4 w-4" loading="lazy">
                <span itemprop="datePublished">{date} &bull; {html.escape(label)}</span>
            </div>

            <h2 itemprop="headline"
                class="text-xl font-serif font-medium text-brand-dark group-hover:text-brand-accent transition-colors mb-3">
                {title}
            </h2>

              <div itemprop="articleBody"
                  class="markdown-content text-gray-600 leading-relaxed text-sm">{body}</div>

            {render_share_bar(post["url"])}
        </article>
    """


def generate_html():
    posts = load_posts()
    posts_html = "\n".join(render_post(post) for post in posts)
    if not posts_html:
        posts_html = '<p class="text-gray-500 text-center py-12">New thoughts will appear here soon.</p>'

    # Dynamically build the BlogPosting objects for the JSON-LD graph
    blog_postings_json = []
    for i, post in enumerate(posts):
        title = post.get("title", "Untitled")
        date_iso = post["date"]
        url = post["url"]
        blog_postings_json.append(f"""
        {{
          "@type": "BlogPosting",
          "@id": "https://druidsmith.github.com/thoughts.html#post-{i}",
          "headline": {json.dumps(title)},
          "datePublished": "{date_iso}",
          "author": {{
            "@id": "https://druidsmith.github.com/#davidgsmith"
          }},
          "isPartOf": {{
            "@id": "https://druidsmith.github.com/thoughts.html#blog"
          }},
          "url": {json.dumps(url)}
        }}""")

    blog_postings_str = ",\n".join(blog_postings_json)
    comma = "," if blog_postings_str else ""

    # Comprehensive JSON-LD Graph for SEO
    json_ld_graph = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@graph": [
        {{
          "@type": "Person",
          "@id": "https://druidsmith.github.com/#davidgsmith",
          "name": "David G. Smith",
          "jobTitle": "Solutions Architect & Data Scientist",
          "url": "https://druidsmith.github.com",
          "sameAs": [
            "https://www.linkedin.com/in/davidgsmith",
            "https://github.com/druidsmith"
          ],
          "knowsAbout": ["Data Science", "Solutions Architecture", "Critical Thinking", "Cognitive Biases"]
        }},
        {{
          "@type": "Blog",
          "@id": "https://druidsmith.github.com/thoughts.html#blog",
          "name": "Thoughts & Insights — David G. Smith",
          "description": "Latest perspectives on technical architecture, enterprise data, and critical thinking.",
          "publisher": {{
            "@id": "https://druidsmith.github.com/#davidgsmith"
          }}
        }}{comma}
        {blog_postings_str}
      ]
    }}
    </script>
    """

    html_template = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Thoughts & Insights — David G. Smith</title>
<meta name="description" content="Read the latest insights from David G. Smith on data science, federal IT modernization, solutions architecture, and applied critical thinking.">

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
    .markdown-content p {{ margin-bottom: 1rem; }}
    .markdown-content p:last-child {{ margin-bottom: 0; }}
    
    /* Clean up empty paragraphs emitted by Markdown */
    .markdown-content p:empty {{ display: none; }}
    
    .markdown-content h1, .markdown-content h2, .markdown-content h3 {{
        color: #111827;
        font-family: Lora, serif;
        font-weight: 500;
        margin: 1.25rem 0 0.5rem;
    }}
    /* Demoted H1 so it doesn't compete with the Page header */
    .markdown-content h1 {{ font-size: 1.25rem; }}
    .markdown-content h2 {{ font-size: 1.125rem; }}
    .markdown-content h3 {{ font-size: 1rem; }}
    .markdown-content ul, .markdown-content ol {{ margin: 0 0 1rem 1.25rem; }}
    .markdown-content ul {{ list-style: disc; }}
    .markdown-content ol {{ list-style: decimal; }}
    .markdown-content blockquote {{ border-left: 3px solid #b45309; color: #4b5563; margin: 1rem 0; padding-left: 1rem; }}
    .markdown-content a {{ color: #92400e; text-decoration: underline; }}
    .markdown-content code {{ background: #f3f4f6; border-radius: 0.25rem; padding: 0.1rem 0.25rem; }}
    .markdown-content pre {{ background: #f3f4f6; border-radius: 0.25rem; margin: 1rem 0; overflow-x: auto; padding: 1rem; }}
    .markdown-content pre code {{ background: transparent; padding: 0; }}
</style>

{json_ld_graph}
</head>

<body class="font-sans text-brand-muted antialiased selection:bg-brand-accent selection:text-white">

<!-- Accessibility Skip Link -->
<a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-brand-dark text-white px-4 py-2 rounded z-[100]">Skip to content</a>

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
                <a href="/#advisory" class="text-gray-600 hover:text-brand-accent transition-colors text-sm font-medium">Advisory</a>
                <a href="/#contact" class="px-5 py-2 rounded border border-gray-300 text-brand-dark hover:border-brand-dark transition-all text-sm font-medium">Contact</a>
            </div>
        </div>
    </div>
</nav>

<header class="pt-32 pb-16 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto text-center border-b border-gray-100">
    <h1 class="text-4xl sm:text-5xl font-serif font-medium text-brand-dark mb-6">Thoughts & Insights</h1>
    <p class="text-lg text-gray-500 max-w-2xl mx-auto">Latest perspectives on technical architecture, enterprise data, and critical thinking.</p>
</header>

<!-- Restructured as MAIN block -->
<main id="main-content" class="py-16 bg-brand-light min-h-screen">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 gap-8">
            {posts_html}
        </div>
    </div>
</main>

<footer class="bg-brand-dark text-gray-400 py-12 border-t border-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
        &copy; {datetime.now().year} David G. Smith. All rights reserved.
    </div>
</footer>

<!-- Floating Back to Top Button -->
<button id="bttButton" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})" class="fixed bottom-8 right-8 bg-brand-accent text-white p-3 rounded-full shadow-lg opacity-0 pointer-events-none transition-opacity duration-300 hover:bg-brand-dark z-50" aria-label="Back to top">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path></svg>
</button>
<script>
    window.addEventListener('scroll', () => {{
        const btt = document.getElementById('bttButton');
        if (window.scrollY > 300) {{
            btt.classList.remove('opacity-0', 'pointer-events-none');
            btt.classList.add('opacity-100', 'pointer-events-auto');
        }} else {{
            btt.classList.add('opacity-0', 'pointer-events-none');
            btt.classList.remove('opacity-100', 'pointer-events-auto');
        }}
    }});
</script>

</body>
</html>"""

    with open("thoughts.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_html()
    print("Successfully generated thoughts.html from posts.json")