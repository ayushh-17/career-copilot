# 🚀 Career Copilot - Deployment Guide

## **Step 1: GitHub Setup** (5 mins)

### 1a. Initialize Git (if not done)
```bash
cd c:\Users\ayush\OneDrive\Desktop\career-copilot
git init
git config user.name "Ayush Karmani"
git config user.email "ayushkarmani2@gmail.com"
git add .
git commit -m "Initial commit: Career Copilot with Phase 3A features"
```

### 1b. Create GitHub Repository
1. Go to [github.com](https://github.com) and login
2. Click **"New Repository"** (top right)
3. Name it: `career-copilot`
4. Description: "AI-Powered Resume & Job Matching Platform"
5. **DO NOT** initialize with README/gitignore (we have them)
6. Click **"Create repository"**

### 1c. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/career-copilot.git
git branch -M main
git push -u origin main
```

**✅ If success**: You'll see your code on GitHub!

---

## **Step 2: Railway Deployment** (10 mins)

### 2a. Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (easiest)
3. Authorize GitHub access

### 2b. Create New Project
1. Click **"+ New Project"**
2. Select **"Deploy from GitHub repo"**
3. Select `career-copilot` repository
4. Railway will auto-detect it's Python/Flask ✓

### 2c. Add Environment Variables
1. After deployment starts, go to **"Variables"** tab
2. Click **"Add Variable"**
3. Add:
   ```
   GEMINI_API_KEY=your_api_key_here
   FLASK_ENV=production
   ```
   - Get API key from: https://aistudio.google.com/apikey
4. Click **"Deploy"**

### 2d. Wait for Deployment
- Railway will build your app (2-3 mins)
- You'll see green checkmarks when done
- Go to **"Deployments"** tab → click domain link

**✅ Live at**: `https://your-project.up.railway.app` 🎉

---

## **Step 3: Test Live**

1. Open the Railway domain URL
2. Test features:
   - ✅ Upload resume
   - ✅ Paste job description
   - ✅ Analyze & check results
   - ✅ Export PDF
   - ✅ Portfolio page

---

## **Step 4: Share & Showcase**

### Portfolio Items:
- ✅ **GitHub Repo**: Link in LinkedIn
- ✅ **Live Demo**: Share Railway URL
- ✅ **README**: Add description + screenshots
- ✅ **LinkedIn**: "Launched Career Copilot - AI Resume Matcher"

---

## **Commands Quick Reference**

```bash
# Local testing
python app.py

# Git operations
git add .
git commit -m "message"
git push

# Install dependencies
pip install -r requirements.txt

# Environment setup
pip install -r requirements.txt
python app.py
```

---

## **Troubleshooting**

### Issue: "PORT not found"
**Fix**: Railway auto-sets PORT. Just ensure `app.run(port=int(os.getenv("PORT", 5000)))` in app.py ✓

### Issue: "API Key not working"
**Fix**: Go to Railway → Variables → Check GEMINI_API_KEY is set correctly

### Issue: "Database errors"
**Fix**: Railway uses /tmp directory. SQLite works, but consider PostgreSQL later (Phase 3B)

### Issue: "Deploy failed"
**Fix**: 
1. Check Procfile exists
2. Check requirements.txt has all packages
3. Check .env.example exists

---

## **Next Steps After Deploy**

### Phase 3B (Later):
- [ ] Recruiter Dashboard (bulk resume analysis)
- [ ] Comparison matrix
- [ ] Export candidates list as CSV

### Phase 3C (Future):
- [ ] PostgreSQL database (instead of SQLite)
- [ ] User authentication
- [ ] Saved job searches
- [ ] Email reports

---

## **Important Notes**

⚠️ **Free Tier Limits:**
- Railway: 5GB/month
- Gemini: 5 requests/min (free tier)

✅ **Best Practices:**
- Add GitHub link to resume
- Add live demo link to portfolio
- Share on LinkedIn
- Get feedback from recruiters

---

## **Questions?**

Debug logs: Railway → Deployments → View build/deploy logs

Good luck! 🚀
