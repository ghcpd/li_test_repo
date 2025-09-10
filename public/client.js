const listEl = document.getElementById('events');
const searchEl = document.getElementById('search');
const categoryEl = document.getElementById('category');

async function loadEvents() {
  const r = await fetch('/api/events');
  const data = await r.json();
  render(data);
}

function render(events) {
  const q = searchEl.value.toLowerCase();
  const cat = categoryEl.value;
  listEl.innerHTML = '';
  for (const e of events.filter(x => (!q || x.title.toLowerCase().includes(q)) && (!cat || x.category === cat))) {
    const t = document.getElementById('event-card').content.cloneNode(true);
    t.querySelector('.title').textContent = e.title;
    t.querySelector('.meta').textContent = `${new Date(e.date).toLocaleString()} • ${e.location}`;
    t.querySelector('.desc').textContent = e.description || '';
    t.querySelector('.remaining').textContent = `${e.registered} registered • ${e.remaining} left`;
    const btn = t.querySelector('.register');
    const isPast = new Date(e.date) < new Date();
    const already = localStorage.getItem('registered:' + e.id) === 'true';
    btn.disabled = isPast || e.remaining === 0 || already;
    btn.textContent = already ? 'Registered' : 'Register';
    if (already) btn.classList.add('success');
    btn.onclick = async () => {
      const name = prompt('Your name?');
      const email = prompt('Your email?');
      if (!name || !email) return;
      const resp = await fetch('/api/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, email, eventId: e.id }) });
      if (resp.ok) {
        localStorage.setItem('registered:' + e.id, 'true');
        btn.textContent = 'Registered';
        btn.classList.add('success');
        btn.disabled = true;
      }
    };
    t.querySelector('.card').addEventListener('click', () => saveRecent(e.id));
    listEl.appendChild(t);
  }
}

function saveRecent(id) {
  const rec = JSON.parse(localStorage.getItem('recent') || '[]');
  if (!rec.includes(id)) rec.unshift(id);
  localStorage.setItem('recent', JSON.stringify(rec.slice(0, 10)));
}

searchEl.addEventListener('input', loadEvents);
categoryEl.addEventListener('change', loadEvents);

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js');
}

const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host);
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.type === 'registration' || msg.type === 'event_created' || msg.type === 'event_updated' || msg.type === 'event_deleted') {
    loadEvents();
  }
};

loadEvents();
