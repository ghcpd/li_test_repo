# Zodiac Explorer Website

A visually appealing and functional web application for exploring zodiac signs, built with Flask and vanilla JavaScript.

## Features

- **Search Functionality**: Search for zodiac signs by name with real-time validation
- **Element Filtering**: Filter zodiac signs by their element (Fire, Earth, Air, Water)
- **Random Zodiac**: Get a random zodiac sign with one click
- **Interactive Cards**: Click any zodiac card to view detailed information
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Color-Coded Elements**: Each element has its own color theme
- **Dynamic Modal**: View detailed zodiac information without page reload
- **Error Handling**: User-friendly error messages for invalid searches

## Tech Stack

- **Backend**: Flask 3.0.0
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Data**: JSON file storage
- **Design**: Responsive, mobile-first design with gradient backgrounds

## Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd li_test_repo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

### API Endpoints

The application provides the following RESTful API endpoints:

- **GET /api/zodiacs** - Get all zodiac signs
  - Optional query parameter: `element` (fire, earth, air, water)
  - Example: `/api/zodiacs?element=fire`

- **GET /api/zodiacs/<name>** - Get a specific zodiac sign by name
  - Example: `/api/zodiacs/aries`

- **GET /api/zodiacs/random/get** - Get a random zodiac sign

### Example API Responses

**Get all zodiacs:**
```json
[
  {
    "id": 1,
    "name": "Aries",
    "date_range": "March 21 - April 19",
    "symbol": "♈",
    "element": "Fire",
    "origin": "...",
    "personality_traits": [...]
  },
  ...
]
```

**Get specific zodiac:**
```json
{
  "id": 1,
  "name": "Aries",
  "date_range": "March 21 - April 19",
  "symbol": "♈",
  "element": "Fire",
  "origin": "...",
  "personality_traits": [...]
}
```

## Project Structure

```
li_test_repo/
├── app.py                 # Flask application with API routes
├── zodiac_data.json      # Zodiac signs data
├── requirements.txt      # Python dependencies
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Styling with element-based colors
│   └── js/
│       └── app.js        # Frontend JavaScript logic
└── README.md             # This file
```

## Features in Detail

### Search & Filter
- Type a zodiac name in the search box to find specific signs
- Use the element filter dropdown to view signs by element type
- Clear search to return to all zodiacs

### Interactive Display
- Click any zodiac card to view detailed information
- Modal appears with origin story and personality traits
- Click outside modal or press ESC to close

### Random Zodiac
- Click the "Random Zodiac" button to discover a surprise sign
- Opens directly in the detail modal

### Color Coding
- **Fire** (🔥): Red/Orange theme (Aries, Leo, Sagittarius)
- **Earth** (🌍): Brown/Tan theme (Taurus, Virgo, Capricorn)
- **Air** (💨): Cyan/Turquoise theme (Gemini, Libra, Aquarius)
- **Water** (💧): Blue theme (Cancer, Scorpio, Pisces)

### Error Handling
- Invalid zodiac searches show friendly error messages
- API failures are caught and displayed to users
- Auto-dismissing error notifications

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Development

### Running in Debug Mode

The application runs in debug mode by default during development:
```bash
python app.py
```

Debug mode provides:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger

### Customization

**To add more zodiac signs:**
Edit `zodiac_data.json` and add new entries following the existing format.

**To change colors:**
Edit `static/css/style.css` and modify the CSS variables in the `:root` section.

**To modify API behavior:**
Edit `app.py` and add or modify routes as needed.

## License

This project is created for educational purposes.

## Contributing

Feel free to submit issues and pull requests for improvements.