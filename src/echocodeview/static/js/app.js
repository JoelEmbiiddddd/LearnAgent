document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("[data-action]");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      const details = document.querySelectorAll(".tree-dir");
      details.forEach((item) => {
        item.open = action === "expand";
      });
    });
  });

  if (window.mermaid) {
    window.mermaid.initialize({
      startOnLoad: true,
      theme: "default",
    });
  }
});
