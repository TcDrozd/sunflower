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