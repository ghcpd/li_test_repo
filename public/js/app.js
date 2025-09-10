class EventManager {
    constructor() {
        this.events = [];
        this.filteredEvents = [];
        this.recentlyViewed = this.getRecentlyViewed();
        this.currentView = 'events';
        this.socket = null;
        this.isOnline = navigator.onLine;
        
        this.initializeApp();
        this.setupEventListeners();
        this.connectWebSocket();
        this.setupServiceWorker();
        this.setupOfflineDetection();
    }

    initializeApp() {
        this.loadEvents();
        this.showLoading(true);
    }

    setupEventListeners() {
        // Navigation
        document.getElementById('home-link').addEventListener('click', (e) => {
            e.preventDefault();
            this.showEventsView();
        });

        document.getElementById('recently-viewed-link').addEventListener('click', (e) => {
            e.preventDefault();
            this.showRecentlyViewedView();
        });

        // Search and filters
        document.getElementById('search-input').addEventListener('input', () => {
            this.filterEvents();
        });

        document.getElementById('category-filter').addEventListener('change', () => {
            this.filterEvents();
        });

        document.getElementById('date-filter').addEventListener('change', () => {
            this.filterEvents();
        });

        // Modal events
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

        // Registration form
        document.getElementById('registration-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegistration();
        });

        document.getElementById('cancel-registration').addEventListener('click', () => {
            this.closeModals();
        });
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}`;
        
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_registration':
                this.handleNewRegistration(data);
                break;
            case 'event_created':
                this.handleEventCreated(data.event);
                break;
            case 'event_updated':
                this.handleEventUpdated(data.event);
                break;
            case 'event_deleted':
                this.handleEventDeleted(data.eventId);
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

        // Update UI if currently viewing events
        if (this.currentView === 'events') {
            this.renderEvents();
        }

        // Show notification
        this.showNotification('New registration received!', 'info');
    }

    handleEventCreated(event) {
        this.events.unshift(event);
        if (this.currentView === 'events') {
            this.filterEvents();
        }
        this.showNotification('New event added!', 'success');
    }

    handleEventUpdated(event) {
        const index = this.events.findIndex(e => e.id === event.id);
        if (index !== -1) {
            this.events[index] = event;
            if (this.currentView === 'events') {
                this.filterEvents();
            }
        }
        this.showNotification('Event updated!', 'info');
    }

    handleEventDeleted(eventId) {
        this.events = this.events.filter(e => e.id !== eventId);
        if (this.currentView === 'events') {
            this.filterEvents();
        }
        this.showNotification('Event removed!', 'info');
    }

    updateConnectionStatus(isConnected) {
        const statusDot = document.getElementById('connection-status');
        statusDot.className = `status-dot ${isConnected ? 'online' : 'offline'}`;
    }

    async loadEvents() {
        try {
            const response = await fetch('/api/events');
            if (response.ok) {
                this.events = await response.json();
                this.cacheEvents(); // Cache for offline use
            } else {
                // Try to load from cache if online request fails
                this.loadCachedEvents();
            }
        } catch (error) {
            console.error('Error loading events:', error);
            this.loadCachedEvents();
        }
        
        this.filterEvents();
        this.showLoading(false);
    }

    cacheEvents() {
        if ('localStorage' in window) {
            localStorage.setItem('cached_events', JSON.stringify(this.events));
            localStorage.setItem('cache_timestamp', Date.now().toString());
        }
    }

    loadCachedEvents() {
        if ('localStorage' in window) {
            const cachedEvents = localStorage.getItem('cached_events');
            if (cachedEvents) {
                this.events = JSON.parse(cachedEvents);
                this.showNotification('Showing cached events (offline)', 'info');
            }
        }
    }

    filterEvents() {
        const searchTerm = document.getElementById('search-input').value.toLowerCase();
        const categoryFilter = document.getElementById('category-filter').value;
        const dateFilter = document.getElementById('date-filter').value;

        this.filteredEvents = this.events.filter(event => {
            const matchesSearch = !searchTerm || 
                event.title.toLowerCase().includes(searchTerm) ||
                event.description.toLowerCase().includes(searchTerm) ||
                event.location.toLowerCase().includes(searchTerm);

            const matchesCategory = !categoryFilter || event.category === categoryFilter;

            const matchesDate = !dateFilter || event.date === dateFilter;

            return matchesSearch && matchesCategory && matchesDate;
        });

        this.renderEvents();
    }

    renderEvents() {
        const grid = document.getElementById('events-grid');
        const noEvents = document.getElementById('no-events');

        if (this.filteredEvents.length === 0) {
            grid.innerHTML = '';
            noEvents.style.display = 'block';
            return;
        }

        noEvents.style.display = 'none';
        
        grid.innerHTML = this.filteredEvents.map(event => this.createEventCard(event)).join('');

        // Add click listeners to event cards
        grid.querySelectorAll('.event-card').forEach((card, index) => {
            card.addEventListener('click', () => {
                this.showEventDetails(this.filteredEvents[index]);
            });
        });
    }

    createEventCard(event) {
        const isEventPast = new Date(`${event.date} ${event.time}`) < new Date();
        const isFull = event.remainingSeats <= 0;
        const isLowSeats = event.remainingSeats <= 5 && event.remainingSeats > 0;

        let seatsClass = 'seats-available';
        if (isFull) seatsClass = 'seats-full';
        else if (isLowSeats) seatsClass = 'seats-low';

        return `
            <div class="event-card" data-event-id="${event.id}">
                <div class="event-header">
                    <div>
                        <h3 class="event-title">${event.title}</h3>
                        <span class="event-category">${event.category || 'General'}</span>
                    </div>
                </div>
                <div class="event-details">
                    <div class="event-detail">
                        <i class="fas fa-calendar"></i>
                        <span>${this.formatDate(event.date)}</span>
                    </div>
                    <div class="event-detail">
                        <i class="fas fa-clock"></i>
                        <span>${event.time}</span>
                    </div>
                    <div class="event-detail">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${event.location}</span>
                    </div>
                </div>
                <div class="event-footer">
                    <div class="event-seats">
                        <i class="fas fa-users"></i>
                        <span class="${seatsClass}">
                            ${event.remainingSeats} seats left
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    async showEventDetails(event) {
        // Add to recently viewed
        this.addToRecentlyViewed(event);

        try {
            // Fetch fresh event data
            const response = await fetch(`/api/events/${event.id}`);
            if (response.ok) {
                event = await response.json();
            }
        } catch (error) {
            console.error('Error fetching event details:', error);
        }

        const modalBody = document.getElementById('modal-body');
        const isEventPast = new Date(`${event.date} ${event.time}`) < new Date();
        const isFull = event.remainingSeats <= 0;

        modalBody.innerHTML = `
            <div class="event-modal-header">
                <h2 class="event-modal-title">${event.title}</h2>
                <span class="event-category">${event.category || 'General'}</span>
            </div>
            
            <div class="event-modal-details">
                <div class="event-modal-detail">
                    <i class="fas fa-calendar"></i>
                    <span><strong>Date:</strong> ${this.formatDate(event.date)}</span>
                </div>
                <div class="event-modal-detail">
                    <i class="fas fa-clock"></i>
                    <span><strong>Time:</strong> ${event.time}</span>
                </div>
                <div class="event-modal-detail">
                    <i class="fas fa-map-marker-alt"></i>
                    <span><strong>Location:</strong> ${event.location}</span>
                </div>
            </div>

            <div class="event-description">
                <h4>Description</h4>
                <p>${event.description || 'No description available.'}</p>
            </div>

            <div class="registration-stats">
                <div class="stat-card">
                    <div class="stat-number">${event.registeredCount || 0}</div>
                    <div class="stat-label">Registered</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${event.remainingSeats || 0}</div>
                    <div class="stat-label">Remaining</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${event.totalSeats || 0}</div>
                    <div class="stat-label">Total Seats</div>
                </div>
            </div>

            <div class="event-actions" style="text-align: center;">
                ${this.getEventActionButton(event, isEventPast, isFull)}
            </div>
        `;

        document.getElementById('event-modal').style.display = 'block';
    }

    getEventActionButton(event, isEventPast, isFull) {
        if (isEventPast) {
            return '<button class="btn btn-secondary" disabled><i class="fas fa-clock"></i> Event Ended</button>';
        }
        
        if (isFull) {
            return '<button class="btn btn-full" disabled><i class="fas fa-users"></i> Event Full</button>';
        }

        return `<button class="btn btn-primary" onclick="eventManager.showRegistrationForm('${event.id}')">
            <i class="fas fa-user-plus"></i> Register for Event
        </button>`;
    }

    showRegistrationForm(eventId) {
        this.currentEventId = eventId;
        document.getElementById('event-modal').style.display = 'none';
        document.getElementById('registration-modal').style.display = 'block';
    }

    async handleRegistration() {
        const formData = new FormData(document.getElementById('registration-form'));
        const registrationData = {
            name: formData.get('name'),
            email: formData.get('email')
        };

        try {
            const response = await fetch(`/api/events/${this.currentEventId}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(registrationData)
            });

            if (response.ok) {
                this.showNotification('Registration successful!', 'success');
                this.closeModals();
                document.getElementById('registration-form').reset();
                
                // Refresh event data
                await this.loadEvents();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showNotification('Registration failed. Please try again.', 'error');
        }
    }

    addToRecentlyViewed(event) {
        // Remove if already exists
        this.recentlyViewed = this.recentlyViewed.filter(e => e.id !== event.id);
        
        // Add to beginning
        this.recentlyViewed.unshift({
            ...event,
            viewedAt: new Date().toISOString()
        });

        // Keep only last 10 items
        this.recentlyViewed = this.recentlyViewed.slice(0, 10);

        // Save to localStorage
        localStorage.setItem('recently_viewed', JSON.stringify(this.recentlyViewed));
    }

    getRecentlyViewed() {
        try {
            const stored = localStorage.getItem('recently_viewed');
            return stored ? JSON.parse(stored) : [];
        } catch {
            return [];
        }
    }

    showEventsView() {
        this.currentView = 'events';
        document.getElementById('home-link').classList.add('active');
        document.getElementById('recently-viewed-link').classList.remove('active');
        
        document.querySelector('.events-section').style.display = 'block';
        document.getElementById('recently-viewed-section').style.display = 'none';
        
        this.filterEvents();
    }

    showRecentlyViewedView() {
        this.currentView = 'recent';
        document.getElementById('recently-viewed-link').classList.add('active');
        document.getElementById('home-link').classList.remove('active');
        
        document.querySelector('.events-section').style.display = 'none';
        document.getElementById('recently-viewed-section').style.display = 'block';
        
        this.renderRecentlyViewed();
    }

    renderRecentlyViewed() {
        const grid = document.getElementById('recently-viewed-grid');
        const noRecent = document.getElementById('no-recent-events');

        if (this.recentlyViewed.length === 0) {
            grid.innerHTML = '';
            noRecent.style.display = 'block';
            return;
        }

        noRecent.style.display = 'none';
        
        grid.innerHTML = this.recentlyViewed.map(event => this.createEventCard(event)).join('');

        // Add click listeners
        grid.querySelectorAll('.event-card').forEach((card, index) => {
            card.addEventListener('click', () => {
                this.showEventDetails(this.recentlyViewed[index]);
            });
        });
    }

    closeModals() {
        document.getElementById('event-modal').style.display = 'none';
        document.getElementById('registration-modal').style.display = 'none';
    }

    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'block' : 'none';
        document.getElementById('events-grid').style.display = show ? 'none' : 'grid';
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
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
    }

    setupOfflineDetection() {
        const offlineIndicator = document.getElementById('offline-indicator');
        
        window.addEventListener('online', () => {
            this.isOnline = true;
            offlineIndicator.style.display = 'none';
            this.connectWebSocket();
            this.loadEvents(); // Refresh events when back online
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            offlineIndicator.style.display = 'block';
        });

        // Initial check
        if (!navigator.onLine) {
            offlineIndicator.style.display = 'block';
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.eventManager = new EventManager();
});