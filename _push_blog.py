#!/usr/bin/env python3
"""Push new blog post to GitHub via Contents API."""
import base64, json, subprocess, os

os.chdir(os.path.dirname(__file__))

# Read files to upload
files = {
    'blog/20-cli-1-pip-install.html': open('blog/20-cli-1-pip-install.html', 'rb').read(),
    'blog/index.html': open('blog/index.html', 'rb').read(),
    'sitemap.xml': open('sitemap.xml', 'rb').read(),
}

api_base = 'repos/evolver-dev/evolver-tools/contents'

# Get SHA of existing files that are being updated
shas = {}
for path in ['blog/index.html', 'sitemap.xml']:
    r = subprocess.run(
        ['gh', 'api', f'{api_base}/{path}?ref=main', '--jq', '.sha'],
        capture_output=True, text=True
    )
    sha = r.stdout.strip()
    if sha:
        shas[path] = sha
        print(f"Got SHA for {path}: {sha[:12]}...")
    else:
        print(f"WARN: No SHA for {path}: {r.stderr[:100]}")

# Push each file
for path, content in files.items():
    encoded = base64.b64encode(content).decode()
    
    payload = {
        'message': f'Blog: add 20-cli-1-pip-install post — update {path}',
        'content': encoded,
        'branch': 'main',
    }
    if path in shas:
        payload['sha'] = shas[path]
    
    # For the new file, we don't need a SHA
    r = subprocess.run(
        ['gh', 'api', f'{api_base}/{path}',
         '-X', 'PUT',
         '--input', '-'],
        input=json.dumps(payload),
        capture_output=True, text=True
    )
    
    if r.returncode == 0:
        print(f"✅ {path} — pushed successfully")
    else:
        print(f"❌ {path} — {r.stderr[:200]}")

print("\nDone.")
