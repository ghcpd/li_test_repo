// State
let allZodiacs = [];
let currentFilter = '';

// DOM Elements
const zodiacGrid = document.getElementById('zodiacGrid');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const elementFilter = document.getElementById('elementFilter');
const randomBtn = document.getElementById('randomBtn');
const modal = document.getElementById('zodiacModal');
const modalBody = document.getElementById('modalBody');
const modalClose = document.querySelector('.modal-close');
const errorMessage = document.getElementById('errorMessage');
const loadingState = document.getElementById('loadingState');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadAllZodiacs();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    
    elementFilter.addEventListener('change', handleFilterChange);
    randomBtn.addEventListener('click', handleRandomZodiac);
    
    modalClose.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            closeModal();
        }
    });
}

// API Functions
async function loadAllZodiacs() {
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch('/api/zodiacs');
        if (!response.ok) {
            throw new Error('Failed to load zodiac signs');
        }
        
        allZodiacs = await response.json();
        displayZodiacs(allZodiacs);
        showLoading(false);
    } catch (error) {
        showError('Failed to load zodiac signs. Please try again.');
        showLoading(false);
        console.error('Error:', error);
    }
}

async function searchZodiacByName(name) {
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch(`/api/zodiacs/${encodeURIComponent(name)}`);
        
        if (response.status === 404) {
            showError(`Zodiac sign "${name}" not found. Please try another name.`);
            displayZodiacs(allZodiacs);
            showLoading(false);
            return;
        }
        
        if (!response.ok) {
            throw new Error('Failed to search zodiac sign');
        }
        
        const zodiac = await response.json();
        displayZodiacs([zodiac]);
        showLoading(false);
    } catch (error) {
        showError('Search failed. Please try again.');
        showLoading(false);
        console.error('Error:', error);
    }
}

async function filterByElement(element) {
    try {
        showLoading(true);
        hideError();
        
        const url = element ? `/api/zodiacs?element=${encodeURIComponent(element)}` : '/api/zodiacs';
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Failed to filter zodiac signs');
        }
        
        const zodiacs = await response.json();
        displayZodiacs(zodiacs);
        showLoading(false);
    } catch (error) {
        showError('Filter failed. Please try again.');
        showLoading(false);
        console.error('Error:', error);
    }
}

async function getRandomZodiac() {
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch('/api/zodiacs/random/get');
        
        if (!response.ok) {
            throw new Error('Failed to get random zodiac sign');
        }
        
        const zodiac = await response.json();
        showLoading(false);
        openModal(zodiac);
    } catch (error) {
        showError('Failed to get random zodiac. Please try again.');
        showLoading(false);
        console.error('Error:', error);
    }
}

// Event Handlers
function handleSearch() {
    const searchTerm = searchInput.value.trim();
    
    if (!searchTerm) {
        // If search is empty, show all or filtered zodiacs
        if (currentFilter) {
            filterByElement(currentFilter);
        } else {
            displayZodiacs(allZodiacs);
        }
        return;
    }
    
    searchZodiacByName(searchTerm);
}

function handleFilterChange(e) {
    const element = e.target.value;
    currentFilter = element;
    
    // Clear search input when filtering
    searchInput.value = '';
    
    filterByElement(element);
}

function handleRandomZodiac() {
    getRandomZodiac();
}

// Display Functions
function displayZodiacs(zodiacs) {
    if (zodiacs.length === 0) {
        zodiacGrid.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">No zodiac signs found.</p>';
        return;
    }
    
    zodiacGrid.innerHTML = zodiacs.map(zodiac => createZodiacCard(zodiac)).join('');
    
    // Add click listeners to cards
    const cards = document.querySelectorAll('.zodiac-card');
    cards.forEach((card, index) => {
        card.addEventListener('click', () => openModal(zodiacs[index]));
    });
}

function createZodiacCard(zodiac) {
    const elementClass = zodiac.element.toLowerCase();
    
    return `
        <article class="zodiac-card ${elementClass}" tabindex="0" role="button" aria-label="View details for ${zodiac.name}">
            <div class="card-header">
                <span class="card-symbol" aria-hidden="true">${zodiac.symbol}</span>
                <h2 class="card-name">${zodiac.name}</h2>
                <p class="card-dates">${zodiac.date_range}</p>
            </div>
            <div class="card-element ${elementClass}">
                ${getElementEmoji(zodiac.element)} ${zodiac.element}
            </div>
        </article>
    `;
}

function openModal(zodiac) {
    const elementClass = zodiac.element.toLowerCase();
    
    modalBody.innerHTML = `
        <div class="modal-header">
            <span class="modal-symbol" aria-hidden="true">${zodiac.symbol}</span>
            <h2 class="modal-name" id="modalTitle">${zodiac.name}</h2>
            <p class="modal-dates">${zodiac.date_range}</p>
            <div class="card-element ${elementClass}">
                ${getElementEmoji(zodiac.element)} ${zodiac.element}
            </div>
        </div>
        
        <div class="modal-section">
            <h3>Origin & History</h3>
            <p>${zodiac.origin}</p>
        </div>
        
        <div class="modal-section">
            <h3>Personality Traits</h3>
            <ul class="trait-list">
                ${zodiac.personality_traits.map(trait => `<li>${trait}</li>`).join('')}
            </ul>
        </div>
    `;
    
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // Focus on close button for accessibility
    setTimeout(() => modalClose.focus(), 100);
}

function closeModal() {
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

// UI Helper Functions
function showLoading(show) {
    loadingState.style.display = show ? 'block' : 'none';
    zodiacGrid.style.display = show ? 'none' : 'grid';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
    
    // Auto-hide error after 5 seconds
    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    errorMessage.classList.remove('show');
}

function getElementEmoji(element) {
    const emojis = {
        'Fire': '🔥',
        'Earth': '🌍',
        'Air': '💨',
        'Water': '💧'
    };
    return emojis[element] || '';
}
