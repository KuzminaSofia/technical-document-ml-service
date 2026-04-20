(() => {
    const root = document.querySelector("[data-task-auto-refresh]");
    if (!root) {
      return;
    }
  
    const autoRefresh = root.getAttribute("data-task-auto-refresh");
    if (autoRefresh !== "true") {
      return;
    }
  
    window.setTimeout(() => {
      window.location.reload();
    }, 5000);
  })();