# Scanbit Trello OAuth Testing Backend

A minimal Flask backend for testing Trello OAuth 1.0a authentication, ready to be deployed to **Render** (`render.com`).

---

## 🛠️ What Was Fixed & Improved

1. **Fixed Link & Syntax Artifacts:**
   - Removed Markdown link formatting (`[https://...](https://...)`) from `REQUEST_TOKEN_URL`, `AUTHORIZE_URL`, `ACCESS_TOKEN_URL`, and Trello API URLs.
   - Corrected `if **name** == "__main__":` to valid Python syntax: `if __name__ == "__main__":`.
2. **Render Port & WSGI Compatibility:**
   - Added `os.environ.get("PORT", 8000)` so Render can bind to its dynamic `$PORT`.
   - Added `gunicorn` to `requirements.txt` and created a `Procfile` for production deployment on Render.
3. **Session & Cookie Handling:**
   - Added error handling if `resource_owner_key` / `resource_owner_secret` is missing from the session.
   - Configured cookie settings (`SESSION_COOKIE_SAMESITE = "Lax"`) so Flask session cookies survive cross-site OAuth redirects from Trello.
4. **Conveniences for Testing:**
   - Added `/` (Home) endpoint so visiting the base URL on Render doesn't return a 400/404 error.
   - Added `/health` endpoint for uptime checks and Render deployment verification.

---

## 🚀 How to Deploy on Render (Step-by-Step)

### Step 1: Push to GitHub
1. Initialize a Git repository and push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Trello OAuth backend"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

### Step 2: Create a Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the service settings:
   - **Name:** `scanbit-trello-backend` (or your choice)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type:** `Free` (or higher if desired)

### Step 3: Add Environment Variables in Render
In the **Environment** tab of your Render Web Service, add the following key-value pairs:

| Key | Value / Example |
| :--- | :--- |
| `FLASK_SECRET_KEY` | A random secure secret string (e.g., `8d7a12b9c8e14e7a8...`) |
| `FLASK_ENV` | `production` |
| `TRELLO_API_KEY` | Your Trello Power-Up / API key |
| `TRELLO_API_SECRET` | Your Trello Power-Up / API secret |
| `CALLBACK_URL` | `https://your-app-name.onrender.com/callback` *(Replace with your actual Render URL)* |

---

## 🔑 Step 4: Register Callback URL in Trello
1. Go to the [Trello Power-Ups Admin Portal](https://trello.com/power-ups/admin).
2. Select your Power-Up / API integration.
3. In the **Allowed Origin / Callback URL** settings, ensure that your exact Render callback URL is allowed:
   ```
   https://your-app-name.onrender.com/callback
   ```

---

## 🧪 Testing Your Backend

1. **Health Check:**
   - Open `https://your-app-name.onrender.com/` or `https://your-app-name.onrender.com/health`.
   - You should see:
     ```json
     {
       "service": "Scanbit Trello OAuth Backend",
       "status": "running"
     }
     ```

2. **Start OAuth Authorization:**
   - Open `https://your-app-name.onrender.com/auth` in your browser.
   - It will redirect you to Trello’s permission screen asking to authorize **Scanbit**.

3. **Complete Callback & Inspect Token:**
   - After approving on Trello, you will be redirected back to `/callback`.
   - The response will display your Trello access token, secret, and user profile data in JSON format:
     ```json
     {
       "status": "Connected",
       "access_token": "your_oauth_access_token",
       "access_secret": "your_oauth_access_secret",
       "user": {
         "id": "...",
         "username": "...",
         "fullName": "..."
       }
     }
     ```
