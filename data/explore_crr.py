"""Run with: python3 data/explore_crr.py (requires pandas and openpyxl)."""

from pathlib import Path

import pandas as pd

from extract_crrah import extract_crrah


# 0. Load CRRs and join account holder entities on their short name.
data_dir = Path(__file__).resolve().parent
crrs = pd.read_csv(data_dir / "Common_ExistingCRR.csv", skipinitialspace=True)
entities = pd.DataFrame(
    extract_crrah(data_dir / "List_of_Market_Participants_in_ERCOT_Region_20261011.xlsx")
)
crrs = crrs.merge(
    entities, left_on="AccountHolder", right_on="short_name", how="left",
    validate="many_to_one",
)
crrs = crrs[crrs["HedgeType"].isin(["OBL", "OPT"])].copy()
crrs["StartDate"] = pd.to_datetime(crrs["StartDate"], format="%m/%d/%Y")
crrs["EndDate"] = pd.to_datetime(crrs["EndDate"], format="%m/%d/%Y")

# Convert MW to MWh using inclusive contract dates and time-of-use hours.
# ERCOT: PeakWD = Mon-Fri HE07-22; PeakWE = Sat-Sun HE07-22.
# Off-peak = all remaining hours. Local time accounts for daylight saving.
# https://www.ercot.com/files/docs/2023/12/11/2024_03_CRR.pdf
def contract_hours(start, end, time_of_use):

    hours: pd.DatetimeIndex = pd.date_range(
        start, end + pd.Timedelta(days=1), freq="h",
        tz="America/Chicago", inclusive="left",
    )

    peak = (hours.hour >= 6) & (hours.hour < 22)
    weekday = hours.dayofweek < 5

    if time_of_use == "PeakWD":
        return (peak & weekday).sum()
    if time_of_use == "PeakWE":
        return (peak & ~weekday).sum()
    if time_of_use == "Off-peak":
        return (~peak).sum()
    raise ValueError(f"Unknown time of use: {time_of_use}")


# Calculate hours once per distinct period/block, rather than once per CRR.
period_columns = ["StartDate", "EndDate", "TimeOfUse"]
periods = crrs[period_columns].drop_duplicates().copy()
periods["Hours"] = [contract_hours(*row) for row in periods.itertuples(index=False, name=None)]
crrs = crrs.merge(periods, on=period_columns, validate="many_to_one")
crrs["MWh"] = crrs["MW"] * crrs["Hours"]


# 1. Top 10 account holders by total contract MWh (OBL + OPT, all paths).
holder_totals = crrs.groupby("AccountHolder", as_index=False)["MWh"].sum()
holder_totals = holder_totals.merge(
    entities, left_on="AccountHolder", right_on="short_name", how="left",
    validate="many_to_one",
)
top_holders = holder_totals.nlargest(50, "MWh")
print("\nTop 10 account holders by total MWh (OBL + OPT)")
print(top_holders[["AccountHolder", "name", "domain", "MWh"]].to_string(
    index=False, float_format="{:,.1f}".format,
))

top_domains = holder_totals.groupby('domain', as_index=False)["MWh"].sum().nlargest(50, "MWh")
print("\nTop by domain")
print(top_domains[["domain", "MWh"]].to_string(
    index=False, float_format="{:,.1f}".format,
))



# 2. Top 10 directed source/sink pairs by total MWh (all account holders).
path_totals = crrs.groupby(["Source", "Sink"], as_index=False)["MWh"].sum()
top_paths = path_totals.nlargest(50, "MWh")
print("\nTop 10 source/sink pairs by total MWh (OBL + OPT)")
print(top_paths.to_string(index=False, float_format="{:,.1f}".format))



# 3. Path breadth vs depth for the largest account holders (OBL + OPT).
# Combine contracts on the same directed path across dates and time-of-use blocks.
holder_paths = crrs.groupby(
    ["AccountHolder", "Source", "Sink"], as_index=False,
)["MWh"].sum()

breadth_depth = holder_paths.groupby("AccountHolder", as_index=False).agg(
    total_mwh=("MWh", "sum"),
    distinct_pairs=("MWh", "size"),  # count rows distinct pairs (source, mwH, irrelevant)
)
breadth_depth["mwh_per_pair"] = breadth_depth["total_mwh"] / breadth_depth["distinct_pairs"]

# Sort paths by volume, then take each holder's five largest paths.
top_five_paths = holder_paths.sort_values("MWh", ascending=False).groupby("AccountHolder").head(5)
top_five_mwh = top_five_paths.groupby("AccountHolder")["MWh"].sum()
breadth_depth["top_5_pairs_share_pct"] = (
    100 * breadth_depth["AccountHolder"].map(top_five_mwh) / breadth_depth["total_mwh"]
)

# Show the same holders as section 1, in the same volume order.
top_breadth_depth = top_holders[["AccountHolder", "name"]].merge(
    breadth_depth, on="AccountHolder", validate="one_to_one",
)
print("\nPath breadth vs depth for the largest account holders (OBL + OPT)")
print(top_breadth_depth.to_string(index=False, float_format="{:,.1f}".format))
