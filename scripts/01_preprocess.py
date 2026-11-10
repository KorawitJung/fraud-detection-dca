"""Clean PaySim and build features. Run from the project root: py scripts/01_preprocess.py

Input : data/raw/*.csv
Output: data/clean/paysim_clean.csv, data/clean/cleaning_log.csv,
        output/tables/fraud_by_type.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = sorted(Path("data/raw").glob("*.csv"))
CLEAN = Path("data/clean")
TABLES = Path("output/tables")
CLEAN.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)
if not RAW:
    raise SystemExit("No CSV in data/raw/. Run scripts/00_download.py first.")

log = []


def note(step, frame):
    log.append({"step": step, "rows": len(frame), "fraud_rows": int(frame["isFraud"].sum())})
    print(f"{step:<45} rows={len(frame):>9,} fraud={int(frame['isFraud'].sum()):>6,}")


df = pd.read_csv(RAW[0]).rename(columns={"oldbalanceOrg": "oldbalanceOrig"})
note("raw", df)

df = df.drop_duplicates()
note("drop exact duplicate rows", df)

df = df.dropna(subset=["step", "type", "amount", "nameOrig", "nameDest", "isFraud"])
note("drop rows missing key fields", df)

df = df[df["amount"] >= 0]
note("drop negative amounts", df)

# Fraud rate by transaction type, on all types, before filtering.
by_type = (
    df.groupby("type")
    .agg(transactions=("isFraud", "size"), fraud=("isFraud", "sum"), total_amount=("amount", "sum"))
    .assign(fraud_rate=lambda t: t["fraud"] / t["transactions"])
    .reset_index()
)
by_type.to_csv(TABLES / "fraud_by_type.csv", index=False)

# Keep only the types where fraud occurs; the others cannot be positives.
fraud_types = by_type.loc[by_type["fraud"] > 0, "type"].tolist()
df = df[df["type"].isin(fraud_types)].copy()
note(f"keep types with fraud: {', '.join(fraud_types)}", df)

# --- Features -------------------------------------------------------------
# Known before the transaction settles: safe to use in a model.
df = df.sort_values(["step", "nameOrig"]).reset_index(drop=True)
df["hour"] = df["step"] % 24
df["day"] = df["step"] // 24
df["log_amount"] = np.log1p(df["amount"])
df["amount_to_balance"] = df["amount"] / (df["oldbalanceOrig"] + 1)
df["drains_account"] = (df["amount"] >= df["oldbalanceOrig"]) & (df["oldbalanceOrig"] > 0)
df["dest_is_merchant"] = df["nameDest"].str.startswith("M")
df["dest_prior_txns"] = df.groupby("nameDest").cumcount()  # receiving-account velocity
df["dest_prior_amount"] = df.groupby("nameDest")["amount"].cumsum() - df["amount"]

# Known only after settlement: kept for EDA, excluded from the model (leakage).
df["orig_balance_error"] = df["oldbalanceOrig"] - df["amount"] - df["newbalanceOrig"]
df["dest_balance_error"] = df["oldbalanceDest"] + df["amount"] - df["newbalanceDest"]

# Time-based split: the last 20% of steps is the test set.
cutoff = int(df["step"].quantile(0.8))
df["split"] = np.where(df["step"] <= cutoff, "train", "test")
note(f"final (train = step <= {cutoff})", df)

df.to_csv(CLEAN / "paysim_clean.csv", index=False)
pd.DataFrame(log).to_csv(CLEAN / "cleaning_log.csv", index=False)
print("wrote", CLEAN / "paysim_clean.csv")
