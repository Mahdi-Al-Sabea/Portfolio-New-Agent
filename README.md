# 🤖 Mahdi Al Sabeh — AI Digital Twin REST API

FastAPI REST API backend for Mahdi Al Sabeh's AI Digital Twin, powered by **Google Gemini**.

Designed for direct external calls from your React Portfolio frontend widget (`AiChatWidget.jsx`).

---

## 📁 Directory Structure

```
Agent/
├── app.py              # FastAPI REST API (/api/chat, /api/health)
├── agent.py            # AI Agent logic, system prompt, Gemini integration & tool calling
├── cv_loader.py        # CV text extractor (reads data/cv.pdf or data/cv.txt)
├── tools.py            # record_user_email & record_unanswered_question tools
├── Dockerfile          # Docker setup for container deployment (Render, etc.)
├── requirements.txt    # Python dependencies
├── .env                # GEMINI_API_KEY
└── data/
    └── cv.pdf          # CV file
```

---

## 🚀 1. Local Testing

```bash
# In the Agent directory:
uv run python app.py
# or:
python app.py
```

- **Root Status**: [http://localhost:7860/](http://localhost:7860/)
- **Health Check**: [http://localhost:7860/api/health](http://localhost:7860/api/health)
- **POST Chat API Endpoint**: `http://localhost:7860/api/chat`

---

## ☁️ 2. Deploying to Render.com (100% Free)

1. Push your project to GitHub.
2. Sign in to [render.com](https://render.com) and click **New +** → **Web Service**.
3. Select your repository.
4. Configure service settings:
   - **Name**: `mahdi-ai-agent`
   - **Root Directory**: `Agent`
   - **Runtime**: `Python 3` (or `Docker`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**
5. Under **Environment Variables**, add:
   - `GEMINI_API_KEY` = `<your-gemini-api-key>`
   - `CV_REMOTE_URL` = `https://<your-portfolio-domain>/Mahdi-Al-Sabeh%20CV.pdf` (optional: auto-syncs with newest CV)
6. Click **Create Web Service**.
7. Once deployed, your API will be live at:
   `https://<your-service-name>.onrender.com/api/chat`

---

## 💻 3. Connecting to React Portfolio

In your `Web/.env`:

```env
VITE_AI_AGENT_URL=https://<your-service-name>.onrender.com/api/chat
```
