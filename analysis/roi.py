import pandas as pd

def load_roi():
    try:
        df = pd.read_csv("data_export/decisions.csv")
    except:
        return pd.DataFrame()

    df = df[df["RESULT"].isin(["WIN", "LOSS"])]
    df["PROFIT"] = df["STAKE"] * (df["ODDS"] - 1)
    df.loc[df["RESULT"] == "LOSS", "PROFIT"] = -df["STAKE"]

    roi = (
        df.groupby("PLAYER_NAME")
        .agg(
            BETS=("RESULT", "count"),
            PROFIT=("PROFIT", "sum")
        )
        .reset_index()
    )

    roi["ROI"] = roi["PROFIT"] / (roi["BETS"] * df["STAKE"].mean()) * 100
    return roi.sort_values("ROI", ascending=False)
