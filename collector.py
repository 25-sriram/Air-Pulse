import os
import json
import requests
import mysql.connector
from datetime import datetime

API_KEY = "ignav_sB0SWyc65pKN9eJ-qvwbYt8yfq7uYYKv"

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Milo@2013"
DATABASE_NAME = "airfare_db"

MAX_API_CALLS = 800
USAGE_FILE = "api_usage.json"

ORIGIN = "MAA"
DESTINATION = "DEL"
FLIGHT_DATE = "2026-09-10"

URL = "https://ignav.com/api/fares/one-way"

def get_api_usage():
    if not os.path.exists(USAGE_FILE):
        return 0

    with open(USAGE_FILE, "r") as file:
        data = json.load(file)

    return data.get("used_calls", 0)

def update_api_usage(used_calls):
    with open(USAGE_FILE, "w") as file:
        json.dump({"used_calls": used_calls}, file, indent=4)

def get_mysql_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DATABASE_NAME
    )

def collect_fares():
    used_calls = get_api_usage()

    if used_calls >= MAX_API_CALLS:
        print("API request limit reached. No request was made.")
        return

    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }

    request_data = {
        "origin": ORIGIN,
        "destination": DESTINATION,
        "departure_date": FLIGHT_DATE,
        "adults": 1,
        "cabin_class": "economy",
        "market": "IN"
    }

    response = requests.post(
        URL,
        headers=headers,
        json=request_data
    )

    used_calls += 1
    update_api_usage(used_calls)

    print(f"API calls used: {used_calls}/{MAX_API_CALLS}")

    if not response.ok:
        print("API Error:", response.status_code)
        print(response.text)
        return

    result = response.json()

    collection_time = datetime.now()

    travel_date = datetime.strptime(
        FLIGHT_DATE,
        "%Y-%m-%d"
    ).date()

    today = datetime.now().date()

    advance_days = (travel_date - today).days

    connection = get_mysql_connection()
    cursor = connection.cursor()

    saved_count = 0

    for itinerary in result.get("itineraries", []):

        if itinerary.get("requires_self_transfer", False):
            continue

        price = itinerary.get("price", {})
        total_fare = price.get("amount")
        currency = price.get("currency")

        outbound = itinerary.get("outbound", {})

        airline = outbound.get("carrier")

        segments = outbound.get("segments", [])

        if len(segments) != 1:
            continue

        segment = segments[0]

        carrier_code = segment.get(
            "marketing_carrier_code"
        )

        flight_number = segment.get(
            "flight_number"
        )

        if not carrier_code or not flight_number:
            continue

        full_flight_number = (
            f"{carrier_code} {flight_number}"
        )

        cursor.execute("""
            INSERT INTO fare_observations (
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
                self_transfer,
                source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ORIGIN,
            DESTINATION,
            airline,
            full_flight_number,
            FLIGHT_DATE,
            collection_time,
            advance_days,
            "economy",
            total_fare,
            currency,
            False,
            "Ignav"
        ))

        saved_count += 1

    connection.commit()

    cursor.close()
    connection.close()

    print(f"{saved_count} fare observations saved to MySQL.")

if __name__ == "__main__":
    collect_fares()