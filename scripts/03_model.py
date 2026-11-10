"""Q4  If the bank checks only the riskiest transactions, how much fraud is stopped?

Run from the project root: py scripts/03_model.py
Trains on the first 80% of transactions in time order and tests on the later 20%.

Input : data/clean/paysim_clean.csv
Output: output/tables/model_metrics.csv, output/tables/threshold_tradeoff.csv,
        output/png/05_fraud_caught_by_review_budget.png, output/png/06_pr_curve.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# Pre-settlement features only. Post-transaction balances are excluded on purpose.
FEATURES = [
    "log_amount", "amount_to_balance", "drains_account", "oldbalanceOrig", "oldbalanceDest",
    "hour", "dest_is_merchant", "dest_prior_txns", "dest_prior_amount", "is_transfer",
]

df = pd.read_csv("data/clean/paysim_clean.csv")
df["is_transfer"] = df["type"].eq("TRANSFER")
X = df[FEATURES].astype(float)
y = df["isFraud"].astype(int)
train, test = df["split"].eq("train"), df["split"].eq("test")

models = {
    "logistic_regression": make_pipeline(
        StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=1000)
    ),
    "gradient_boosting": HistGradientBoostingClassifier(
        class_weight="balanced", max_iter=200, learning_rate=0.1, random_state=42
    ),
}

metrics, tradeoff = [], []
fig, ax = plt.subplots(figsize=(7, 5))
for name, model in models.items():
    model.fit(X[train], y[train])
    p = model.predict_proba(X[test])[:, 1]
    metrics.append({
        "model": name,
        "test_rows": int(test.sum()),
        "test_fraud": int(y[test].sum()),
        "pr_auc": average_precision_score(y[test], p),
        "roc_auc": roc_auc_score(y[test], p),
        "baseline_pr_auc": y[test].mean(),
    })
    prec, rec, _ = precision_recall_curve(y[test], p)
    ax.plot(rec, prec, label=f"{name} (PR-AUC {metrics[-1]['pr_auc']:.3f})")

    # What an analyst team would see if it reviewed the top-k% riskiest transactions.
    amount = df.loc[test, "amount"].to_numpy()
    truth = y[test].to_numpy()
    order = np.argsort(-p)
    for share in (0.001, 0.005, 0.01, 0.05):
        k = max(1, int(len(order) * share))
        top = order[:k]
        tradeoff.append({
            "model": name,
            "reviewed_share": share,
            "alerts": k,
            "precision": truth[top].mean(),
            "recall": truth[top].sum() / max(1, truth.sum()),
            "fraud_amount_caught_share": amount[top][truth[top] == 1].sum() / max(1.0, amount[truth == 1].sum()),
        })

ax.set(xlabel="Recall", ylabel="Precision", title="Precision-recall on the held-out time period")
ax.legend()
fig.tight_layout()
Path("output/png").mkdir(parents=True, exist_ok=True)
Path("output/tables").mkdir(parents=True, exist_ok=True)
fig.savefig("output/png/06_pr_curve.png", dpi=150)
plt.close(fig)
pd.DataFrame(metrics).to_csv("output/tables/model_metrics.csv", index=False)
pd.DataFrame(tradeoff).to_csv("output/tables/threshold_tradeoff.csv", index=False)

# Q4 chart: the better model, in plain terms.
best = max(metrics, key=lambda m: m["pr_auc"])["model"]
t = pd.DataFrame(tradeoff).query("model == @best")
labels = [f"Riskiest {s:.1%}" for s in t["reviewed_share"]]
x = np.arange(len(t))
fig, ax = plt.subplots(figsize=(8, 4.5))
b1 = ax.bar(x - 0.2, t["recall"], 0.4, color="#c1121f", label="Fraud cases caught")
b2 = ax.bar(x + 0.2, t["fraud_amount_caught_share"], 0.4, color="#2a6f97", label="Fraud money caught")
ax.bar_label(b1, labels=[f"{v:.0%}" for v in t["recall"]])
ax.bar_label(b2, labels=[f"{v:.0%}" for v in t["fraud_amount_caught_share"]])
ax.set_xticks(x, labels)
ax.set_ylim(0, 1.15)
ax.set_yticks([])
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.legend(frameon=False, loc="upper left")
ax.set(title="Q4. If the bank checks only the riskiest transactions, how much fraud is stopped?",
       xlabel="Share of transactions reviewed")
fig.tight_layout()
fig.savefig("output/png/05_fraud_caught_by_review_budget.png", dpi=150)
print(pd.DataFrame(metrics).to_string(index=False))
print(pd.DataFrame(tradeoff).to_string(index=False))
