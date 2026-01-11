import pandas as pd
from datetime import datetime

file_path = "data\\bets_history.csv"

print("Add a new bet")

date = datetime.now().strftime("%Y-%m-%d")
player = input("Player name: ")
market = input("Market (PTS / PRA / AST / REB): ")
line = float(input("Line: "))
odds = float(input("Odds: "))
stake = float(input("Stake: "))
result = input("Result (WIN / LOSS): ").upper()

if result == "WIN":
    profit = stake * (odds - 1)
else:
    profit = -stake

df = pd.read_csv(file_path)

new_row = {
    "DATE": date,
    "PLAYER": player,
    "MARKET": market,
    "LINE": line,
    "ODDS": odds,
    "STAKE": stake,
    "RESULT": result,
    "PROFIT": profit
}

df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
df.to_csv(file_path, index=False)

print("Bet added successfully")
