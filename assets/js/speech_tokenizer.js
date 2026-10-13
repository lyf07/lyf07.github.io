(() => {
  "use strict";

  const root = document.querySelector(".speech-tokenizer");
  if (!root) return;

  const players = Array.from(root.querySelectorAll("audio"));
  const pauseButton = root.querySelector("#st-pause-all");
  const search = root.querySelector("#st-search-input");
  const groups = Array.from(root.querySelectorAll(".st-group"));
  const modePanels = Array.from(root.querySelectorAll("[data-mode-panel]"));
  const modeButtons = Array.from(root.querySelectorAll(".st-mode-button"));
  const modeContexts = Array.from(root.querySelectorAll("[data-mode-context]"));
  const count = root.querySelector("#st-group-count");
  const emptyState = root.querySelector("#st-empty-state");
  const variantsById = new Map();
  let activeMode = "reconstruction";

  function pauseAll() {
    players.forEach((player) => player.pause());
    updatePauseButton();
  }

  function selectMode(mode) {
    if (!modePanels.some((panel) => panel.dataset.modePanel === mode)) return;
    if (mode !== activeMode) pauseAll();
    activeMode = mode;
    root.dataset.mode = mode;
    modePanels.forEach((panel) => {
      panel.hidden = panel.dataset.modePanel !== mode;
    });
    modeContexts.forEach((context) => {
      context.hidden = context.dataset.modeContext !== mode;
    });
    modeButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.mode === mode));
    });
    filterGroups();
  }

  function selectVariant(group, variantId) {
    const selector = group.querySelector(".st-tokenizer-select");
    const option = Array.from(selector.options).find((item) => item.value === variantId);
    if (!option) return;

    group.querySelectorAll(".st-variant-fragment").forEach((fragment) => {
      const selected = fragment.dataset.variantId === variantId;
      if (!selected) fragment.querySelectorAll("audio").forEach((player) => player.pause());
      fragment.hidden = !selected;
      if (selected) {
        fragment.querySelectorAll("audio").forEach((player) => {
          if (player.preload === "none") {
            player.preload = "metadata";
            player.load();
          }
        });
      }
    });
    selector.value = variantId;
    group.dataset.currentVariant = variantId;
    group.querySelector(".st-group-title").textContent = option.dataset.title;
    group.querySelector(".st-tokenizer-badge").setAttribute("aria-label", `本组使用的 tokenizer：${option.textContent.trim()}`);
    const permalink = group.querySelector(".st-permalink");
    permalink.setAttribute("href", `#${variantId}`);
    permalink.setAttribute("aria-label", `链接到 ${option.dataset.title}，${option.textContent.trim()}`);
    updatePauseButton();
  }

  groups.forEach((group) => {
    const selector = group.querySelector(".st-tokenizer-select");
    selector.disabled = selector.options.length < 2;
    Array.from(selector.options).forEach((option) => variantsById.set(option.value, group));
    selectVariant(group, selector.value);
    selector.addEventListener("change", () => {
      selectVariant(group, selector.value);
      const linkedGroup = variantsById.get(location.hash.slice(1));
      if (linkedGroup === group) history.replaceState(null, "", `#${selector.value}`);
    });
  });

  function updatePauseButton() {
    pauseButton.disabled = !players.some((player) => !player.paused && !player.ended);
  }

  players.forEach((player) => {
    player.addEventListener("play", () => {
      if (player.closest("[hidden]")) {
        player.pause();
        return;
      }
      players.forEach((other) => {
        if (other !== player) other.pause();
      });
      updatePauseButton();
    });
    player.addEventListener("pause", updatePauseButton);
    player.addEventListener("ended", updatePauseButton);
    player.addEventListener("error", () => {
      player.closest(".st-audio-clip").querySelector(".st-audio-error").hidden = false;
      updatePauseButton();
    });
  });

  pauseButton.addEventListener("click", () => {
    pauseAll();
  });

  function filterGroups() {
    const query = search.value.trim().toLocaleLowerCase();
    const activeGroups = groups.filter((group) => group.dataset.mode === activeMode);
    let visible = 0;
    activeGroups.forEach((group) => {
      const matches = (group.dataset.search || "").toLocaleLowerCase().includes(query);
      group.hidden = !matches;
      if (matches) {
        visible += 1;
        if (query) {
          const selector = group.querySelector(".st-tokenizer-select");
          const selected = selector.selectedOptions[0];
          if (!(selected.dataset.search || "").toLocaleLowerCase().includes(query)) {
            const matching = Array.from(selector.options).find((option) => (option.dataset.search || "").toLocaleLowerCase().includes(query));
            if (matching) selectVariant(group, matching.value);
          }
        }
      } else group.querySelectorAll("audio").forEach((player) => player.pause());
    });
    count.textContent = query ? `${visible} / ${activeGroups.length} 组对比` : `${activeGroups.length} 组对比`;
    emptyState.hidden = visible !== 0;
  }

  function followVariantLink() {
    let variantId;
    try {
      variantId = decodeURIComponent(location.hash.slice(1));
    } catch {
      return;
    }
    const group = variantsById.get(variantId);
    if (!group) return;
    search.value = "";
    selectMode(group.dataset.mode);
    selectVariant(group, variantId);
    group.scrollIntoView({ block: "start" });
  }

  search.addEventListener("input", filterGroups);
  modeButtons.forEach((button) => {
    button.disabled = false;
    button.addEventListener("click", () => {
      selectMode(button.dataset.mode);
      let linkedGroup;
      try {
        linkedGroup = variantsById.get(decodeURIComponent(location.hash.slice(1)));
      } catch {
        return;
      }
      if (linkedGroup && linkedGroup.dataset.mode !== activeMode) {
        history.replaceState(null, "", `${location.pathname}${location.search}`);
      }
    });
  });
  window.addEventListener("hashchange", followVariantLink);
  selectMode(activeMode);
  followVariantLink();
})();
