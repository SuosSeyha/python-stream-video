# Stream Video Token Backend (Python)

Mints short-lived Stream user tokens for the Flutter app. This is the only
place your Stream **Secret** should live — it never goes in the mobile app.

## Setup

```bash
cd stream-backend-python
python3 -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and paste your real Secret from the Stream dashboard:

```
STREAM_API_KEY=7jfwj7kcbqtd
STREAM_API_SECRET=your_secret_here
PORT=3000
```

## Run locally

```bash
python server.py
```

You should see: `Stream token server listening on http://0.0.0.0:3000`

Test it:

```bash
curl -X POST http://localhost:3000/stream/token \
  -H "Content-Type: application/json" \
  -d '{"userId":"user-1"}'
```

You should get back `{ "token": "eyJ..." }`.

## Connect the Flutter app

In `lib/main.dart`, set `kBackendBaseUrl` to wherever this server is
reachable from the device:

- iOS Simulator: `http://127.0.0.1:3000`
- Physical device on same Wi-Fi: `http://<your-computer-LAN-IP>:3000`
  (find it with `ipconfig getifaddr en0` on Mac)
- Deployed server: `https://your-deployed-url.com`

The request/response shape is identical to the Node version, so nothing
in the Flutter app needs to change — just swap which backend it points to.

## Endpoints

| Method | Path                  | Body                                   | Returns             |
|--------|-----------------------|-----------------------------------------|----------------------|
| GET    | `/health`             | —                                        | `{ status: "ok" }`  |
| POST   | `/stream/token`       | `{ "userId": "user-1" }`                | `{ "token": "..." }`|
| POST   | `/stream/upsert-user` | `{ "userId", "name", "image" }`         | `{ "ok": true }`     |

## Deploy to Render

1. **Push this folder to a GitHub repo** (Render deploys from a git repo).
   ```bash
   git init
   git add .
   git commit -m "Stream video token backend"
   git branch -M main
   git remote add origin https://github.com/<you>/stream-backend-python.git
   git push -u origin main
   ```
   Your `.gitignore` already excludes `.env`, so your Secret won't be committed — good.

2. **Create the service on Render**
   - Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**.
   - Connect your GitHub account and select this repo.
   - Render will detect `render.yaml` in this folder and pre-fill the settings. If it doesn't auto-detect, set manually:
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT server:app`
     - **Plan**: Free (fine for testing; free tier sleeps after inactivity and takes ~30–60s to wake on the next request)

3. **Set environment variables** (Render dashboard → your service → **Environment**):
   ```
   STREAM_API_KEY = 7jfwj7kcbqtd
   STREAM_API_SECRET = your_real_secret
   ```
   Do **not** put these in `render.yaml` or commit them — set them directly in Render's dashboard, which is what `sync: false` in `render.yaml` signals.

4. **Deploy** — Render will build and give you a URL like:
   ```
   https://stream-video-token-backend.onrender.com
   ```

5. **Verify it**:
   ```bash
   curl -X POST https://stream-video-token-backend.onrender.com/stream/token \
     -H "Content-Type: application/json" \
     -d '{"userId":"user-1"}'
   ```

6. **Update the Flutter app** — in `lib/main.dart`:
   ```dart
   const String kBackendBaseUrl = 'https://stream-video-token-backend.onrender.com';
   ```
   Since this is now real `https://`, you can **remove** the `NSAppTransportSecurity` exception you added earlier to `ios/Runner/Info.plist` for local `http://` testing — it's no longer needed.



- **Add real authentication** to `/stream/token`. Right now it trusts
  whatever `userId` is sent in the request body — anyone who can reach this
  endpoint could request a token for any user. Replace the `TODO` in
  `server.py` with a check against your own session/JWT so a caller can
  only get a token for *their own* authenticated user.
- Run with a production WSGI server instead of Flask's dev server, e.g.:
  ```bash
  pip install gunicorn
  gunicorn -w 2 -b 0.0.0.0:3000 server:app
  ```
- Deploy behind HTTPS (Render, Railway, Fly.io, a VPS + nginx, etc.).
- Restrict `CORS(app)` to your actual app's origin(s) instead of the open
  default, if you ever call this from web.
