# 🎓 ScholarAI — Academic Literature Review Generator

> Upload your articles. Input your topic. Receive a complete, cited Literature Review. Download in any citation style. Instantly.

![ScholarAI Banner](https://img.shields.io/badge/ScholarAI-v1.0-4361EE?style=for-the-badge&logo=openai)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-06D6A0?style=flat)

---

## ✨ What It Does

ScholarAI is a Streamlit web app that helps university students write literature reviews:

1. **Input your research topic** (your university-approved area of study)
2. **Upload 1–5 academic articles** (PDF, DOCX, or TXT — up to 15 MB each)
3. **Select your citation style** (APA 7th, Harvard, MLA 9th, Chicago 17th, Vancouver, IEEE)
4. **Click Generate** — GPT-4o writes a complete literature review with:
   - Structured Introduction, thematic body sections, and Conclusion
   - In-text citations from your uploaded articles
   - Full reference list in your chosen style
5. **Download** as PDF, DOCX, or plain text — or copy directly

---

## 🚀 Quick Start (Local)

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/scholarai.git
cd scholarai
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```
Edit `.env`:
```
OPENAI_API_KEY=sk-your-key-here
ADMIN_PASSWORD=your_secure_password
```

### 5. Run the app
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🛡 Admin Dashboard

Access the admin dashboard at [http://localhost:8501/Admin_Dashboard](http://localhost:8501/Admin_Dashboard)

**Default password:** `scholarai_admin_2026` (change in `.env`)

**Dashboard shows:**
- Total users (sessions) and active users today
- Reviews generated (today / this week / all time)
- Downloads by format (PDF, DOCX, TXT)
- Citation style distribution chart
- Daily review volume chart (last 14 days)
- Recent reviews table with topic, style, word count

---

## 📁 Project Structure

```
scholarai/
├── app.py                      # Main Streamlit app
├── pages/
│   └── Admin_Dashboard.py      # Admin analytics panel
├── extractor.py                # PDF/DOCX/TXT text extraction
├── reviewer.py                 # AI pipeline (metadata → review → citations)
├── reference_formatter.py      # 6 citation style formatters
├── exporter.py                 # PDF (ReportLab) + DOCX generation
├── database.py                 # SQLite session & review tracking
├── prompts.py                  # GPT-4o system prompt templates
├── utils.py                    # Shared helper functions
├── assets/
│   └── style.css               # Custom brand CSS
├── .streamlit/
│   └── config.toml             # Theme + server config
├── data/
│   └── scholarai.db            # SQLite database (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📚 Supported Citation Styles

| Style | Use Case |
|-------|----------|
| APA 7th | Social sciences, psychology, education |
| Harvard | UK & African universities, natural sciences |
| MLA 9th | Humanities, literature, language studies |
| Chicago 17th | History, arts, some social sciences |
| Vancouver | Medicine, nursing, biomedical sciences |
| IEEE | Engineering, computer science, technology |

---

## 🔒 Privacy & Security

- **API keys** are stored in `st.session_state` only — never written to disk or logs
- **Uploaded articles** are processed in memory — never saved to the server
- **Generated reviews** are session-only — cleared on page refresh
- **No user accounts** — fully anonymous; only anonymous session IDs are tracked
- **Database** stores only: session ID (UUID), topic, article count, style, word count, timestamps

---

## ☁️ Deploy to Streamlit Cloud

1. Push your repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → set `app.py` as the entry point
4. Add secrets in Streamlit Cloud settings:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ADMIN_PASSWORD = "your_password"
   ```
5. Deploy!

> **Note:** Streamlit Cloud has an ephemeral filesystem — the SQLite database resets on each deployment. For persistent admin stats in production, replace `database.py` with a Supabase or PostgreSQL connection.

---

## ⚠️ Academic Integrity

ScholarAI generates an **AI-assisted first draft**. Students must:
- Review all AI-generated content for accuracy
- Verify citations against the original source articles
- Ensure compliance with their institution's academic integrity policy
- Make necessary edits before submission

ScholarAI is a writing tool, not a submission tool.

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | Streamlit 1.32+ |
| AI — Review Writer | OpenAI GPT-4o |
| AI — Metadata | OpenAI GPT-4o-mini |
| PDF Extraction | PyMuPDF (fitz) |
| DOCX Extraction | python-docx |
| PDF Generation | ReportLab |
| DOCX Generation | python-docx |
| Analytics Charts | Plotly |
| Database | SQLite (via Python stdlib) |
| Hosting | Streamlit Community Cloud |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ for African university students · Powered by OpenAI GPT-4o*
