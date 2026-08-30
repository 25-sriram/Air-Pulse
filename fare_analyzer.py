import pandas as pd
import mysql.connector
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Milo@2013",
        database="airfare_db"
    )

def load_data():

    connection = get_connection()

    query = """
        SELECT
            origin,
            destination,
            airline,
            advance_days,
            total_fare
        FROM cleaned_fares
        WHERE total_fare IS NOT NULL
          AND advance_days IS NOT NULL
    """

    df = pd.read_sql(query, connection)

    connection.close()

    return df


def train_model(df):

    X = df[
        [
            "origin",
            "destination",
            "airline",
            "advance_days"
        ]
    ]

    y = df["total_fare"]

    categorical_features = [
        "origin",
        "destination",
        "airline"
    ]

    numerical_features = [
        "advance_days"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features
            ),
            (
                "numerical",
                "passthrough",
                numerical_features
            )
        ]
    )

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model)
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(
        y_test,
        predictions
    ) ** 0.5
    r2 = r2_score(y_test, predictions)

    return pipeline, mae, rmse, r2

def save_model(model):

    joblib.dump(
        model,
        "fare_prediction_model.pkl"
    )

def generate_predictions(model):

    routes = [
        ("MAA", "DEL"),
        ("DEL", "BOM"),
        ("DEL", "BLR"),
        ("BOM", "BLR"),
        ("BLR", "HYD"),
        ("DEL", "CCU")
    ]

    airlines = [
        "IndiGo",
        "Air India",
        "Air India Express",
        "Akasa Air",
        "SpiceJet"
    ]

    advance_windows = [
        1,
        7,
        15,
        30,
        45
    ]

    rows = []

    for origin, destination in routes:

        for airline in airlines:

            for days in advance_windows:

                input_data = pd.DataFrame(
                    [{
                        "origin": origin,
                        "destination": destination,
                        "airline": airline,
                        "advance_days": days
                    }]
                )

                predicted_fare = model.predict(
                    input_data
                )[0]

                rows.append({
                    "origin": origin,
                    "destination": destination,
                    "airline": airline,
                    "advance_days": days,
                    "predicted_fare": round(
                        predicted_fare,
                        2
                    )
                })

    return pd.DataFrame(rows)

def save_predictions(predictions):

    connection = get_connection()

    cursor = connection.cursor()

    create_table = """
        CREATE TABLE IF NOT EXISTS fare_predictions (

            prediction_id INT AUTO_INCREMENT PRIMARY KEY,

            origin VARCHAR(10),

            destination VARCHAR(10),

            airline VARCHAR(100),

            advance_days INT,

            predicted_fare DECIMAL(10,2),

            prediction_date TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
    """

    cursor.execute(create_table)

    insert_query = """
        INSERT INTO fare_predictions
        (
            origin,
            destination,
            airline,
            advance_days,
            predicted_fare
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    for _, row in predictions.iterrows():

        cursor.execute(
            insert_query,
            (
                row["origin"],
                row["destination"],
                row["airline"],
                int(row["advance_days"]),
                float(row["predicted_fare"])
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

def main():

    print("AIRFARE ML PREDICTION ENGINE")
    print("--------------------------------")

    df = load_data()

    print("Training records :", len(df))

    model, mae, rmse, r2 = train_model(df)

    print("\nMODEL PERFORMANCE")
    print("--------------------------------")

    print(
        f"MAE  : ₹{mae:.2f}"
    )

    print(
        f"RMSE : ₹{rmse:.2f}"
    )

    print(
        f"R²   : {r2:.4f}"
    )

    save_model(model)

    print("\nModel saved : fare_prediction_model.pkl")

    predictions = generate_predictions(model)

    save_predictions(predictions)

    print(
        "Predictions generated :",
        len(predictions)
    )

    print(
        "Predictions saved to MySQL table: "
        "fare_predictions"
    )

    print("--------------------------------")
    print("ML PREDICTION COMPLETED")


if __name__ == "__main__":
    main()