const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

const PORT = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
  const { url, method } = req;
  if (method === 'GET' && (url === '/' || url === '/index.html')) {
    const filePath = path.join(__dirname, 'index.html');
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Server error');
      } else {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(data);
      }
    });
  } else if (method === 'GET' && url === '/app.js') {
    const filePath = path.join(__dirname, 'app.js');
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not found');
      } else {
        res.writeHead(200, { 'Content-Type': 'application/javascript' });
        res.end(data);
      }
    });
  } else if (method === 'GET' && url === '/styles.css') {
    const filePath = path.join(__dirname, 'styles.css');
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not found');
      } else {
        res.writeHead(200, { 'Content-Type': 'text/css' });
        res.end(data);
      }
    });
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  }
});

// In-memory task store
const tasks = new Map(); // id -> task

function broadcast(wss, data, exclude) {
  const msg = JSON.stringify(data);
  wss.clients.forEach((client) => {
    if (client !== exclude && client.readyState === WebSocket.OPEN) {
      client.send(msg);
    }
  });
}

const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  // Send initial tasks
  ws.send(JSON.stringify({ type: 'init', tasks: Array.from(tasks.values()) }));

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      if (data.type === 'create') {
        const id = data.task && data.task.id ? data.task.id : String(Date.now()) + Math.random().toString(16).slice(2);
        const task = {
          id,
          title: data.task?.title || '',
          description: data.task?.description || '',
          dueDate: data.task?.dueDate || '',
          assignee: data.task?.assignee || '',
          status: data.task?.status || 'todo',
        };
        tasks.set(id, task);
        const payload = { type: 'created', task };
        broadcast(wss, payload);
      } else if (data.type === 'update') {
        const existing = tasks.get(data.task?.id);
        if (existing) {
          const updated = { ...existing, ...data.task };
          tasks.set(updated.id, updated);
          const payload = { type: 'updated', task: updated };
          broadcast(wss, payload);
        }
      } else if (data.type === 'delete') {
        const id = data.id;
        if (tasks.has(id)) {
          tasks.delete(id);
          const payload = { type: 'deleted', id };
          broadcast(wss, payload);
        }
      } else if (data.type === 'move') {
        const existing = tasks.get(data.id);
        if (existing) {
          existing.status = data.status;
          tasks.set(existing.id, existing);
          const payload = { type: 'moved', id: existing.id, status: existing.status };
          broadcast(wss, payload);
        }
      }
    } catch (_e) {
      // ignore bad messages
    }
  });
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
