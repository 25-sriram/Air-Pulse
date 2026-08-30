import mysql.connector
import pandas as pd
import os


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Milo@2013"),
    "database": os.getenv("DB_NAME", "airfare_db")
}



def get_connection():
    return mysql.connector.connect(**DB_CONFIG)



def load_data():

    connection = get_connection()

    query = """
        SELECT
            origin,
            destination,
            flight_date,
            total_fare
        FROM cleaned_fares
        WHERE total_fare IS NOT NULL
    """

    df = pd.read_sql(query, connection)

    connection.close()

    return df


def load_weights():

    connection = get_connection()

    query = """
        SELECT
            origin,
            destination,
            weight
        FROM route_weights
    """

    weights = pd.read_sql(query, connection)

    connection.close()

    return weights




def calculate_monthly_route_fares(df):

    df["flight_date"] = pd.to_datetime(df["flight_date"])

    df["month"] = df["flight_date"].dt.to_period("M")

    monthly = (
        df.groupby(
            ["month", "origin", "destination"],
            as_index=False
        )
        .agg(
            average_fare=("total_fare", "mean"),
            observations=("total_fare", "count")
        )
    )

    return monthly



def calculate_weighted_fares(monthly, weights):

    merged = monthly.merge(
        weights,
        on=["origin", "destination"],
        how="inner"
    )

    merged["contribution"] = (
        merged["average_fare"] *
        merged["weight"] /
        100
    )

    monthly_weighted = (
        merged.groupby("month", as_index=False)
        .agg(
            weighted_fare=("contribution", "sum")
        )
    )

    return monthly_weighted, merged


def calculate_index(monthly_weighted):

    monthly_weighted = monthly_weighted.sort_values("month")

    base_month = monthly_weighted.iloc[0]["month"]

    base_fare = monthly_weighted.iloc[0]["weighted_fare"]

    monthly_weighted["index_value"] = (
        monthly_weighted["weighted_fare"] /
        base_fare
    ) * 100

    monthly_weighted["base_month"] = base_month

    return monthly_weighted


def save_results(index_data):

    connection = get_connection()

    cursor = connection.cursor()

    # Remove previous calculations
    cursor.execute(
        "DELETE FROM monthly_airfare_index"
    )

    for _, row in index_data.iterrows():

        month_date = row["month"].to_timestamp().date()

        base_date = (
            row["base_month"]
            .to_timestamp()
            .date()
        )

        cursor.execute(
            """
            INSERT INTO monthly_airfare_index
            (
                index_month,
                weighted_fare,
                index_value,
                base_month
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                month_date,
                round(float(row["weighted_fare"]), 2),
                round(float(row["index_value"]), 2),
                base_date
            )
        )

    connection.commit()

    cursor.close()
    connection.close()




def display_results(index_data, route_data):

    print()
    print("MONTHLY AIRFARE PRICE INDEX")
    print("--------------------------------")

    base_month = index_data.iloc[0]["month"]

    print(
        f"Base month      : {base_month}"
    )

    print(
        f"Base index      : 100.00"
    )

    print("--------------------------------")

    for _, row in index_data.iterrows():

        print(
            f"{row['month']} | "
            f"Weighted Fare: ₹{row['weighted_fare']:,.2f} | "
            f"Index: {row['index_value']:.2f}"
        )

    print("--------------------------------")

    print()
    print("MONTHLY ROUTE ANALYSIS")
    print("--------------------------------")

    for _, row in route_data.sort_values(
        ["month", "origin", "destination"]
    ).iterrows():

        print(
            f"{row['month']} | "
            f"{row['origin']} -> {row['destination']} | "
            f"Average: ₹{row['average_fare']:,.2f} | "
            f"Weight: {row['weight']:.4f}% | "
            f"Contribution: ₹{row['contribution']:,.2f}"
        )




def main():

    print("MONTHLY AIRFARE INDEX ENGINE")
    print("--------------------------------")

    fares = load_data()

    weights = load_weights()

    print(
        f"Fare observations : {len(fares)}"
    )

    print(
        f"Routes weighted   : {len(weights)}"
    )

    monthly_routes = calculate_monthly_route_fares(
        fares
    )

    monthly_weighted, route_data = calculate_weighted_fares(
        monthly_routes,
        weights
    )

    if monthly_weighted.empty:

        print()
        print("ERROR: No matching route data found.")

        return

    index_data = calculate_index(
        monthly_weighted
    )

    display_results(
        index_data,
        route_data
    )

    save_results(
        index_data
    )

    print()
    print("MONTHLY INDEX CALCULATION COMPLETED")
    print("--------------------------------")
    print(
        "Results saved to MySQL table:"
    )
    print(
        "monthly_airfare_index"
    )


if __name__ == "__main__":
    main()