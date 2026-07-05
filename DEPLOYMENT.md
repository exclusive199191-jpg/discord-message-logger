# Installation and Deployment Guide

## Quick Start (Local with Docker Compose)

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+
- PostgreSQL 15 (or use Docker)

### 1. Clone and Setup
```bash
git clone https://github.com/exclusive199191-jpg/discord-message-logger.git
cd discord-message-logger
cp .env.example .env
```

### 2. Edit .env
```bash
# Add your Discord token and generate a secret key
echo "DISCORD_USER_TOKEN=$(python3 -c 'import uuid; print(uuid.uuid4().hex)')" >> .env
echo "FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env
```

### 3. Run with Docker Compose
```bash
docker-compose up
```

The application will be available at:
- Web UI: http://localhost:8000
- API: http://localhost:8000/api

---

## Railway.com Deployment

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### Step 2: Create Railway Project
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize and select your repository

### Step 3: Add PostgreSQL Database
1. In Railway dashboard, click "+New"
2. Select "Add Service" → "PostgreSQL"
3. Railway will automatically create the database

### Step 4: Configure Environment Variables
In Railway dashboard, go to Variables and add:
```
DATABASE_URL=<automatically set by PostgreSQL service>
DISCORD_USER_TOKEN=your_discord_token_here
FLASK_SECRET_KEY=your_secret_key_here
PORT=8000
```

### Step 5: Deploy
- Railway will automatically detect Dockerfile and deploy
- Health checks run every 30 seconds
- Application will restart on failure

---

## Getting Your Discord Token

⚠️ **WARNING: Never share your token!**

### Method 1: Browser Console (Recommended)
1. Open Discord in browser (discord.com)
2. Press `F12` to open Developer Tools
3. Go to Console tab
4. Paste:
```javascript
window.webpackChunkdiscord_app.push([['__DISCORD_APP__'], {}, (req) => {
  return Object.values(req.c).find(m => m.exports.default?.getToken?.toString?.()).exports.default.getToken();
}]);
```
5. Copy the token that appears

### Method 2: Local Storage
1. Open Discord
2. Press `F12`
3. Go to Storage → Local Storage
4. Look for your token in the Application data

---

## Local Development Setup

### Without Docker

1. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup PostgreSQL Locally**
```bash
# Install PostgreSQL if needed
# Create database
createb discord_logger
createu discord_logger -P  # Set password when prompted
```

4. **Configure .env**
```bash
cp .env.example .env
# Edit with your values
```

5. **Run Both Services**

Terminal 1 (Web):
```bash
python app.py
```

Terminal 2 (Bot):
```bash
python bot.py
```

---

## Monitoring and Troubleshooting

### Check Logs
```bash
# Docker Compose
docker-compose logs -f web
docker-compose logs -f bot

# Railway
# View in dashboard → Logs tab
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Database Issues
```bash
# Check connection
psql $DATABASE_URL

# View tables
\dt

# Check message count
SELECT COUNT(*) FROM messages;
```

### Bot Issues
- Verify token is valid
- Check bot has message content intents
- Ensure bot is in servers you want to monitor
- Check Discord API status

---

## Production Checklist

- [ ] Change FLASK_SECRET_KEY
- [ ] Set DISCORD_USER_TOKEN
- [ ] Use strong PostgreSQL password
- [ ] Enable HTTPS (Railway handles this)
- [ ] Set up monitoring/alerts
- [ ] Regular database backups
- [ ] Monitor error logs
- [ ] Test health endpoint

---

## Scaling

### Railway Scaling
1. Go to Service Settings
2. Increase Memory/CPU as needed
3. Add replicas for web service if needed

### Database
- PostgreSQL automatically scales with Railway
- Monitor connections: `SELECT count(*) FROM pg_stat_activity;`

---

## Updates and Maintenance

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Database Migrations
Run automatically on startup via `init_db()`

### Backup Database
```bash
pg_dump $DATABASE_URL > backup.sql
```

---

## Support

For issues:
1. Check logs
2. Verify environment variables
3. Test health endpoint
4. Check GitHub issues

---

**Happy logging!** 🎉
