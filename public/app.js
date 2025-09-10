const eventsEl = document.getElementById('events');
const detailEl = document.getElementById('detail');
const searchEl = document.getElementById('search');
const dateEl = document.getElementById('dateFilter');
const typeEl = document.getElementById('typeFilter');
const applyFiltersBtn = document.getElementById('applyFilters');
const notificationsEl = document.getElementById('notifications');
const recentlyViewedEl = document.getElementById('recentlyViewed');

const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host);
ws.onmessage = (evt) => {
  const msg = JSON.parse(evt.data);
  if (msg.type === 'userRegistered') {
    showToast('New user registered');
    // Update counts
    const card = document.querySelector(`[data-id="${msg.payload.id}"]`);
    if (card) {
      const countEl = card.querySelector('.counts');
      if (countEl) countEl.textContent = `${msg.payload.registered} registered, ${msg.payload.remaining} remaining`;
      const btn = card.querySelector('button');
      if (btn && msg.payload.remaining <= 0) btn.disabled = true;
    }
    // If details open
    if (detailEl.dataset.id === msg.payload.id) {
      renderDetail(msg.payload.id);
    }
  }
  if (msg.type === 'eventCreated' || msg.type === 'eventUpdated' || msg.type === 'eventDeleted') {
    loadEvents();
  }
};

function showToast(text) {
  const div = document.createElement('div');
  div.className = 'toast';
  div.textContent = text;
  notificationsEl.appendChild(div);
  setTimeout(() => div.remove(), 3000);
}

async function loadEvents() {
  const params = new URLSearchParams();
  if (searchEl.value) params.set('search', searchEl.value);
  if (dateEl.value) params.set('date', dateEl.value);
  if (typeEl.value) params.set('type', typeEl.value);
  const res = await fetch('/api/events?' + params.toString());
  const data = await res.json();
  renderList(data);
}

function cardTemplate(e) {
  const overText = e.over ? 'Event ended' : `${e.remaining} seats left`;
  return `
    <div class="card" data-id="${e.id}">
      <h3>${e.title}</h3>
      <p>${new Date(e.datetime).toLocaleString()} @ ${e.location}</p>
      <p class="counts">${e.registered} registered, ${e.remaining} remaining</p>
      <p>${e.description || ''}</p>
      <button class="button" ${e.over || e.remaining<=0 ? 'disabled' : ''} onclick="viewDetail('${e.id}')">View</button>
    </div>
  `;
}

function renderList(list) {
  eventsEl.innerHTML = list.map(cardTemplate).join('');
}

window.viewDetail = async function(id) {
  await renderDetail(id);
  addRecentlyViewed(id);
}

async function renderDetail(id) {
  const res = await fetch('/api/events/' + id);
  const e = await res.json();
  detailEl.dataset.id = e.id;
  detailEl.innerHTML = `
    <h2>${e.title}</h2>
    <p>${new Date(e.datetime).toLocaleString()} @ ${e.location}</p>
    <p>${e.description}</p>
    <p>${e.registered} registered, ${e.remaining} remaining</p>
    <form id="regForm">
      <input name="name" placeholder="Your Name" required />
      <input name="email" type="email" placeholder="Your Email" required />
      <button class="button" type="submit" ${e.over || e.remaining<=0 ? 'disabled' : ''}>${e.over? 'Event Ended' : e.remaining<=0 ? 'Sold Out' : 'Register'}</button>
    </form>
  `;
  const form = document.getElementById('regForm');
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const fd = new FormData(form);
    const payload = Object.fromEntries(fd.entries());
    const res = await fetch('/api/events/' + id + '/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.error || 'Registration failed');
      return;
    }
    showToast('Registered!');
    await renderDetail(id);
    loadEvents();
  });
}

function addRecentlyViewed(id) {
  try {
    const key = 'recent-events';
    const list = JSON.parse(localStorage.getItem(key) || '[]');
    const newList = [id, ...list.filter((x) => x !== id)].slice(0, 5);
    localStorage.setItem(key, JSON.stringify(newList));
    renderRecentlyViewed();
  } catch {}
}

async function renderRecentlyViewed() {
  try {
    const key = 'recent-events';
    const list = JSON.parse(localStorage.getItem(key) || '[]');
    if (!list.length) {
      recentlyViewedEl.innerHTML = '';
      return;
    }
    const items = await Promise.all(
      list.map(async (id) => {
        const res = await fetch('/api/events/' + id);
        if (!res.ok) return null;
        const e = await res.json();
        return `<span class="chip" onclick="viewDetail('${e.id}')">${e.title}</span>`;
      })
    );
    recentlyViewedEl.innerHTML = `<h3>Recently Viewed</h3>${items.filter(Boolean).join(' ')}`;
  } catch {}
}

applyFiltersBtn.addEventListener('click', loadEvents);

// Service worker registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js');
  });
}

loadEvents();
renderRecentlyViewed();
