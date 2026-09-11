const encoder = new TextEncoder();
const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

function response(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { ...cors, 'Content-Type': 'application/json' } });
}

function base64Url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function sign(value, secret) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);
  return base64Url(await crypto.subtle.sign('HMAC', key, encoder.encode(value)));
}

async function createSession(env) {
  const expires = Date.now() + 60 * 60 * 1000;
  const value = `${expires}.${crypto.randomUUID()}`;
  return `${value}.${await sign(value, env.POSTING_SESSION_SECRET)}`;
}

async function validSession(request, env) {
  const token = request.headers.get('Authorization')?.replace(/^Bearer\s+/i, '');
  if (!token) return false;
  const parts = token.split('.');
  if (parts.length !== 3 || Number(parts[0]) < Date.now()) return false;
  return parts[2] === await sign(`${parts[0]}.${parts[1]}`, env.POSTING_SESSION_SECRET);
}

function platformForUrl(value) {
  const hostname = new URL(value).hostname.replace(/^www\./, '').toLowerCase();
  if (hostname.includes('linkedin.com')) return 'linkedin';
  if (hostname === 'twitter.com' || hostname === 'x.com') return 'twitter';
  for (const name of ['facebook', 'instagram', 'youtube', 'tiktok', 'threads', 'medium', 'github']) {
    if (hostname.includes(name)) return name;
  }
  return 'other';
}

function decodeContent(value) {
  return new TextDecoder().decode(Uint8Array.from(atob(value.replace(/\s/g, '')), character => character.charCodeAt(0)));
}

function encodeContent(value) {
  return btoa(String.fromCharCode(...encoder.encode(value)));
}

async function githubRequest(env, method, path, body) {
  return fetch(`https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPOSITORY}/contents/${path}`, {
    method,
    headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'personal-site-posting-worker', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { headers: cors });
    try {
      if (request.method !== 'POST') return response({ error: 'Method not allowed.' }, 405);
      if (new URL(request.url).pathname === '/login') {
        const { password } = await request.json();
        if (!password || password !== env.POSTING_PASSWORD) return response({ error: 'Invalid password.' }, 401);
        return response({ token: await createSession(env) });
      }
      if (new URL(request.url).pathname !== '/posts' || !(await validSession(request, env))) return response({ error: 'Unauthorized.' }, 401);

      const input = await request.json();
      if (typeof input.title !== 'string' || !input.title.trim() || input.title.length > 200 || typeof input.body !== 'string' || !input.body.trim()) return response({ error: 'Title and body are required.' }, 400);
      const url = new URL(input.url);
      if (!['http:', 'https:'].includes(url.protocol)) return response({ error: 'A valid HTTP(S) URL is required.' }, 400);

      const fileResponse = await githubRequest(env, 'GET', 'posts.json');
      if (!fileResponse.ok) return response({ error: 'Could not read posts.json.' }, 502);
      const file = await fileResponse.json();
      const posts = JSON.parse(decodeContent(file.content));
      posts.push({ title: input.title.trim(), body: input.body.trim(), url: url.href, date: new Date().toISOString(), platform: platformForUrl(url.href) });
      const update = await githubRequest(env, 'PUT', 'posts.json', { message: `Add thought: ${input.title.trim()}`, content: encodeContent(JSON.stringify(posts, null, 2) + '\n'), sha: file.sha, branch: env.GITHUB_BRANCH || 'main' });
      if (!update.ok) return response({ error: 'GitHub rejected the update. Please retry.' }, 502);
      return response({ saved: true });
    } catch (error) {
      return response({ error: error.message || 'Request failed.' }, 400);
    }
  },
};