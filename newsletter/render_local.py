from pathlib import Path
from render_newsletter import render_newsletter, sample_context

# Assuming render_newsletter() and sample_context are defined above
output_dir = Path("dist")
output_dir.mkdir(exist_ok=True)

# 1. Generate the Email-Safe HTML (strips JS & web-only buttons, sets utm_medium=email)
email_html = render_newsletter("newsletter_template.html", sample_context, is_email=True)
(output_dir / "issue-42-email.html").write_text(email_html, encoding="utf-8")

# 2. Generate the Website HTML (enables Print/Copy buttons & GA/Plausible tracking, sets utm_medium=web)
web_html = render_newsletter("newsletter_template.html", sample_context, is_email=False)
(output_dir / "issue-42-web.html").write_text(web_html, encoding="utf-8")

print("Rendered dist/issue-42-email.html and dist/issue-42-web.html successfully.")