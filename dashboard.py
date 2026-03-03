# dashboard.py  –  Pharma CRM Analytics  |  Veeva CRM simulation
import warnings; warnings.filterwarnings("ignore")
import logging;  logging.getLogger("streamlit").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests, sys, os

sys.path.insert(0, os.path.dirname(__file__))
from crm_data_generator import generate_crm_data
from crm_kpi_engine      import CRMKPIEngine

st.set_page_config(page_title="Pharma CRM Analytics", page_icon="💊",
                   layout="wide", initial_sidebar_state="expanded")

# ── language ──────────────────────────────────────────────────────────────────
T = {
    "title":    {"pl": "Analityka CRM – Zespół Sprzedażowy",
                 "en": "CRM Analytics – Sales Performance"},
    "subtitle": {"pl": "Symulacja danych Veeva CRM · Farmaceutyczne Business Units",
                 "en": "Veeva CRM Data Simulation · Pharmaceutical Business Units"},
    "filters":  {"pl": "Filtry", "en": "Filters"},
    "bu":       {"pl": "Business Unit", "en": "Business Unit"},
    "region":   {"pl": "Region", "en": "Region"},
    "period":   {"pl": "Okres (miesiąc)", "en": "Period (month)"},
    "kpi_rx":   {"pl": "Wartość Rx", "en": "Rx Value"},
    "kpi_calls":{"pl": "Wizyty łącznie", "en": "Total Calls"},
    "kpi_att":  {"pl": "Realizacja celu", "en": "Target Attainment"},
    "kpi_conv": {"pl": "Skuteczność wizyt", "en": "Visit Conversion Rate"},
    "kpi_hcps": {"pl": "Unikalnych lekarzy", "en": "Unique HCPs Visited"},
    "kpi_risk": {"pl": "Reps zagrożeni", "en": "At-Risk Reps"},
    "sec_reps": {"pl": "Efektywność Przedstawicieli Medycznych",
                 "en": "Medical Rep Performance"},
    "sec_trend":{"pl": "Trend Miesięczny Rx wg Business Unit",
                 "en": "Monthly Rx Trend by Business Unit"},
    "sec_bu":   {"pl": "Wyniki wg Business Unit", "en": "Results by Business Unit"},
    "sec_prod": {"pl": "Ranking Produktów", "en": "Product Ranking"},
    "sec_tier": {"pl": "Pokrycie Lekarzy wg Segmentu (Tier)",
                 "en": "HCP Coverage by Segment (Tier)"},
    "sec_calls":{"pl": "Mix Kanałów Kontaktu", "en": "Contact Channel Mix"},
    "sec_risk": {"pl": "Przedstawiciele poniżej 80% realizacji celu",
                 "en": "Representatives Below 80% Target Attainment"},
    "ai_btn":   {"pl": "🤖  Generuj Insight AI", "en": "🤖  Generate AI Insight"},
    "ai_spin":  {"pl": "Analizuję dane…", "en": "Analysing data…"},
    "ai_label": {"pl": "✦ Insight AI", "en": "✦ AI Insight"},
    "footer":   {"pl": "Symulacja danych Veeva CRM · Dane demonstracyjne · GPT-4o mini",
                 "en": "Veeva CRM Data Simulation · Demo Data · Powered by GPT-4o mini"},
    "no_key":   {"pl": "⚠️ Brak klucza. Dodaj OPENAI_API_KEY do .streamlit/secrets.toml",
                 "en": "⚠️ Missing key. Add OPENAI_API_KEY to .streamlit/secrets.toml"},
    "act_label":    {"pl": "aktywności CRM",  "en": "CRM activities"},
    "on_track":     {"pl": "✓ cel realizowany", "en": "✓ on track"},
    "below_target": {"pl": "⚠ poniżej celu",   "en": "⚠ below target"},
    "at_risk_note": {"pl": "✗ zagrożony",       "en": "✗ at risk"},
    "reps_below":   {"pl": "reps < 80% celu",   "en": "reps < 80% target"},
    "col_rep":   {"pl": "Przedstawiciel",  "en": "Representative"},
    "col_level": {"pl": "Poziom",          "en": "Level"},
    "col_calls": {"pl": "Wizyty",          "en": "Calls"},
    "col_rx":    {"pl": "Wartość Rx",      "en": "Rx Value"},
    "col_att":   {"pl": "Realizacja %",    "en": "Attainment %"},
    "col_conv":  {"pl": "Konwersja %",     "en": "Conversion %"},
    "col_tiera": {"pl": "Tier A %",        "en": "Tier A %"},
    "col_hcps":  {"pl": "Lekarze",         "en": "HCPs"},
    "tier_a":    {"pl": "A – strategiczni","en": "A – strategic"},
    "tier_b":    {"pl": "B – średni",      "en": "B – medium"},
    "tier_c":    {"pl": "C – niski",       "en": "C – low"},
    "target_line": {"pl": "Cel",           "en": "Target"},
}
def t(k): return T[k][st.session_state.get("lang", "pl")]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&family=Fraunces:wght@700;900&display=swap');

html,body,[class*="css"]{ font-family:'DM Sans',sans-serif; }
.stApp{ background:#f4f2ed; color:#1c1c2e; }
.block-container{ padding-top:1.6rem !important; }

/* KPI cards */
.kpi-card{
    background:#fff; border-radius:16px; padding:22px 24px 18px;
    border:1px solid #e2ddd4; box-shadow:0 2px 8px rgba(0,0,0,.06);
    position:relative; overflow:hidden;
}
.kpi-card::before{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:#cbd0da;
}
.kpi-card.good::before  { background:#2dce89; }
.kpi-card.warn::before  { background:#f4a100; }
.kpi-card.alert::before { background:#e53e3e; }
.kpi-card.blue::before  { background:#3a6fcc; }
.kpi-label{
    font-family:'DM Mono',monospace; font-size:10px; letter-spacing:1.8px;
    text-transform:uppercase; color:#9090a8; margin-bottom:8px;
}
.kpi-value{
    font-family:'Fraunces',serif; font-size:36px; font-weight:900;
    color:#1c1c2e; line-height:1; margin-bottom:4px;
}
.kpi-sub{ font-family:'DM Mono',monospace; font-size:11px; color:#9090a8; }

/* section headers */
.sec{
    font-family:'Fraunces',serif; font-size:22px; font-weight:700;
    color:#1c1c2e; margin:32px 0 14px;
    display:flex; align-items:center; gap:10px;
}
.sec::after{ content:''; flex:1; height:1px; background:#e2ddd4; margin-left:8px; }

/* AI insight */
.ai-box{
    background:linear-gradient(135deg,#fffdf5,#fff8e6);
    border:1px solid #f0d990; border-left:4px solid #f4a100;
    border-radius:12px; padding:18px 22px; margin-top:4px;
    font-size:14px; color:#2a2a3c; line-height:1.8;
}
.ai-title{
    font-family:'DM Mono',monospace; font-size:10px; letter-spacing:1.8px;
    text-transform:uppercase; color:#c07a00; margin-bottom:8px;
}

/* BUTTONS – always visible */
div[data-testid="stButton"] > button {
    background: #1c1c2e !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.22) !important;
    transition: all .15s ease !important;
    min-width: 180px !important;
}
div[data-testid="stButton"] > button:hover {
    background: #3a3a5c !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.28) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0px) !important;
}

/* sidebar */
section[data-testid="stSidebar"] { background:#1c1c2e !important; }
section[data-testid="stSidebar"] * { color:#c8c8e0 !important; }
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background:#3a3a5c !important;
    border:1px solid #5a5a80 !important;
    min-width:unset !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background:#5a5a80 !important;
}

hr { border:none; border-top:1px solid #e2ddd4; margin:8px 0; }
h1,h2,h3 { font-family:'Fraunces',serif !important; font-weight:700 !important; }
</style>
""", unsafe_allow_html=True)

# ── chart defaults ─────────────────────────────────────────────────────────────
CL = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#4a4a6a", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
)
PAL = ["#3a6fcc", "#e05c5c", "#2dce89", "#f4a100", "#9b59b6", "#1abc9c"]

LEGEND_STYLE = dict(
    bgcolor="#ffffff",
    bordercolor="#1c1c2e",
    borderwidth=1.5,
    font=dict(family="DM Sans", size=13, color="#1c1c2e"),
    itemsizing="constant",
)

# ── AI engine ─────────────────────────────────────────────────────────────────
def get_insight(ppl, pen, ctx):
    lang    = st.session_state.get("lang", "pl")
    api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    if not api_key:
        return t("no_key")
    sys_pl = ("Jesteś doświadczonym analitykiem CRM w branży farmaceutycznej. "
              "Odpowiadasz po polsku. 3-5 konkretnych zdań z liczbami z danych. "
              "Zakończ jedną rekomendacją dla managera sprzedaży. Bez ogólników.")
    sys_en = ("You are an experienced pharma CRM analyst. Reply in English. "
              "3-5 specific sentences with numbers from the data. "
              "End with one clear recommendation for the sales manager. No fluff.")
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "max_tokens": 350,
                "messages": [
                    {"role": "system",
                     "content": sys_pl if lang == "pl" else sys_en},
                    {"role": "user",
                     "content": f"{ppl if lang == 'pl' else pen}\n\nDATA:\n{ctx}"},
                ],
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ {e}"


def ai_block(key, ppl, pen, ctx):
    if st.button(t("ai_btn"), key=key):
        with st.spinner(t("ai_spin")):
            st.session_state[f"i_{key}"] = get_insight(ppl, pen, ctx)
    if f"i_{key}" in st.session_state:
        st.markdown(
            f'<div class="ai-box"><div class="ai-title">{t("ai_label")}</div>'
            f'{st.session_state[f"i_{key}"]}</div>',
            unsafe_allow_html=True,
        )

# ── helpers ───────────────────────────────────────────────────────────────────
def fv(v, pre="", suf=""):
    if abs(v) >= 1e6: return f"{pre}{v/1e6:.1f}M{suf}"
    if abs(v) >= 1e3: return f"{pre}{v/1e3:.0f}K{suf}"
    return f"{pre}{v:.1f}{suf}"


def kpi_card(col, label, value, pre="", suf="", note="", variant="blue"):
    col.markdown(
        f'<div class="kpi-card {variant}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{fv(value, pre, suf)}</div>'
        f'{"<div class=kpi-sub>" + note + "</div>" if note else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def att_color(v):
    if v >= 100: return "#2dce89"
    if v >= 80:  return "#f4a100"
    return "#e53e3e"

# ── load & cache ──────────────────────────────────────────────────────────────
@st.cache_data
def load():
    d = generate_crm_data(months=6)
    e = CRMKPIEngine(d["activities"], d["targets"])
    return d, e

data, engine = load()

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    lc = st.radio("🌐 Language / Język", ["PL", "EN"], horizontal=True)
    st.session_state["lang"] = "pl" if lc == "PL" else "en"
    st.markdown("---")
    st.markdown(f"**{t('filters')}**")

    all_bu  = sorted(data["activities"]["bu"].unique())
    sel_bu  = st.multiselect(t("bu"), all_bu, default=all_bu)

    all_reg = sorted(data["activities"]["region"].unique())
    sel_reg = st.multiselect(t("region"), all_reg, default=all_reg)

    all_mo  = sorted(data["activities"]["date"].dt.strftime("%Y-%m").unique())
    sel_mo  = st.multiselect(t("period"), all_mo, default=all_mo)

    st.markdown("---")
    st.markdown(
        '<div style="font-family:DM Mono,monospace;font-size:10px;'
        'color:#505070;line-height:2.2">'
        'PIPELINE<br>crm_data_generator<br>'
        '→ CRMKPIEngine<br>→ GPT-4o mini</div>',
        unsafe_allow_html=True,
    )

# ── filter ────────────────────────────────────────────────────────────────────
act = data["activities"].copy()
act["year_month"] = act["date"].dt.strftime("%Y-%m")
if sel_bu:  act = act[act["bu"].isin(sel_bu)]
if sel_reg: act = act[act["region"].isin(sel_reg)]
if sel_mo:  act = act[act["year_month"].isin(sel_mo)]

tgt = data["targets"].copy()
if sel_bu:  tgt = tgt[tgt["bu"].isin(sel_bu)]
if sel_reg: tgt = tgt[tgt["region"].isin(sel_reg)]
if sel_mo:  tgt = tgt[tgt["year_month"].isin(sel_mo)]

eng     = CRMKPIEngine(act, tgt)
rep_sum = eng.rep_summary()
bu_sum  = eng.bu_summary()
monthly = eng.monthly_trend()
prod    = eng.product_performance()
at_risk = eng.at_risk_reps()

total_rx    = rep_sum["total_rx"].sum()
total_calls = rep_sum["total_calls"].sum()
avg_att     = rep_sum["target_attainment"].mean()
avg_conv    = rep_sum["conversion_rate"].mean()
unique_hcps = act["hcp_id"].nunique()
n_risk      = len(at_risk)

# ── header ────────────────────────────────────────────────────────────────────
st.markdown(f"# 💊 {t('title')}")
st.markdown(
    f"<span style='font-family:DM Mono,monospace;font-size:11px;color:#9090a8'>"
    f"{t('subtitle')} &nbsp;·&nbsp; "
    f"{act['date'].min().strftime('%b %Y')} – {act['date'].max().strftime('%b %Y')}"
    f" &nbsp;·&nbsp; {len(act):,} {t('act_label')}"
    f"</span>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
kpi_card(k1, t("kpi_rx"),    total_rx,    pre="$", variant="blue")
kpi_card(k2, t("kpi_calls"), total_calls, variant="blue")
kpi_card(k3, t("kpi_att"),   avg_att,     suf="%",
         note=t("on_track") if avg_att >= 100 else t("below_target") if avg_att >= 80 else t("at_risk_note"),
         variant="good" if avg_att >= 100 else "warn" if avg_att >= 80 else "alert")
kpi_card(k4, t("kpi_conv"),  avg_conv,    suf="%", variant="blue")
kpi_card(k5, t("kpi_hcps"),  unique_hcps, variant="blue")
kpi_card(k6, t("kpi_risk"),  n_risk,
         note=t("reps_below"),
         variant="alert" if n_risk > 2 else "warn" if n_risk > 0 else "good")
st.markdown("<br>", unsafe_allow_html=True)

# AI — executive summary
top3 = rep_sum.nlargest(3, "target_attainment")[["rep_name","target_attainment","total_rx"]].to_string(index=False)
bot3 = rep_sum.nsmallest(3, "target_attainment")[["rep_name","target_attainment","total_rx"]].to_string(index=False)
ai_block(
    "exec",
    "Napisz executive summary dla managera sprzedaży pharma. Oceń kondycję zespołu, wskaż kto potrzebuje wsparcia i co zrobić w tym miesiącu.",
    "Write an executive summary for a pharma sales manager. Assess team health, flag who needs support, recommend actions for this month.",
    f"Rx: ${total_rx:,.0f} | Calls: {total_calls} | Avg Attainment: {avg_att:.1f}% | Conv: {avg_conv:.1f}%\n"
    f"At-risk: {n_risk}\nTop 3:\n{top3}\nBottom 3:\n{bot3}\n"
    f"BU:\n{bu_sum[['bu','attainment','total_rx']].to_string(index=False)}",
)

# ── rep performance ────────────────────────────────────────────────────────────
st.markdown(f'<div class="sec">👤 {t("sec_reps")}</div>', unsafe_allow_html=True)

# attainment bar chart
fig_att = go.Figure()
fig_att.add_trace(go.Bar(
    x=rep_sum["rep_name"],
    y=rep_sum["target_attainment"],
    marker_color=[att_color(v) for v in rep_sum["target_attainment"]],
    text=rep_sum["target_attainment"].apply(lambda x: f"{x:.0f}%"),
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Attainment: %{y:.1f}%<extra></extra>",
))
fig_att.add_hline(y=100, line_dash="dot", line_color="#1c1c2e", line_width=1.5,
                  annotation_text="100% target", annotation_position="top right")
fig_att.add_hline(y=80,  line_dash="dot", line_color="#e53e3e", line_width=1,
                  annotation_text="80% threshold", annotation_position="bottom right")
fig_att.update_layout(
    **CL, height=320, showlegend=False,
    xaxis=dict(tickangle=-25, gridcolor="rgba(0,0,0,0)"),
    yaxis=dict(gridcolor="#e2ddd4", ticksuffix="%",
               range=[0, max(rep_sum["target_attainment"].max() * 1.18, 120)]),
)
st.plotly_chart(fig_att, width='stretch')

# rep table
rc = {
    "rep_name":          t("col_rep"),
    "bu":                "BU",
    "region":            "Region",
    "seniority":         t("col_level"),
    "total_calls":       t("col_calls"),
    "total_rx":          t("col_rx"),
    "target_attainment": t("col_att"),
    "conversion_rate":   t("col_conv"),
    "tier_a_ratio":      t("col_tiera"),
    "unique_hcps":       t("col_hcps"),
}
rd = rep_sum[list(rc.keys())].rename(columns=rc).copy()
rd[t("col_rx")]  = rd[t("col_rx")].apply(lambda x: f"${x:,.0f}")
rd[t("col_att")] = rd[t("col_att")].apply(lambda x: f"{x:.1f}%")
rd[t("col_conv")]= rd[t("col_conv")].apply(lambda x: f"{x:.1f}%")
rd[t("col_tiera")]= rd[t("col_tiera")].apply(lambda x: f"{x:.1f}%")
st.dataframe(rd, width='stretch', hide_index=True)

ai_block(
    "reps",
    "Przeanalizuj efektywność przedstawicieli medycznych. Kto jest na ryzyku nierealizacji celu? Jakie działania coaching/wsparcie polecasz managerowi?",
    "Analyse medical rep performance. Who is at risk of missing target? What coaching or support actions do you recommend to the manager?",
    rep_sum[["rep_name","bu","seniority","target_attainment","conversion_rate","tier_a_ratio","total_calls"]].to_string(index=False),
)

# ── monthly trend ──────────────────────────────────────────────────────────────
st.markdown(f'<div class="sec">📈 {t("sec_trend")}</div>', unsafe_allow_html=True)

bum = (monthly
       .groupby(["bu","year_month"])
       .agg(rx=("rx","sum"), target=("target_rx","sum"))
       .reset_index())

fig_tr = go.Figure()
for i, bu in enumerate(bum["bu"].unique()):
    d = bum[bum["bu"] == bu]

    # linia celu — tylko pierwsza BU pokazuje legendę "--- Cel"
    fig_tr.add_trace(go.Scatter(
        x=d["year_month"], y=d["target"],
        mode="lines",
        name=t("target_line") if i == 0 else f"_target_{bu}",  # _ = ukryj z legendy
        showlegend=(i == 0),
        line=dict(color="#aaaaaa", width=1.4, dash="dot"),
        hovertemplate=f"{bu} target: $%{{y:,.0f}}<extra></extra>",
    ))

    # linia rzeczywista
    fig_tr.add_trace(go.Scatter(
        x=d["year_month"], y=d["rx"],
        mode="lines+markers", name=bu,
        line=dict(color=PAL[i], width=2.5),
        marker=dict(size=7, color=PAL[i]),
        hovertemplate=f"<b>{bu}</b><br>%{{x}}<br>Rx: $%{{y:,.0f}}<extra></extra>",
    ))

fig_tr.update_layout(
    **CL, height=360, hovermode="x unified",
    xaxis=dict(gridcolor="#e2ddd4", tickfont=dict(size=12)),
    yaxis=dict(gridcolor="#e2ddd4", tickprefix="$", tickfont=dict(size=12)),
    legend=dict(
        **LEGEND_STYLE,
        orientation="v",
        x=1.01, xanchor="left",
        y=1.0,  yanchor="top",
        tracegroupgap=6,
    ),
)
st.plotly_chart(fig_tr, width='stretch')

ai_block(
    "trend",
    "Przeanalizuj trend miesięczny sprzedaży per Business Unit. Które BU rośnie, które spada? Co może wyjaśniać różnice?",
    "Analyse monthly Rx trend per Business Unit. Which BU is growing? Which is declining? What might explain the differences?",
    bum.to_string(index=False),
)

# ── BU + product ───────────────────────────────────────────────────────────────
cl, cr = st.columns(2, gap="large")

with cl:
    st.markdown(f'<div class="sec">🏢 {t("sec_bu")}</div>', unsafe_allow_html=True)
    fig_bu = go.Figure()
    for i, row in bu_sum.iterrows():
        fig_bu.add_trace(go.Bar(
            name=row["bu"], x=[row["bu"]], y=[row["total_rx"]],
            marker_color=PAL[i % len(PAL)],
            text=f'${row["total_rx"]/1000:.0f}K · {row["attainment"]:.0f}%',
            textposition="inside", insidetextanchor="middle",
            hovertemplate=f'<b>{row["bu"]}</b><br>Rx: $%{{y:,.0f}}<br>Att: {row["attainment"]:.1f}%<extra></extra>',
        ))
    fig_bu.update_layout(
        **CL, height=300, showlegend=False,
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="#e2ddd4", tickprefix="$"),
    )
    st.plotly_chart(fig_bu, width='stretch')

with cr:
    st.markdown(f'<div class="sec">💊 {t("sec_prod")}</div>', unsafe_allow_html=True)
    pt = prod.nlargest(8, "rx")
    fig_pr = go.Figure(go.Bar(
        x=pt["rx"], y=pt["product"], orientation="h",
        marker=dict(
            color=pt["rx"],
            colorscale=[[0,"#c8daf5"],[0.5,"#3a6fcc"],[1,"#1a3a7c"]],
            line=dict(color="rgba(0,0,0,0)"),
        ),
        text=pt["rx"].apply(lambda x: f"${x/1000:.0f}K"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
    ))
    fig_pr.update_layout(
        **CL, height=300,
        xaxis=dict(gridcolor="#e2ddd4", tickprefix="$"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_pr, width='stretch')

# ── tier coverage + call mix ───────────────────────────────────────────────────
ca, cb = st.columns(2, gap="large")

with ca:
    st.markdown(f'<div class="sec">🩺 {t("sec_tier")}</div>', unsafe_allow_html=True)
    td = act.groupby("hcp_tier").agg(calls=("activity_id","count")).reset_index()

    # Translate tier labels
    tier_label_map = {
        "A": t("tier_a"),
        "B": t("tier_b"),
        "C": t("tier_c"),
    }
    td["tier_label"] = td["hcp_tier"].map(tier_label_map)

    fig_ti = go.Figure(go.Pie(
        labels=td["tier_label"],
        values=td["calls"],
        hole=0.56,
        marker=dict(
            colors=["#3a6fcc", "#f4a100", "#e8e4dc"],
            line=dict(color="white", width=3),
        ),
        textinfo="percent",           # tylko procent NA wykresie, bez długich etykiet
        textfont=dict(family="DM Mono", size=13, color="#1c1c2e"),
        hovertemplate="%{label}<br>Calls: %{value:,} (%{percent})<extra></extra>",
        direction="clockwise",
        sort=False,
    ))
    fig_ti.update_layout(
        **CL, height=300,
        legend=dict(
            **LEGEND_STYLE,
            orientation="v",
            x=1.02, xanchor="left",
            y=0.5,  yanchor="middle",
        ),
    )
    st.plotly_chart(fig_ti, width='stretch')

with cb:
    st.markdown(f'<div class="sec">📞 {t("sec_calls")}</div>', unsafe_allow_html=True)
    cd = act.groupby("call_type").agg(count=("activity_id","count")).reset_index()
    fig_cm = go.Figure(go.Bar(
        x=cd["count"], y=cd["call_type"], orientation="h",
        marker=dict(color=PAL[:len(cd)], line=dict(color="rgba(0,0,0,0)")),
        text=cd["count"], textposition="outside",
        hovertemplate="%{y}: %{x:,}<extra></extra>",
    ))
    fig_cm.update_layout(
        **CL, height=300,
        xaxis=dict(gridcolor="#e2ddd4"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        showlegend=False,
    )
    st.plotly_chart(fig_cm, width='stretch')

ai_block(
    "coverage",
    "Oceń pokrycie HCP według segmentów (Tier A/B/C) i mix kanałów kontaktu. Czy zespół skupia się na właściwych lekarzach? Jakie rekomendacje dla field teamu?",
    "Evaluate HCP tier coverage (A/B/C) and contact channel mix. Is the team focusing on the right physicians? What are your recommendations for the field team?",
    f"Tier coverage:\n{td[['tier_label','calls']].to_string(index=False)}\n\nCall mix:\n{cd.to_string(index=False)}",
)

# ── at-risk section ────────────────────────────────────────────────────────────
if len(at_risk) > 0:
    st.markdown(f'<div class="sec">⚠️ {t("sec_risk")}</div>', unsafe_allow_html=True)

    rd2 = at_risk[[
        "rep_name","bu","region","seniority",
        "target_attainment","total_calls","conversion_rate"
    ]].copy()
    rd2.columns = [
        t("col_rep"), "BU", "Region", t("col_level"),
        t("col_att"), t("col_calls"), t("col_conv"),
    ]
    rd2[t("col_att")]  = rd2[t("col_att")].apply(lambda x: f"{x:.1f}%")
    rd2[t("col_conv")] = rd2[t("col_conv")].apply(lambda x: f"{x:.1f}%")
    st.dataframe(rd2, width='stretch', hide_index=True)

    ai_block(
        "risk",
        "Przeanalizuj przedstawicieli medycznych zagrożonych nierealizacją celu (poniżej 80%). Jakie konkretne działania powinien podjąć manager w ciągu najbliższych 30 dni?",
        "Analyse medical reps at risk of missing target (<80% attainment). What specific actions should the manager take in the next 30 days?",
        at_risk[[
            "rep_name","bu","seniority","target_attainment",
            "total_calls","conversion_rate","tier_a_ratio"
        ]].to_string(index=False),
    )

# ── footer ─────────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<div style='font-family:DM Mono,monospace;font-size:10px;"
    f"color:#b0b0c8;text-align:center'>{t('footer')}</div>",
    unsafe_allow_html=True,
)