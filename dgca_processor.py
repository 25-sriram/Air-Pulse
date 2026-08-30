import pandas as pd
import mysql.connector
from pathlib import Path

CSV_FILE = Path("city.csv")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Milo@2013",
    "database": "airfare_db"
}

TARGET_YEAR = 2025

ROUTES = [
    ("MAA", "DEL", "CHENNAI", "DELHI"),
    ("DEL", "BOM", "DELHI", "MUMBAI"),
    ("DEL", "BLR", "DELHI", "BENGALURU"),
    ("BOM", "BLR", "MUMBAI", "BENGALURU"),
    ("BLR", "HYD", "BENGALURU", "HYDERABAD"),
    ("DEL", "CCU", "DELHI", "KOLKATA")
]

def load_data():
    df = pd.read_csv(CSV_FILE)
    required = ["Year", "Month", "City1", "City2", "PaxToCity2", "PaxFromCity2"]
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    for column in ["City1", "City2"]:
        df[column] = df[column].astype(str).str.strip().str.upper()

    for column in ["PaxToCity2", "PaxFromCity2"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    return df

def calculate_route_traffic(df):
    year_data = df[df["Year"] == TARGET_YEAR].copy()
    results = []

    for origin_code, destination_code, city_a, city_b in ROUTES:
        forward = year_data[
            (year_data["City1"] == city_a) &
            (year_data["City2"] == city_b)
        ]

        reverse = year_data[
            (year_data["City1"] == city_b) &
            (year_data["City2"] == city_a)
        ]

        forward_passengers = forward["PaxToCity2"].sum()
        reverse_passengers = reverse["PaxToCity2"].sum()

        if len(forward) == 0 and len(reverse) == 0:
            forward = year_data[
                (year_data["City1"] == city_b) &
                (year_data["City2"] == city_a)
            ]
            reverse = year_data[
                (year_data["City1"] == city_a) &
                (year_data["City2"] == city_b)
            ]

            forward_passengers = forward["PaxFromCity2"].sum()
            reverse_passengers = reverse["PaxFromCity2"].sum()

        total_passengers = forward_passengers + reverse_passengers

        results.append({
            "origin": origin_code,
            "destination": destination_code,
            "passengers": int(total_passengers)
        })

    result = pd.DataFrame(results)

    if result["passengers"].sum() == 0:
        raise ValueError("No passenger traffic found for the selected routes.")

    result["weight"] = (
        result["passengers"] / result["passengers"].sum() * 100
    ).round(4)

    return result

def save_to_mysql(result):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_traffic (
            route_id INT AUTO_INCREMENT PRIMARY KEY,
            origin VARCHAR(10) NOT NULL,
            destination VARCHAR(10) NOT NULL,
            passengers BIGINT NOT NULL,
            traffic_year INT NOT NULL,
            UNIQUE KEY unique_route_year (origin, destination, traffic_year)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_weights (
            route_id INT AUTO_INCREMENT PRIMARY KEY,
            origin VARCHAR(10) NOT NULL,
            destination VARCHAR(10) NOT NULL,
            weight DECIMAL(8,4) NOT NULL,
            traffic_year INT NOT NULL,
            UNIQUE KEY unique_weight_route_year (origin, destination, traffic_year)
        )
    """)

    for _, row in result.iterrows():
        cursor.execute("""
            INSERT INTO route_traffic
            (origin, destination, passengers, traffic_year)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                passengers = VALUES(passengers)
        """, (
            row["origin"],
            row["destination"],
            int(row["passengers"]),
            TARGET_YEAR
        ))

        cursor.execute("""
            INSERT INTO route_weights
            (origin, destination, weight, traffic_year)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                weight = VALUES(weight)
        """, (
            row["origin"],
            row["destination"],
            float(row["weight"]),
            TARGET_YEAR
        ))

    connection.commit()
    cursor.close()
    connection.close()

def main():
    print("DGCA ROUTE TRAFFIC PROCESSOR")
    print("--------------------------------")

    df = load_data()
    print(f"Dataset records : {len(df)}")
    print(f"Traffic year    : {TARGET_YEAR}")

    result = calculate_route_traffic(df)

    print("\nROUTE TRAFFIC AND WEIGHTS")
    print("--------------------------------")

    for _, row in result.iterrows():
        print(
            f'{row["origin"]} -> {row["destination"]} | '
            f'Passengers: {int(row["passengers"]):,} | '
            f'Weight: {row["weight"]:.4f}%'
        )

    print("--------------------------------")
    print(f'Total passengers : {int(result["passengers"].sum()):,}')
    print(f'Total weight     : {result["weight"].sum():.4f}%')

    save_to_mysql(result)

    print("\nDGCA PROCESSING COMPLETED")
    print("Traffic and weights saved to MySQL.")

if __name__ == "__main__":
    main()
