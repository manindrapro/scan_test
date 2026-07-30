import os
import requests
from flask import Blueprint, redirect, request, session, jsonify
from requests_oauthlib import OAuth2Session

cloudflare_bp = Blueprint("cloudflare", __name__)

# ==========================
# Configuration (Render & OAuth 2.0)
# ==========================
CLIENT_ID = os.getenv("CLOUDFLARE_CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLOUDFLARE_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

AUTHORIZATION_BASE_URL = "https://dash.cloudflare.com/oauth2/auth"
TOKEN_URL = "https://dash.cloudflare.com/oauth2/token"
REDIRECT_URI = os.getenv("CLOUDFLARE_REDIRECT_URI", "https://your-app-name.onrender.com/cloudflare/callback")

SCOPES = [
    "account:read",
    "zone:read"
]

# Allow insecure OAuth transport only in local development (remove/disable in Render production)
if os.getenv("FLASK_ENV") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


# -----------------------------------
# Helper: Get Cloudflare Headers
# -----------------------------------
def get_cloudflare_headers():
    """
    Returns Cloudflare API headers using session OAuth token, query param, or env CLOUDFLARE_API_TOKEN.
    """
    token = (request.args.get("token") or 
             request.headers.get("X-Cloudflare-Token") or 
             session.get("cloudflare_token") or
             os.getenv("CLOUDFLARE_API_TOKEN"))
    if not token:
        return None, jsonify({
            "error": "Missing Cloudflare token. Visit /cloudflare/login to authenticate via OAuth 2.0, or pass ?token=, or set CLOUDFLARE_API_TOKEN in .env."
        }), 401

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }, None, None


# ===================================================================
# CLOUDFLARE OAUTH 2.0 ENDPOINTS (YOUR CODE ADAPTED FOR RENDER)
# ===================================================================

@cloudflare_bp.route("/cloudflare/login")
@cloudflare_bp.route("/cloudflare/auth")
def login():
    """Start Cloudflare OAuth 2.0 authorization flow."""
    if CLIENT_ID == "YOUR_CLIENT_ID" or not CLIENT_ID:
        return jsonify({
            "error": "CLOUDFLARE_CLIENT_ID is not configured in environment variables.",
            "hint": "Add CLOUDFLARE_CLIENT_ID, CLOUDFLARE_CLIENT_SECRET, and CLOUDFLARE_REDIRECT_URI in your Render Dashboard."
        }), 500

    oauth = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES
    )

    authorization_url, state = oauth.authorization_url(
        AUTHORIZATION_BASE_URL
    )

    # Store OAuth state in session (thread-safe for Render production)
    session["cloudflare_oauth_state"] = state

    return redirect(authorization_url)


@cloudflare_bp.route("/cloudflare/callback")
def callback():
    """Handle Cloudflare OAuth 2.0 callback, fetch token, and store in session."""
    if not CLIENT_ID or not CLIENT_SECRET or CLIENT_ID == "YOUR_CLIENT_ID":
        return jsonify({"error": "CLOUDFLARE_CLIENT_ID or CLOUDFLARE_CLIENT_SECRET missing."}), 500

    oauth = OAuth2Session(
        CLIENT_ID,
        state=session.get("cloudflare_oauth_state"),
        redirect_uri=REDIRECT_URI
    )

    token = oauth.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=request.url
    )

    print("\n========== CLOUDFLARE TOKEN ==========")
    print(token)
    print("======================================\n")

    # Store token in session so subsequent API calls (/cloudflare/zones) work automatically
    access_token = token.get("access_token")
    session["cloudflare_token"] = access_token

    # Return HTML response matching your snippet (with a handy link to test zones!)
    return f"""
    <h2>Cloudflare OAuth Success</h2>
    <pre>{token}</pre>
    <p><a href="/cloudflare/zones" style="font-weight:bold; color:#0284c7;">Test Fetching Cloudflare Zones &rarr;</a></p>
    """


# ===================================================================
# CLOUDFLARE API TESTING ENDPOINTS
# ===================================================================

@cloudflare_bp.route("/cloudflare/verify", methods=["GET"])
def cloudflare_verify():
    """Verify Cloudflare API Token validity and status."""
    headers, err_json, status_code = get_cloudflare_headers()
    if err_json:
        return err_json, status_code

    res = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", headers=headers)
    if res.status_code != 200:
        return jsonify({"error": "Cloudflare token verification failed", "details": res.text}), res.status_code

    return jsonify(res.json())


@cloudflare_bp.route("/cloudflare/zones", methods=["GET"])
def cloudflare_list_zones():
    """List all Cloudflare Zones (domains) accessible by the OAuth token / API token."""
    headers, err_json, status_code = get_cloudflare_headers()
    if err_json:
        return err_json, status_code

    res = requests.get("https://api.cloudflare.com/client/v4/zones", headers=headers)
    if res.status_code != 200:
        return jsonify({"error": "Failed to fetch Cloudflare zones", "details": res.text}), res.status_code

    data = res.json()
    zones = [
        {
            "id": z["id"],
            "name": z["name"],
            "status": z["status"],
            "plan": z.get("plan", {}).get("name")
        }
        for z in data.get("result", [])
    ]
    return jsonify({"count": len(zones), "zones": zones, "success": data.get("success", True)})


@cloudflare_bp.route("/cloudflare/zones/<zone_id>/dns", methods=["GET"])
def cloudflare_list_dns(zone_id):
    """List all DNS records for a specific Cloudflare Zone ID."""
    headers, err_json, status_code = get_cloudflare_headers()
    if err_json:
        return err_json, status_code

    res = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records", headers=headers)
    if res.status_code != 200:
        return jsonify({"error": "Failed to fetch DNS records", "details": res.text}), res.status_code

    data = res.json()
    records = [
        {
            "id": r["id"],
            "type": r["type"],
            "name": r["name"],
            "content": r["content"],
            "proxied": r.get("proxied", False)
        }
        for r in data.get("result", [])
    ]
    return jsonify({"zone_id": zone_id, "count": len(records), "records": records})


@cloudflare_bp.route("/cloudflare/zones/<zone_id>/dns", methods=["POST"])
def cloudflare_create_dns(zone_id):
    """Create a new DNS record in a Cloudflare Zone via JSON body."""
    headers, err_json, status_code = get_cloudflare_headers()
    if err_json:
        return err_json, status_code

    data = request.get_json(silent=True) or {}
    record_type = data.get("type", "TXT").upper()
    name = data.get("name")
    content = data.get("content")
    ttl = data.get("ttl", 3600)
    proxied = data.get("proxied", False)

    if not name or not content:
        return jsonify({"error": "Missing required fields: 'name' and 'content' are required in JSON body."}), 400

    payload = {
        "type": record_type,
        "name": name,
        "content": content,
        "ttl": ttl,
        "proxied": proxied
    }

    res = requests.post(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
        headers=headers,
        json=payload
    )
    if res.status_code != 200 and not res.json().get("success"):
        return jsonify({"error": "Failed to create DNS record", "details": res.json()}), res.status_code

    return jsonify({"status": "DNS record created successfully", "record": res.json().get("result")}), 201
