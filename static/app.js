const cards = document.getElementById('cards');
const details = document.getElementById('details');
const search = document.getElementById('search');
const elementFilter = document.getElementById('elementFilter');
const randomBtn = document.getElementById('randomBtn');

let allZodiacs = [];

function setLoading(msg = 'Loading...') {
  cards.innerHTML = `<div class="loading">${msg}</div>`;
}

async function fetchZodiacs(params = {}) {
  const query = new URLSearchParams(params);
  const res = await fetch(`/zodiacs?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to load zodiacs');
  return res.json();
}

function renderCards(list) {
  if (!list.length) {
    cards.innerHTML = '<div class="error">No matching zodiac signs found.</div>';
    return;
  }
  cards.innerHTML = list.map(z => `
    <div class="card" data-name="${z.name}" data-element="${z.element}">
      <h3>${z.name}</h3>
      <div class="badge">${z.element}</div>
      <p>${z.symbol} • ${z.date_range}</p>
    </div>
  `).join('');
}

async function showDetails(name) {
  const res = await fetch(`/zodiacs/${encodeURIComponent(name)}`);
  if (!res.ok) {
    details.classList.remove('hidden');
    details.innerHTML = '<div class="error">Zodiac not found.</div>';
    return;
  }
  const z = await res.json();
  details.classList.remove('hidden');
  details.innerHTML = `
    <h2>${z.name}</h2>
    <p><strong>Symbol:</strong> ${z.symbol}</p>
    <p><strong>Date range:</strong> ${z.date_range}</p>
    <p><strong>Element:</strong> ${z.element}</p>
    <p><strong>Origin:</strong> ${z.origin}</p>
    <p><strong>Traits:</strong> ${z.traits.join(', ')}</p>
  `;
}

function attachCardHandlers() {
  cards.addEventListener('click', (e) => {
    const el = e.target.closest('.card');
    if (!el) return;
    showDetails(el.dataset.name);
  });
}

async function init() {
  setLoading();
  try {
    allZodiacs = await fetchZodiacs();
    renderCards(allZodiacs);
  } catch (e) {
    cards.innerHTML = '<div class="error">Could not load zodiac data.</div>';
  }
  attachCardHandlers();
}

search.addEventListener('input', async () => {
  setLoading('Searching...');
  try {
    const filtered = await fetchZodiacs({ q: search.value, element: elementFilter.value });
    renderCards(filtered);
  } catch {
    cards.innerHTML = '<div class="error">Search failed.</div>';
  }
});

elementFilter.addEventListener('change', async () => {
  setLoading('Filtering...');
  try {
    const filtered = await fetchZodiacs({ q: search.value, element: elementFilter.value });
    renderCards(filtered);
  } catch {
    cards.innerHTML = '<div class="error">Filter failed.</div>';
  }
});

randomBtn.addEventListener('click', async () => {
  details.classList.add('hidden');
  setLoading('Picking for you...');
  try {
    const res = await fetch('/zodiacs/random');
    const z = await res.json();
    renderCards([z]);
  } catch {
    cards.innerHTML = '<div class="error">Random pick failed.</div>';
  }
});

init();