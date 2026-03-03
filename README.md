# 💊 Pharma CRM Analytics Dashboard

**Pharmaceutical sales team performance analytics — Veeva CRM simulation**

> Portfolio project demonstrating CRM analytics skills for a pharma CRM Analyst role.

---

## What this project shows

- **CRM data modelling** — Veeva-style activity data: calls, HCP records, targets, Business Units
- **KPI monitoring** — Target attainment, conversion rate, HCP tier coverage, call mix
- **Rep performance analysis** — Individual rep tracking with at-risk flagging (<80% attainment)
- **AI-generated insights** — GPT-4o mini produces business recommendations from live data
- **Bilingual UI** — Polish / English toggle (PL/EN)

---

## Project structure

```
crm_project/
├── dashboard.py              # Main Streamlit app
├── crm_data_generator.py     # Veeva-style synthetic data (10 reps, 3 BUs, 6 months)
├── crm_kpi_engine.py         # KPI calculations (attainment, conversion, tier coverage)
├── requirements.txt
└── .streamlit/
    └── secrets.toml          # API key (not committed to git)
```

---

## Setup

```bash
pip install -r requirements.txt
```

Add your OpenAI API key:
```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-..."
```

Run:
```bash
streamlit run dashboard.py
```

---

## Data model

| Entity | Description |
|--------|-------------|
| **Rep** | 10 sales reps across 3 Business Units (Cardiology, Oncology, Neurology) |
| **HCP** | ~350 Healthcare Professionals with Tier A/B/C segmentation |
| **Activity** | ~2,000 CRM call records (F2F, Remote, Phone) with outcomes |
| **Target** | Monthly Rx targets per rep, growing quarterly |

---

## Key metrics

| KPI | Definition |
|-----|-----------|
| **Target Attainment** | Actual Rx value / Monthly target × 100 |
| **Conversion Rate** | Prescription Intent calls / Total calls × 100 |
| **Tier A Ratio** | Calls to Tier A HCPs / Total calls × 100 |
| **At-Risk** | Reps with attainment < 80% |

---

*Built with Streamlit · Plotly · GPT-4o mini*
