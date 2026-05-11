"""
Superstore Sales Analysis
=========================
Starter script for exploratory data analysis using pandas and SQL (pandasql).

Requirements:
    pip install pandas pandasql openpyxl

Usage:
    python analysis.py
"""

# pandas is the core data analysis library in Python.
# By convention it's always imported as 'pd' — you'll see this everywhere.
# It gives you the DataFrame: a table with rows and columns, like Excel in code.
import pandas as pd

# pandasql lets you run real SQL queries directly on pandas DataFrames.
# Under the hood it converts your DataFrame into a temporary SQLite database,
# runs your SQL, then gives you the result back as a DataFrame.
import pandasql as ps
import sqlite3

# ── 1. LOAD ───────────────────────────────────────────────────────────────────

# This must match your filename exactly — including spaces and capitalisation.
# Both this file and Sample_ Superstore.csv must be in the same folder.
FILE = "Sample - Superstore.csv"


def load_data(path: str) -> pd.DataFrame:
    """
    Load the dataset from CSV or Excel based on file extension.

    The 'path: str' and '-> pd.DataFrame' are type hints — they tell you
    (and your editor) what type goes in and what comes out. Python doesn't
    enforce them, but they make code much easier to read and debug.
    """
    if path.endswith(".xlsx"):
        return pd.read_excel(path)
    # encoding="latin1" handles special characters (accents, symbols) that
    # sometimes appear in CSVs exported from Windows machines.
    return pd.read_csv(path, encoding="latin1")


# Call our function and store the result in 'df'.
# 'df' is the standard variable name for a DataFrame — use it everywhere.
df = load_data(FILE)

# df.shape returns (number_of_rows, number_of_columns)
# The :, format inside an f-string adds thousand separators → 9,994 not 9994
print("=" * 60)
print(f"Rows: {df.shape[0]:,}  |  Columns: {df.shape[1]}")
print("=" * 60)


# ── 2. CLEAN ──────────────────────────────────────────────────────────────────
# Raw CSVs store dates as plain text strings like "01/03/2021".
# pd.to_datetime() converts those strings into real datetime objects,
# which unlocks .dt.year, .dt.month, date math, and time-series operations.
# Without this step, grouping by month/year won't work.

df["Order Date"] = pd.to_datetime(df["Order Date"])
df["Ship Date"]  = pd.to_datetime(df["Ship Date"])

# --- Derived columns ---
# These don't exist in the raw data — we calculate and add them ourselves.
# Adding a new column to a DataFrame: df["new_col"] = expression

# .dt is the "datetime accessor" — exposes year, month, day etc.
df["Year"]  = df["Order Date"].dt.year   # e.g. 2021, 2022, 2023
df["Month"] = df["Order Date"].dt.month  # e.g. 1 = January, 12 = December

# to_period("M") creates a label like "2021-03" — useful for monthly grouping.
df["Month_Period"] = df["Order Date"].dt.to_period("M").astype(str)

# Subtracting two datetime columns gives a Timedelta (a duration).
# .dt.days converts it to a plain integer number of days.
df["Days_to_Ship"] = (df["Ship Date"] - df["Order Date"]).dt.days

# --- Null check ---
# isnull().sum() counts missing values per column.
nulls = df.isnull().sum()
if nulls.any():
    print("\nNull counts:")
    print(nulls[nulls > 0])   # only show columns that actually have nulls
else:
    print("\nNo nulls found — data is clean.")

# dtypes shows the data type of each column.
# 'object' = string. Always verify dates parsed as datetime64, not object.
print("\nColumn types:")
print(df.dtypes.to_string())


# ── 3. QUICK SUMMARY ─────────────────────────────────────────────────────────
# .describe() gives count, mean, std, min, quartiles, max for numeric columns.
# Run this before any analysis — it immediately reveals outliers and skew.

print("\n" + "=" * 60)
print("SUMMARY STATS")
print("=" * 60)
print(df[["Sales", "Profit", "Quantity", "Discount"]].describe().round(2))


# ── 4. SQL QUERIES ────────────────────────────────────────────────────────────
# Helper function so we don't repeat print/format boilerplate for every query.
# This is the DRY principle: Don't Repeat Yourself.

def run(query: str, title: str) -> pd.DataFrame:
    """
    Run a pandasql query against 'df' and print the results with a title.
    ps.sqldf() needs {"df": df} so it knows 'df' in SQL = our DataFrame.
    Returns the result so you can save it to CSV if needed.
    """
    result = ps.sqldf(query, {"df": df})
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)
    # index=False hides the row numbers — cleaner terminal output
    print(result.to_string(index=False))
    return result


# 4a. Revenue & profit by region
# GROUP BY collapses all rows with the same Region into one summary row.
# SUM() totals all values in that group.
# ROUND(x, 0) = whole numbers, ROUND(x, 1) = one decimal place.
# ORDER BY Revenue DESC = highest revenue first.
run("""
    SELECT
        Region,
        ROUND(SUM(Sales), 0)                  AS Revenue,
        ROUND(SUM(Profit), 0)                 AS Profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 1)  AS Margin_Pct
    FROM df
    GROUP BY Region
    ORDER BY Revenue DESC
""", "Revenue & Profit by Region")


# 4b. Year-over-year performance
# COUNT(DISTINCT "Order ID") counts unique orders, not rows.
# One order has multiple rows (one per product line), so DISTINCT
# prevents counting the same order multiple times.
# Note: pandasql uses double quotes for column names with spaces.
run("""
    SELECT
        Year,
        ROUND(SUM(Sales), 0)           AS Revenue,
        ROUND(SUM(Profit), 0)          AS Profit,
        COUNT(DISTINCT "Order ID")     AS Orders
    FROM df
    GROUP BY Year
    ORDER BY Year
""", "Year-over-Year Performance")


# 4c. Revenue by category & sub-category
# GROUP BY two columns → one row per unique combination.
# e.g. (Technology, Phones), (Technology, Accessories), (Furniture, Chairs)...
# ORDER BY Category first (alphabetical), then Revenue DESC within each category.
run("""
    SELECT
        Category,
        "Sub-Category",
        ROUND(SUM(Sales), 0)                  AS Revenue,
        ROUND(SUM(Profit), 0)                 AS Profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 1)  AS Margin_Pct
    FROM df
    GROUP BY Category, "Sub-Category"
    ORDER BY Category, Revenue DESC
""", "Revenue by Category & Sub-Category")


# 4d. Top 10 products by profit margin
# HAVING filters AFTER grouping (WHERE filters before grouping).
#   WHERE Sales > 1000     ← drops individual rows before aggregation
#   HAVING SUM(Sales) > 1000 ← drops groups after aggregation  ← what we want
# The $1,000 threshold removes products with one lucky sale
# that would otherwise show an inflated margin %.
run("""
    SELECT
        "Product Name",
        ROUND(SUM(Sales), 0)                  AS Revenue,
        ROUND(SUM(Profit), 0)                 AS Profit,
        ROUND(SUM(Profit)/SUM(Sales)*100, 1)  AS Margin_Pct
    FROM df
    GROUP BY "Product Name"
    HAVING SUM(Sales) > 1000
    ORDER BY Margin_Pct DESC
    LIMIT 10
""", "Top 10 Products by Profit Margin")


# 4e. Bottom 10 products (biggest loss-makers)
# ORDER BY Profit ASC = smallest (most negative) first.
# Negative profit = the company lost money selling that product.
run("""
    SELECT
        "Product Name",
        ROUND(SUM(Sales), 0)  AS Revenue,
        ROUND(SUM(Profit), 0) AS Profit
    FROM df
    GROUP BY "Product Name"
    ORDER BY Profit ASC
    LIMIT 10
""", "Bottom 10 Products (Loss-Makers)")


# 4f. Impact of discounts on profit margin
# CASE WHEN is SQL's if/elif/else — evaluates conditions top-to-bottom,
# returns the label for the first condition that matches.
# This "bins" continuous discount values (0.0–0.8) into readable groups.
# The output will likely show margin collapsing as discount bands increase.
run("""
    SELECT
        CASE
            WHEN Discount = 0     THEN '0%'
            WHEN Discount <= 0.10 THEN '1-10%'
            WHEN Discount <= 0.20 THEN '11-20%'
            WHEN Discount <= 0.30 THEN '21-30%'
            ELSE '30%+'
        END                                   AS Discount_Band,
        COUNT(*)                              AS Orders,
        ROUND(AVG(Sales), 0)                  AS Avg_Sale,
        ROUND(SUM(Profit)/SUM(Sales)*100, 1)  AS Margin_Pct
    FROM df
    GROUP BY Discount_Band
    ORDER BY Discount_Band
""", "Discount Impact on Margin")


# 4g. Shipping speed by ship mode
# Uses Days_to_Ship — the derived column we created in section 2.
# AVG() = mean days across all orders in each shipping group.
run("""
    SELECT
        "Ship Mode",
        COUNT(*)                    AS Orders,
        ROUND(AVG(Days_to_Ship), 1) AS Avg_Days
    FROM df
    GROUP BY "Ship Mode"
    ORDER BY Avg_Days
""", "Average Shipping Speed by Mode")


# 4h. Seasonality — average revenue by calendar month
# Uses a subquery (a query nested inside another query).
#
# Step 1 — inner query (aliased 'sub'):
#   Sums sales per Month + Year → e.g. Jan-2021: $50k, Jan-2022: $55k
#
# Step 2 — outer query:
#   Averages those values per month → Jan average across all years: $52k
#
# This smooths year-to-year noise and reveals the true seasonal pattern.
run("""
    SELECT
        Month,
        ROUND(AVG(monthly_sales), 0) AS Avg_Monthly_Revenue
    FROM (
        SELECT Month, Year, SUM(Sales) AS monthly_sales
        FROM df
        GROUP BY Month, Year
    ) sub
    GROUP BY Month
    ORDER BY Month
""", "Average Revenue by Month (Seasonality)")


# ── 5. PANDAS-ONLY INSIGHTS ───────────────────────────────────────────────────
# Method chaining: stack .method() calls — each one returns a new DataFrame.
# Read it as a pipeline: start with df, transform step by step.

print("\n" + "=" * 60)
print("  Top 10 Customers by Revenue")
print("=" * 60)

top_customers = (
    df.groupby("Customer Name")   # GROUP BY Customer Name

      # .agg() applies different functions to different columns.
      # "nunique" = COUNT DISTINCT, "sum" = SUM()
      .agg(
          Orders  = ("Order ID", "nunique"),
          Revenue = ("Sales",    "sum"),
          Profit  = ("Profit",   "sum")
      )

      .sort_values("Revenue", ascending=False)   # ORDER BY Revenue DESC
      .head(10)                                   # LIMIT 10
      .round(0)
)
print(top_customers.to_string())


print("\n" + "=" * 60)
print("  Performance by Customer Segment")
print("=" * 60)

segment = (
    df.groupby("Segment")
      .agg(
          Revenue = ("Sales",    "sum"),
          Profit  = ("Profit",   "sum"),
          Orders  = ("Order ID", "nunique")
      )
      # .assign() adds a new column mid-chain.
      # lambda x: ... is a one-line anonymous function; x = the DataFrame here.
      .assign(Margin_Pct=lambda x: (x["Profit"] / x["Revenue"] * 100).round(1))
      .round(0)
      .sort_values("Revenue", ascending=False)
)
print(segment.to_string())

# ── 6. EXPORT ─────────────────────────────────────────────────────────────────
# Remove the # from any line below to save that result as a CSV file.
# index=False stops pandas writing row numbers as an extra column.

# top_customers.to_csv("top_customers.csv", index=False)
# segment.to_csv("segment_performance.csv", index=False)

print("\n" + "=" * 60)
print("Analysis complete. Review the output above for your README findings.")
print("=" * 60)

# Creates superstore.db in the same folder if it doesn't exist yet.
# If it does exist, it connects to the existing one.
conn = sqlite3.connect("superstore.db")

# .to_sql() writes the DataFrame as a table inside the database.
# name="orders"       → the table will be called 'orders'
# if_exists="replace" → overwrites the table if you run the script again
# index=False         → don't write the row numbers as a column
df.to_sql(name="orders", con=conn, if_exists="replace", index=False)

print("Saved to superstore.db — table: orders")
conn.close()
