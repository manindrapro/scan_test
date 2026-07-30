import os
import base64
import requests
from flask import Blueprint, redirect, request, session, jsonify

notion_bp = Blueprint("notion", __name__)

# ==========================================
# NOTION CREDENTIALS & URLS
# ==========================================
NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI", "https://your-app-name.onrender.com/notion/callback")
NOTION_VERSION = "2022-06-28"


# -----------------------------------
# Helper: Get Authenticated Notion Headers
# -----------------------------------
def get_notion_headers():
    """
    Returns Notion API headers using session token, query param, or env NOTION_TOKEN.
    """
    token = (request.args.get("token") or 
             request.headers.get("X-Notion-Token") or 
             session.get("notion_token") or 
             os.getenv("NOTION_TOKEN"))
    if not token:
        return None, jsonify({
            "error": "Not authenticated with Notion. Visit /notion/auth, pass ?token=, or set NOTION_TOKEN in .env."
        }), 401

    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }, None, None


# ===================================================================
# NOTION ENDPOINTS (OAUTH 2.0 + API TESTING)
# ===================================================================

@notion_bp.route("/notion/auth")
def notion_auth():
    """Start Notion OAuth 2.0 authorization flow."""
    if not NOTION_CLIENT_ID:
        return jsonify({
            "error": "NOTION_CLIENT_ID is not configured in environment variables.",
            "hint": "Set NOTION_TOKEN in .env for direct access, or NOTION_CLIENT_ID for OAuth."
        }), 500

    notion_authorize_url = (
        f"https://api.notion.com/v1/oauth/authorize?client_id={NOTION_CLIENT_ID}"
        f"&response_type=code&owner=user&redirect_uri={NOTION_REDIRECT_URI}"
    )
    return redirect(notion_authorize_url)


@notion_bp.route("/notion/callback")
def notion_callback():
    """Handle Notion OAuth 2.0 callback and exchange authorization code for access token."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Missing authorization code from Notion redirect."}), 400

    if not NOTION_CLIENT_ID or not NOTION_CLIENT_SECRET:
        return jsonify({"error": "NOTION_CLIENT_ID or NOTION_CLIENT_SECRET missing."}), 500

    auth_str = f"{NOTION_CLIENT_ID}:{NOTION_CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    response = requests.post(
        "https://api.notion.com/v1/oauth/token",
        headers={
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        },
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": NOTION_REDIRECT_URI
        }
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to exchange Notion token", "details": response.text}), response.status_code

    token_data = response.json()
    session["notion_token"] = token_data.get("access_token")

    return jsonify({
        "status": "Connected to Notion",
        "workspace_name": token_data.get("workspace_name"),
        "workspace_id": token_data.get("workspace_id"),
        "bot_id": token_data.get("bot_id"),
        "access_token": token_data.get("access_token")
    })


@notion_bp.route("/notion/users", methods=["GET"])
def notion_list_users():
    """List users in the connected Notion workspace (verifies authentication)."""
    headers, err_json, status_code = get_notion_headers()
    if err_json:
        return err_json, status_code

    res = requests.get("https://api.notion.com/v1/users", headers=headers)
    if res.status_code != 200:
        return jsonify({"error": "Failed to fetch Notion users", "details": res.text}), res.status_code

    return jsonify(res.json())


@notion_bp.route("/notion/search", methods=["GET", "POST"])
def notion_search():
    """Search for pages and databases in the connected Notion workspace."""
    headers, err_json, status_code = get_notion_headers()
    if err_json:
        return err_json, status_code

    query_payload = request.get_json(silent=True) or {}
    res = requests.post("https://api.notion.com/v1/search", headers=headers, json=query_payload)
    if res.status_code != 200:
        return jsonify({"error": "Failed to search Notion workspace", "details": res.text}), res.status_code

    data = res.json()
    return jsonify({
        "count": len(data.get("results", [])),
        "results": [
            {
                "id": item.get("id"),
                "object": item.get("object"),
                "url": item.get("url"),
                "title": _extract_notion_title(item)
            }
            for item in data.get("results", [])
        ]
    })


def _extract_notion_title(item):
    """Extract readable title string from Notion page or database objects."""
    try:
        if item.get("object") == "database":
            title_array = item.get("title", [])
            return title_array[0]["plain_text"] if title_array else "Untitled Database"
        elif item.get("object") == "page":
            props = item.get("properties", {})
            for prop in props.values():
                if prop.get("type") == "title" and prop.get("title"):
                    return prop["title"][0]["plain_text"]
            return "Untitled Page"
    except Exception:
        pass
    return "Untitled"


@notion_bp.route("/notion/pages", methods=["POST"])
def notion_create_page():
    """Create a new page in a Notion database or parent page via JSON body."""
    headers, err_json, status_code = get_notion_headers()
    if err_json:
        return err_json, status_code

    data = request.get_json(silent=True) or {}
    parent_id = data.get("parent_id")
    parent_type = data.get("parent_type", "database_id")
    title = data.get("title", "Test Page from Render Backend")

    if not parent_id:
        return jsonify({"error": "Missing required field: 'parent_id' is required."}), 400

    payload = {
        "parent": {parent_type: parent_id},
        "properties": {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        }
    }

    res = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
    if res.status_code != 200:
        return jsonify({"error": "Failed to create Notion page", "details": res.text}), res.status_code

    return jsonify({"status": "Page created successfully", "page": res.json()}), 201
