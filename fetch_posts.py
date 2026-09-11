import os
import sys
from datetime import datetime
from linkedin_api import Linkedin

def main():
    # Pull the session cookie from GitHub Secrets
    li_at_cookie = os.environ.get('LINKEDIN_LI_AT')
    username = 'davidgsmith'

    if not li_at_cookie:
        print("Error: LINKEDIN_LI_AT environment variable not found.")
        sys.exit(1)

    # Authenticate using the session cookie to bypass datacenter IP blocks
    try:
        api = Linkedin('', '', cookies={'li_at': li_at_cookie})
        # Fetch the last 12 posts
        posts = api.get_profile_posts(username, post_count=12)
    except Exception as e:
        print(f"Authentication failed (likely expired cookie). Error: {e}")
        sys.exit(1) # Forces the GitHub Action to fail and trigger your email alert

    # Setup the HTML shell with Tailwind
    # NOTE: Standard string here (no 'f' prefix), so we use standard single { } for CSS/JS
    html_content = """
    <!DOCTYPE html>
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
    tailwind.config = {
        theme: {
            extend: {
                fontFamily: { sans: ['Inter', 'sans-serif'], serif: ['Lora', 'serif'] },
                colors: {
                    brand: { dark: '#111827', muted: '#374151', accent: '#b45309', light: '#f9fafb' }
                }
            }
        }
    }
</script>
<style>
    body { background-color: #fcfcfc; }
    .glass-nav { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
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
    """

    for post in posts:
        # Voyager API payloads are deeply nested and occasionally change. 
        # This checks the two most common locations for post text.
        text = "No text content found."
        try:
            if 'commentary' in post:
                text = post['commentary'].get('text', {}).get('text', '')
            elif 'summary' in post:
                text = post['summary'].get('text', '')
        except Exception:
            pass
        
        # Build the Tailwind card (f-string used here)
        html_content += f"""
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <p class="text-slate-700 whitespace-pre-wrap">{text}</p>
                <div class="mt-4 pt-4 border-t border-slate-100">
                    <a href="https://www.linkedin.com/in/{username}/recent-activity/all/" 
                       class="text-sm text-blue-600 hover:text-blue-800 font-medium" 
                       target="_blank">
                       View on LinkedIn &rarr;
                    </a>
                </div>
            </div>
        """

    # NOTE: Added 'f' prefix here so datetime evaluates properly
    html_content += f"""
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

    # Write the output file
    with open('thoughts2.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Successfully generated thoughts2.html with the latest posts.")

if __name__ == "__main__":
    main()