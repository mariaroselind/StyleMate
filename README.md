# StyleMate — AI Fashion Advisor Agent

A Flask web app for fashion suggestions. Rule-based or optional AI-powered.

## Setup
1. Create folder `C:\Users\MARIA ROSELIND\vibe_flask`.
2. Save files: `app.py`, `requirements.txt`, templates, static.
3. Create virtual env: `python -m venv venv` and activate: `venv\Scripts\activate`.
4. Install: `pip install -r requirements.txt`.
5. Copy `.env.example` to `.env`, add `SECRET_KEY=your_secret`, optional `OPENAI_API_KEY=sk-your-key`.
6. Download 8 images from Unsplash (search "fashion outfit"), rename to outfit1.jpg–outfit8.jpg, place in static/images/.
7. Run: `flask run`.
8. Open http://127.0.0.1:5000/.

## Images
Search Unsplash[](https://unsplash.com/s/photos/fashion-outfit), download 8 images, rename to outfit1.jpg–outfit8.jpg.

## Features
- Home: Form + gallery (8 images).
- Auth: Signup/login/logout/profile.
- Suggestions: Rule-based (color detection, categorization) or OpenAI if enabled.
