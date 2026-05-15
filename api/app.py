from flask import Flask, jsonify, request
import sqlite3
import pandas as pd

app = Flask(__name__)

# Allow React (localhost:5173) to talk to Flask (localhost:5000)
from flask_cors import CORS
CORS(app)

DB = "../superstore.db"  # path to your existing database

# -------------------------------------------------------------------
# Global Year Filter Support
# -------------------------------------------------------------------
VALID_YEARS = {"2014", "2015", "2016", "2017"}

def get_year_filter():
    """
    Returns:
        ("", []) for All Years
        ('WHERE strftime("%Y", "Order Date") = ?', ["2016"]) for a specific year
    """
    year = request.args.get("year", "All")

    if year == "All":
        return "", []

    if year not in VALID_YEARS:
        raise ValueError(f"Invalid year: {year}")

    return 'WHERE strftime("%Y", "Order Date") = ?', [year]


def query(sql, params=None):
    """Execute SQL and return as list of dicts"""
    try:
        conn = sqlite3.connect(DB)
        df = pd.read_sql(sql, conn, params=params or [])
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        raise Exception(str(e))


# -------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------

@app.route("/api/kpis")
def kpis():
    """Overall KPIs"""
    where_clause, params = get_year_filter()

    return jsonify(query(f"""
        SELECT
            ROUND(SUM(Sales), 0) AS total_revenue,
            ROUND(SUM(Profit), 0) AS total_profit,
            ROUND(SUM(Profit) / SUM(Sales) * 100, 1) AS margin_pct,
            COUNT(DISTINCT "Order ID") AS total_orders
        FROM orders
        {where_clause}
    """, params))


@app.route("/api/revenue-by-region")
def revenue_by_region():
    """Revenue & profit by region with margins"""
    where_clause, params = get_year_filter()

    return jsonify(query(f"""
        SELECT
            Region,
            ROUND(SUM(Sales), 0) AS Revenue,
            ROUND(SUM(Profit), 0) AS Profit,
            ROUND(SUM(Profit) / SUM(Sales) * 100, 1) AS Margin_Pct
        FROM orders
        {where_clause}
        GROUP BY Region
        ORDER BY Revenue DESC
    """, params))


@app.route("/api/revenue-by-month")
def revenue_by_month():
    """Monthly revenue trend"""
    where_clause, params = get_year_filter()

    return jsonify(query(f"""
        SELECT
            Month,
            ROUND(SUM(Sales), 0) AS Revenue
        FROM orders
        {where_clause}
        GROUP BY Month
        ORDER BY Month
    """, params))


@app.route("/api/category-performance")
def category_performance():
    """Revenue and profit by category"""
    where_clause, params = get_year_filter()

    return jsonify(query(f"""
        SELECT
            Category,
            ROUND(SUM(Sales), 0) AS Revenue,
            ROUND(SUM(Profit), 0) AS Profit
        FROM orders
        {where_clause}
        GROUP BY Category
        ORDER BY Revenue DESC
    """, params))


@app.route("/api/top-products")
def top_products():
    """Top 10 products by profit margin"""
    where_clause, params = get_year_filter()

    return jsonify(query(f"""
        SELECT
            "Product Name",
            ROUND(SUM(Sales), 0) AS Revenue,
            ROUND(SUM(Profit), 0) AS Profit,
            ROUND(SUM(Profit) / SUM(Sales) * 100, 1) AS Margin_Pct
        FROM orders
        {where_clause}
        GROUP BY "Product Name"
        HAVING SUM(Sales) > 1000
        ORDER BY Margin_Pct DESC
        LIMIT 10
    """, params))


@app.route("/api/discount-impact")
def discount_impact():
    """How discounts affect profit margins"""
    where_clause, params = get_year_filter()

    return jsonify(query(f"""
        SELECT
            CASE
                WHEN Discount = 0 THEN '0%'
                WHEN Discount <= 0.10 THEN '1-10%'
                WHEN Discount <= 0.20 THEN '11-20%'
                WHEN Discount <= 0.30 THEN '21-30%'
                ELSE '30%+'
            END AS Discount_Band,
            COUNT(*) AS Orders,
            ROUND(AVG(Sales), 0) AS Avg_Sale,
            ROUND(SUM(Profit) / SUM(Sales) * 100, 1) AS Margin_Pct
        FROM orders
        {where_clause}
        GROUP BY Discount_Band
        ORDER BY
            CASE Discount_Band
                WHEN '0%' THEN 1
                WHEN '1-10%' THEN 2
                WHEN '11-20%' THEN 3
                WHEN '21-30%' THEN 4
                ELSE 5
            END
    """, params))


# -------------------------------------------------------------------
# Custom SQL Query Endpoint
# -------------------------------------------------------------------

@app.route("/api/query", methods=["POST"])
def run_query():
    """Execute custom SQL query (SELECT only)"""
    sql = request.json.get("sql", "").strip()

    # Basic safety check — only allow SELECT statements
    if not sql.upper().startswith("SELECT"):
        return jsonify({"error": "Only SELECT queries allowed"}), 400

    try:
        return jsonify(query(sql))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -------------------------------------------------------------------
# Run Flask App
# -------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
