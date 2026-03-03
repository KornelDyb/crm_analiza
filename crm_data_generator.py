# crm_data_generator.py
# Simulates Veeva CRM-style data for a pharmaceutical sales team

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# ─── MASTER DATA ─────────────────────────────────────────────────────────────

BUSINESS_UNITS = ["Cardiology", "Oncology", "Neurology"]

REPS = [
    {"id": "REP001", "name": "Anna Kowalska",    "bu": "Cardiology",  "region": "Warsaw",  "seniority": "Senior"},
    {"id": "REP002", "name": "Piotr Nowak",      "bu": "Cardiology",  "region": "Kraków",  "seniority": "Mid"},
    {"id": "REP003", "name": "Maria Wiśniewska", "bu": "Oncology",    "region": "Warsaw",  "seniority": "Senior"},
    {"id": "REP004", "name": "Tomasz Zając",     "bu": "Oncology",    "region": "Gdańsk",  "seniority": "Junior"},
    {"id": "REP005", "name": "Karolina Lewandowska", "bu": "Oncology","region": "Wrocław", "seniority": "Mid"},
    {"id": "REP006", "name": "Michał Dąbrowski", "bu": "Neurology",   "region": "Warsaw",  "seniority": "Senior"},
    {"id": "REP007", "name": "Agnieszka Kamińska","bu": "Neurology",  "region": "Poznań",  "seniority": "Mid"},
    {"id": "REP008", "name": "Bartosz Kowalczyk","bu": "Cardiology",  "region": "Łódź",    "seniority": "Junior"},
    {"id": "REP009", "name": "Natalia Szymańska","bu": "Neurology",   "region": "Kraków",  "seniority": "Junior"},
    {"id": "REP010", "name": "Rafał Woźniak",    "bu": "Oncology",    "region": "Warsaw",  "seniority": "Senior"},
]

PRODUCTS = {
    "Cardiology":  ["CardioMax 10mg", "CardioMax 20mg", "VascuPro"],
    "Oncology":    ["OncoClear", "TumorBlock 50mg", "TumorBlock 100mg"],
    "Neurology":   ["NeuroPatch", "CogniFlex", "NeuroRelief"],
}

DOCTOR_SPECIALTIES = {
    "Cardiology":  ["Cardiologist", "Internist", "GP"],
    "Oncology":    ["Oncologist", "Hematologist", "Radiologist"],
    "Neurology":   ["Neurologist", "Psychiatrist", "GP"],
}

CALL_TYPES    = ["Face-to-Face", "Remote / e-Detail", "Phone Call"]
CALL_OUTCOMES = ["Prescription Intent", "Information Only", "Follow-up Needed", "Not Interested"]
CHANNELS      = ["Direct Visit", "Medical Conference", "Webinar", "Email"]


def generate_crm_data(months: int = 6, start_date: str = "2024-01-01") -> dict:
    """
    Generate Veeva-style CRM activity & sales data.
    Returns dict with DataFrames: activities, targets, hcp_master
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end   = start + timedelta(days=30 * months)

    # ── HCP Master (Healthcare Professionals) ────────────────────────────────
    hcps = []
    hcp_id = 1
    for rep in REPS:
        bu = rep["bu"]
        n_hcps = random.randint(25, 45)
        for _ in range(n_hcps):
            spec = random.choice(DOCTOR_SPECIALTIES[bu])
            hcps.append({
                "hcp_id":     f"HCP{hcp_id:04d}",
                "specialty":  spec,
                "city":       rep["region"],
                "bu":         bu,
                "tier":       random.choice(["A", "A", "B", "B", "B", "C"]),
                "assigned_rep": rep["id"],
            })
            hcp_id += 1
    df_hcp = pd.DataFrame(hcps)

    # ── Activities (calls / visits) ───────────────────────────────────────────
    activities = []
    act_id = 1
    for rep in REPS:
        bu        = rep["bu"]
        seniority = rep["seniority"]
        base_calls = {"Senior": 18, "Mid": 14, "Junior": 10}[seniority]

        rep_hcps = df_hcp[df_hcp["assigned_rep"] == rep["id"]]

        current = start
        while current <= end:
            # ~base_calls visits per month
            if current.day == 1:
                n_calls = int(np.random.normal(base_calls, 2))
                n_calls = max(5, n_calls)

                for _ in range(n_calls):
                    call_date = current + timedelta(days=random.randint(0, 27))
                    if call_date > end:
                        continue
                    # Skip weekends
                    if call_date.weekday() >= 5:
                        call_date -= timedelta(days=call_date.weekday() - 4)

                    hcp      = rep_hcps.sample(1).iloc[0] if len(rep_hcps) > 0 else None
                    product  = random.choice(PRODUCTS[bu])
                    outcome  = random.choices(
                        CALL_OUTCOMES,
                        weights=[0.35, 0.30, 0.25, 0.10]
                    )[0]
                    call_type = random.choice(CALL_TYPES)

                    # Prescription value — higher for Tier A, Senior reps, positive outcomes
                    base_rx = {"Cardiology": 4200, "Oncology": 8500, "Neurology": 3800}[bu]
                    tier_mult = {"A": 1.4, "B": 1.0, "C": 0.6}[hcp["tier"]] if hcp is not None else 1.0
                    outcome_mult = {"Prescription Intent": 1.5, "Information Only": 0.8,
                                    "Follow-up Needed": 0.9, "Not Interested": 0.2}[outcome]
                    senior_mult = {"Senior": 1.2, "Mid": 1.0, "Junior": 0.8}[seniority]
                    noise = np.random.uniform(0.85, 1.15)

                    rx_value = base_rx * tier_mult * outcome_mult * senior_mult * noise

                    activities.append({
                        "activity_id":  f"ACT{act_id:06d}",
                        "date":         call_date,
                        "rep_id":       rep["id"],
                        "rep_name":     rep["name"],
                        "bu":           bu,
                        "region":       rep["region"],
                        "seniority":    seniority,
                        "hcp_id":       hcp["hcp_id"] if hcp is not None else None,
                        "hcp_tier":     hcp["tier"]    if hcp is not None else "B",
                        "specialty":    hcp["specialty"] if hcp is not None else "GP",
                        "product":      product,
                        "call_type":    call_type,
                        "outcome":      outcome,
                        "channel":      random.choice(CHANNELS),
                        "rx_value":     round(rx_value, 2),
                        "call_duration_min": random.randint(8, 35),
                    })
                    act_id += 1

            current += timedelta(days=1)

    df_act = pd.DataFrame(activities)
    df_act["date"] = pd.to_datetime(df_act["date"])
    df_act = df_act.sort_values("date").reset_index(drop=True)

    # ── Monthly Targets ───────────────────────────────────────────────────────
    targets = []
    for rep in REPS:
        bu = rep["bu"]
        base_target = {"Cardiology": 55000, "Oncology": 95000, "Neurology": 48000}[bu]
        senior_mult = {"Senior": 1.3, "Mid": 1.0, "Junior": 0.75}[rep["seniority"]]
        monthly_target = base_target * senior_mult

        for m in range(months):
            month_date = start + timedelta(days=30 * m)
            # Targets grow slightly each quarter
            growth = 1 + (m // 3) * 0.05
            targets.append({
                "rep_id":       rep["id"],
                "rep_name":     rep["name"],
                "bu":           rep["bu"],
                "region":       rep["region"],
                "seniority":    rep["seniority"],
                "year_month":   month_date.strftime("%Y-%m"),
                "target_rx":    round(monthly_target * growth, 2),
                "target_calls": {"Senior": 18, "Mid": 14, "Junior": 10}[rep["seniority"]],
            })

    df_targets = pd.DataFrame(targets)

    return {
        "activities": df_act,
        "targets":    df_targets,
        "hcp_master": df_hcp,
        "reps":       pd.DataFrame(REPS),
    }


if __name__ == "__main__":
    data = generate_crm_data()
    print(f"Activities: {len(data['activities'])} rows")
    print(f"HCPs:       {len(data['hcp_master'])} records")
    print(f"Targets:    {len(data['targets'])} rows")
    print(data["activities"].head())
