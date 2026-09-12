# Deploy Lakeview Results to Railway + Custom Domain

## Official URL after setup
https://results.lakeviewjunior.ac.ke

---

## Step 1 – Create Railway account
1. Go to https://railway.app
2. Sign up with GitHub (recommended) or email
3. Confirm your email if needed

## Step 2 – Deploy the app
1. In Railway dashboard click **New Project**
2. Choose **Deploy from GitHub repo**  
   (or **Empty Project** then upload these files)
3. If using GitHub:
   - Push this whole folder to a GitHub repository first
   - Then select that repository in Railway
4. Railway will detect Python and start building
5. When it finishes you will get a temporary URL like:  
   `https://lakeview-results-production-xxxx.up.railway.app`

## Step 3 – Add the custom domain
1. In your Railway project click the service
2. Go to the **Settings** tab
3. Scroll to **Networking** → **Public Networking** → **Custom Domain**
4. Click **Add Custom Domain**
5. Enter exactly:  
   `results.lakeviewjunior.ac.ke`
6. Railway will show you a **CNAME** value (something like `xxxx.up.railway.app`)

## Step 4 – Create the DNS record (very important)
Ask the person who manages the domain **lakeviewjunior.ac.ke** to add this DNS record:

| Type  | Host / Name | Value (from Railway)      | TTL  |
|-------|-------------|---------------------------|------|
| CNAME | results     | xxxx.up.railway.app       | 300  |

(Replace `xxxx.up.railway.app` with the exact value Railway shows you)

## Step 5 – Wait and test
- DNS usually takes 5–30 minutes (sometimes up to a few hours)
- Open on your phone: https://results.lakeviewjunior.ac.ke
- You should see the Lakeview Junior School Results login page

## Logins after deployment
- Admin:   admin  /  Lakeview@Admin2026
- DOS:     dos    /  Lakeview@DOS2026
- Teacher: teacher1 / Lakeview@Teach2026

**Change these passwords immediately after first login.**

## Need help?
If Railway asks for a start command, use:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
