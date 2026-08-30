import os
import json
import requests
import mysql.connector
from datetime import datetime, timedelta

API_KEY = "ignav_sB0SWyc65pKN9eJ-qvwbYt8yfq7uYYKv"

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Milo@2013"
DATABASE_NAME = "airfare_db"

API_URL = "https://ignav.com/api/fares/one-way"

MAX_API_CALLS = 800
MAX_REQUESTS_PER_RUN = 30

USAGE_FILE = "api_usage.json"
RAW_DATA_FOLDER = "raw_data"

ROUTES = [
    ("MAA", "DEL"),
    ("DEL", "BOM"),
    ("DEL", "BLR"),
    ("BOM", "BLR"),
    ("BLR", "HYD"),
    ("DEL", "CCU")
]

ADVANCE_WINDOWS = [1, 7, 15, 30, 45]

ALLOWED_AIRLINES = {
    "IndiGo",
    "Air India",
    "Air India Express",
    "Akasa Air",
    "SpiceJet"
}


def get_api_usage():
    if not os.path.exists(USAGE_FILE):
        return 0

    try:
        with open(USAGE_FILE, "r") as file:
            data = json.load(file)

        return data.get("used_calls", 0)

    except (json.JSONDecodeError, OSError):
        return 0


def update_api_usage(used_calls):
    with open(USAGE_FILE, "w") as file:
        json.dump(
            {"used_calls": used_calls},
            file,
            indent=4
        )


def get_mysql_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DATABASE_NAME
    )


def save_raw_response(origin, destination, flight_date, data):
    os.makedirs(RAW_DATA_FOLDER, exist_ok=True)

    filename = f"{origin}_{destination}_{flight_date}.json"

    filepath = os.path.join(
        RAW_DATA_FOLDER,
        filename
    )

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def get_flight_numbers(segments):
    flight_numbers = []

    for segment in segments:
        carrier_code = segment.get(
            "marketing_carrier_code"
        )

        flight_number = segment.get(
            "flight_number"
        )

        if carrier_code and flight_number:
            flight_numbers.append(
                f"{carrier_code} {flight_number}"
            )

    return ", ".join(flight_numbers)


def insert_fare(
    cursor,
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
    self_transfer
):
    cursor.execute(
        """
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
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        """,
        (
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
            "Ignav"
        )
    )


def collect_route(
    cursor,
    origin,
    destination,
    flight_date,
    advance_days
):
    used_calls = get_api_usage()

    if used_calls >= MAX_API_CALLS:
        print("API limit reached.")
        return 0

    data = {
        "origin": origin,
        "destination": destination,
        "departure_date": flight_date,
        "adults": 1,
        "cabin_class": "economy",
        "market": "IN"
    }

    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
            timeout=60
        )

        used_calls += 1
        update_api_usage(used_calls)

        print(
            f"API usage: {used_calls}/{MAX_API_CALLS}"
        )

        if not response.ok:
            print(
                f"API error {response.status_code} "
                f"for {origin} → {destination}"
            )
            print(response.text)
            return 0

        result = response.json()

        save_raw_response(
            origin,
            destination,
            flight_date,
            result
        )

        itineraries = result.get(
            "itineraries",
            []
        )

        saved_count = 0

        collection_timestamp = datetime.now()

        for itinerary in itineraries:

            self_transfer = itinerary.get(
                "requires_self_transfer",
                False
            )

            if self_transfer:
                continue

            price = itinerary.get(
                "price",
                {}
            )

            total_fare = price.get(
                "amount"
            )

            currency = price.get(
                "currency",
                "INR"
            )

            outbound = itinerary.get(
                "outbound",
                {}
            )

            airline = outbound.get(
                "carrier"
            )

            segments = outbound.get(
                "segments",
                []
            )

            cabin_class = itinerary.get(
                "cabin_class",
                "economy"
            )

            if not airline:
                continue

            if total_fare is None:
                continue

            if currency != "INR":
                continue

            if not segments:
                continue

            flight_number = get_flight_numbers(
                segments
            )

            if not flight_number:
                continue

            insert_fare(
                cursor,
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
                False
            )

            saved_count += 1

        return saved_count

    except requests.RequestException as error:
        print(
            f"Request failed for "
            f"{origin} → {destination}: {error}"
        )
        return 0

    except json.JSONDecodeError:
        print(
            f"Invalid JSON response for "
            f"{origin} → {destination}"
        )
        return 0


def main():

    used_calls = get_api_usage()

    remaining_calls = MAX_API_CALLS - used_calls

    total_planned_requests = (
        len(ROUTES) *
        len(ADVANCE_WINDOWS)
    )

    requests_to_make = min(
        total_planned_requests,
        MAX_REQUESTS_PER_RUN,
        remaining_calls
    )

    print()
    print("MULTI-ROUTE AIRFARE COLLECTOR")
    print("--------------------------------")
    print(f"API calls already used : {used_calls}")
    print(f"API calls remaining    : {remaining_calls}")
    print(f"Requests this run     : {requests_to_make}")
    print()

    if requests_to_make <= 0:
        print("No API calls available.")
        return

    connection = get_mysql_connection()
    cursor = connection.cursor()

    total_saved = 0
    completed_requests = 0

    today = datetime.now().date()

    stop_collection = False

    for origin, destination in ROUTES:

        if stop_collection:
            break

        print(
            f"Route: {origin} → {destination}"
        )

        for advance_days in ADVANCE_WINDOWS:

            if completed_requests >= requests_to_make:
                stop_collection = True
                break

            flight_date = (
                today +
                timedelta(days=advance_days)
            ).strftime("%Y-%m-%d")

            print(
                f"T+{advance_days} "
                f"→ {flight_date}"
            )

            saved = collect_route(
                cursor,
                origin,
                destination,
                flight_date,
                advance_days
            )

            connection.commit()

            total_saved += saved
            completed_requests += 1

            print(
                f"Records saved: {saved}"
            )
            print()

    cursor.close()
    connection.close()

    print("--------------------------------")
    print("COLLECTION COMPLETED")
    print("--------------------------------")
    print(
        f"Requests completed : "
        f"{completed_requests}"
    )
    print(
        f"Records saved      : "
        f"{total_saved}"
    )
    print(
        f"API usage          : "
        f"{get_api_usage()}/{MAX_API_CALLS}"
    )


if __name__ == "__main__":
    main()