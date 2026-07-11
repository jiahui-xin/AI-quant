(function () {
  const tasks = window.AIQ_TASKS || [];
  const grid = document.getElementById("taskPortalGrid");
  if (!grid) return;

  grid.innerHTML = tasks.map((task, index) => `
    <article class="portal-card ${index === tasks.length - 1 ? "featured" : ""}">
      <div class="task-card-head">
        <span class="task-mark">${task.id}</span>
        <span class="task-status">已完成</span>
      </div>
      <h3>${task.title}</h3>
      <p>${task.description}</p>
      <div class="tags">${task.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
      <div class="task-actions">
        <a class="csv-link" href="${task.page}">进入 ${task.id}</a>
        <a class="csv-link secondary-link" href="${task.pdf}">下载 PDF</a>
      </div>
    </article>
  `).join("");
})();
