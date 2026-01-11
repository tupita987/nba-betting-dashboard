import pandas as pd

df = pd.read_csv("data\\bets_history.csv")

if df.empty:
    print("No bets yet")
    exit()

total_stake = df["STAKE"].sum()
total_profit = df["PROFIT"].sum()
roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
winrate = (df["RESULT"] == "WIN").mean() * 100

print("Total bets:", len(df))
print("Total stake:", round(total_stake, 2))
print("Total profit:", round(total_profit, 2))
print("ROI %:", round(roi, 2))
print("Winrate %:", round(winrate, 2))
