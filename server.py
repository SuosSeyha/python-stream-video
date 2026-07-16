"""
Stream Video token backend (Python / Flask).

This is the only place your Stream API Secret should ever live.
The Flutter app never sees it — it only calls this server to get a
short-lived user token.
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from getstream import Stream
from getstream.models import UserRequest

load_dotenv()

API_KEY = os.environ.get("STREAM_API_KEY")
API_SECRET = os.environ.get("STREAM_API_SECRET")
PORT = int(os.environ.get("PORT", 3000))

if not API_KEY or not API_SECRET:
    raise SystemExit(
        "Missing STREAM_API_KEY or STREAM_API_SECRET. "
        "Copy .env.example to .env and fill them in."
    )

stream_client = Stream(api_key=API_KEY, api_secret=API_SECRET)

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/stream/token")
def issue_token():
    """
    Issue a Stream user token.

    In a real app, this route should sit behind YOUR OWN authentication
    (e.g. verify a session cookie / JWT for the logged-in user) so that
    anyone can't mint a token for an arbitrary userId. This example trusts
    the userId in the request body for simplicity — replace that with your
    actual auth check before shipping.

    Body: { "userId": "user-1" }
    Response: { "token": "eyJhbGciOi..." }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("userId")

    if not user_id or not isinstance(user_id, str):
        return jsonify(error="userId (string) is required"), 400

    # TODO: verify the caller is actually authorized to act as `user_id`
    # before issuing a token, e.g.:
    #   authed_user_id = get_user_id_from_session_or_jwt(request)
    #   if authed_user_id != user_id:
    #       return jsonify(error="Forbidden"), 403

    try:
        token = stream_client.create_token(user_id)
        return jsonify(token=token)
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Failed to generate token")
        return jsonify(error="Failed to generate token"), 500


@app.post("/stream/upsert-user")
def upsert_user():
    """
    Optional: ensure a user exists in Stream (upsert) before issuing a
    token. Useful if you want the user's name/image to show up correctly
    in the call UI on first use.

    Body: { "userId": "user-1", "name": "Jane Doe", "image": "https://..." }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("userId")
    name = data.get("name")
    image = data.get("image")

    if not user_id or not isinstance(user_id, str):
        return jsonify(error="userId (string) is required"), 400

    try:
        stream_client.upsert_users(
            UserRequest(
                id=user_id,
                name=name or user_id,
                image=image,
                role="user",
            )
        )
        return jsonify(ok=True)
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Failed to upsert user")
        return jsonify(error="Failed to upsert user"), 500


if __name__ == "__main__":
    print(f"Stream token server listening on http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
