[Personal Website for David G. Smith](https://davidgsmith.net "Personal Page")

## Private posting

`thoughts2.html` is generated from `posts.json` by `build_thoughts.py`. The workflow in `.github/workflows/linkedin.yml` runs when `posts.json` changes, on a daily schedule, or manually. The old LinkedIn API fetch is no longer part of this publishing path.

GitHub Pages cannot securely protect a password or write to a repository by itself. `posting.html` therefore expects an authenticated HTTPS endpoint:

1. Deploy `posting-worker.js` as a Cloudflare Worker.
2. Set Worker secrets `POSTING_PASSWORD`, `POSTING_SESSION_SECRET`, and `GITHUB_TOKEN`.
3. Set Worker variables `GITHUB_OWNER`, `GITHUB_REPOSITORY`, and optionally `GITHUB_BRANCH`.
4. Give the fine-grained `GITHUB_TOKEN` Contents: Read and write access to this repository only.
5. Set `window.POSTING_CONFIG.endpoint` in `posting.html` to the Worker URL.

The Worker returns a short-lived signed session after login, validates the title, body, and URL, detects the platform, timestamps the post, and commits the updated JSON file. Never put a GitHub token or the posting password in this repository or in browser storage.