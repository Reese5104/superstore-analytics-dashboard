"""
Flask REST API for Superstore Analytics Dashboard

This backend serves data from the SQLite database (superstore.db) to the React frontend.
Each endpoint returns JSON data that gets visualized in charts and tables.

Key patterns:
- All endpoints support a ?year=XXXX query parameter for year filtering
- Only SELECT queries allowed (security: prevents DELETE/UPDATE/DROP)
- CORS enabled so React on :5173 can call Flask on :5000
"""

from flask import Flask, jsonify, request
import sqlite3
import pandas as pd

app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
# Without this, React (localhost:5173) cannot call Flask (localhost:5000)
from flask_cors import CORS
CORS(app)

# Path to the SQLite database created by analysis.py
DB = "../superstore.db"

def query(sql):
    """
    Execute SQL query and return results as list of dictionaries.
    
    Args:
        sql (str): SQL SELECT statement
    
    Returns:
        list: List of dicts, one per row. JSON-serializable.
    
    Raises:
        Exception: If SQL fails
    """
    try:
        conn = sqlite3.connect(DB)
        # pandas.read_sql executes SQL and returns a DataFrame
        df = pd.read_sql(sql, conn)
        conn.close()
        # to_dict(orient="records") converts each row to a dict
        # [{col1: val1, col2: val2}, {col1: val3, col2: val4}, ...]
        return df.to_dict(orient="records")
    except Exception as e:
        raise Exception(str(e))


def apply_year_filter(sql, year):
    """
    Modify SQL to filter by year if provided.
    
    If year is "all", returns SQL unchanged.
    Otherwise, adds WHERE Year = {year} to the query.
    
    Args:
        sql (str): Original SQL
        year (str): "all" or a year like "2014"
    
    Returns:
        str: Modified SQL with year filter
    """
    if year == "all":
        return sql
    # Simple approach: add WHERE clause after FROM orders
    if "WHERE" not in sql.upper():
        return sql.replace("FROM orders", f'FROM orders WHERE Year = {year}')
    else:
        # If WHERE already exists, append AND
        return sql.replace("WHERE", f'WHERE Year = {year} AND', 1)


# --- REST Endpoints ---

@app.route("/api/kpis")
def kpis():
    """
    High-level KPIs: total revenue, profit, margin %, order count
    
    Query params:
        ?year=2015  — filter to 2015 data only
        ?year=all   — all years (default)
    
    Returns:
        {
            "total_revenue": 500000,
            "total_profit": 50000,
            "margin_pct": 10.0,
            "total_orders": 1000
        }
    """
    year = request.args.get("year", "all")
    sql = """
        SELECT
            ROUND(SUM(Sales), 0)   AS total_revenue,
            ROUND(SUM(Profit), 0)  AS total_profit,
            ROUND(SUM(Profit)/SUM(Sales)*100, 1) AS margin_pct,
            COUNT(DISTINCT "Order ID") AS total_orders
        FROM orders
    """
    sql = apply_year_filter(sql, year)
    return jsonify(query(sql))


@app.route("/api/revenue-by-region")
def revenue_by_region():
    """
    Revenue and profit broken down by sales region.
    
    Returns:
        [
            {"Region": "West", "Revenue": 725458, "Profit": 108418, "Margin_Pct": 14.9},
            ...
        ]
    
    Used in: Overview tab, region bar chart
    """
    year = request.args.get("year", "all")
    sql = """
        SELECT 
            Region,
            ROUND(SUM(Sales), 0)                  AS Revenue,
            ROUND(SUM(Profit), 0)                 AS Profit,
            ROUND(SUM(Profit)/SUM(Sales)*100, 1)  AS Margin_Pct
        FROM orders
        GROUP BY Region
        ORDER BY Revenue DESC
    """
    sql = apply_year_filter(sql, year)
    return jsonify(query(sql))


@app.route("/api/revenue-by-month")
def revenue_by_month():
    """
    Monthly revenue trend across all years (for seasonality analysis).
    
    Returns:
        [
            {"Month": 1, "Revenue": 23731},
            {"Month": 2, "Revenue": 14938},
            ...
        ]
    
    Used in: Overview tab, line chart showing seasonality
    """
    year = request.args.get("year", "all")
    sql = """
        SELECT 
            Month,
            ROUND(SUM(Sales), 0) AS Revenue
        FROM orders
        GROUP BY Month
        ORDER BY Month
    """
    sql = apply_year_filter(sql, year)
    return jsonify(query(sql))


@app.route("/api/category-performance")
def category_performance():
    """
    Revenue vs profit by product category (Technology, Furniture, Office Supplies).
    
    Returns:
        [
            {"Category": "Technology", "Revenue": 626154, "Profit": 100858},
            ...
        ]
    
    Used in: Overview tab, grouped bar chart
    """
    year = request.args.get("year", "all")
    sql = """
        SELECT 
            Category,
            ROUND(SUM(Sales), 0)  AS Revenue,
            ROUND(SUM(Profit), 0) AS Profit
        FROM orders
        GROUP BY Category
        ORDER BY Revenue DESC
    """
    sql = apply_year_filter(sql, year)
    return jsonify(query(sql))


@app.route("/api/top-products")
def top_products():
    """
    Top 10 products ranked by profit margin (products with >$1k sales).
    
    The >$1k filter removes outliers (one lucky sale with high margin).
    
    Returns:
        [
            {"Product Name": "Canon MF7460", "Revenue": 3992, "Profit": 1996, "Margin_Pct": 50.0},
            ...
        ]
    
    Used in: Insights tab, table of best-margin products
    """
    year = request.args.get("year", "all")
    sql = """
        SELECT
            "Product Name",
            ROUND(SUM(Sales), 0)                  AS Revenue,
            ROUND(SUM(Profit), 0)                 AS Profit,
            ROUND(SUM(Profit)/SUM(Sales)*100, 1)  AS Margin_Pct
        FROM orders
        GROUP BY "Product Name"
        HAVING SUM(Sales) > 1000
        ORDER BY Margin_Pct DESC
        LIMIT 10
    """
    sql = apply_year_filter(sql, year)
    return jsonify(query(sql))


@app.route("/api/discount-impact")
def discount_impact():
    """
    Critical insight: how discounts destroy profit margins.
    
    Buckets discount % and shows how margin % drops as discounts increase.
    This is THE key finding: heavy discounting is unprofitable.
    
    Returns:
        [
            {"Discount_Band": "0%", "Orders": 4798, "Avg_Sale": 227, "Margin_Pct": 29.5},
            {"Discount_Band": "1-10%", "Orders": 94, "Avg_Sale": 578, "Margin_Pct": 16.6},
            {"Discount_Band": "11-20%", "Orders": 3709, "Avg_Sale": 214, "Margin_Pct": 11.6},
            {"Discount_Band": "21-30%", "Orders": 227, "Avg_Sale": 455, "Margin_Pct": -10.0},
            {"Discount_Band": "30%+", "Orders": 1166, "Avg_Sale": 223, "Margin_Pct": -48.2}
        ]
    
    Used in: Overview tab, line chart showing margin collapse
    """
    year = request.args.get("year", "all")
    sql = """
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
        FROM orders
        GROUP BY Discount_Band
        ORDER BY 
            CASE Discount_Band
                WHEN '0%' THEN 1
                WHEN '1-10%' THEN 2
                WHEN '11-20%' THEN 3
                WHEN '21-30%' THEN 4
                ELSE 5
            END
    """
    sql = apply_year_filter(sql, year)
    return jsonify(query(sql))


@app.route("/api/query", methods=["POST"])
def run_query():
    """
    SQL Query Explorer endpoint.
    
    Accepts arbitrary SELECT queries from the React frontend.
    Only allows SELECT statements (blocks DELETE, UPDATE, DROP, etc).
    
    Request body:
        {"sql": "SELECT * FROM orders WHERE Region = 'West' LIMIT 10"}
    
    Returns:
        - Success: list of result rows as dicts
        - Error: {"error": "message"}
    """
    sql = request.json.get("sql", "").strip()
    
    # Security check: only allow SELECT
    # Prevents accidental/malicious DELETE, UPDATE, DROP, CREATE etc.
    if not sql.upper().startswith("SELECT"):
        return jsonify({"error": "Only SELECT queries allowed"}), 400
    
    try:
        return jsonify(query(sql))
    except Exception as e:
        # Return error message to React so user sees what went wrong
        return jsonify({"error": str(e)}), 400


# Run the Flask dev server
# debug=True enables auto-reload on code changes and detailed error pages
# port=5000 is where the API listens for requests
if __name__ == "__main__":
    app.run(debug=True, port=5000)
