# Zodiac Explorer

A minimal Flask-based Zodiac Explorer that lets you search zodiac signs by name, filter by element, and view details dynamically.

Quickstart

- Install dependencies: pip install -r requirements.txt
- Run the app: python app.py
- Open http://127.0.0.1:5000 in your browser

API Endpoints

- GET /zodiacs — List all zodiac signs, with optional query params:
  - search: case-insensitive partial name match (e.g., /zodiacs?search=ar)
  - element: filter by element (Fire, Earth, Air, Water) (e.g., /zodiacs?element=Water)
  - random: when true, returns a single random sign from the current result set (e.g., /zodiacs?random=true)
- GET /zodiacs/<name> — Get details for a specific zodiac (e.g., /zodiacs/Aries)

Features

- Search and filter with instant updates
- Click a card to display a details panel
- Color-coded elements (Fire, Earth, Air, Water)
- Loading and error states

Screenshots

- Full view: https://github.com/user-attachments/assets/7671aa22-197d-4d69-b645-04a8232b4f7c
- Filtered view: https://github.com/user-attachments/assets/c20c376b-cf51-4af7-8106-b6ae9dd0b3b1
