// posting-worker.js
const encoder = new TextEncoder();
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Allow-Methods": "POST, OPTIONS, GET",
  "Access-Control-Max-Age": "86400"
};

function response(body, status = 200) {
  return new Response(JSON.stringify(body), { 
    status, 
    headers: { ...cors, "Content-Type": "application/json" } 
  });
}

function base64Url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

async function sign(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw", 
    encoder.encode(secret), 
    { name: "HMAC", hash: "SHA-256" }, 
    false, 
    ["sign", "verify"]
  );
  return base64Url(await crypto.subtle.sign("HMAC", key, encoder.encode(value)));
}

async function createSession(env) {
  const expires = Date.now() + 60 * 60 * 1000;
  const value = `${expires}.${crypto.randomUUID()}`;
  return `${value}.${await sign(value, env.POSTING_SESSION_SECRET)}`;
}

async function validSession(request, env) {
  const token = request.headers.get("Authorization")?.replace(/^Bearer\s+/i, "");
  if (!token) return false;
  const parts = token.split(".");
  if (parts.length !== 3 || Number(parts[0]) < Date.now()) return false;
  return parts[2] === await sign(`${parts[0]}.${parts[1]}`, env.POSTING_SESSION_SECRET);
}

function platformForUrl(value) {
  if (!value) return "post";
  try {
    const hostname = new URL(value).hostname.replace(/^www\./, "").toLowerCase();
    if (hostname.includes("davidgsmith.net")) return "post";
    if (hostname.includes("linkedin.com")) return "linkedin";
    if (hostname === "twitter.com" || hostname === "x.com") return "twitter";
    for (const name of ["facebook", "instagram", "youtube", "tiktok", "threads", "medium", "github"]) {
      if (hostname.includes(name)) return name;
    }
    return "other";
  } catch {
    return "post";
  }
}

function decodeContent(value) {
  return new TextDecoder().decode(Uint8Array.from(atob(value.replace(/\s/g, "")), (c) => c.charCodeAt(0)));
}

function encodeContent(value) {
  return btoa(String.fromCharCode(...encoder.encode(value)));
}

function encodeBytes(bytes) {
  let binary = "";
  const chunkSize = 32768;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary);
}

function imageExtension(contentType) {
  return { 
    "image/jpeg": "jpg", 
    "image/png": "png", 
    "image/gif": "gif", 
    "image/webp": "webp", 
    "image/avif": "avif" 
  }[contentType];
}

function safeImageName(name, extension) {
  const stem = name.replace(/\.[^.]+$/, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+\vert{}-+$/g, "").slice(0, 80) || "image";
  return `${stem}-${Date.now().toString(36)}-${crypto.randomUUID().slice(0, 8)}.${extension}`;
}

async function githubRequest(env, method, path, body) {
  return fetch(`https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPOSITORY}/contents/${path}`, {
    method,
    headers: { 
      Authorization: `Bearer ${env.GITHUB_TOKEN}`, 
      Accept: "application/vnd.github+json", 
      "User-Agent": "personal-site-posting-worker", 
      "Content-Type": "application/json" 
    },
    body: body ? JSON.stringify(body) : undefined
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    try {
      const urlPath = new URL(request.url).pathname;

      if (request.method === "GET" && urlPath === "/posts") {
        const fileResponse = await githubRequest(env, "GET", "posts.json");
        if (!fileResponse.ok) return response([], 200);
        const file = await fileResponse.json();
        return response(JSON.parse(decodeContent(file.content)));
      }

      if (request.method === "GET" && urlPath === "/images") {
        const fileResponse = await githubRequest(env, "GET", "thoughts/images");
        if (!fileResponse.ok) return response([]);
        const files = await fileResponse.json();
        return response(files.filter((f) => f.type === "file").map((f) => ({
          name: f.name,
          url: `https://davidgsmith.net/thoughts/images/${encodeURIComponent(f.name)}`
        })).sort((a, b) => a.name.localeCompare(b.name)));
      }

      if (request.method !== "POST") return response({ error: "Method not allowed." }, 405);

      if (urlPath === "/login") {
        const { password } = await request.json();
        if (!password || password !== env.POSTING_PASSWORD) {
          return response({ error: "Invalid password." }, 401);
        }
        return response({ token: await createSession(env) });
      }

      if (!(await validSession(request, env))) {
        return response({ error: "Unauthorized session or token expired." }, 401);
      }

      const targetBranch = env.GITHUB_BRANCH || "main";

      if (urlPath === "/images") {
        const input = await request.json();
        const extension = imageExtension(input.type);
        if (!extension || typeof input.data !== "string" || !input.data || input.data.length > 14e6) {
          return response({ error: "Upload a PNG, JPEG, GIF, WebP, or AVIF image smaller than 10 MB." }, 400);
        }

        const bytes = Uint8Array.from(atob(input.data), (c) => c.charCodeAt(0));
        if (bytes.byteLength > 10 * 1024 * 1024) {
          return response({ error: "Image must be smaller than 10 MB." }, 400);
        }

        const filename = safeImageName(typeof input.name === "string" ? input.name : "image", extension);
        const path = `thoughts/images/${filename}`;
        const update = await githubRequest(env, "PUT", path, {
          message: `Add post image: ${filename}`,
          content: encodeBytes(bytes),
          branch: targetBranch
        });

        if (!update.ok) {
          const detail = await update.text();
          console.error("GitHub image upload error:", update.status, detail);
          return response({ error: "GitHub rejected image upload.", detail }, 502);
        }

        const url = `https://davidgsmith.net/thoughts/images/${encodeURIComponent(filename)}`;
        return response({ name: filename, url, markdown: `![${filename.replace(/\.[^.]+$/, "")}](${url})` });
      }

      if (urlPath === "/posts") {
        const input = await request.json();
        if (typeof input.title !== "string" || !input.title.trim() || input.title.length > 200 || typeof input.body !== "string" || !input.body.trim()) {
          return response({ error: "Title and body are required." }, 400);
        }

        let targetUrl = "";
        let detectedPlatform = "post";
        const rawUrl = (input.url || "").trim();

        if (rawUrl) {
          try {
            const parsed = new URL(rawUrl);
            if (!["http:", "https:"].includes(parsed.protocol)) {
              return response({ error: "The URL must start with http:// or https://" }, 400);
            }
            targetUrl = parsed.href;
            detectedPlatform = platformForUrl(targetUrl);
          } catch {
            return response({ error: "Please enter a valid URL or leave the field blank." }, 400);
          }
        }

        const tags = Array.isArray(input.tags) ? input.tags : [];
        const originalDate = input.original_date;
        const postType = input.type === "BlogPosting" ? "BlogPosting" : "TechArticle";

        const fileResponse = await githubRequest(env, "GET", "posts.json");
        if (!fileResponse.ok) {
          const detail = await fileResponse.text();
          console.error("GitHub GET posts.json error:", fileResponse.status, detail);
          return response({ error: "Could not read posts.json from GitHub.", detail }, 502);
        }

        const file = await fileResponse.json();
        const posts = JSON.parse(decodeContent(file.content));
        let message = "";

        if (originalDate) {
          const index = posts.findIndex((p) => p.date === originalDate);
          if (index !== -1) {
            posts[index].title = input.title.trim();
            posts[index].body = input.body.trim();
            posts[index].tags = tags;
            posts[index].type = postType;
            posts[index].url = targetUrl;
            posts[index].platform = detectedPlatform;
            message = `Update thought: ${input.title.trim()}`;
          } else {
            return response({ error: "Original post not found for editing." }, 404);
          }
        } else {
          posts.unshift({
            title: input.title.trim(),
            body: input.body.trim(),
            tags,
            type: postType,
            format: "markdown",
            url: targetUrl,
            date: new Date().toISOString(),
            platform: detectedPlatform
          });
          message = `Add thought: ${input.title.trim()}`;
        }

        const update = await githubRequest(env, "PUT", "posts.json", {
          message,
          content: encodeContent(JSON.stringify(posts, null, 2) + "\n"),
          sha: file.sha,
          branch: targetBranch
        });

        if (!update.ok) {
          const detail = await update.text();
          console.error("GitHub PUT posts.json error:", update.status, detail);
          return response({ error: "GitHub rejected posts.json update.", detail }, 502);
        }

        return response({ saved: true });
      }

      return response({ error: "Endpoint not found." }, 404);

    } catch (error) {
      console.error("Worker unhandled error:", error);
      return response({ error: error.message || "Request failed." }, 500);
    }
  }
};