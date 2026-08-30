import requests
import json

API_KEY = "ignav_sB0SWyc65pKN9eJ-qvwbYt8yfq7uYYKv"

url = "https://ignav.com/api/fares/one-way"

headers = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json"
}

data = {
    "origin": "MAA",
    "destination": "DEL",
    "departure_date": "2026-09-10",
    "adults": 1,
    "cabin_class": "economy",
    "market": "IN"
}

response = requests.post(
    url,
    headers=headers,
    json=data
)

print("Status code:", response.status_code)

if response.ok:
    result = response.json()
    with open("response.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)
    print("Raw API response saved to response.json")
    print("\nFlight offers found:")

    for itinerary in result.get("itineraries", []):
        price = itinerary["price"]
        outbound = itinerary["outbound"]

        print("--------------------------------")
        print("Airline:", outbound["carrier"])
        print("Price:", price["amount"], price["currency"])
        print("Cabin:", itinerary["cabin_class"])
        print("Self transfer:", itinerary["requires_self_transfer"])

        for segment in outbound["segments"]:
            print("Flight:", segment["marketing_carrier_code"],
                  segment["flight_number"])
            print("Departure:", segment["departure_time_local"])
            print("Arrival:", segment["arrival_time_local"])

else:
    print("Error:")
    print(response.text)