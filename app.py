from flask import Flask, render_template, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Milo@2013"),
    "database": os.getenv("DB_NAME", "airfare_db")
}


def fetch(query, params=()):
    conn = mysql.connector.connect(**DB)
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/summary")
def summary():
    return jsonify(fetch("""
        SELECT
            (SELECT ROUND(AVG(total_fare),2)
             FROM cleaned_fares) AS avg_market_fare,
            (SELECT COUNT(*)
             FROM fare_predictions) AS total_predictions
    """)[0])


@app.route("/api/index")
def index():
    return jsonify(fetch("""
        SELECT advance_days, weighted_fare, index_value
        FROM airfare_index
        ORDER BY advance_days
    """))


@app.route("/api/monthly-index")
def monthly_index():
    return jsonify(fetch("""
        SELECT index_month, weighted_fare, index_value, base_month
        FROM monthly_airfare_index
        ORDER BY index_month
    """))


@app.route("/api/routes")
def routes():
    return jsonify(fetch("""
        SELECT origin, destination,
               ROUND(AVG(total_fare),2) AS average_fare,
               MIN(total_fare) AS min_fare,
               MAX(total_fare) AS max_fare,
               COUNT(*) AS observations
        FROM cleaned_fares
        GROUP BY origin, destination
        ORDER BY average_fare
    """))


@app.route("/api/heatmap")
def heatmap():
    return jsonify(fetch("""
        SELECT origin, destination, advance_days,
               ROUND(AVG(total_fare),2) AS average_fare
        FROM cleaned_fares
        GROUP BY origin, destination, advance_days
        ORDER BY origin, destination, advance_days
    """))


@app.route("/api/predictions")
def predictions():
    route = request.args.get("route")

    if route and "-" in route:
        origin, destination = route.split("-", 1)

        return jsonify(fetch("""
            SELECT origin, destination, airline,
                   advance_days, predicted_fare
            FROM fare_predictions
            WHERE origin=%s AND destination=%s
            ORDER BY advance_days, airline
        """, (origin, destination)))

    return jsonify(fetch("""
        SELECT origin, destination, airline,
               advance_days, predicted_fare
        FROM fare_predictions
        ORDER BY origin, destination, advance_days, airline
    """))


@app.route("/api/recommendations")
def recommendations():
    return jsonify(fetch("""
        SELECT origin, destination,
               recommended_advance_days,
               recommended_average_fare,
               recommendation
        FROM fare_recommendations
        ORDER BY origin, destination
    """))


if __name__ == "__main__":
    app.run(debug=True)