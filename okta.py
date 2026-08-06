import os
import secrets
import requests

from flask import Blueprint, redirect, request, session, jsonify

okta_bp = Blueprint("okta", __name__)

# ======================================================
# OKTA CONFIGURATION
# ======================================================

OKTA_DOMAIN = os.getenv("OKTA_DOMAIN")                     # https://company.okta.com
OKTA_CLIENT_ID = os.getenv("OKTA_CLIENT_ID")
OKTA_CLIENT_SECRET = os.getenv("OKTA_CLIENT_SECRET")
OKTA_REDIRECT_URI = os.getenv(
    "OKTA_REDIRECT_URI",
    "https://your-app-name.onrender.com/okta/callback"
)

AUTHORIZATION_SERVER = "default"

AUTHORIZE_URL = f"{OKTA_DOMAIN}/oauth2/{AUTHORIZATION_SERVER}/v1/authorize"
TOKEN_URL = f"{OKTA_DOMAIN}/oauth2/{AUTHORIZATION_SERVER}/v1/token"
USERINFO_URL = f"{OKTA_DOMAIN}/oauth2/{AUTHORIZATION_SERVER}/v1/userinfo"

SCOPES = (
    "openid profile email offline_access "
    "okta.users.read okta.groups.read okta.apps.read"
)


# ======================================================
# Helper
# ======================================================

def get_headers():

    token = (
        request.args.get("token")
        or request.headers.get("X-Okta-Token")
        or session.get("okta_access_token")
        or os.getenv("OKTA_ACCESS_TOKEN")
    )

    if not token:
        return None, jsonify({
            "error": "Not authenticated. Visit /okta/auth first."
        }), 401

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }, None, None


# ======================================================
# OAuth Login
# ======================================================

@okta_bp.route("/okta/auth")
def okta_auth():

    state = secrets.token_urlsafe(32)
    session["okta_state"] = state

    auth_url = (
        f"{AUTHORIZE_URL}"
        f"?client_id={OKTA_CLIENT_ID}"
        f"&response_type=code"
        f"&scope={SCOPES}"
        f"&redirect_uri={OKTA_REDIRECT_URI}"
        f"&state={state}"
    )

    return redirect(auth_url)


# ======================================================
# OAuth Callback
# ======================================================

@okta_bp.route("/okta/callback")
def okta_callback():

    if request.args.get("state") != session.get("okta_state"):
        return jsonify({"error": "Invalid state"}), 400

    code = request.args.get("code")

    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    response = requests.post(
        TOKEN_URL,
        auth=(OKTA_CLIENT_ID, OKTA_CLIENT_SECRET),
        headers={
            "Accept": "application/json"
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OKTA_REDIRECT_URI
        }
    )

    if response.status_code != 200:
        return jsonify({
            "error": "Token exchange failed",
            "details": response.text
        }), response.status_code

    token = response.json()

    session["okta_access_token"] = token["access_token"]
    session["okta_refresh_token"] = token.get("refresh_token")

    return jsonify({
        "status": "Connected to Okta",
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token")
    })


# ======================================================
# Current User
# ======================================================

@okta_bp.route("/okta/me")
def me():

    headers, err, code = get_headers()

    if err:
        return err, code

    res = requests.get(USERINFO_URL, headers=headers)

    return jsonify(res.json()), res.status_code


# ======================================================
# List Users
# ======================================================

@okta_bp.route("/okta/users")
def users():

    headers, err, code = get_headers()

    if err:
        return err, code

    res = requests.get(
        f"{OKTA_DOMAIN}/api/v1/users",
        headers=headers
    )

    return jsonify(res.json()), res.status_code


# ======================================================
# List Groups
# ======================================================

@okta_bp.route("/okta/groups")
def groups():

    headers, err, code = get_headers()

    if err:
        return err, code

    res = requests.get(
        f"{OKTA_DOMAIN}/api/v1/groups",
        headers=headers
    )

    return jsonify(res.json()), res.status_code


# ======================================================
# List Applications
# ======================================================

@okta_bp.route("/okta/apps")
def apps():

    headers, err, code = get_headers()

    if err:
        return err, code

    res = requests.get(
        f"{OKTA_DOMAIN}/api/v1/apps",
        headers=headers
    )

    return jsonify(res.json()), res.status_code