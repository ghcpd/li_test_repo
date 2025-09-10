// Global variables
let allZodiacs = [];
let currentFilter = '';
let currentSearch = '';

// DOM elements
const zodiacGrid = document.getElementById('zodiacGrid');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const elementFilter = document.getElementById('elementFilter');
const randomBtn = document.getElementById('randomBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const noResults = document.getElementById('noResults');
const clearFiltersBtn = document.getElementById('clearFilters');
const modal = document.getElementById('zodiacModal');
const modalBody = document.getElementById('modalBody');
const closeModalBtn = document.getElementById('closeModal');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    loadAllZodiacs();
    setupEventListeners();
});

// Set up event listeners
function setupEventListeners() {
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    
    elementFilter.addEventListener('change', handleFilter);
    randomBtn.addEventListener('click', showRandomZodiac);
    clearFiltersBtn.addEventListener('click', clearFilters);
    closeModalBtn.addEventListener('click', closeModal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
}

// Load all zodiac signs
async function loadAllZodiacs() {
    try {
        showLoading(true);
        hideError();
        hideNoResults();
        
        const response = await fetch('/zodiacs');
        const data = await response.json();
        
        if (data.zodiacs) {
            allZodiacs = data.zodiacs;
            displayZodiacs(allZodiacs);
        } else {
            throw new Error('Failed to load zodiac data');
        }
    } catch (error) {
        console.error('Error loading zodiacs:', error);
        showError();
    } finally {
        showLoading(false);
    }
}

// Display zodiac cards
function displayZodiacs(zodiacs) {
    zodiacGrid.innerHTML = '';
    
    if (zodiacs.length === 0) {
        showNoResults();
        return;
    }
    
    hideNoResults();
    
    zodiacs.forEach(zodiac => {
        const card = createZodiacCard(zodiac);
        zodiacGrid.appendChild(card);
    });
}

// Create individual zodiac card
function createZodiacCard(zodiac) {
    const card = document.createElement('div');
    card.className = `zodiac-card ${zodiac.element.toLowerCase()}`;
    card.addEventListener('click', () => showZodiacDetails(zodiac));
    
    // Get preview of personality traits (first 2)
    const previewTraits = zodiac.personality_traits.slice(0, 2).join(', ');
    
    card.innerHTML = `
        <div class="card-header">
            <h2 class="zodiac-name">${zodiac.name}</h2>
            <span class="zodiac-symbol">${zodiac.symbol}</span>
        </div>
        <p class="zodiac-dates">${zodiac.date_range}</p>
        <span class="zodiac-element element-${zodiac.element.toLowerCase()}">
            ${getElementIcon(zodiac.element)} ${zodiac.element}
        </span>
        <p class="card-preview">${previewTraits}...</p>
    `;
    
    return card;
}

// Get element icon
function getElementIcon(element) {
    const icons = {
        'Fire': '🔥',
        'Earth': '🌍',
        'Air': '💨',
        'Water': '💧'
    };
    return icons[element] || '';
}

// Get element color
function getElementColor(element) {
    const colors = {
        'Fire': '#ff6b6b',
        'Earth': '#4ecdc4',
        'Air': '#45b7d1',
        'Water': '#96ceb4'
    };
    return colors[element] || '#667eea';
}

// Handle search
function handleSearch() {
    currentSearch = searchInput.value.trim().toLowerCase();
    filterAndDisplayZodiacs();
}

// Handle filter
function handleFilter() {
    currentFilter = elementFilter.value;
    filterAndDisplayZodiacs();
}

// Filter and display zodiacs based on current search and filter
async function filterAndDisplayZodiacs() {
    try {
        showLoading(true);
        hideError();
        
        let url = '/zodiacs?';
        const params = new URLSearchParams();
        
        if (currentFilter) {
            params.append('element', currentFilter);
        }
        
        if (currentSearch) {
            params.append('search', currentSearch);
        }
        
        url += params.toString();
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.zodiacs) {
            displayZodiacs(data.zodiacs);
        } else {
            throw new Error('Failed to filter zodiac data');
        }
    } catch (error) {
        console.error('Error filtering zodiacs:', error);
        showError();
    } finally {
        showLoading(false);
    }
}

// Show random zodiac
async function showRandomZodiac() {
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch('/zodiacs/random');
        const zodiac = await response.json();
        
        if (zodiac.name) {
            showZodiacDetails(zodiac);
        } else {
            throw new Error('Failed to get random zodiac');
        }
    } catch (error) {
        console.error('Error getting random zodiac:', error);
        showError();
    } finally {
        showLoading(false);
    }
}

// Clear all filters
function clearFilters() {
    currentSearch = '';
    currentFilter = '';
    searchInput.value = '';
    elementFilter.value = '';
    displayZodiacs(allZodiacs);
}

// Show zodiac details in modal
function showZodiacDetails(zodiac) {
    const elementColor = getElementColor(zodiac.element);
    
    modalBody.innerHTML = `
        <div class="modal-header" style="--modal-element-color: ${elementColor}">
            <div class="modal-symbol">${zodiac.symbol}</div>
            <h2 class="modal-title">${zodiac.name}</h2>
            <p class="modal-dates">${zodiac.date_range}</p>
        </div>
        <div class="modal-body">
            <div class="modal-section">
                <h3>${getElementIcon(zodiac.element)} Element: ${zodiac.element}</h3>
            </div>
            
            <div class="modal-section">
                <h3>📜 Origin & History</h3>
                <p>${zodiac.origin}</p>
            </div>
            
            <div class="modal-section">
                <h3>✨ Personality Traits</h3>
                <ul class="traits-list" style="--modal-element-color: ${elementColor}">
                    ${zodiac.personality_traits.map(trait => `<li>${trait}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

// Close modal
function closeModal() {
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

// Show/hide loading indicator
function showLoading(show) {
    if (show) {
        loadingIndicator.classList.remove('hidden');
        zodiacGrid.classList.add('hidden');
    } else {
        loadingIndicator.classList.add('hidden');
        zodiacGrid.classList.remove('hidden');
    }
}

// Show error message
function showError() {
    errorMessage.classList.remove('hidden');
    zodiacGrid.classList.add('hidden');
    hideNoResults();
}

// Hide error message
function hideError() {
    errorMessage.classList.add('hidden');
}

// Show no results message
function showNoResults() {
    noResults.classList.remove('hidden');
}

// Hide no results message
function hideNoResults() {
    noResults.classList.add('hidden');
}