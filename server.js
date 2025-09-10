const express = require('express');
const path = require('path');
const http = require('http');
const { WebSocketServer } = require('ws');

const app = express();
app.use(express.json());

// Simple in-memory store
let events = [
  {
    id: '1',
    title: 'Tech Meetup',
    description: 'A meetup for tech enthusiasts.',
    type: 'meetup',
    datetime: new Date(Date.now() + 86400000).toISOString(),
    location: 'Community Hall',
    totalSeats: 50,
    registered: 0,
  },
  {
    id: '2',
    title: 'Art Workshop',
    description: 'Hands-on art workshop for beginners.',
    type: 'workshop',
    datetime: new Date(Date.now() + 2 * 86400000).toISOString(),
    location: 'Art Center',
    totalSeats: 20,
    registered: 5,
  },
];

const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin';
const activeTokens = new Set();

function isEventOver(e) {
  return new Date(e.datetime).getTime() < Date.now();
}

function remainingSeats(e) {
  return Math.max(0, e.totalSeats - e.registered);
}

function broadcast(wss, type, payload) {
  const message = JSON.stringify({ type, payload });
  wss.clients.forEach((client) => {
    if (client.readyState === 1) {
      client.send(message);
    }
  });
}

// API routes
app.get('/api/events', (req, res) => {
  const { search = '', date = '', type = '' } = req.query;
  let filtered = [...events];
  if (search) {
    const s = String(search).toLowerCase();
    filtered = filtered.filter(
      (e) => e.title.toLowerCase().includes(s) || e.description.toLowerCase().includes(s)
    );
  }
  if (type) {
    filtered = filtered.filter((e) => e.type === type);
  }
  if (date) {
    const d = new Date(date);
    filtered = filtered.filter((e) => new Date(e.datetime).toDateString() === d.toDateString());
  }
  res.json(
    filtered.map((e) => ({
      id: e.id,
      title: e.title,
      description: e.description,
      type: e.type,
      datetime: e.datetime,
      location: e.location,
      totalSeats: e.totalSeats,
      registered: e.registered,
      remaining: remainingSeats(e),
      over: isEventOver(e),
    }))
  );
});

app.get('/api/events/:id', (req, res) => {
  const e = events.find((x) => x.id === req.params.id);
  if (!e) return res.status(404).json({ error: 'Not found' });
  res.json({ ...e, remaining: remainingSeats(e), over: isEventOver(e) });
});

app.post('/api/events/:id/register', (req, res) => {
  const e = events.find((x) => x.id === req.params.id);
  if (!e) return res.status(404).json({ error: 'Not found' });
  if (isEventOver(e)) return res.status(400).json({ error: 'Event is over' });
  if (remainingSeats(e) <= 0) return res.status(400).json({ error: 'No seats left' });
  const { name, email } = req.body || {};
  if (!name || !email) return res.status(400).json({ error: 'Invalid input' });
  e.registered += 1;
  const payload = { id: e.id, registered: e.registered, remaining: remainingSeats(e) };
  broadcast(wss, 'userRegistered', payload);
  res.json({ success: true, ...payload });
});

// Admin
app.post('/api/login', (req, res) => {
  const { password } = req.body || {};
  if (password === ADMIN_PASSWORD) {
    const token = `token-${Date.now()}`;
    activeTokens.add(token);
    return res.json({ token });
  }
  res.status(401).json({ error: 'Unauthorized' });
});

function auth(req, res, next) {
  const auth = req.headers.authorization || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (activeTokens.has(token)) return next();
  res.status(401).json({ error: 'Unauthorized' });
}

app.post('/api/events', auth, (req, res) => {
  const { title, description, type, datetime, location, totalSeats } = req.body || {};
  if (!title || !datetime || !location || !totalSeats) {
    return res.status(400).json({ error: 'Missing fields' });
  }
  const e = {
    id: String(Date.now()),
    title,
    description: description || '',
    type: type || 'general',
    datetime,
    location,
    totalSeats: Number(totalSeats),
    registered: 0,
  };
  events.push(e);
  broadcast(wss, 'eventCreated', e);
  res.json(e);
});

app.put('/api/events/:id', auth, (req, res) => {
  const idx = events.findIndex((x) => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  const e = events[idx];
  const { title, description, type, datetime, location, totalSeats } = req.body || {};
  if (title !== undefined) e.title = title;
  if (description !== undefined) e.description = description;
  if (type !== undefined) e.type = type;
  if (datetime !== undefined) e.datetime = datetime;
  if (location !== undefined) e.location = location;
  if (totalSeats !== undefined) e.totalSeats = Number(totalSeats);
  events[idx] = e;
  broadcast(wss, 'eventUpdated', e);
  res.json(e);
});

app.delete('/api/events/:id', auth, (req, res) => {
  const idx = events.findIndex((x) => x.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  const [deleted] = events.splice(idx, 1);
  broadcast(wss, 'eventDeleted', { id: deleted.id });
  res.json({ success: true });
});

// Serve static files
const publicDir = path.join(__dirname, 'public');
app.use(express.static(publicDir));
app.get(/.*/, (req, res) => res.sendFile(path.join(publicDir, 'index.html')));

// Create server and WebSocket
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ type: 'welcome', payload: 'Connected' }));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
