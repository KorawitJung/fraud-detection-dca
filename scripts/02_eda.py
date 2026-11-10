"""Charts that answer the first three questions. Run from the project root: py scripts/02_eda.py

Q1  Which kinds of transaction do fraudsters use?
Q2  What time of day does fraud happen?
Q3  How much do they take, and do they empty the account?

Input : data/clean/paysim_clean.csv, output/tables/fraud_by_type.csv
Output: output/png/01..04_*.png, output/tables/fraud_by_hour.csv, output/tables/amount_summary.csv
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

PNG = Path("output/png")
TABLES = Path("output/tables")
PNG.mkdir(parents=True, exist_ok=True)
RED, BLUE = "#c1121f", "#2a6f97"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(PNG / name, dpi=150)
    plt.close(fig)


df = pd.read_csv("data/clean/paysim_clean.csv")
by_type = pd.read_csv(TABLES / "fraud_by_type.csv").sort_values("fraud_rate")
fraud, legit = df[df["isFraud"] == 1], df[df["isFraud"] == 0]

# Q1. Which kinds of transaction do fraudsters use?
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(by_type["type"], by_type["fraud_rate"], color=[RED if f > 0 else "#bbbbbb" for f in by_type["fraud"]])
for y, (rate, n) in enumerate(zip(by_type["fraud_rate"], by_type["fraud"])):
    ax.text(rate, y, f"  {rate:.2%}  ({n:,} cases)", va="center")
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=1))
ax.set_xlim(0, by_type["fraud_rate"].max() * 1.45 + 1e-9)
ax.set(title="Q1. Which kinds of transaction do fraudsters use?", xlabel="Share of transactions that are fraud")
save(fig, "01_fraud_by_type.png")

# Q2. What time of day does fraud happen?
by_hour = (
    df.groupby("hour")
    .agg(transactions=("isFraud", "size"), fraud=("isFraud", "sum"), fraud_rate=("isFraud", "mean"))
    .reindex(range(24), fill_value=0)
    .reset_index()
)
by_hour.to_csv(TABLES / "fraud_by_hour.csv", index=False)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True)
a1.bar(by_hour["hour"] - 0.2, by_hour["transactions"] / by_hour["transactions"].sum(), 0.4, color=BLUE, label="All transactions")
a1.bar(by_hour["hour"] + 0.2, by_hour["fraud"] / max(1, by_hour["fraud"].sum()), 0.4, color=RED, label="Fraud")
a1.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
a1.set(title="Q2. What time of day does fraud happen?", ylabel="Share of the day's total")
a1.legend(frameon=False)
a2.plot(by_hour["hour"], by_hour["fraud_rate"], color=RED, marker="o")
a2.yaxis.set_major_formatter(PercentFormatter(1, decimals=1))
a2.set(xlabel="Hour of day", ylabel="Chance a transaction is fraud", xticks=range(0, 24, 2))
save(fig, "02_fraud_by_hour.png")

# Q3. How much do they take, and do they empty the account?
summary = pd.DataFrame({
    "group": ["Fraud", "Legitimate"],
    "transactions": [len(fraud), len(legit)],
    "median_amount": [fraud["amount"].median(), legit["amount"].median()],
    "mean_amount": [fraud["amount"].mean(), legit["amount"].mean()],
    "max_amount": [fraud["amount"].max(), legit["amount"].max()],
    "total_amount": [fraud["amount"].sum(), legit["amount"].sum()],
    "share_emptying_account": [fraud["drains_account"].mean(), legit["drains_account"].mean()],
})
summary.to_csv(TABLES / "amount_summary.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 4.5))
bins = np.logspace(0, np.log10(df["amount"].max() + 1), 50)
ax.hist(legit["amount"] + 1, bins=bins, density=True, alpha=0.6, color=BLUE, label="Legitimate")
ax.hist(fraud["amount"] + 1, bins=bins, density=True, alpha=0.6, color=RED, label="Fraud")
ax.set_xscale("log")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_yticks([])
ax.set(title="Q3. How much is taken per transaction?", xlabel="Amount per transaction (log scale)")
ax.legend(frameon=False)
save(fig, "03_amount_fraud_vs_legit.png")

fig, ax = plt.subplots(figsize=(6, 4.5))
bars = ax.bar(summary["group"], summary["share_emptying_account"], color=[RED, BLUE])
ax.bar_label(bars, labels=[f"{v:.0%}" for v in summary["share_emptying_account"]])
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set(title="Q3. Does the transaction empty the sender's account?", ylabel="Share of transactions")
save(fig, "04_account_emptied.png")

print(by_type.to_string(index=False))
print(summary.to_string(index=False))
print("charts written to", PNG)
