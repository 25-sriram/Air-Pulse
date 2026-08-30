import mysql.connector
from datetime import datetime

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Milo@2013"
DATABASE_NAME = "airfare_db"

ALLOWED_AIRLINES = {
    "IndiGo",
    "Air India",
    "Air India Express",
    "Akasa Air",
    "SpiceJet"
}

def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DATABASE_NAME
    )

def create_clean_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleaned_fares (
            clean_id INT AUTO_INCREMENT PRIMARY KEY,
            observation_id INT,
            origin VARCHAR(10) NOT NULL,
            destination VARCHAR(10) NOT NULL,
            airline VARCHAR(100) NOT NULL,
            flight_number VARCHAR(30),
            flight_date DATE NOT NULL,
            collection_timestamp DATETIME NOT NULL,
            advance_days INT,
            cabin_class VARCHAR(30),
            total_fare DECIMAL(10,2) NOT NULL,
            currency VARCHAR(10) NOT NULL,
            source VARCHAR(50),
            UNIQUE KEY unique_observation (observation_id)
        )
    """)

def clean_data():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    create_clean_table(cursor)

    cursor.execute("""
        SELECT *
        FROM fare_observations
    """)

    records = cursor.fetchall()

    if not records:
        print("No records found in fare_observations.")
        cursor.close()
        connection.close()
        return

    cursor.execute("DELETE FROM cleaned_fares")

    valid_records = 0
    rejected_records = 0

    for record in records:

        origin = record["origin"]
        destination = record["destination"]
        airline = record["airline"]
        flight_date = record["flight_date"]
        collection_timestamp = record["collection_timestamp"]
        total_fare = record["total_fare"]
        currency = record["currency"]
        advance_days = record["advance_days"]

        if not origin or not destination:
            rejected_records += 1
            continue

        if origin == destination:
            rejected_records += 1
            continue

        if not airline or airline not in ALLOWED_AIRLINES:
            rejected_records += 1
            continue

        if total_fare is None or total_fare <= 0:
            rejected_records += 1
            continue

        if currency != "INR":
            rejected_records += 1
            continue

        if flight_date is None or collection_timestamp is None:
            rejected_records += 1
            continue

        if advance_days is None or advance_days < 0:
            rejected_records += 1
            continue

        cursor.execute("""
            INSERT IGNORE INTO cleaned_fares (
                observation_id,
                origin,
                destination,
                airline,
                flight_number,
                flight_date,
                collection_timestamp,
                advance_days,
                cabin_class,
                total_fare,
                currency,
                source
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """, (
            record["observation_id"],
            origin,
            destination,
            airline,
            record["flight_number"],
            flight_date,
            collection_timestamp,
            advance_days,
            record["cabin_class"],
            total_fare,
            currency,
            record["source"]
        ))

        valid_records += 1

    connection.commit()

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            MIN(total_fare) AS minimum_fare,
            MAX(total_fare) AS maximum_fare,
            AVG(total_fare) AS average_fare
        FROM cleaned_fares
    """)

    summary = cursor.fetchone()

    print("\nDATA CLEANING SUMMARY")
    print("----------------------------")
    print(f"Original records : {len(records)}")
    print(f"Valid records    : {summary['total']}")
    print(f"Rejected records : {rejected_records}")
    print(f"Minimum fare     : ₹{summary['minimum_fare']}")
    print(f"Maximum fare     : ₹{summary['maximum_fare']}")
    print(f"Average fare     : ₹{summary['average_fare']:.2f}")

    cursor.close()
    connection.close()

if __name__ == "__main__":
    clean_data()