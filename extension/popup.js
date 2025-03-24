document.getElementById("update").addEventListener("click", () => {
    const leetcode_username = document.getElementById("leetcode_username").value;
    const github_username = document.getElementById("github_username").value;
    const repo = document.getElementById("repo").value;
    const token = document.getElementById("token").value;
  
    const config = {
      leetcode_username,
      github_username,
      repo,
      token
    };
  
    chrome.storage.local.set({ config }, () => {
      console.log("Config saved!");
      chrome.runtime.sendMessage({ action: "runUpdater" });
    });
  });
  