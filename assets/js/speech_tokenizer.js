(() => {
  "use strict";

  const root = document.querySelector(".speech-tokenizer");
  if (!root) return;

  const players = Array.from(root.querySelectorAll("audio"));
  const pauseButton = root.querySelector("#st-pause-all");
  const search = root.querySelector("#st-search-input");
  const groups = Array.from(root.querySelectorAll(".st-group"));
  const count = root.querySelector("#st-group-count");
  const emptyState = root.querySelector("#st-empty-state");

  function updatePauseButton() {
    pauseButton.disabled = !players.some((player) => !player.paused && !player.ended);
  }

  players.forEach((player) => {
    player.addEventListener("play", () => {
      players.forEach((other) => {
        if (other !== player) other.pause();
      });
      updatePauseButton();
    });
    player.addEventListener("pause", updatePauseButton);
    player.addEventListener("ended", updatePauseButton);
    player.addEventListener("error", () => {
      player.closest(".st-audio-card").querySelector(".st-audio-error").hidden = false;
      updatePauseButton();
    });
  });

  pauseButton.addEventListener("click", () => {
    players.forEach((player) => player.pause());
    updatePauseButton();
  });

  search.addEventListener("input", () => {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    groups.forEach((group) => {
      const matches = (group.dataset.search || "").toLocaleLowerCase().includes(query);
      group.hidden = !matches;
      if (matches) visible += 1;
      else group.querySelectorAll("audio").forEach((player) => player.pause());
    });
    count.textContent = query ? `${visible} / ${groups.length} 组对比` : `${groups.length} 组对比`;
    emptyState.hidden = visible !== 0;
  });
})();
