class AdminDashboard {
    constructor() {
        this.events = [];
        this.filteredEvents = [];
        this.socket = null;
        this.currentEventId = null;
        this.isLoggedIn = false;

        this.initializeApp();
        this.setupEventListeners();
    }

    initializeApp() {
        // Check if already logged in (in real app, use proper session management)
        const isLoggedIn = sessionStorage.getItem('admin_logged_in');
        if (isLoggedIn) {
            this.showDashboard();
        } else {
            this.showLogin();
        }
    }

    setupEventListeners() {
        // Login form
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Dashboard actions
        document.getElementById('new-event-btn').addEventListener('click', () => {
            this.showEventForm();
        });

        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Event form
        document.getElementById('event-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleEventSubmit();
        });

        document.getElementById('cancel-event-form').addEventListener('click', () => {
            this.closeModals();
        });

        // Delete confirmation
        document.getElementById('confirm-delete').addEventListener('click', () => {
            this.deleteEvent();
        });

        document.getElementById('cancel-delete').addEventListener('click', () => {
            this.closeModals();
        });

        // Search
        document.getElementById('admin-search').addEventListener('input', () => {
            this.filterEvents();
        });

        // Modal close buttons
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', () => {
                this.closeModals();
            });
        });

        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModals();
            }
        });
    }

    async handleLogin() {
        const formData = new FormData(document.getElementById('login-form'));
        const credentials = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(credentials)
            });

            if (response.ok) {
                sessionStorage.setItem('admin_logged_in', 'true');
                this.showDashboard();
                this.showNotification('Login successful!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Login failed. Please try again.', 'error');
        }
    }

    handleLogout() {
        sessionStorage.removeItem('admin_logged_in');
        this.showLogin();
        this.showNotification('Logged out successfully', 'success');
    }

    showLogin() {
        this.isLoggedIn = false;
        document.getElementById('login-screen').style.display = 'flex';
        document.getElementById('admin-dashboard').style.display = 'none';
        if (this.socket) {
            this.socket.close();
        }
    }

    showDashboard() {
        this.isLoggedIn = true;
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('admin-dashboard').style.display = 'block';
        this.loadEvents();
        this.connectWebSocket();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}`;
        
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('Admin WebSocket connected');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.socket.onclose = () => {
            console.log('Admin WebSocket disconnected');
            // Attempt to reconnect after 3 seconds if still logged in
            if (this.isLoggedIn) {
                setTimeout(() => this.connectWebSocket(), 3000);
            }
        };

        this.socket.onerror = (error) => {
            console.error('Admin WebSocket error:', error);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_registration':
                this.handleNewRegistration(data);
                break;
            case 'event_created':
            case 'event_updated':
            case 'event_deleted':
                this.loadEvents(); // Refresh the events list
                break;
        }
    }

    handleNewRegistration(data) {
        // Update event in local array
        const event = this.events.find(e => e.id === data.eventId);
        if (event) {
            event.registeredCount = (event.registeredCount || 0) + 1;
            event.remainingSeats = data.remainingSeats;
        }

        this.renderEvents();
        this.updateStats();
        this.showNotification(`New registration for "${event?.title || 'an event'}"`, 'info');
    }

    async loadEvents() {
        try {
            const response = await fetch('/api/events');
            if (response.ok) {
                this.events = await response.json();
                this.filterEvents();
                this.updateStats();
            } else {
                this.showNotification('Failed to load events', 'error');
            }
        } catch (error) {
            console.error('Error loading events:', error);
            this.showNotification('Error loading events', 'error');
        }
    }

    updateStats() {
        const totalEvents = this.events.length;
        const totalRegistrations = this.events.reduce((sum, event) => sum + (event.registeredCount || 0), 0);
        const upcomingEvents = this.events.filter(event => 
            new Date(`${event.date} ${event.time}`) > new Date()
        ).length;

        document.getElementById('total-events').textContent = totalEvents;
        document.getElementById('total-registrations').textContent = totalRegistrations;
        document.getElementById('upcoming-events').textContent = upcomingEvents;
    }

    filterEvents() {
        const searchTerm = document.getElementById('admin-search').value.toLowerCase();
        
        this.filteredEvents = this.events.filter(event => {
            return !searchTerm || 
                event.title.toLowerCase().includes(searchTerm) ||
                event.location.toLowerCase().includes(searchTerm) ||
                event.category.toLowerCase().includes(searchTerm);
        });

        this.renderEvents();
    }

    renderEvents() {
        const tbody = document.getElementById('events-table-body');
        
        if (this.filteredEvents.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 2rem; color: #666;">
                        No events found
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.filteredEvents.map(event => this.createEventRow(event)).join('');
    }

    createEventRow(event) {
        const eventDateTime = new Date(`${event.date} ${event.time}`);
        const now = new Date();
        const isUpcoming = eventDateTime > now;
        const isFull = event.remainingSeats <= 0;
        
        let status = 'upcoming';
        let statusText = 'Upcoming';
        let statusIcon = 'fa-calendar-check';

        if (!isUpcoming) {
            status = 'ended';
            statusText = 'Ended';
            statusIcon = 'fa-calendar-times';
        } else if (isFull) {
            status = 'full';
            statusText = 'Full';
            statusIcon = 'fa-users';
        }

        return `
            <tr>
                <td>
                    <div>
                        <strong>${event.title}</strong>
                        <br>
                        <small style="color: #666;">${event.category || 'General'}</small>
                    </div>
                </td>
                <td>
                    <div>
                        ${this.formatDate(event.date)}
                        <br>
                        <small style="color: #666;">${event.time}</small>
                    </div>
                </td>
                <td>${event.location}</td>
                <td>${event.totalSeats}</td>
                <td>
                    <strong>${event.registeredCount || 0}</strong>
                    <br>
                    <small style="color: #666;">${event.remainingSeats || event.totalSeats} left</small>
                </td>
                <td>
                    <span class="event-status status-${status}">
                        <i class="fas ${statusIcon}"></i>
                        ${statusText}
                    </span>
                </td>
                <td>
                    <div class="event-actions">
                        <button class="btn btn-sm btn-warning" onclick="adminDashboard.editEvent('${event.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="adminDashboard.confirmDelete('${event.id}', '${event.title}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    showEventForm(event = null) {
        this.currentEventId = event ? event.id : null;
        const form = document.getElementById('event-form');
        const title = document.getElementById('form-title');

        if (event) {
            title.innerHTML = '<i class="fas fa-edit"></i> Edit Event';
            // Populate form with event data
            document.getElementById('event-title').value = event.title || '';
            document.getElementById('event-category').value = event.category || '';
            document.getElementById('event-description').value = event.description || '';
            document.getElementById('event-date').value = event.date || '';
            document.getElementById('event-time').value = event.time || '';
            document.getElementById('event-location').value = event.location || '';
            document.getElementById('event-seats').value = event.totalSeats || '';
        } else {
            title.innerHTML = '<i class="fas fa-plus"></i> Create New Event';
            form.reset();
            // Set minimum date to today
            document.getElementById('event-date').min = new Date().toISOString().split('T')[0];
        }

        document.getElementById('event-form-modal').style.display = 'block';
    }

    async editEvent(eventId) {
        const event = this.events.find(e => e.id === eventId);
        if (event) {
            this.showEventForm(event);
        }
    }

    async handleEventSubmit() {
        const formData = new FormData(document.getElementById('event-form'));
        const eventData = {
            title: formData.get('title'),
            category: formData.get('category'),
            description: formData.get('description'),
            date: formData.get('date'),
            time: formData.get('time'),
            location: formData.get('location'),
            totalSeats: parseInt(formData.get('totalSeats'))
        };

        try {
            const url = this.currentEventId ? `/api/events/${this.currentEventId}` : '/api/events';
            const method = this.currentEventId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            });

            if (response.ok) {
                const action = this.currentEventId ? 'updated' : 'created';
                this.showNotification(`Event ${action} successfully!`, 'success');
                this.closeModals();
                this.loadEvents();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to save event', 'error');
            }
        } catch (error) {
            console.error('Error saving event:', error);
            this.showNotification('Failed to save event', 'error');
        }
    }

    confirmDelete(eventId, eventTitle) {
        this.currentEventId = eventId;
        document.getElementById('delete-event-title').textContent = eventTitle;
        document.getElementById('delete-modal').style.display = 'block';
    }

    async deleteEvent() {
        try {
            const response = await fetch(`/api/events/${this.currentEventId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('Event deleted successfully!', 'success');
                this.closeModals();
                this.loadEvents();
            } else {
                this.showNotification('Failed to delete event', 'error');
            }
        } catch (error) {
            console.error('Error deleting event:', error);
            this.showNotification('Failed to delete event', 'error');
        }
    }

    closeModals() {
        document.getElementById('event-form-modal').style.display = 'none';
        document.getElementById('delete-modal').style.display = 'none';
        this.currentEventId = null;
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div><strong>${type === 'error' ? 'Error' : type === 'success' ? 'Success' : 'Info'}</strong></div>
            <div>${message}</div>
        `;

        container.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }
}

// Initialize the admin dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminDashboard = new AdminDashboard();
});