import os
from flask import Flask, redirect, request, session, jsonify
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv()

app = Flask(__name__)
# Use a default secret key for local dev, but ensure FLASK_SECRET_KEY is set in Render
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-render")

# Modern browser cookie settings so sessions survive OAuth redirects across domains
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"

API_KEY = os.getenv("TRELLO_API_KEY")
API_SECRET = os.getenv("TRELLO_API_SECRET")
CALLBACK_URL = os.getenv("CALLBACK_URL")

REQUEST_TOKEN_URL = "https://trello.com/1/OAuthGetRequestToken"
AUTHORIZE_URL = "https://trello.com/1/OAuthAuthorizeToken"
ACCESS_TOKEN_URL = "https://trello.com/1/OAuthGetAccessToken"


# -----------------------------------
# Root & Health Check Endpoints
# -----------------------------------
@app.route("/")
def home():
    return {
        "service": "Scanbit Trello OAuth Backend",
        "status": "running",
        "endpoints": {
            "start_oauth": "/auth",
            "callback": "/callback",
            "health": "/health"
        }
    }


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


# -----------------------------------
# Connect Trello
# -----------------------------------
@app.route("/auth")
def auth():
    if not API_KEY or not API_SECRET:
        return jsonify({
            "error": "Missing environment variables: TRELLO_API_KEY or TRELLO_API_SECRET must be configured."
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


# -----------------------------------
# Callback
# -----------------------------------
@app.route("/callback")
def callback():
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

    api = OAuth1Session(
        client_key=API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret
    )

    user = api.get("https://api.trello.com/1/members/me")

    return {
        "status": "Connected",
        "access_token": access_token,
        "access_secret": access_secret,
        "user": user.json()
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
