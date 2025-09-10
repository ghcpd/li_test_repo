const express = require('express');
const http = require('http');
const path = require('path');
const { WebSocketServer } = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

let events = [
  { id: '1', title: 'Tech Conference', date: new Date(Date.now() + 86400000).toISOString(), location: 'Hall A', totalSeats: 50, registered: 0, category: 'Technology', description: 'A great conference about tech.' },
  { id: '2', title: 'Music Night', date: new Date(Date.now() + 172800000).toISOString(), location: 'Auditorium', totalSeats: 100, registered: 0, category: 'Entertainment', description: 'Enjoy live music performances.' },
  { id: '3', title: 'Past Meetup', date: new Date(Date.now() - 86400000).toISOString(), location: 'Cafe', totalSeats: 20, registered: 5, category: 'Community', description: 'Casual meetup that already happened.' },
];

const clients = new Set();

wss.on('connection', (ws) => {
  clients.add(ws);
  ws.on('close', () => clients.delete(ws));
});

function broadcast(type, payload) {
  const msg = JSON.stringify({ type, payload });
  for (const client of clients) {
    if (client.readyState === 1) client.send(msg);
  }
}

app.get('/api/events', (req, res) => {
  res.json(events.map(e => ({ ...e, remaining: Math.max(0, e.totalSeats - e.registered) })));
});

app.get('/api/events/:id', (req, res) => {
  const e = events.find(ev => ev.id === req.params.id);
  if (!e) return res.status(404).json({ error: 'Not found' });
  res.json({ ...e, remaining: Math.max(0, e.totalSeats - e.registered) });
});

app.post('/api/register', (req, res) => {
  const { name, email, eventId } = req.body || {};
  const e = events.find(ev => ev.id === eventId);
  if (!e) return res.status(404).json({ error: 'Event not found' });
  if (new Date(e.date) < new Date()) return res.status(400).json({ error: 'Event ended' });
  if (e.registered >= e.totalSeats) return res.status(400).json({ error: 'Full' });
  e.registered += 1;
  broadcast('registration', { id: e.id, registered: e.registered, remaining: e.totalSeats - e.registered });
  res.json({ ok: true });
});

// Admin endpoints
app.post('/api/events', (req, res) => {
  const { title, date, location, totalSeats, category, description } = req.body || {};
  const id = String(Date.now());
  const newEvent = { id, title, date, location, totalSeats: Number(totalSeats), registered: 0, category, description };
  events.push(newEvent);
  broadcast('event_created', newEvent);
  res.json(newEvent);
});

app.put('/api/events/:id', (req, res) => {
  const idx = events.findIndex(e => e.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  events[idx] = { ...events[idx], ...req.body };
  broadcast('event_updated', events[idx]);
  res.json(events[idx]);
});

app.delete('/api/events/:id', (req, res) => {
  const idx = events.findIndex(e => e.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  const removed = events.splice(idx, 1)[0];
  broadcast('event_deleted', removed);
  res.json({ ok: true });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log('Server running on http://localhost:' + PORT));
