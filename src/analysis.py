"""Run the SQL queries against the hospital database, save tables and charts.

Run:  python src/analysis.py
Outputs go to the outputs/ folder (CSV tables, PNG charts, findings.txt).
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "hospital.db"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "outputs"


def run_query(conn, filename):
    """Read a .sql file and return the result as a pandas DataFrame."""
    sql = (SQL_DIR / filename).read_text()
    return pd.read_sql_query(sql, conn)


def save(df, name):
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)


def chart_los(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(df["department"], df["avg_los_days"], color="#2a6f97")
    ax.invert_yaxis()
    ax.set_xlabel("Average length of stay (days)")
    ax.set_title("Average length of stay by department, 2025")
    for i, v in enumerate(df["avg_los_days"]):
        ax.text(v + 0.05, i, f"{v:.1f}", va="center")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "01_avg_los.png", dpi=150)
    plt.close(fig)


def chart_occupancy(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#c1121f" if v >= 85 else "#2a6f97" for v in df["avg_occupancy_pct"]]
    ax.bar(df["department"], df["avg_occupancy_pct"], color=colors)
    ax.axhline(85, color="grey", linestyle="--", linewidth=1)
    ax.text(len(df) - 0.5, 86, "85% threshold", ha="right", fontsize=8, color="grey")
    ax.set_ylabel("Average bed occupancy (%)")
    ax.set_title("Average bed occupancy by department, 2025")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "02_bed_occupancy.png", dpi=150)
    plt.close(fig)


def chart_hours(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df["hour_of_day"], df["admissions"], color="#2a6f97")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Admissions (2025)")
    ax.set_title("Admissions by hour of day")
    ax.set_xticks(range(0, 24, 2))
    fig.tight_layout()
    fig.savefig(OUT_DIR / "03_admissions_by_hour.png", dpi=150)
    plt.close(fig)


def chart_monthly(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df["month"], df["admissions"], marker="o", color="#2a6f97")
    ax.set_ylabel("Admissions")
    ax.set_title("Monthly admissions, 2025")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_ylim(0, df["admissions"].max() * 1.15)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "04_monthly_admissions.png", dpi=150)
    plt.close(fig)


def chart_readmissions(df):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(df["department"], df["readmission_rate_pct"], color="#2a6f97")
    ax.invert_yaxis()
    ax.set_xlabel("30-day readmission rate (%)")
    ax.set_title("30-day readmission rate by department")
    for i, v in enumerate(df["readmission_rate_pct"]):
        ax.text(v + 0.1, i, f"{v:.1f}%", va="center")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "05_readmissions.png", dpi=150)
    plt.close(fig)


def write_findings(los, occ, hours, monthly, readm):
    """Turn the tables into plain-English findings (computed, not hand-typed)."""
    top_occ = occ.iloc[0]
    peak_hour = hours.loc[hours["admissions"].idxmax()]
    peak_month = monthly.loc[monthly["admissions"].idxmax()]
    low_month = monthly.loc[monthly["admissions"].idxmin()]
    top_readm = readm.iloc[0]
    longest = los.iloc[0]
    lines = [
        "KEY FINDINGS (synthetic data, 2025)",
        "",
        f"1. Bed pressure: {top_occ['department']} has the highest average occupancy "
        f"({top_occ['avg_occupancy_pct']}%) and is at >=90% of capacity on "
        f"{top_occ['pct_days_at_90pct_or_more']}% of days.",
        f"2. Longest stays: {longest['department']} averages {longest['avg_los_days']} days per admission.",
        f"3. Peak arrival hour: {int(peak_hour['hour_of_day']):02d}:00 "
        f"({int(peak_hour['admissions'])} admissions in the year).",
        f"4. Seasonality: admissions peak in {peak_month['month']} ({int(peak_month['admissions'])}) "
        f"and are lowest in {low_month['month']} ({int(low_month['admissions'])}).",
        f"5. Readmissions: {top_readm['department']} has the highest 30-day readmission rate "
        f"({top_readm['readmission_rate_pct']}%).",
    ]
    text = "\n".join(lines)
    (OUT_DIR / "findings.txt").write_text(text + "\n")
    print(text)


def main():
    if not DB_PATH.exists():
        raise SystemExit("Database not found. Run:  python src/create_db.py")
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    los = run_query(conn, "01_avg_los_by_department.sql")
    occ = run_query(conn, "02_bed_occupancy.sql")
    hours = run_query(conn, "03_admissions_by_hour.sql")
    monthly = run_query(conn, "04_monthly_admissions.sql")
    readm = run_query(conn, "05_readmissions_30d.sql")
    workload = run_query(conn, "06_doctor_workload_rank.sql")
    conn.close()

    for name, df in [("01_avg_los", los), ("02_bed_occupancy", occ),
                     ("03_admissions_by_hour", hours), ("04_monthly_admissions", monthly),
                     ("05_readmissions", readm), ("06_doctor_workload", workload)]:
        save(df, name)

    chart_los(los)
    chart_occupancy(occ)
    chart_hours(hours)
    chart_monthly(monthly)
    chart_readmissions(readm)
    write_findings(los, occ, hours, monthly, readm)


if __name__ == "__main__":
    main()
