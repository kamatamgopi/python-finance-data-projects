"""
Monthly MIS report for a small quick-service food outlet.
Generates sample sales data, then builds an Excel report with:
monthly P&L summary, channel mix, item margins and raw data.
"""
import numpy as np
import pandas as pd

ITEMS = {  # item: (price, food cost %)
    "Mirchi Pakoda": (60, 0.38), "Onion Pakoda": (50, 0.35), "Paneer Pakoda": (90, 0.45),
    "Aloo Bonda": (40, 0.33), "Masala Chai": (20, 0.30), "Combo Plate": (120, 0.42),
}
CHANNELS = ["Dine-in/Takeaway", "Swiggy", "Zomato"]


def make_sales(seed=7):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2024-01-01", "2024-06-30", freq="D")
    rows = []
    for d in days:
        boost = 1.25 if d.weekday() >= 5 else 1.0
        trend = 1 + 0.003 * (d - days[0]).days
        for item, (price, _) in ITEMS.items():
            for ch, share in zip(CHANNELS, [0.6, 0.25, 0.15]):
                qty = rng.poisson(40 * boost * share * trend)
                rows.append((d, item, ch, qty, price))
    df = pd.DataFrame(rows, columns=["date", "item", "channel", "qty", "price"])
    df["revenue"] = df["qty"] * df["price"]
    df["food_cost"] = df["revenue"] * df["item"].map(lambda i: ITEMS[i][1])
    return df


def build_report(df, fixed_monthly=95000):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly = df.groupby("month").agg(revenue=("revenue", "sum"), food_cost=("food_cost", "sum"))
    monthly["gross_profit"] = monthly["revenue"] - monthly["food_cost"]
    monthly["food_cost_%"] = monthly["food_cost"] / monthly["revenue"] * 100
    monthly["fixed_costs"] = fixed_monthly
    monthly["net_profit"] = monthly["gross_profit"] - monthly["fixed_costs"]
    monthly["mom_growth_%"] = monthly["revenue"].pct_change() * 100
    monthly = monthly.round(1)

    channel = df.pivot_table(index="month", columns="channel", values="revenue", aggfunc="sum")
    channel_pct = (channel.div(channel.sum(axis=1), axis=0) * 100).round(1)

    items = (df.groupby("item").agg(qty=("qty", "sum"), revenue=("revenue", "sum"),
                                    food_cost=("food_cost", "sum"))
               .assign(margin=lambda x: x["revenue"] - x["food_cost"])
               .sort_values("margin", ascending=False).round(0))
    return monthly, channel, channel_pct, items


if __name__ == "__main__":
    sales = make_sales()
    monthly, channel, channel_pct, items = build_report(sales)
    with pd.ExcelWriter("outlet_mis_report.xlsx", engine="openpyxl") as xw:
        monthly.to_excel(xw, sheet_name="Monthly P&L")
        channel.to_excel(xw, sheet_name="Channel Revenue")
        channel_pct.to_excel(xw, sheet_name="Channel Mix %")
        items.to_excel(xw, sheet_name="Item Margins")
        sales.to_excel(xw, sheet_name="Raw Data", index=False)
        for ws in xw.book.worksheets:
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = max(
                    12, max(len(str(c.value)) if c.value is not None else 0 for c in col[:30]) + 2)
    print(monthly)
    print("\nSaved outlet_mis_report.xlsx")
