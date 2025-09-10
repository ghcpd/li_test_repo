const express = require('express');
const WebSocket = require('ws');
const cors = require('cors');
const path = require('path');
const fs = require('fs').promises;
const { v4: uuidv4 } = require('uuid');

const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Data files
const EVENTS_FILE = path.join(__dirname, 'data', 'events.json');
const REGISTRATIONS_FILE = path.join(__dirname, 'data', 'registrations.json');
const ADMINS_FILE = path.join(__dirname, 'data', 'admins.json');

// Initialize data files
async function initializeData() {
    try {
        await fs.access('data');
    } catch {
        await fs.mkdir('data');
    }

    // Initialize events file
    try {
        await fs.access(EVENTS_FILE);
    } catch {
        await fs.writeFile(EVENTS_FILE, JSON.stringify([]));
    }

    // Initialize registrations file
    try {
        await fs.access(REGISTRATIONS_FILE);
    } catch {
        await fs.writeFile(REGISTRATIONS_FILE, JSON.stringify([]));
    }

    // Initialize admins file with default admin
    try {
        await fs.access(ADMINS_FILE);
    } catch {
        const defaultAdmin = [{ username: 'admin', password: 'admin123' }];
        await fs.writeFile(ADMINS_FILE, JSON.stringify(defaultAdmin));
    }
}

// Helper functions
async function readJsonFile(filePath) {
    try {
        const data = await fs.readFile(filePath, 'utf8');
        return JSON.parse(data);
    } catch {
        return [];
    }
}

async function writeJsonFile(filePath, data) {
    await fs.writeFile(filePath, JSON.stringify(data, null, 2));
}

// WebSocket setup
const server = require('http').createServer(app);
const wss = new WebSocket.Server({ server });

function broadcast(message) {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(message));
        }
    });
}

wss.on('connection', (ws) => {
    console.log('Client connected');
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// API Routes

// Get all events
app.get('/api/events', async (req, res) => {
    const events = await readJsonFile(EVENTS_FILE);
    const registrations = await readJsonFile(REGISTRATIONS_FILE);
    
    const eventsWithStats = events.map(event => {
        const eventRegistrations = registrations.filter(r => r.eventId === event.id);
        return {
            ...event,
            registeredCount: eventRegistrations.length,
            remainingSeats: event.totalSeats - eventRegistrations.length
        };
    });
    
    res.json(eventsWithStats);
});

// Get single event
app.get('/api/events/:id', async (req, res) => {
    const events = await readJsonFile(EVENTS_FILE);
    const registrations = await readJsonFile(REGISTRATIONS_FILE);
    
    const event = events.find(e => e.id === req.params.id);
    if (!event) {
        return res.status(404).json({ error: 'Event not found' });
    }
    
    const eventRegistrations = registrations.filter(r => r.eventId === event.id);
    const eventWithStats = {
        ...event,
        registeredCount: eventRegistrations.length,
        remainingSeats: event.totalSeats - eventRegistrations.length,
        registrations: eventRegistrations
    };
    
    res.json(eventWithStats);
});

// Create event (admin only)
app.post('/api/events', async (req, res) => {
    const { title, description, date, time, location, totalSeats, category } = req.body;
    
    const newEvent = {
        id: uuidv4(),
        title,
        description,
        date,
        time,
        location,
        totalSeats: parseInt(totalSeats),
        category,
        createdAt: new Date().toISOString()
    };
    
    const events = await readJsonFile(EVENTS_FILE);
    events.push(newEvent);
    await writeJsonFile(EVENTS_FILE, events);
    
    // Broadcast new event
    broadcast({ type: 'event_created', event: newEvent });
    
    res.status(201).json(newEvent);
});

// Update event (admin only)
app.put('/api/events/:id', async (req, res) => {
    const events = await readJsonFile(EVENTS_FILE);
    const eventIndex = events.findIndex(e => e.id === req.params.id);
    
    if (eventIndex === -1) {
        return res.status(404).json({ error: 'Event not found' });
    }
    
    events[eventIndex] = { ...events[eventIndex], ...req.body };
    await writeJsonFile(EVENTS_FILE, events);
    
    // Broadcast event update
    broadcast({ type: 'event_updated', event: events[eventIndex] });
    
    res.json(events[eventIndex]);
});

// Delete event (admin only)
app.delete('/api/events/:id', async (req, res) => {
    const events = await readJsonFile(EVENTS_FILE);
    const eventIndex = events.findIndex(e => e.id === req.params.id);
    
    if (eventIndex === -1) {
        return res.status(404).json({ error: 'Event not found' });
    }
    
    events.splice(eventIndex, 1);
    await writeJsonFile(EVENTS_FILE, events);
    
    // Broadcast event deletion
    broadcast({ type: 'event_deleted', eventId: req.params.id });
    
    res.status(204).send();
});

// Register for event
app.post('/api/events/:id/register', async (req, res) => {
    const { name, email } = req.body;
    const eventId = req.params.id;
    
    const events = await readJsonFile(EVENTS_FILE);
    const event = events.find(e => e.id === eventId);
    
    if (!event) {
        return res.status(404).json({ error: 'Event not found' });
    }
    
    const registrations = await readJsonFile(REGISTRATIONS_FILE);
    const eventRegistrations = registrations.filter(r => r.eventId === eventId);
    
    if (eventRegistrations.length >= event.totalSeats) {
        return res.status(400).json({ error: 'Event is full' });
    }
    
    // Check if user already registered
    const existingRegistration = eventRegistrations.find(r => r.email === email);
    if (existingRegistration) {
        return res.status(400).json({ error: 'Already registered for this event' });
    }
    
    const newRegistration = {
        id: uuidv4(),
        eventId,
        name,
        email,
        registeredAt: new Date().toISOString()
    };
    
    registrations.push(newRegistration);
    await writeJsonFile(REGISTRATIONS_FILE, registrations);
    
    // Broadcast new registration
    broadcast({ 
        type: 'new_registration', 
        eventId, 
        registration: newRegistration,
        remainingSeats: event.totalSeats - (eventRegistrations.length + 1)
    });
    
    res.status(201).json(newRegistration);
});

// Admin login
app.post('/api/admin/login', async (req, res) => {
    const { username, password } = req.body;
    const admins = await readJsonFile(ADMINS_FILE);
    
    const admin = admins.find(a => a.username === username && a.password === password);
    if (!admin) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    res.json({ success: true, message: 'Login successful' });
});

// Serve admin dashboard
app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'admin', 'index.html'));
});

// Start server
initializeData().then(() => {
    server.listen(port, () => {
        console.log(`Event Management Server running at http://localhost:${port}`);
    });
});