import requests
import json
import os
import subprocess
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv

# Load GitHub credentials from environment variables
GITHUB_USERNAME = os.getenv("GIT_USERNAME")
GITHUB_REPO = os.getenv("GIT_REPO")  # e.g. "https://github.com/yourusername/yourrepo"
GITHUB_TOKEN = os.getenv("GIT_TOKEN")

# LeetCode API URL (dynamic based on env variable if desired)
LEETCODE_USERNAME = os.getenv("LEETCODE_USERNAME")
LEETCODE_API_URL = f"https://leetcode-api-faisalshohag.vercel.app/ibrah342"

# Fetch solved problems from LeetCode API
response = requests.get(LEETCODE_API_URL)
print("Raw API response:", response.text)

if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict):
        solved_problems = data.get("recentSubmissions", [])
    else:
        solved_problems = data
else:
    print(f"Error fetching problems: {response.status_code}")
    exit()

# Load existing problems
if os.path.exists("solved_problems.json"):
    with open("solved_problems.json", "r") as file:
        solved_data = json.load(file)
else:
    solved_data = {"solved": []}

existing_entries = {(p["title"], p["date_solved"]) for p in solved_data["solved"]}
print("Existing:", existing_entries)
print("Fetched:", solved_problems)

# Filter new problems
new_problems = [
    problem for problem in solved_problems
    if (problem["title"], datetime.now().strftime("%Y-%m-%d")) not in existing_entries
]

if not new_problems:
    print("No new problems to update.")
    exit()

# Add new problems
for problem in new_problems:
    solved_data["solved"].append({
        "title": problem["title"],
        "difficulty": problem.get("difficulty", "Unknown"),
        "date_solved": datetime.now().strftime("%Y-%m-%d")
    })

# Save to JSON
with open("solved_problems.json", "w") as file:
    json.dump(solved_data, file, indent=4)

print(f"Added {len(new_problems)} new problems.")

# Git commit & push
commit_message = f"Updated solved problems ({len(new_problems)} new)"
subprocess.run(["git", "add", "solved_problems.json"], check=True)
subprocess.run(["git", "commit", "-m", commit_message], check=True)

# Set Git remote using secure tokenized URL
GITHUB_USERNAME = "ibra342"
GITHUB_TOKEN = "your_token_here"  # paste your actual token here
GITHUB_REPO = "https://github.com/ibra342/Leetcode-Github-Updater"

# Create the remote URL with token included
remote_url = GITHUB_REPO.replace("https://", f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@")

# Use it to push your changes
import subprocess
subprocess.run(["git", "remote", "set-url", "origin", remote_url])
subprocess.run(["git", "push", "origin", "main"])

print("✅ Successfully updated GitHub!")
