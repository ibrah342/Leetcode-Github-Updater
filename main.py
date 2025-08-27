import os
import json
import subprocess
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

# ----------------------------
# Env setup (works local + CI)
# ----------------------------
load_dotenv()  # no-op in CI unless you create one there

LEETCODE_USERNAME = os.getenv("LEETCODE_USERNAME")
if not LEETCODE_USERNAME:
    print("ERROR: LEETCODE_USERNAME is missing.")
    raise SystemExit(1)

# optional / informative
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_REPO_URL = os.getenv("GIT_REPO")  # not required if 'origin' already set by checkout
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")  # owner/repo when in Actions
GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
# Prefer the built-in Actions token; fall back to your PAT names if you use them
GIT_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_PAT") or os.getenv("GIT_TOKEN")

print(f"Using LeetCode username: {LEETCODE_USERNAME}")

# --------------------------------
# Fetch recent submissions from API
# --------------------------------
API_URL = f"https://leetcode-api-faisalshohag.vercel.app/{LEETCODE_USERNAME}"
try:
    resp = requests.get(API_URL, timeout=20)
    resp.raise_for_status()
except requests.RequestException as e:
    print("ERROR: Failed to fetch from API:", e)
    raise SystemExit(1)

try:
    payload = resp.json()
except Exception as e:
    print("ERROR: Response not JSON:", e)
    print("Raw:", resp.text[:500])
    raise SystemExit(1)

# API may return dict with 'recentSubmissions' or a list
recent = payload.get("recentSubmissions", []) if isinstance(payload, dict) else payload

def normalize(item):
    title = item.get("title") or item.get("titleSlug") or item.get("question") or "Unknown"
    difficulty = item.get("difficulty") or "Unknown"
    ts = item.get("timestamp") or item.get("submitTime") or item.get("submissionTime") or item.get("time")
    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    else:
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(tz=timezone.utc)
    return {"title": title, "difficulty": difficulty, "date_solved": dt.strftime("%Y-%m-%d")}

normalized = [normalize(x) for x in recent]
print(f"Fetched {len(normalized)} submissions.")

# -------------------------
# Update solved_problems DB
# -------------------------
DB_PATH = "solved_problems.json"
if os.path.exists(DB_PATH):
    try:
        with open(DB_PATH, "r") as f:
            solved_data = json.load(f)
    except Exception:
        solved_data = {"solved": []}
else:
    solved_data = {"solved": []}

existing = {(p.get("title"), p.get("date_solved")) for p in solved_data.get("solved", [])}

new_items = [p for p in normalized if (p["title"], p["date_solved"]) not in existing]

if not new_items:
    print("No new problems to update.")
    # Still try to push in case you want to confirm no-op — but usually we just exit.
    raise SystemExit(0)

solved_data["solved"].extend(new_items)
with open(DB_PATH, "w") as f:
    json.dump(solved_data, f, indent=4)

print(f"Added {len(new_items)} new problems.")

# -------------------------
# Git commit & push (auto)
# -------------------------
def run(cmd, check=True, capture=False):
    return subprocess.run(cmd, check=check, text=True,
                          capture_output=capture)

# Ensure git identity exists (works in CI and local)
try:
    name = run(["git", "config", "--get", "user.name"], check=False, capture=True)
    email = run(["git", "config", "--get", "user.email"], check=False, capture=True)
    if not name.stdout.strip():
        run(["git", "config", "user.name", (GIT_USERNAME or "github-actions[bot]")])
    if not email.stdout.strip():
        run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])
except Exception:
    # If config fails, keep going; git will error later with a clear message
    pass

# If we're in Actions and have a token, make sure 'origin' uses it
# (checkout@v4 usually sets this for us; this is a safety net)
if GITHUB_ACTIONS and GIT_TOKEN and GITHUB_REPOSITORY:
    try:
        authed = f"https://x-access-token:{GIT_TOKEN}@github.com/{GITHUB_REPOSITORY}.git"
        run(["git", "remote", "set-url", "origin", authed])
    except Exception as e:
        print("Warning: could not set remote with token (may still be okay):", e)

# Stage and commit
run(["git", "add", DB_PATH], check=True)
commit_msg = f"Auto update: {len(new_items)} new problem(s) [{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}]"
commit = run(["git", "commit", "-m", commit_msg], check=False)
if commit.returncode != 0:
    print("No changes to commit (git reported no diff).")
    raise SystemExit(0)

# Determine branch to push
branch = os.getenv("GITHUB_REF_NAME")  # e.g., "main" in Actions
if not branch:
    # fallback to current
    res = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True, check=True)
    branch = res.stdout.strip() or "main"

# Push
try:
    run(["git", "push", "origin", branch], check=True)
    print("✅ Successfully pushed update to GitHub.")
except subprocess.CalledProcessError as e:
    print("ERROR: git push failed:", e)
    raise SystemExit(1)
