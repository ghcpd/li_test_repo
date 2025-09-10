let token = '';
const loginSection = document.getElementById('adminLogin');
const panelSection = document.getElementById('adminPanel');
const adminEventsEl = document.getElementById('adminEvents');

async function login() {
  const password = document.getElementById('adminPassword').value;
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  const data = await res.json();
  if (res.ok) {
    token = data.token;
    loginSection.style.display = 'none';
    panelSection.style.display = 'block';
    loadAdminEvents();
    document.getElementById('loginStatus').textContent = '';
  } else {
    document.getElementById('loginStatus').textContent = data.error || 'Login failed';
  }
}

document.getElementById('loginBtn').addEventListener('click', login);

document.getElementById('createEvent').addEventListener('click', async () => {
  const payload = {
    title: document.getElementById('title').value,
    datetime: new Date(document.getElementById('datetime').value).toISOString(),
    location: document.getElementById('location').value,
    type: document.getElementById('type').value || 'general',
    totalSeats: Number(document.getElementById('totalSeats').value),
    description: document.getElementById('description').value,
  };
  const res = await fetch('/api/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    loadAdminEvents();
  }
});

async function loadAdminEvents() {
  const res = await fetch('/api/events');
  const list = await res.json();
  adminEventsEl.innerHTML = list
    .map((e) => `
      <div class="card" data-id="${e.id}">
        <h3 contenteditable="true" data-field="title">${e.title}</h3>
        <p><input type="datetime-local" data-field="datetime" value="${new Date(e.datetime).toISOString().slice(0,16)}" /></p>
        <p><input data-field="location" value="${e.location}" /></p>
        <p><input data-field="type" value="${e.type}" /></p>
        <p><input type="number" data-field="totalSeats" value="${e.totalSeats}" /></p>
        <p><textarea data-field="description">${e.description || ''}</textarea></p>
        <button class="button" onclick="updateEvent('${e.id}', this.parentElement)">Save</button>
        <button class="button" onclick="deleteEvent('${e.id}')">Delete</button>
      </div>
    `)
    .join('');
}

window.updateEvent = async function(id, el) {
  const body = {};
  el.querySelectorAll('[data-field]').forEach((field) => {
    const key = field.getAttribute('data-field');
    if (field.tagName === 'H3') body[key] = field.textContent;
    else if (field.type === 'datetime-local') body[key] = new Date(field.value).toISOString();
    else if (field.type === 'number') body[key] = Number(field.value);
    else body[key] = field.value;
  });
  const res = await fetch('/api/events/' + id, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
    body: JSON.stringify(body)
  });
  if (res.ok) loadAdminEvents();
}

window.deleteEvent = async function(id) {
  const res = await fetch('/api/events/' + id, {
    method: 'DELETE',
    headers: { Authorization: 'Bearer ' + token }
  });
  if (res.ok) loadAdminEvents();
}
