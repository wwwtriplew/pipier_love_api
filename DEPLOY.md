# 🚀 RENDER DEPLOYMENT CHECKLIST

## ✅ Repository Status: PRODUCTION READY

All redundant files deleted. Clean, minimal structure for Render deployment.

---

## 📁 Final Structure

```
pipier_love_api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies (3 packages)
├── render.yaml         # Render auto-deploy config
├── README.md           # Clean documentation
├── src/                # Chess engine (12 files)
└── testing/            # Essential tests (2 files)
```

---

## 🎯 Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Production-ready chess engine API"
git push origin main
```

### 2. Deploy on Render
1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select repository: **`wwwtriplew/pipier_love_api`**
5. Render will auto-detect `render.yaml`
6. Click **"Create Web Service"**

### 3. Wait for Build
- Build time: ~1-2 minutes
- Render installs dependencies automatically
- Status will show "Live" when ready

### 4. Get Your API URL
- Format: `https://pipier-chess-engine.onrender.com`
- Copy this URL for your frontend

---

## 🔧 Post-Deployment Configuration

### Update CORS in Your Frontend
Once deployed, if you need to add more origins, edit `main.py` line 42:

```python
allow_origins=[
    "https://wwwtriplew.me",
    "https://www.wwwtriplew.me",
    # Add more domains here
]
```

Then commit and push - Render will auto-redeploy.

---

## 🧪 Test Your API

### Health Check
```bash
curl https://your-service.onrender.com/health
```

Expected: `{"status":"healthy"}`

### Calculate Move
```bash
curl -X POST "https://your-service.onrender.com/move" \
  -H "Content-Type: application/json" \
  -d '{
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "ai_thinking_ms": 2000
  }'
```

Expected: JSON with move, score, depth, etc.

### API Documentation
Visit: `https://your-service.onrender.com/docs`

---

## 🎮 Frontend Integration

```javascript
// Your chess UI JavaScript
const API_URL = 'https://your-service.onrender.com';

async function getAIMove(fen) {
  const response = await fetch(`${API_URL}/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fen: fen,
      ai_thinking_ms: 2000
    })
  });
  
  const data = await response.json();
  return data.move; // "e2e4"
}
```

---

## ⚠️ Important Notes

### Free Tier Limitations
- **Cold starts**: First request after 15min idle takes 2-3s
- **Sleep time**: Sleeps after 15min of inactivity
- **Performance**: 512MB RAM, 0.1 CPU
- **Solution**: Upgrade to paid tier ($7/mo) for always-on

### Render Configuration
All settings are in `render.yaml`:
- **Build**: `pip install -r requirements.txt`
- **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Python**: 3.11.0
- **Region**: Oregon (change if needed)

### Monitoring
- View logs: Render Dashboard → Your Service → Logs
- Check health: `/health` endpoint
- View metrics: Render Dashboard → Metrics tab

---

## 🔒 Security Notes

✅ **Configured:**
- CORS restricted to your domains only
- Input validation (Pydantic)
- Request timeouts (100-30000ms)
- No shared state between requests
- Limited HTTP methods (POST, GET, OPTIONS)

⚠️ **Consider Adding:**
- Rate limiting (if you get heavy traffic)
- API keys (if you want access control)
- Logging/monitoring (for production insights)

---

## 🎉 You're Ready to Launch!

**Next step:** Push to GitHub and create Render service.

Your chess engine will be live in 2 minutes! 🚀
