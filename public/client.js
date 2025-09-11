const socket = io();
const zones = {
  todo: document.getElementById('todo'),
  inprogress: document.getElementById('inprogress'),
  completed: document.getElementById('completed')
};
let tasks = [];

function render() {
  Object.values(zones).forEach(z => z.innerHTML = '');
  const ft = document.getElementById('filterText').value.toLowerCase();
  const fa = document.getElementById('filterAssignee').value.toLowerCase();
  const fd = document.getElementById('filterDue').value;
  tasks.filter(t => (
    (!ft || t.title.toLowerCase().includes(ft)) &&
    (!fa || (t.assignee||'').toLowerCase().includes(fa)) &&
    (!fd || (t.dueDate||'') === fd)
  )).forEach(t => addCard(t));
}

function addCard(task) {
  const div = document.createElement('div');
  div.className = 'card';
  div.draggable = true;
  div.dataset.id = task.id;
  div.innerHTML = `<strong>${task.title}</strong><br>${task.description||''}<br>Assignee: ${task.assignee||''}<br>Due: ${task.dueDate||''}`;
  div.addEventListener('dragstart', e => {
    e.dataTransfer.setData('text/plain', String(task.id));
  });
  const del = document.createElement('button');
  del.textContent = 'Delete';
  del.onclick = async () => {
    await fetch(`/api/tasks/${task.id}`, { method: 'DELETE' });
  };
  div.appendChild(document.createElement('br'));
  div.appendChild(del);
  zones[task.status].appendChild(div);
}

for (const [status, el] of Object.entries(zones)) {
  el.addEventListener('dragover', e => e.preventDefault());
  el.addEventListener('drop', async (e) => {
    e.preventDefault();
    const id = Number(e.dataTransfer.getData('text/plain'));
    await fetch(`/api/tasks/${id}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ status }) });
    socket.emit('move', { id, status });
  });
}

socket.on('init', (serverTasks) => { tasks = serverTasks; render(); });
socket.on('task_created', (t) => { tasks.push(t); render(); });
socket.on('task_updated', (t) => { const i = tasks.findIndex(x => x.id === t.id); if (i>=0) tasks[i]=t; else tasks.push(t); render(); });
socket.on('task_deleted', (t) => { tasks = tasks.filter(x => x.id !== t.id); render(); });

// Form handling
const form = document.getElementById('taskForm');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const body = {
    title: document.getElementById('title').value,
    assignee: document.getElementById('assignee').value,
    dueDate: document.getElementById('dueDate').value,
    description: document.getElementById('description').value
  };
  const res = await fetch('/api/tasks', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  if (res.ok) {
    form.reset();
  }
});

document.getElementById('filterText').addEventListener('input', render);
document.getElementById('filterAssignee').addEventListener('input', render);
document.getElementById('filterDue').addEventListener('change', render);
document.getElementById('clearFilters').addEventListener('click', () => {
  document.getElementById('filterText').value = '';
  document.getElementById('filterAssignee').value = '';
  document.getElementById('filterDue').value = '';
  render();
});
