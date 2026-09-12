# Lakeview Junior School – Results System  
## Simple Deployment Guide (Teachers can use from phones)

This system is a **mobile-friendly web app**. Teachers open it in the phone browser (Chrome / Safari) and can even “Add to Home Screen” so it looks like a real app.

---

### Option A – Quickest for one school (Recommended starting point)

**Use a free cloud service that runs Python apps**

#### 1. Railway.app (easiest)
1. Create a free account at https://railway.app
2. Click **New Project** → **Deploy from GitHub** (or upload the folder)
3. Add a new service and point it to this project folder
4. Set the start command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Railway gives you a public URL, e.g.  
   `https://lakeview-results.up.railway.app`

Teachers just open that link on their phones.

#### 2. Render.com
1. Go to https://render.com → New → Web Service
2. Connect the project
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Free tier is enough for one school

#### 3. PythonAnywhere (very simple for Kenya users)
1. Create account at https://www.pythonanywhere.com
2. Upload the project files
3. Create a Web App (Manual configuration)
4. Point it to the FastAPI app

---

### Option B – Run on a school computer / small server

1. Install Python 3.10+ on the computer that will stay on.
2. Open terminal in the project folder and run:
   ```bash
   pip install fastapi uvicorn sqlalchemy python-multipart jinja2 python-jose passlib bcrypt reportlab pydantic-settings aiofiles
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. Find the computer’s local IP (e.g. `192.168.1.50`)
4. Teachers on the same Wi-Fi open:  
   `http://192.168.1.50:8000`

To make it available from outside the school network you need:
- A public IP or
- A free tunnel such as **Cloudflare Tunnel** or **ngrok**

---

### Making it feel like a real mobile app

On any Android or iPhone:
1. Open the school URL in Chrome / Safari
2. Tap the browser menu → **Add to Home Screen** / **Install App**
3. An icon appears on the phone home screen
4. Teachers open it like any other app

---

### Default logins (change these in production!)

| Role                    | Username  | Password    |
|-------------------------|-----------|-------------|
| Admin                   | admin     | admin123    |
| Director of Studies     | dos       | dos123      |
| Teacher (demo)          | teacher1  | teacher123  |

**Important security steps before real use:**
1. Change all default passwords
2. Create real teacher accounts (Admin can do this later)
3. Assign each teacher their streams and subjects under **Teacher Assignments**
4. Keep regular backups of the file `lakeview_results.db`

---

### Daily use by teachers (on phone)

1. Open the link or the home-screen icon
2. Login with username + password
3. Tap **Assessments & Marks**
4. Create or open an assessment
5. Filter by **Stream** if needed
6. Enter scores → they convert automatically to EE1–BE2
7. Save → Submit for Countersign
8. Admin / DOS countersigns
9. Admin / DOS generates PDF report cards from the **Report Cards** menu

Parents use the **Parent / Learner View** and only need the unique View Code (no login).

---

### Need help?

If you want, I can also prepare:
- A one-click Docker setup
- Automatic daily backups
- Custom school logo on the report cards
- SMS notifications of View Codes to parents

Just ask.

---

## Official School URL

**https://results.lakeviewjunior.ac.ke**

This is the address teachers and parents will use on their phones.

### How to make results.lakeviewjunior.ac.ke work

1. **Own the domain** `lakeviewjunior.ac.ke` (or ask the person who manages the school website).
2. **Create a DNS record** (usually in the domain control panel):
   - Type: **CNAME** (or A record)
   - Name / Host: `results`
   - Value / Points to: the address given by your hosting provider  
     (e.g. `your-app.up.railway.app` or `your-app.onrender.com`)
3. **Deploy the app** (Railway or Render recommended).
4. In the hosting dashboard, add the custom domain:  
   `results.lakeviewjunior.ac.ke`
5. Wait 5–30 minutes for DNS to update.
6. Open **https://results.lakeviewjunior.ac.ke** on a phone to test.

Once live, teachers simply bookmark or “Add to Home Screen”.

