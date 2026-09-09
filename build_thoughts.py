import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

RSS_URL = 'https://rss.app/feeds/YuGr16MsXmjBoomz.xml'
POST_LIMIT = 8

def clean_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ")
    return text[:210] + "..." if len(text) > 180 else text

def generate_html():
    feed = feedparser.parse(RSS_URL)
    
    posts_html = ""
    for entry in feed.entries[:POST_LIMIT]:
        # Parse standard RSS dates
        try:
            dt = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
            date_str = dt.strftime("%B %d, %Y")
        except:
            date_str = entry.published

        description = clean_text(entry.description)
        
        posts_html += f"""
        <article class="group bg-white p-8 border border-gray-200 rounded shadow-sm hover:shadow-md transition-shadow">
            <span class="text-sm text-gray-400 mb-2 block">{date_str} • LinkedIn</span>
            <a href="{entry.link}" target="_blank" class="block">
                <h4 class="text-xl font-serif font-medium text-brand-dark group-hover:text-brand-accent transition-colors mb-3">
                    {entry.title}
                </h4>
                <p class="text-gray-600 leading-relaxed text-sm">
                    {description}
                </p>
            </a>
            <a href="{entry.link}" target="_blank" class="mt-4 inline-block text-sm font-medium text-brand-dark border-b border-gray-300 hover:border-brand-dark transition-colors pb-1">Read Post &rarr;</a>
        </article>
        """

    # HTML Template matching your index.html styling
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

    with open("thoughts.html", "w", encoding="utf-8") as f:
        f.write(html_template)
        
if __name__ == "__main__":
    generate_html()
    print("Successfully generated thoughts.html")