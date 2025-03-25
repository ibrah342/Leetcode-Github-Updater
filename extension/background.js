chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "runUpdater") {
      import(chrome.runtime.getURL("updater.js")).then((module) => {
        module.runUpdater(request.config).then(message => {
          sendResponse({ message });
        });
      });
      return true; 
    }
  });
  