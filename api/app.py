from flask import Flask, jsonify, request
import sqlite3
import pandas as pd
from flask_cors import CORS
from functools import lru_cache

app = Flask(__name__)
CORS(app)

DB = "../superstore.db"

# ---------------- DATABASE ----------------
def run_query(sql):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df.to_dict(orient="records")

# ---------------- CACHE LAYER ----------------
@lru_cache(maxsize=32)
def cached(sql):
    return run_query(sql)

# ---------------- KPI ----------------
@app.route("/api/kpis")
def kpis():
    data = run_query("""
        SELECT
            ROUND(SUM(Sales), 0) AS revenue,
            ROUND(SUM(Profit), 0) AS profit,
            ROUND(SUM(Profit)/SUM(Sales)*100, 1) AS margin,
            COUNT(DISTINCT "Order ID") AS orders
        FROM orders
    """)[0]

    return jsonify({
        "data": data,
        "meta": {"type": "kpis"}
    })

# ---------------- REGION ----------------
@app.route("/api/revenue-by-region")
def region():
    return jsonify({
        "data": cached("""
            SELECT Region,
                   ROUND(SUM(Sales),0) AS revenue,
                   ROUND(SUM(Profit),0) AS profit
            FROM orders
            GROUP BY Region
            ORDER BY revenue DESC
        """),
        "meta": {"type": "region"}
    })

# ---------------- MONTH ----------------
@app.route("/api/revenue-by-month")
def month():
    return jsonify({
        "data": cached("""
            SELECT Month,
                   ROUND(SUM(Sales),0) AS revenue
            FROM orders
            GROUP BY Month
            ORDER BY Month
        """),
        "meta": {"type": "time_series"}
    })

# ---------------- CATEGORY ----------------
@app.route("/api/category-performance")
def category():
    return jsonify({
        "data": cached("""
            SELECT Category,
                   ROUND(SUM(Sales),0) AS revenue,
                   ROUND(SUM(Profit),0) AS profit
            FROM orders
            GROUP BY Category
        """),
        "meta": {"type": "category"}
    })

# ---------------- SQL EXPLORER ----------------
@app.route("/api/query", methods=["POST"])
def sql_query():
    sql = request.json.get("sql")

    if not sql.strip().lower().startswith("select"):
        return jsonify({"error": "Only SELECT allowed"}), 400

    try:
        return jsonify({"data": run_query(sql)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
