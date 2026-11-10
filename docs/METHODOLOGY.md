# Methodology

## Objective
Answer four plain questions about fraud in mobile-money transactions:

1. Which kinds of transaction do fraudsters use?
2. What time of day does fraud happen?
3. How much do they take, and do they empty the account?
4. If the bank checks only the riskiest 1% of transactions, how much fraud is stopped?

## Data source
PaySim synthetic mobile money dataset (Lopez-Rojas, Elmir and Axelsson, 2016), from Kaggle `ealaxi/paysim1`.
About 6.3 million transactions over 743 hourly steps (about 31 days). See `data/reference/sources.csv`.

The data is simulated from the logs of a real mobile-money service. It is not Thai data and not real customer data.
Findings describe the simulation and are a methods exercise, not evidence about fraud in Thailand.

## Data collection
`scripts/00_download.py` downloads the file with `kagglehub` into `data/raw/`. Raw files are not committed.

## Data cleaning (`scripts/01_preprocess.py`)
Each step and its row count is written to `data/clean/cleaning_log.csv`.

| Step | Rule |
|---|---|
| Rename | `oldbalanceOrg` to `oldbalanceOrig` for consistency |
| Duplicates | Drop exact duplicate rows |
| Missing | Drop rows missing step, type, amount, account names or label |
| Invalid | Drop negative amounts |
| Scope | Keep only transaction types in which fraud occurs (computed from the data, saved in `output/tables/fraud_by_type.csv`) |
| Split | Train = first 80% of transactions in time order (steps 1-354 of 743), test = the rest. Fraud is steady over time while normal volume falls, so the test period has a higher fraud rate (0.77%) than the training period (0.18%) |

## Features
Used in the model (known before settlement): log amount, amount relative to sender balance, whether the amount drains the sender account, sender and receiver opening balances, hour of day, receiver is a merchant, receiver's prior transaction count and prior amount received, transaction type.

Built but excluded from the model: `orig_balance_error`, `dest_balance_error`. They use post-transaction balances, which a real-time system would not have, and they leak the label in this dataset.

## Analysis
All in Python (pandas, matplotlib, scikit-learn).

| Question | Method |
|---|---|
| Q1 | Fraud count and fraud rate per transaction type, on all types before filtering |
| Q2 | Share of all transactions and of fraud per hour of day, and fraud rate per hour (`hour = step mod 24`) |
| Q3 | Median, mean and total amount for fraud and legitimate transactions; share of each that empties the sender's account |
| Q4 | Logistic regression and histogram gradient boosting, balanced class weights, trained on the first 80% of transactions in time order. On the later 20%, transactions are ranked by predicted risk and the top 0.1%, 0.5%, 1% and 5% are "reviewed"; the chart reports the share of fraud cases and of fraud money inside that group, for the model with the higher PR-AUC |

PR-AUC is used to compare models because fraud is far below 1% of transactions and ROC-AUC is misleading at that base rate.

## Limitations
- Simulated data; fraud behaviour is rule-generated and easier to detect than real fraud.
- `isFlaggedFraud` is a rule output of the simulator and is not used.
- Receiver velocity features are computed over the whole period in time order, with no look-ahead, but accounts are not split between train and test.
- No customer attributes, device or channel data.
