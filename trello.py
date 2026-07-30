import os
from flask import Blueprint, redirect, request, session, jsonify
from requests_oauthlib import OAuth1Session

trello_bp = Blueprint("trello", __name__)

# ==========================================
# TRELLO CREDENTIALS & URLS
# ==========================================
API_KEY = os.getenv("TRELLO_API_KEY")
API_SECRET = os.getenv("TRELLO_API_SECRET")
CALLBACK_URL = os.getenv("CALLBACK_URL")

REQUEST_TOKEN_URL = "https://trello.com/1/OAuthGetRequestToken"
AUTHORIZE_URL = "https://trello.com/1/OAuthAuthorizeToken"
ACCESS_TOKEN_URL = "https://trello.com/1/OAuthGetAccessToken"

# In-memory log for testing Trello webhooks
WEBHOOK_LOGS = []


# -----------------------------------
# Helper: Get Authenticated Trello Client
# -----------------------------------
def get_trello_client():
    """
    Returns an OAuth1Session for Trello using either session cookies,
    query parameters (?token=...&secret=...), or headers (X-Trello-Token / X-Trello-Secret).
    """
    token = request.args.get("token") or request.headers.get("X-Trello-Token") or session.get("access_token")
    secret = request.args.get("secret") or request.headers.get("X-Trello-Secret") or session.get("access_secret")

    if not token or not secret:
        return None, jsonify({
            "error": "Not authenticated with Trello. Visit /auth or pass ?token=&secret=.",
            "hint": "Start OAuth at /auth"
        }), 401

    api = OAuth1Session(
        client_key=API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=token,
        resource_owner_secret=secret
    )
    return api, None, None


# ===================================================================
# TRELLO ENDPOINTS (YOUR ORIGINAL CODE + TESTING ROUTES)
# ===================================================================

@trello_bp.route("/auth")
def auth():
    """Start Trello OAuth 1.0a authorization flow."""
    if not API_KEY or not API_SECRET:
        return jsonify({
            "error": "Missing TRELLO_API_KEY or TRELLO_API_SECRET in environment variables."
        }), 500

    oauth = OAuth1Session(
        client_key=API_KEY,
        client_secret=API_SECRET,
        callback_uri=CALLBACK_URL
    )

    tokens = oauth.fetch_request_token(REQUEST_TOKEN_URL)

    session["resource_owner_key"] = tokens["oauth_token"]
    session["resource_owner_secret"] = tokens["oauth_token_secret"]

    authorization_url = oauth.authorization_url(
        AUTHORIZE_URL,
        name="Scanbit",
        scope="read,write",
        expiration="never"
    )

    return redirect(authorization_url)


@trello_bp.route("/callback")
def callback():
    """Handle Trello OAuth callback, exchange for access token & secret."""
    if "resource_owner_key" not in session or "resource_owner_secret" not in session:
        return jsonify({
            "error": "OAuth session tokens missing. Please visit /auth again to start authentication."
        }), 400

    oauth = OAuth1Session(
        client_key=API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=session["resource_owner_key"],
        resource_owner_secret=session["resource_owner_secret"],
        verifier=request.args.get("oauth_verifier")
    )

    tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)

    access_token = tokens["oauth_token"]
    access_secret = tokens["oauth_token_secret"]

    # Save to session so /boards and /cards work automatically in browser
    session["access_token"] = access_token
    session["access_secret"] = access_secret

    api = OAuth1Session(
        client_key=API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret
    )

    user = api.get("https://api.trello.com/1/members/me")

    return jsonify({
        "status": "Connected to Trello",
        "access_token": access_token,
        "access_secret": access_secret,
        "user": user.json()
    })


@trello_bp.route("/boards", methods=["GET"])
def list_boards():
    """List all boards belonging to the authenticated Trello user."""
    api, err_json, status_code = get_trello_client()
    if err_json:
        return err_json, status_code

    response = api.get("https://api.trello.com/1/members/me/boards", params={"fields": "name,url,closed"})
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch boards from Trello", "details": response.text}), response.status_code

    return jsonify({"count": len(response.json()), "boards": response.json()})


@trello_bp.route("/boards/<board_id>/lists", methods=["GET"])
def list_board_lists(board_id):
    """List all columns/lists on a specific Trello board."""
    api, err_json, status_code = get_trello_client()
    if err_json:
        return err_json, status_code

    response = api.get(f"https://api.trello.com/1/boards/{board_id}/lists", params={"fields": "name,idBoard"})
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch lists", "details": response.text}), response.status_code

    return jsonify({"board_id": board_id, "lists": response.json()})


@trello_bp.route("/cards", methods=["POST"])
def create_card():
    """Create a new card on a Trello list via JSON body (name, idList, desc)."""
    api, err_json, status_code = get_trello_client()
    if err_json:
        return err_json, status_code

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    id_list = data.get("idList")
    desc = data.get("desc", "")

    if not name or not id_list:
        return jsonify({"error": "Missing required fields: 'name' and 'idList' are required in JSON body."}), 400

    response = api.post("https://api.trello.com/1/cards", json={
        "name": name,
        "idList": id_list,
        "desc": desc
    })

    if response.status_code != 200:
        return jsonify({"error": "Failed to create card", "details": response.text}), response.status_code

    return jsonify({"status": "Card created successfully", "card": response.json()}), 201


@trello_bp.route("/webhook", methods=["HEAD", "POST", "GET"])
def trello_webhook():
    """Trello webhook receiver and HEAD verification handler."""
    if request.method in ["HEAD", "GET"]:
        return "", 200

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        WEBHOOK_LOGS.insert(0, payload)
        if len(WEBHOOK_LOGS) > 50:
            WEBHOOK_LOGS.pop()

        print("Received Trello Webhook Event:", payload.get("action", {}).get("type", "Unknown Action"))
        return jsonify({"status": "received"}), 200


@trello_bp.route("/webhook-logs", methods=["GET"])
def view_webhook_logs():
    """Inspect the most recent Trello webhook event payloads captured by the server."""
    return jsonify({
        "total_captured": len(WEBHOOK_LOGS),
        "events": WEBHOOK_LOGS
    })
