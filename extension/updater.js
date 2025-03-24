export async function runUpdater(config) {
    const { leetcode_username, github_username, repo, token } = config;
  
    const leetcodeApiUrl = `https://leetcode-api-faisalshohag.vercel.app/${leetcode_username}`;
  
    try {
      // Fetch recent submissions from LeetCode API
      const leetRes = await fetch(leetcodeApiUrl);
      const leetData = await leetRes.json();
  
      if (!leetData || !leetData.recentSubmissions) {
        throw new Error("Invalid response from LeetCode API");
      }
  
      const problems = leetData.recentSubmissions.map(p => ({
        title: p.title,
        url: `https://leetcode.com/problems/${p.titleSlug}`,
        timestamp: p.timestamp
      }));
  
      const content = JSON.stringify(problems, null, 2);
      const filename = "solved_problems.json";
  
      const githubApiUrl = `https://api.github.com/repos/${github_username}/${repo}/contents/${filename}`;
  
      // Check if the file already exists to get the SHA
      const res = await fetch(githubApiUrl, {
        headers: { Authorization: `token ${token}` }
      });
  
      let sha = null;
      if (res.ok) {
        const existing = await res.json();
        sha = existing.sha;
      }
  
      // Create or update the file
      const updateRes = await fetch(githubApiUrl, {
        method: "PUT",
        headers: {
          Authorization: `token ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: `🔁 Auto-update LeetCode problems - ${new Date().toISOString()}`,
          content: btoa(unescape(encodeURIComponent(content))),
          sha: sha
        })
      });
  
      if (updateRes.ok) {
        console.log("✅ GitHub update successful!");
        return "✅ Successfully updated your GitHub!";
      } else {
        const error = await updateRes.json();
        console.error("❌ GitHub update failed:", error);
        return `❌ GitHub update failed: ${error.message || "Unknown error"}`;
      }
  
    } catch (err) {
      console.error("🔥 Error in updater:", err);
      return `❌ Update failed: ${err.message}`;
    }
  }
  