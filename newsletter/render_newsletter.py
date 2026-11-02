import urllib.parse
from jinja2 import Environment, FileSystemLoader

def render_newsletter(template_path: str, context: dict, is_email: bool = True) -> str:
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_path)

    # Pre-encode URL and Title for email-safe UTM social sharing
    canonical_url = context["canonical_url"]
    share_title = f"{context['newsletter_title']} (Issue #{context['issue_number']}) — {context['author_name']}"

    render_ctx = {
        **context,
        "is_email_delivery": is_email,
        "utm_medium": "email" if is_email else "web",
        "encoded_canonical_url": urllib.parse.quote(canonical_url, safe=""),
        "encoded_share_title": urllib.parse.quote(share_title, safe=""),
    }
    return template.render(**render_ctx)

# Example Payload Structure
sample_context = {
    "newsletter_name": "The Spatial & Data Architecture Dispatch",
    "newsletter_title": "You're Not Too Old For This & Cloud-Native GeoAI",
    "newsletter_kicker": "Weekly Briefing & Reference Hub",
    "newsletter_tagline": "Curated cloud-native geospatial essays, AI research papers, and engineering leadership.",
    "author_name": "David G. Smith",
    "publisher_or_company_name": "David G. Smith",
    "volume_number": "1",
    "issue_number": "42",
    "issue_date": "October 28, 2026",
    "canonical_url": "https://davidgsmith.net/newsletter/issue-42.html",
    "archive_url": "https://davidgsmith.net/thoughts.html",
    "rss_url": "https://davidgsmith.net/rss.xml",
    "editorial_opening_text": "Welcome to this week's briefing. We are looking at why curiosity has no expiration date in tech, alongside three pivotal papers on spatial indexing.",
    "original_posts": [
        {
            "title": "You're Not Too Old For This",
            "url": "https://davidgsmith.net/thoughts/youre-not-too-old-for-this.html",
            "image_url": "https://davidgsmith.net/thoughts/images/not-too-old-mvri1yrs-b358bbd3.jpg",
            "date": "October 28, 2026",
            "read_time": "4 min",
            "tags": ["Critical Thinking", "Future of Work", "Engineering Leadership"],
            "excerpt": "Somewhere along the way, a lot of us picked up the idea that understanding technology is something you either have by a certain age or you don't. Here is why curiosity doesn't have an expiration date."
        }
    ],
    "external_blogs": [
        {
            "source_name": "Wizard Zines",
            "title": "How Containers & Networking Actually Work Underneath",
            "url": "https://wizardzines.com/",
            "summary": "A playful, visual breakdown of Linux namespaces and networking fundamentals that demystifies container abstractions."
        }
    ],
    "news_items": [
        {
            "title": "DuckDB Spatial Extension Adds Native GeoParquet 1.1 Pushdown",
            "url": "https://duckdb.org/",
            "summary": "Bounding-box filter pushdown reduces cloud object storage reads by up to 80%.",
            "source": "DuckDB Blog",
            "time_ago": "2 days ago"
        }
    ],
    "research_papers": [
        {
            "title": "Adaptive Hierarchical Indexing for Petabyte-Scale Vector Cubes",
            "url": "https://arxiv.org/",
            "authors": "Chen et al.",
            "year": "2026",
            "key_finding": "Reduces spatial join latency by 3.4x over standard R-tree partitioning on object storage."
        }
    ],
    "featured_creator": {
        "name": "Julia Evans",
        "platform_type": "Technical Zines & Blog",
        "description": "Creator of Wizard Zines, turning intimidating systems programming and debugging topics into approachable illustrations.",
        "url": "https://wizardzines.com/"
    },
    "learning_resources": [
        {
            "title": "CS50's Introduction to Computer Science",
            "type": "Free Course",
            "provider": "Harvard OpenCourseWare",
            "url": "https://cs50.harvard.edu/x/"
        },
        {
            "title": "MIT OpenCourseWare Systems Engineering",
            "type": "Lecture Series",
            "provider": "MIT OCW",
            "url": "https://ocw.mit.edu/"
        }
    ],
    "events_list": [
        {
            "date": "Nov 14, 2026",
            "name": "Cloud-Native Geospatial Outreach Day",
            "location": "Reston, VA & Virtual",
            "url": "https://davidgsmith.net/"
        }
    ],
    "social_links": {
        "twitter": "https://twitter.com/",
        "linkedin": "https://www.linkedin.com/",
        "github": "https://github.com/",
        "bluesky": "https://bsky.app/"
    },
    "current_year": "2026",
    "physical_publishing_address": "Washington, D.C. Metro Area, USA",
    "unsubscribe_url": "https://davidgsmith.net/unsubscribe",
    "manage_preferences_url": "https://davidgsmith.net/preferences",
    "privacy_policy_url": "https://davidgsmith.net/privacy.html"
}

# Render Email HTML (hides web-only JS buttons, sets utm_medium=email)
email_html = render_newsletter("newsletter_template.html", sample_context, is_email=True)

# Render Web Archive HTML (enables Print & Copy Link buttons + analytics script, sets utm_medium=web)
web_html = render_newsletter("newsletter_template.html", sample_context, is_email=False)