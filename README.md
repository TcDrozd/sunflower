# 🌻 Sunflower Photo Journal

A simple Flask web app for logging, previewing, and tracking the growth of a sunflower (or any other plant) over time — complete with photo uploads, modal views, and lazy loading for smooth performance.

---

## ✨ Features

- 📸 Upload daily or milestone photos of your sunflower
- 🖼️ Lazy-loaded thumbnails and previews to reduce load time
- 🔍 Modal view with metadata for each photo
- 🗑️ Delete functionality for managing your photo journal
- 🧠 Cleanly separated routes and logic for easy maintenance
- ⚙️ Planned Dockerization for portable deployment

---

## 🚀 Planned Dockerization

We are working toward a Dockerized deployment that will:

- Use a `Dockerfile` and `docker-compose.yml` to spin up the app and any future backing services
- Provide production-ready builds while supporting local development workflows
- Include an `.env` file for environment-specific settings (excluded from version control)

---

## 🛠️ Tech Stack

- **Backend**: Python + Flask
- **Frontend**: Jinja2 templates + vanilla JS
- **Storage**: JSON-based metadata, local file storage
- **Image Processing**: Pillow for generating thumbnails and previews

---

## 📁 Project Structure

sunflower2/
├── app/                  # App logic (routes, helpers)
├── static/               # Uploads, thumbnails, previews, JS
├── templates/            # Jinja2 templates
├── venv/                 # Virtual environment (excluded)
├── app.py                # App initialization
├── .gitignore
└── requirements.txt      # Python dependencies

---

## ⚙️ Running Locally

1. Clone the repo:
   ```bash
   git clone git@github.com:TcDrozd/sunflower.git
   cd sunflower2

	2.	Create a virtual environment and install dependencies:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


	3.	Run the app:

python app.py



Then open your browser to http://127.0.0.1:5000.

⸻

📦 To-Do
	•	Add Dockerfile and docker-compose.yml
	•	Enable optional cloud photo storage
	•	Add tagging or notes for photos
	•	Improve responsive layout for mobile
	•	Add user auth (optional for multi-user)

⸻

📝 License

MIT (or specify if you want another).

⸻

🌻 Why?

Because tracking the growth of something you care about is meaningful — and this app makes it beautifully simple.
Or in other words,

## Because I can