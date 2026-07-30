# Scanbit Modular Testing Backend (Trello, Notion, Cloudflare)

A clean, modularized Flask application for testing **Trello**, **Notion**, and **Cloudflare** integrations on **Render** (`render.com`).

---

## 📂 Modular File Structure

The backend is cleanly divided into separate Python files by service, connected via Flask Blueprints in `app.py`:

```text
├── trello.py                         # Trello OAuth 1.0a & Trello API endpoints
├── notion.py                         # Notion OAuth 2.0 & Notion API endpoints
├── cloudflare.py                     # Cloudflare API Token & DNS endpoints
├── app.py                            # Orchestrator & Interactive HTML Dashboard
├── requirements.txt                  # Python dependencies
├── Procfile                          # Render / WSGI start command
├── render.yaml                       # Optional Render Blueprint spec
└── .env.example                      # Environment variables template
```

---

## 🛠️ Service Modules & Endpoints

### 1️⃣ `trello.py` (Trello Integration)
| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| **`/auth`** | `GET` | Starts Trello OAuth 1.0a authorization flow. |
| **`/callback`** | `GET` | Handles OAuth callback & saves tokens in session. |
| **`/boards`** | `GET` | Lists all Trello boards for the user. |
| **`/boards/<id>/lists`** | `GET` | Lists all columns/lists on a board. |
| **`/cards`** | `POST` | Creates a card (`{"name": "...", "idList": "..."}`). |
| **`/webhook`** | `HEAD`/`POST` | Verifies and captures real-time Trello webhook payloads. |
| **`/webhook-logs`** | `GET` | Inspects captured webhook event payloads. |

### 2️⃣ `notion.py` (Notion Integration)
| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| **`/notion/auth`** | `GET` | Starts Notion OAuth 2.0 authorization flow. |
| **`/notion/callback`** | `GET` | Exchanges code for Notion access token & saves to session. |
| **`/notion/users`** | `GET` | Lists users & bots in the workspace (verifies token). |
| **`/notion/search`** | `GET`/`POST` | Searches shared databases & pages in the workspace. |
| **`/notion/pages`** | `POST` | Creates a Notion page (`{"parent_id": "...", "title": "..."}`). |

### 3️⃣ `cloudflare.py` (Cloudflare Integration)
| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| **`/cloudflare/verify`** | `GET` | Verifies Cloudflare API Token validity. |
| **`/cloudflare/zones`** | `GET` | Lists all Cloudflare Zones (domains). |
| **`/cloudflare/zones/<id>/dns`** | `GET`/`POST` | Lists or creates DNS records (`{"type": "TXT", "name": "...", "content": "..."}`). |

### 4️⃣ `app.py` (Orchestrator & UI)
| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| **`/`** | `GET` | Renders a styled HTML dashboard with buttons to test all 3 services. (Returns JSON if requested via API/curl). |
| **`/health`** | `GET` | Health check endpoint for Render. |

---

## 🚀 How to Deploy on Render (Step-by-Step)

### Step 1: Push to GitHub
In this folder, run:
```bash
git init
git add .
git commit -m "Deploy modular Trello, Notion, and Cloudflare testing backend"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### Step 2: Create a Render Web Service
1. Go to [dashboard.render.com](https://dashboard.render.com/) → **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type:** `Free`

### Step 3: Add Environment Variables in Render
In the **Environment** tab of your Render Web Service, configure the keys you need:

| Key | Example / Value | Required For |
| :--- | :--- | :--- |
| `FLASK_SECRET_KEY` | `your_secure_random_string` | All services |
| `FLASK_ENV` | `production` | All services |
| `TRELLO_API_KEY` | `your_trello_api_key` | `trello.py` |
| `TRELLO_API_SECRET` | `your_trello_api_secret` | `trello.py` |
| `CALLBACK_URL` | `https://your-app.onrender.com/callback` | `trello.py` |
| `NOTION_TOKEN` | `secret_notion_integration_token` | `notion.py` (direct API) |
| `NOTION_CLIENT_ID` | `your_notion_client_id` | `notion.py` (OAuth) |
| `NOTION_CLIENT_SECRET` | `your_notion_client_secret` | `notion.py` (OAuth) |
| `CLOUDFLARE_API_TOKEN` | `your_cloudflare_token` | `cloudflare.py` |

---

## 🧪 Testing Once Deployed
Open `https://your-app.onrender.com/` in your browser. You will see an interactive web dashboard with buttons to test **Trello**, **Notion**, and **Cloudflare** endpoints directly from your browser!
