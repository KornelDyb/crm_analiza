# crm_kpi_engine.py
# Calculates sales rep KPIs from CRM activity data

import pandas as pd
import numpy as np


class CRMKPIEngine:
    """
    Computes KPIs for pharmaceutical sales reps from CRM activity data.
    Mirrors metrics typically tracked in Veeva CRM / Veeva Vault.
    """

    def __init__(self, activities: pd.DataFrame, targets: pd.DataFrame):
        self.act = activities.copy()
        self.act["date"] = pd.to_datetime(self.act["date"])
        self.act["year_month"] = self.act["date"].dt.strftime("%Y-%m")
        self.targets = targets.copy()

    # ── Rep-level summary ─────────────────────────────────────────────────────
    def rep_summary(self) -> pd.DataFrame:
        """Aggregate KPIs per rep across the full period."""
        grp = self.act.groupby(["rep_id", "rep_name", "bu", "region", "seniority"])

        summary = grp.agg(
            total_calls   = ("activity_id", "count"),
            total_rx      = ("rx_value", "sum"),
            avg_rx_per_call = ("rx_value", "mean"),
            tier_a_calls  = ("hcp_tier", lambda x: (x == "A").sum()),
            prescription_intent_calls = ("outcome", lambda x: (x == "Prescription Intent").sum()),
            avg_call_duration = ("call_duration_min", "mean"),
            unique_hcps   = ("hcp_id", "nunique"),
        ).reset_index()

        summary["conversion_rate"] = (
            summary["prescription_intent_calls"] / summary["total_calls"] * 100
        ).round(1)

        summary["tier_a_ratio"] = (
            summary["tier_a_calls"] / summary["total_calls"] * 100
        ).round(1)

        # Merge with targets (sum over months)
        target_totals = self.targets.groupby("rep_id").agg(
            total_target_rx    = ("target_rx", "sum"),
            total_target_calls = ("target_calls", "sum"),
        ).reset_index()

        summary = summary.merge(target_totals, on="rep_id", how="left")
        summary["target_attainment"] = (
            summary["total_rx"] / summary["total_target_rx"] * 100
        ).round(1)
        summary["call_attainment"] = (
            summary["total_calls"] / summary["total_target_calls"] * 100
        ).round(1)

        return summary.sort_values("target_attainment", ascending=False)

    # ── Monthly trend per rep ─────────────────────────────────────────────────
    def monthly_trend(self) -> pd.DataFrame:
        """Monthly rx_value and call count per rep."""
        monthly = self.act.groupby(["rep_id", "rep_name", "bu", "year_month"]).agg(
            calls  = ("activity_id", "count"),
            rx     = ("rx_value", "sum"),
        ).reset_index()

        monthly = monthly.merge(
            self.targets[["rep_id", "year_month", "target_rx", "target_calls"]],
            on=["rep_id", "year_month"], how="left"
        )
        monthly["attainment"] = (monthly["rx"] / monthly["target_rx"] * 100).round(1)
        return monthly.sort_values(["rep_id", "year_month"])

    # ── BU-level KPIs ─────────────────────────────────────────────────────────
    def bu_summary(self) -> pd.DataFrame:
        """Aggregate KPIs per Business Unit."""
        grp = self.act.groupby("bu").agg(
            total_calls = ("activity_id", "count"),
            total_rx    = ("rx_value", "sum"),
            unique_hcps = ("hcp_id", "nunique"),
            conversion  = ("outcome", lambda x: (x == "Prescription Intent").sum()),
        ).reset_index()
        grp["conversion_rate"] = (grp["conversion"] / grp["total_calls"] * 100).round(1)

        target_bu = self.targets.groupby("bu")["target_rx"].sum().reset_index()
        grp = grp.merge(target_bu, on="bu", how="left")
        grp["attainment"] = (grp["total_rx"] / grp["target_rx"] * 100).round(1)
        return grp

    # ── Call mix analysis ─────────────────────────────────────────────────────
    def call_mix(self) -> pd.DataFrame:
        """Call type distribution per rep."""
        return (
            self.act.groupby(["rep_name", "call_type"])
            .size().reset_index(name="count")
            .pivot(index="rep_name", columns="call_type", values="count")
            .fillna(0).astype(int)
            .reset_index()
        )

    # ── Outcome distribution ──────────────────────────────────────────────────
    def outcome_distribution(self) -> pd.DataFrame:
        return (
            self.act.groupby(["bu", "outcome"])
            .size().reset_index(name="count")
        )

    # ── Top / bottom performers ───────────────────────────────────────────────
    def top_performers(self, n: int = 3) -> pd.DataFrame:
        return self.rep_summary().head(n)

    def bottom_performers(self, n: int = 3) -> pd.DataFrame:
        return self.rep_summary().tail(n)

    # ── At-risk reps (attainment < 80%) ──────────────────────────────────────
    def at_risk_reps(self) -> pd.DataFrame:
        summary = self.rep_summary()
        return summary[summary["target_attainment"] < 80].sort_values("target_attainment")

    # ── Product performance ───────────────────────────────────────────────────
    def product_performance(self) -> pd.DataFrame:
        return (
            self.act.groupby(["bu", "product"]).agg(
                calls = ("activity_id", "count"),
                rx    = ("rx_value",    "sum"),
                conv  = ("outcome", lambda x: (x == "Prescription Intent").sum()),
            ).reset_index()
            .assign(conversion_rate=lambda d: (d["conv"] / d["calls"] * 100).round(1))
            .sort_values("rx", ascending=False)
        )

    # ── HCP tier coverage ─────────────────────────────────────────────────────
    def tier_coverage(self) -> pd.DataFrame:
        return (
            self.act.groupby(["rep_name", "hcp_tier"])
            .size().reset_index(name="calls")
            .pivot(index="rep_name", columns="hcp_tier", values="calls")
            .fillna(0).astype(int)
            .reset_index()
        )


if __name__ == "__main__":
    from crm_data_generator import generate_crm_data
    data   = generate_crm_data()
    engine = CRMKPIEngine(data["activities"], data["targets"])
    print(engine.rep_summary()[["rep_name", "total_calls", "target_attainment", "conversion_rate"]])
