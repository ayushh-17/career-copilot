# AI Career Copilot — Phase 1 Setup

## Kya hai ye?
Ye ek AI-powered tool hai jo resume aur job description dekh kar:
- ATS match score deta hai
- Missing keywords batata hai
- Tailored resume bullets aur cover letter generate karta hai

Abhi hum **Phase 1** kar rahe hain: basic setup + Claude API connection test.

## Setup Steps (ek-ek karke follow karo)

### 1. Python installed hai check karo
Terminal/CMD me type karo:
```
python --version
```
Agar 3.9+ nahi hai, to python.org se install kar lo.

### 2. Virtual environment banao (recommended)
```
python -m venv venv
```
Activate karo:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

### 3. Dependencies install karo
```
pip install -r requirements.txt
```

### 4. Gemini API key lo (FREE — no credit card chahiye)
1. https://aistudio.google.com pe jaake apne Google account se login karo
2. "Get API Key" pe click karo → "Create API Key"
3. `.env.example` file ka naam badal ke `.env` kar do
4. `.env` file me apni key paste karo:
   ```
   GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxx
   ```

### 5. App run karo
```
python app.py
```

### 6. Browser me check karo
- http://localhost:5000 → placeholder homepage dikhega
- http://localhost:5000/test-ai → Gemini ka reply dikhna chahiye (JSON format me)

Agar `/test-ai` pe success message aaye — **Phase 1 complete!** 🎉

## Next: Phase 2
Isme hum asli frontend form banayenge (resume + job description input) — jab ready ho, bata dena.
