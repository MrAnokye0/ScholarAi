# 📊 ScholarAI Database Information

## 📍 Database Location

### Local Development
```
scholarai/data/scholarai.db
```

**Full Path on Your Computer**:
```
C:\Users\LENOVO PC\Downloads\ScholarAI_Full_App\scholarai\data\scholarai.db
```

**File Size**: ~72 KB (73,728 bytes)  
**Type**: SQLite Database  
**Last Modified**: April 15, 2026 14:51:13

---

## 🗄️ Database Structure

The database contains **4 main tables**:

### 1. **users** Table
Stores user account information.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key (auto-increment) |
| `username` | TEXT | Unique username |
| `email` | TEXT | Unique email address |
| `password_hash` | TEXT | SHA-256 hashed password |
| `is_verified` | INTEGER | 0 = not verified, 1 = verified |
| `verification_code` | TEXT | 6-digit OTP code |
| `reset_token` | TEXT | Password reset token |
| `tier` | TEXT | "free" or "premium" |
| `credits_used` | INTEGER | Number of reviews generated |
| `remember_token` | TEXT | Persistent login token |
| `created_at` | TEXT | Account creation timestamp |

**Example Data**:
```sql
id: 1
username: "eddy"
email: "anokyegyasiedward@gmail.com"
password_hash: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
is_verified: 1
tier: "free"
credits_used: 5
created_at: "2026-04-15 10:30:00"
```

### 2. **sessions** Table
Tracks user sessions for analytics.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT | Primary key (UUID) |
| `created_at` | TEXT | Session start time |
| `last_active` | TEXT | Last activity time |

**Example Data**:
```sql
session_id: "abc123-def456-ghi789"
created_at: "2026-04-15 10:00:00"
last_active: "2026-04-15 14:51:13"
```

### 3. **reviews** Table
Stores generated literature reviews.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key (auto-increment) |
| `session_id` | TEXT | Foreign key to sessions |
| `topic` | TEXT | Research topic (max 200 chars) |
| `article_count` | INTEGER | Number of articles used |
| `citation_style` | TEXT | APA, Harvard, MLA, etc. |
| `word_count` | INTEGER | Review word count |
| `created_at` | TEXT | Generation timestamp |

**Example Data**:
```sql
id: 1
session_id: "abc123-def456-ghi789"
topic: "Climate change impacts on agriculture"
article_count: 5
citation_style: "APA 7th"
word_count: 2500
created_at: "2026-04-15 11:00:00"
```

### 4. **downloads** Table
Tracks PDF/DOCX downloads.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key (auto-increment) |
| `review_id` | INTEGER | Foreign key to reviews |
| `format` | TEXT | "pdf" or "docx" |
| `created_at` | TEXT | Download timestamp |

**Example Data**:
```sql
id: 1
review_id: 1
format: "pdf"
created_at: "2026-04-15 11:05:00"
```

---

## 🔒 Security & Privacy

### What's Stored:
- ✅ **Usernames** (not sensitive)
- ✅ **Email addresses** (for verification only)
- ✅ **Hashed passwords** (SHA-256, not reversible)
- ✅ **Session IDs** (anonymous)
- ✅ **Review metadata** (topics, word counts)
- ✅ **Usage statistics** (for analytics)

### What's NOT Stored:
- ❌ **Plain text passwords** (only hashes)
- ❌ **Article content** (only metadata)
- ❌ **Generated review text** (only statistics)
- ❌ **Personal information** (beyond email)
- ❌ **Payment information** (not implemented yet)

### Security Features:
- 🔐 **Password Hashing**: SHA-256 encryption
- 🔐 **Email Verification**: Required before login
- 🔐 **Secure Tokens**: 32-byte hex tokens for "Remember Me"
- 🔐 **No PII**: Minimal personal information stored

---

## 📂 File System Structure

```
ScholarAI_Full_App/
├── scholarai/
│   ├── data/
│   │   └── scholarai.db          ← DATABASE FILE HERE
│   ├── app.py
│   ├── database.py
│   ├── mailer.py
│   └── ...
├── .env
└── requirements.txt
```

---

## 🌐 On Streamlit Cloud

### Database Location on Cloud:
```
/mount/src/scholarai/data/scholarai.db
```

### Important Notes:

⚠️ **CRITICAL**: On Streamlit Cloud, the database is **ephemeral** (temporary)!

**What This Means**:
- ✅ Database works during app runtime
- ❌ Database is **deleted** when app restarts
- ❌ User accounts are **lost** on reboot
- ❌ All data is **temporary**

**Why This Happens**:
- Streamlit Cloud uses **ephemeral file systems**
- Files are not persisted between deployments
- Each reboot starts with a fresh file system

**Solution for Production**:
You need to use a **persistent database**:
1. **PostgreSQL** (recommended)
2. **MySQL**
3. **MongoDB**
4. **Supabase** (easiest)
5. **Firebase**

---

## 🔄 Database Persistence Solutions

### Option 1: Supabase (Recommended - Free & Easy)

**Why Supabase**:
- ✅ Free tier (500 MB storage)
- ✅ PostgreSQL database
- ✅ Built-in authentication
- ✅ Real-time updates
- ✅ Easy setup (5 minutes)

**Setup**:
1. Go to: https://supabase.com/
2. Create free account
3. Create new project
4. Get connection string
5. Update `database.py` to use PostgreSQL

**Code Changes Needed**:
```python
# Instead of SQLite
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")  # From Supabase
conn = psycopg2.connect(DATABASE_URL)
```

### Option 2: PostgreSQL on Render

**Why Render**:
- ✅ Free tier (90 days)
- ✅ PostgreSQL database
- ✅ Easy integration
- ✅ Good for production

**Setup**:
1. Go to: https://render.com/
2. Create PostgreSQL database
3. Get connection string
4. Update code

### Option 3: SQLite with Persistent Volume

**Why This**:
- ✅ Keep using SQLite
- ✅ No code changes
- ❌ Requires paid Streamlit plan

**Setup**:
1. Upgrade to Streamlit Teams/Enterprise
2. Request persistent volume
3. Mount volume to `/data`

---

## 🛠️ Database Management Tools

### View Database Locally:

#### Option 1: DB Browser for SQLite (GUI)
1. Download: https://sqlitebrowser.org/
2. Open `scholarai/data/scholarai.db`
3. Browse tables, run queries

#### Option 2: Command Line
```bash
cd scholarai/data
sqlite3 scholarai.db

# List tables
.tables

# View users
SELECT * FROM users;

# View reviews
SELECT * FROM reviews;

# Exit
.quit
```

#### Option 3: Python Script
```python
import sqlite3

conn = sqlite3.connect('scholarai/data/scholarai.db')
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT username, email, tier FROM users")
for row in cursor.fetchall():
    print(row)

conn.close()
```

---

## 📊 Database Statistics

### Current Database:
- **Size**: 72 KB
- **Tables**: 4
- **Users**: ~1-5 (estimated)
- **Reviews**: ~0-10 (estimated)
- **Sessions**: ~5-20 (estimated)

### Growth Estimates:
- **Per User**: ~1 KB
- **Per Review**: ~500 bytes (metadata only)
- **Per Session**: ~200 bytes

**1,000 users** = ~1 MB  
**10,000 users** = ~10 MB  
**100,000 users** = ~100 MB

---

## 🔍 Querying the Database

### Get All Users:
```sql
SELECT username, email, is_verified, tier, credits_used 
FROM users 
ORDER BY created_at DESC;
```

### Get Unverified Users:
```sql
SELECT username, email, verification_code 
FROM users 
WHERE is_verified = 0;
```

### Get Premium Users:
```sql
SELECT username, email, credits_used 
FROM users 
WHERE tier = 'premium';
```

### Get Review Statistics:
```sql
SELECT 
    COUNT(*) as total_reviews,
    AVG(article_count) as avg_articles,
    AVG(word_count) as avg_words,
    citation_style,
    COUNT(*) as count
FROM reviews 
GROUP BY citation_style;
```

### Get Active Users Today:
```sql
SELECT COUNT(DISTINCT session_id) 
FROM sessions 
WHERE date(last_active) = date('now');
```

---

## 🚨 Database Backup

### Manual Backup (Local):
```bash
# Copy database file
cp scholarai/data/scholarai.db scholarai/data/scholarai_backup_$(date +%Y%m%d).db

# Or use git
git add scholarai/data/scholarai.db
git commit -m "Backup database"
git push
```

### Automated Backup Script:
```python
import shutil
from datetime import datetime

source = "scholarai/data/scholarai.db"
backup = f"scholarai/data/backups/scholarai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

shutil.copy2(source, backup)
print(f"Backup created: {backup}")
```

---

## ⚠️ Important Warnings

### 1. **Streamlit Cloud = Temporary Database**
- Database is deleted on every reboot
- Users will lose accounts
- Not suitable for production

### 2. **No Automatic Backups**
- SQLite file is not backed up automatically
- You must manually backup
- Consider using persistent database

### 3. **Concurrent Access**
- SQLite has limited concurrent write support
- May cause issues with many users
- PostgreSQL recommended for production

### 4. **File Size Limits**
- Streamlit Cloud has storage limits
- Large databases may cause issues
- Monitor database size

---

## ✅ Recommendations

### For Development (Current):
- ✅ SQLite is perfect
- ✅ Fast and simple
- ✅ No setup needed

### For Production (Live Site):
- ⚠️ **Switch to PostgreSQL** (Supabase)
- ⚠️ **Enable automatic backups**
- ⚠️ **Monitor database size**
- ⚠️ **Set up database migrations**

---

## 🎯 Next Steps

### Immediate (Keep SQLite):
1. ✅ Database works locally
2. ⚠️ Accept data loss on Streamlit Cloud reboots
3. ⚠️ Manually verify users if needed

### Long-term (Production):
1. 🔄 Migrate to Supabase/PostgreSQL
2. 🔄 Set up automatic backups
3. 🔄 Implement database migrations
4. 🔄 Add monitoring and alerts

---

## 📞 Database Access

### Admin Tools Available:
```bash
# List all users
python scholarai/admin_tools.py

# Get user's verification code
python scholarai/get_user_code.py user@email.com

# Manually verify user
python scholarai/bypass_verification.py user@email.com

# Check login issues
python scholarai/check_login_issue.py user@email.com
```

---

## 📚 Summary

**Location**: `scholarai/data/scholarai.db`  
**Type**: SQLite  
**Size**: ~72 KB  
**Tables**: 4 (users, sessions, reviews, downloads)  
**Security**: Passwords hashed, minimal PII  
**Persistence**: ⚠️ Temporary on Streamlit Cloud  
**Recommendation**: Migrate to PostgreSQL for production  

---

**Last Updated**: April 15, 2026  
**Database Version**: 1.0  
**Status**: Working locally, temporary on cloud
