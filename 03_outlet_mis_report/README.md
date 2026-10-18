# Food Outlet MIS Report Generator

Builds a multi-sheet Excel report (monthly P&L, channel mix, item margins)
from daily sales data using pandas. Based on the kind of reporting a small
quick-service outlet needs. All data here is synthetic.

**Run:** `python mis_report.py` (creates `outlet_mis_report.xlsx`)

**Adapt it:** replace `make_sales()` with `pd.read_csv("your_sales.csv")` using
columns date, item, channel, qty, price. The same report works for any small retail or F&B business.
