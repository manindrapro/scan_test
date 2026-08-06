# ===============================================================================
# SCANBIT MULTI-SERVICE TESTING BACKEND (ORCHESTRATOR FOR RENDER)
# Modularized into: trello.py, notion.py, cloudflare.py
# ===============================================================================

import os
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

# Import our modularized service Blueprints
from trello import trello_bp
from notion import notion_bp
from cloudflare import cloudflare_bp
from okta import okta_bp

load_dotenv()

app = Flask(__name__)

# Secure secret key for Flask sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-render")

# Modern browser cookie settings so sessions survive OAuth redirects across domains
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"

# ===============================================================================
# REGISTER MODULAR BLUEPRINTS
# ===============================================================================
app.register_blueprint(trello_bp)
app.register_blueprint(notion_bp)
app.register_blueprint(cloudflare_bp)
app.register_blueprint(okta_bp)

# ===============================================================================
# HOME / DASHBOARD ROUTE (ONE-PAGE UI + JSON API)
# ===============================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scanbit Backend Testing Hub</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            color: #38bdf8;
            border-bottom: 2px solid #1e293b;
            padding-bottom: 0.5rem;
        }
        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        .card h2 {
            margin-top: 0;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .btn {
            display: inline-block;
            background: #0284c7;
            color: white;
            text-decoration: none;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: 600;
            margin-right: 10px;
            margin-bottom: 10px;
            transition: background 0.2s;
        }
        .btn:hover {
            background: #0369a1;
        }
        .btn-green { background: #16a34a; }
        .btn-green:hover { background: #15803d; }
        .btn-purple { background: #9333ea; }
        .btn-purple:hover { background: #7e22ce; }
        .btn-orange { background: #ea580c; }
        .btn-orange:hover { background: #c2410c; }
        code {
            background: #0f172a;
            padding: 2px 6px;
            border-radius: 4px;
            color: #38bdf8;
            font-size: 0.9em;
        }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            background: #065f46;
            color: #a7f3d0;
            font-size: 0.85em;
            font-weight: 700;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Scanbit Backend Testing Hub <span class="status">ONLINE</span></h1>
        <p>Modular Flask server for testing <b>Trello</b>, <b>Notion</b>, and <b>Cloudflare</b> APIs on Render.</p>

        <!-- TRELLO CARD -->
        <div class="card">
            <h2>🟦 Trello Integration (trello.py)</h2>
            <p>Connect your Trello Power-Up / API and test board & card endpoints.</p>
            <div>
                <a href="/auth" class="btn">1. Start OAuth (/auth)</a>
                <a href="/boards" class="btn btn-green" target="_blank">2. List Boards (/boards)</a>
                <a href="/webhook-logs" class="btn" target="_blank">Webhook Logs</a>
            </div>
            <p><small>Callback URL: <code>/callback</code> | Webhook Receiver: <code>/webhook</code></small></p>
        </div>

        <!-- NOTION CARD -->
        <div class="card">
            <h2>⬛ Notion Integration (notion.py)</h2>
            <p>Connect your Notion workspace and search shared pages & databases.</p>
            <div>
                <a href="/notion/auth" class="btn btn-purple">1. Connect Notion (/notion/auth)</a>
                <a href="/notion/users" class="btn btn-green" target="_blank">2. Test Users (/notion/users)</a>
                <a href="/notion/search" class="btn" target="_blank">Search Workspace (/notion/search)</a>
            </div>
            <p><small>Callback URL: <code>/notion/callback</code> | Create Page: <code>POST /notion/pages</code></small></p>
        </div>

        <!-- CLOUDFLARE CARD -->
        <div class="card">
            <h2>🟧 Cloudflare Integration (cloudflare.py)</h2>
            <p>Connect your Cloudflare account via OAuth 2.0 or test API token zones.</p>
            <div>
                <a href="/cloudflare/login" class="btn btn-orange">1. Connect Cloudflare OAuth (/cloudflare/login)</a>
                <a href="/cloudflare/verify" class="btn" target="_blank">2. Verify Token (/cloudflare/verify)</a>
                <a href="/cloudflare/zones" class="btn btn-green" target="_blank">3. List Zones (/cloudflare/zones)</a>
            </div>
            <p><small>Callback URL: <code>/cloudflare/callback</code> | DNS Records: <code>GET/POST /cloudflare/zones/&lt;zone_id&gt;/dns</code></small></p>
        </div>

        <!-- OKTA CARD -->
        <div class="card">
            <h2>🟪 Okta Integration (okta.py)</h2>
            <p>Connect your Okta account and test user & group endpoints.</p>
            <div>
                <a href="/okta/auth" class="btn btn-purple">1. Connect Okta (/okta/auth)</a>
                <a href="/okta/me" class="btn" target="_blank">2. View User (/okta/me)</a>
                <a href="/okta/users" class="btn btn-green" target="_blank">3. List Users (/okta/users)</a>
            </div>
            <p><small>Callback URL: <code>/okta/callback</code> | User Info: <code>GET /okta/me</code></small></p>
        </div>

        <!-- SYSTEM CARD -->
        <div class="card">
            <h2>⚙️ System & Health</h2>
            <div>
                <a href="/health" class="btn" target="_blank">Health Check (/health)</a>
                <a href="/?format=json" class="btn" target="_blank">View JSON API Summary</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    # Return JSON directory if requested via curl / API
    if request.args.get("format") == "json" or "application/json" in request.headers.get("Accept", ""):
        return jsonify({
            "service": "Scanbit Modular Testing Backend",
            "status": "running",
            "modules": {
                "trello_file": "trello.py",
                "notion_file": "notion.py",
                "cloudflare_file": "cloudflare.py",
                "okta_file": "okta.py"
            },
            "endpoints": {
                "trello": {
                    "oauth_start": "/auth",
                    "oauth_callback": "/callback",
                    "boards": "/boards",
                    "lists": "/boards/<board_id>/lists",
                    "create_card": "POST /cards",
                    "webhook_receiver": "/webhook (HEAD/POST)",
                    "webhook_logs": "/webhook-logs"
                },
                "notion": {
                    "oauth_start": "/notion/auth",
                    "oauth_callback": "/notion/callback",
                    "list_users": "/notion/users",
                    "search_workspace": "/notion/search",
                    "create_page": "POST /notion/pages"
                },
                "cloudflare": {
                    "oauth_login": "/cloudflare/login",
                    "oauth_callback": "/cloudflare/callback",
                    "verify_token": "/cloudflare/verify",
                    "list_zones": "/cloudflare/zones",
                    "list_dns": "/cloudflare/zones/<zone_id>/dns",
                    "create_dns": "POST /cloudflare/zones/<zone_id>/dns"
                },
                "okta": {
                    "oauth_login": "/okta/auth",
                    "oauth_callback": "/okta/callback",
                    "view_user": "/okta/me",
                    "list_users": "/okta/users"
                },
                
                "system": {
                    "health": "/health",
                    "json_summary": "/?format=json"
                }
            }
        })
    return render_template_string(DASHBOARD_HTML)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
