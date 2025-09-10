# 🌟 Zodiac Explorer Website

A visually appealing and functional Zodiac Explorer Website built with Flask that allows users to discover and explore all 12 zodiac signs with detailed information, interactive features, and beautiful design.

## ✨ Features

### Core Functionality
- **Search Zodiac Signs**: Search for any zodiac sign by name with real-time filtering
- **Element Filtering**: Filter zodiac signs by their elements (Fire, Earth, Air, Water)
- **Interactive Display**: Click any zodiac card to view detailed information in a beautiful modal
- **Random Zodiac**: Discover a random zodiac sign with the click of a button
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

### Detailed Information
Each zodiac sign includes:
- **Name & Symbol**: Traditional zodiac name and Unicode symbol
- **Date Range**: Birth date ranges for each sign
- **Element**: Fire, Earth, Air, or Water with color-coding
- **Origin & History**: Historical background and mythology
- **Personality Traits**: Comprehensive list of characteristics

### UI/UX Features
- **Color-Coded Elements**: Each element has its own color scheme (Fire: Red, Earth: Teal, Air: Blue, Water: Green)
- **Card-Style Layout**: Clean, modern card design for each zodiac sign
- **Loading States**: Smooth loading indicators for better user experience
- **Error Handling**: Graceful handling of invalid searches with helpful messages
- **Keyboard Navigation**: Support for Enter key in search and Escape key to close modals

## 🛠️ Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Data**: JSON-based zodiac information storage
- **Styling**: Custom CSS with responsive design and animations
- **Icons**: Unicode symbols and emoji

## 📋 API Endpoints

### GET /
Main application page serving the zodiac explorer interface

### GET /zodiacs
Get all zodiac signs with optional filtering
- **Query Parameters**:
  - `element` (optional): Filter by element (fire, earth, air, water)
  - `search` (optional): Search by zodiac name

### GET /zodiacs/{name}
Get detailed information for a specific zodiac sign
- **Path Parameter**: `name` - Name of the zodiac sign (case-insensitive)

### GET /zodiacs/random
Get a random zodiac sign for discovery

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd li_test_repo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000` to start exploring!

## 📁 Project Structure

```
li_test_repo/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── zodiac_data.json       # Zodiac signs data
├── templates/
│   └── index.html         # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   └── js/
│       └── script.js      # JavaScript functionality
└── README.md              # This file
```

## 🎨 Design Features

### Color Scheme
- **Fire Signs**: Warm red gradient (#ff6b6b)
- **Earth Signs**: Natural teal (#4ecdc4)
- **Air Signs**: Sky blue (#45b7d1)
- **Water Signs**: Ocean green (#96ceb4)
- **Background**: Purple gradient for mystical feel

### Typography
- **Font**: Poppins (Google Fonts) for modern, clean appearance
- **Hierarchy**: Clear heading structure with appropriate sizing

### Animations
- **Hover Effects**: Cards lift with shadow on hover
- **Modal Transitions**: Smooth slide-in animation
- **Loading Spinner**: Elegant rotating spinner for loading states

## 🔧 Customization

### Adding New Zodiac Signs
Edit `zodiac_data.json` to add or modify zodiac information:

```json
{
  "name": "SignName",
  "date_range": "Month Day - Month Day",
  "symbol": "♈ Symbol",
  "element": "Element",
  "origin": "Historical background...",
  "personality_traits": [
    "Trait 1",
    "Trait 2"
  ]
}
```

### Styling Modifications
- Main styles: `static/css/style.css`
- Color variables defined at the top of CSS file
- Responsive breakpoints for mobile optimization

## 🌟 Screenshots

The application features a beautiful, responsive design with:
- Clean card layout showing all zodiac signs
- Interactive modals with detailed information
- Element-based filtering and search functionality
- Color-coded elements for easy identification

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🎯 Future Enhancements

- Compatibility calculations between zodiac signs
- Daily horoscope integration
- Zodiac calendar view
- Social sharing features
- User favorites and bookmarking
- Multi-language support