const tabs = document.querySelectorAll(".theme-tab");
const panels = document.querySelectorAll(".concept-panel");

function setActiveConcept(theme) {
  tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.target === theme);
  });
  panels.forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.theme === theme);
  });
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => setActiveConcept(tab.dataset.target));
});

panels.forEach((panel) => {
  panel.addEventListener("click", () => setActiveConcept(panel.dataset.theme));
});
