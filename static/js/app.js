const state = {
  allSigns: [],
  filteredSigns: [],
  activeSign: null,
  loading: false,
  debounceTimer: null,
};

const refs = {
  searchInput: document.getElementById("searchInput"),
  elementFilter: document.getElementById("elementFilter"),
  randomButton: document.getElementById("randomButton"),
  grid: document.getElementById("zodiacGrid"),
  detail: document.getElementById("detailPanel"),
  status: document.getElementById("statusMessage"),
  cardTemplate: document.getElementById("zodiacCardTemplate"),
};

const setLoading = (isLoading) => {
  state.loading = isLoading;
  if (isLoading) {
    refs.grid.setAttribute("data-loading", "true");
    refs.detail.setAttribute("data-loading", "true");
    showStatus("Loading constellation data…", false);
  } else {
    refs.grid.removeAttribute("data-loading");
    refs.detail.removeAttribute("data-loading");
  }
};

const showStatus = (message, isError = false) => {
  if (!refs.status) return;
  refs.status.textContent = message || "";
  refs.status.style.color = isError ? "#f87171" : "rgba(226, 232, 240, 0.85)";
};

const debounce = (fn, delay = 280) => {
  return (...args) => {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(() => fn(...args), delay);
  };
};

const applyFilters = () => {
  const query = refs.searchInput.value.trim().toLowerCase();
  const element = refs.elementFilter.value.trim().toLowerCase();

  const filtered = state.allSigns.filter((sign) => {
    const matchesQuery = !query || sign.name.toLowerCase().includes(query);
    const matchesElement = !element || sign.element.toLowerCase() === element;
    return matchesQuery && matchesElement;
  });

  state.filteredSigns = filtered;
  renderCards(filtered);

  if (!filtered.length) {
    showStatus("No constellations match your search – try a different spell.", true);
  } else {
    const descriptor = element ? `${element[0].toUpperCase()}${element.slice(1)} ` : "";
    const message = `Showing ${filtered.length} ${descriptor}zodiac sign${filtered.length === 1 ? "" : "s"}.`;
    showStatus(message, false);
  }
};

const attachCardInteractions = (card, sign) => {
  const activate = () => selectSign(sign, card);
  card.addEventListener("click", activate);
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activate();
    }
  });
};

const renderCards = (signs) => {
  const fragment = document.createDocumentFragment();
  refs.grid.innerHTML = "";

  signs.forEach((sign) => {
    const node = refs.cardTemplate.content.firstElementChild.cloneNode(true);
    node.dataset.slug = sign.slug;
    node.style.setProperty("--accent-color", sign.color);
    node.querySelector(".card__element").textContent = sign.element;
    node.querySelector(".card__element").style.backgroundColor = sign.color;
    node.querySelector(".card__title").textContent = sign.name;
    node.querySelector(".card__dates").textContent = sign.date_range;
    node.querySelector(".card__symbol").textContent = `Symbol · ${sign.symbol}`;
    attachCardInteractions(node, sign);
    fragment.appendChild(node);
  });

  refs.grid.appendChild(fragment);

  const activeMatches = signs.find((sign) => state.activeSign && sign.slug === state.activeSign.slug);
  if (!activeMatches && signs[0]) {
    selectSign(signs[0], refs.grid.querySelector(`[data-slug="${signs[0].slug}"]`));
  }
};

const selectSign = (sign, cardNode) => {
  state.activeSign = sign;
  document.querySelectorAll(".card[aria-pressed]").forEach((card) => {
    card.setAttribute("aria-pressed", String(card === cardNode));
  });

  const detailHtml = `
    <div class="detail__content" style="--accent-color:${sign.color}">
      <h2>${sign.name}</h2>
      <div class="detail__meta">
        <span class="badge">${sign.date_range}</span>
        <span class="badge">Symbol: ${sign.symbol}</span>
        <span class="detail__element" style="background:${sign.color}">
          <span class="dot"></span>
          ${sign.element}
        </span>
      </div>
      <section>
        <h3>Signature Traits</h3>
        <ul class="detail__traits">
          ${sign.traits.map((trait) => `<li>${trait}</li>`).join("")}
        </ul>
      </section>
      <section>
        <h3>Origins</h3>
        <p class="detail__origin">${sign.origin}</p>
      </section>
    </div>
  `;

  refs.detail.innerHTML = detailHtml;
};

const fetchAllSigns = async () => {
  try {
    setLoading(true);
    const response = await fetch("/zodiacs");
    if (!response.ok) {
      throw new Error(`Failed to fetch zodiacs: ${response.status}`);
    }
    const payload = await response.json();
    state.allSigns = payload.zodiacs || [];
    state.filteredSigns = [...state.allSigns];
    renderCards(state.filteredSigns);
    showStatus(`Loaded ${state.allSigns.length} zodiac constellations.`);
  } catch (error) {
    console.error(error);
    showStatus("We lost sight of the stars. Please try again.", true);
  } finally {
    setLoading(false);
  }
};

const revealRandomSign = async () => {
  try {
    setLoading(true);
    const response = await fetch("/zodiacs/random");
    if (!response.ok) {
      throw new Error(`Random zodiac failed: ${response.status}`);
    }
    const sign = await response.json();
    const matchingCard = refs.grid.querySelector(`[data-slug="${sign.slug}"]`);
    if (matchingCard) {
      matchingCard.scrollIntoView({ behavior: "smooth", block: "center" });
      selectSign(sign, matchingCard);
    } else {
      selectSign(sign, null);
    }
    showStatus(`The cosmos chose ${sign.name} for you.`);
  } catch (error) {
    console.error(error);
    showStatus("The cosmos is quiet right now. Try again soon.", true);
  } finally {
    setLoading(false);
  }
};

const initEvents = () => {
  refs.searchInput.addEventListener(
    "input",
    debounce(() => {
      applyFilters();
    })
  );

  refs.elementFilter.addEventListener("change", applyFilters);
  refs.randomButton.addEventListener("click", revealRandomSign);
};

const init = () => {
  if (!refs.grid || !refs.cardTemplate) {
    console.error("Missing required DOM nodes for Zodiac Explorer.");
    return;
  }
  initEvents();
  fetchAllSigns();
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
