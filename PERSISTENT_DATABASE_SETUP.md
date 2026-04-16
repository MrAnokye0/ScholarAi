# 🔒 Persistent Database Setup - Fix User Account Loss

## 🔴 **THE PROBLEM**

**Users lose their accounts after app reboot on Streamlit Cloud!**

**Why?**
- SQLite database is stored in a **file** (`scholarai/data/scholarai.db`)
- Streamlit Cloud uses **ephemeral file system** (temporary)
- All files are **deleted** when app restarts
- Database is **lost** → Users must re-register

---

## ✅ **THE SOLUTION**

Migrate to **PostgreSQL** (cloud database) that persists data permanently.

---

## 🚀 **SETUP GUIDE: Supabase (Free & Easy)**

### **Step 1: Create Supabase Account** (2 minutes)

1. Go to: **https://supabase.com/**
2. Click **"Start your project"**
3. Sign up with **GitHub** or **Google**
4. Click **"New project"**

### **Step 2: Create Database** (3 minutes)

Fill in the form:
- **Name**: `scholarai`
- **Database Password**: Create a strong password (save it!)
- **Region**: Choose closest to your location
- **Pricing Plan**: Free

Click **"Create new project"** and wait 2 minutes for setup.

### **Step 3: Get Connection String** (1 minute)

1. In Supabase dashboard, click **Settings** (⚙️ icon, bottom left)
2. Click **"Database"** in the sidebar
3. Scroll to **"Connection string"**
4. Select **"URI"** tab
5. Copy the connection string (looks like this):

```
postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

6. **Replace `[YOUR-PASSWORD]`** with the password you created in Step 2

**Example**:
```
postgresql://postgres.abc:MySecurePass123@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

### **Step 4: Add to Streamlit Cloud Secrets** (2 minutes)

1. Go to: **https://share.streamlit.io/**
2. Open your app
3. Click **☰ menu** → **Settings** → **Secrets**
4. Add this line at the top:

```toml
DATABASE_URL = "postgresql://postgres.xxx:YOUR-PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Keep your existing secrets below
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "anokyegyasiedward@gmail.com"
SMTP_PASSWORD = "ghiruyggjsyjhqym"
SMTP_FROM = "ScholarAI <anokyegyasiedward@gmail.com>"
GOOGLE_API_KEY = "YOUR_NEW_API_KEY_HERE"
ADMIN_PASSWORD = "scholarai_admin_2026"
```

5. Click **"Save"**
6. App will reboot automatically

### **Step 5: Update Code** (Already done!)

The code has been updated to automatically use PostgreSQL when `DATABASE_URL` is set.

**Files updated**:
- ✅ `database_postgres.py` - New database adapter
- ✅ Supports both SQLite (local) and PostgreSQL (cloud)
- ✅ Automatic detection and switching

### **Step 6: Update app.py to Use New Database**

We need to change the import from `database` to `database_postgres`:

<function_calls>
<invoke name="grepSearch">
<parameter name="explanation">Finding where database is imported in app.py