const listEl = document.getElementById('admin-events');
const form = document.getElementById('create-form');

async function load() {
  const r = await fetch('/api/events');
  const data = await r.json();
  render(data);
}

function render(events) {
  listEl.innerHTML = '';
  for (const e of events) {
    const t = document.getElementById('admin-card').content.cloneNode(true);
    t.querySelector('.title').textContent = `${e.title} (${e.registered}/${e.totalSeats})`;
    t.querySelector('.delete').onclick = async () => {
      if (!confirm('Delete event?')) return;
      await fetch('/api/events/' + e.id, { method: 'DELETE' });
    };
    t.querySelector('.edit').onclick = async () => {
      const title = prompt('Title', e.title);
      if (!title) return;
      await fetch('/api/events/' + e.id, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title }) });
    };
    listEl.appendChild(t);
  }
}

form.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const fd = new FormData(form);
  const data = Object.fromEntries(fd.entries());
  await fetch('/api/events', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  form.reset();
});

const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host);
ws.onmessage = () => load();

load();
