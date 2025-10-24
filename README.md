# Zodiac Explorer

An interactive Flask application for exploring zodiac signs. The experience features dynamic search and filtering, a surprise-me randomiser, and richly styled detail panels that surface mythology, symbols, and personality traits for every sign.

## Getting started

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the development server**
   ```bash
   flask --app app run --debug
   ```
   The site will be available at <http://127.0.0.1:5000>.

> ℹ️ The project uses a simple Flask factory (`create_app`) so you can also start it with `python app.py` if you prefer a direct script entrypoint.

## Running tests

Execute the automated test suite with:
```bash
python -m pytest
```

## Available API routes

| Route | Description |
| --- | --- |
| `GET /zodiacs` | Returns all zodiac signs. Optional query params: `q` (search by name/symbol) and `element` (Fire, Earth, Air, Water). |
| `GET /zodiacs/<slug>` | Returns the full payload for a specific zodiac sign. |
| `GET /zodiacs/random` | Surface a random sign for the “Surprise me” interaction. |

## Project structure

```
.
├── app.py              # Flask application factory and routes
├── data/
│   └── zodiacs.json    # Canonical zodiac catalogue
├── templates/
│   └── index.html      # Primary layout and controls
├── static/
│   ├── css/styles.css  # Visual styling and responsive layout
│   └── js/app.js       # Client-side interactions & rendering
├── tests/
│   └── test_zodiac_api.py
└── requirements.txt
```

## Design notes

- Cards are colour-coded by element and render without page reload via the JSON API.
- Client-side filtering keeps the UI responsive while backend routes power deep links and validation.
- Loading states and error messaging ensure graceful feedback even when the cosmos goes quiet.
