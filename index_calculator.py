import mysql.connector
import pandas as pd

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Milo@2013",
    "database": "airfare_db"
}

ADVANCE_WINDOWS = [1, 7, 15, 30, 45]

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def calculate_index():
    connection = get_connection()

    query = """
        SELECT
            cf.origin,
            cf.destination,
            cf.advance_days,
            AVG(cf.total_fare) AS average_fare,
            rw.weight
        FROM cleaned_fares cf
        JOIN route_weights rw
            ON cf.origin = rw.origin
            AND cf.destination = rw.destination
        WHERE cf.advance_days IN (1, 7, 15, 30, 45)
        GROUP BY
            cf.origin,
            cf.destination,
            cf.advance_days,
            rw.weight
        ORDER BY
            cf.origin,
            cf.destination,
            cf.advance_days
    """

    df = pd.read_sql(query, connection)
    connection.close()

    if df.empty:
        raise ValueError("No matching airfare and route-weight data found.")

    df["weighted_fare"] = df["average_fare"] * (df["weight"] / 100)

    index_by_window = (
        df.groupby("advance_days")["weighted_fare"]
        .sum()
        .reindex(ADVANCE_WINDOWS)
        .dropna()
        .reset_index()
        .rename(columns={"weighted_fare": "weighted_fare"})
    )

    if 30 not in index_by_window["advance_days"].values:
        raise ValueError("30-day advance window is required as the base.")

    base_value = index_by_window.loc[
        index_by_window["advance_days"] == 30,
        "weighted_fare"
    ].iloc[0]

    index_by_window["index_value"] = (
        index_by_window["weighted_fare"] / base_value * 100
    ).round(2)

    return df, index_by_window

def save_index(index_by_window):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airfare_index (
            index_id INT AUTO_INCREMENT PRIMARY KEY,
            advance_days INT NOT NULL,
            weighted_fare DECIMAL(12,2) NOT NULL,
            index_value DECIMAL(10,2) NOT NULL,
            base_advance_days INT NOT NULL,
            UNIQUE KEY unique_advance_days (advance_days)
        )
    """)

    cursor.execute("DELETE FROM airfare_index")

    for _, row in index_by_window.iterrows():
        cursor.execute("""
            INSERT INTO airfare_index
            (advance_days, weighted_fare, index_value, base_advance_days)
            VALUES (%s, %s, %s, %s)
        """, (
            int(row["advance_days"]),
            float(row["weighted_fare"]),
            float(row["index_value"]),
            30
        ))

    connection.commit()
    cursor.close()
    connection.close()

def main():
    print("AIRFARE PRICE INDEX CALCULATOR")
    print("--------------------------------")

    detail, index = calculate_index()

    print("\nROUTE WEIGHTED FARES")
    print("--------------------------------")

    for _, row in detail.iterrows():
        print(
            f'{row["origin"]} -> {row["destination"]} | '
            f'{int(row["advance_days"])} days | '
            f'Average fare: ₹{row["average_fare"]:.2f} | '
            f'Weight: {row["weight"]:.4f}% | '
            f'Contribution: ₹{row["weighted_fare"]:.2f}'
        )

    print("\nAIRFARE PRICE INDEX")
    print("--------------------------------")
    print("Base window: 30 days = 100")

    for _, row in index.iterrows():
        print(
            f'{int(row["advance_days"])} days | '
            f'Weighted fare: ₹{row["weighted_fare"]:.2f} | '
            f'Index: {row["index_value"]:.2f}'
        )

    save_index(index)

    print("--------------------------------")
    print("INDEX CALCULATION COMPLETED")
    print("Results saved to MySQL table: airfare_index")

if __name__ == "__main__":
    main()
