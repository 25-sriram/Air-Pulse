import mysql.connector
from mysql.connector import Error

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Milo@2013"

DATABASE_NAME = "airfare_db"


def create_database():
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )

        cursor = connection.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"
        )

        print(f"Database '{DATABASE_NAME}' is ready.")


        cursor.execute(f"USE {DATABASE_NAME}")


        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fare_observations (
                observation_id INT AUTO_INCREMENT PRIMARY KEY,

                origin VARCHAR(10) NOT NULL,
                destination VARCHAR(10) NOT NULL,

                airline VARCHAR(100) NOT NULL,
                flight_number VARCHAR(30),

                flight_date DATE NOT NULL,
                collection_timestamp DATETIME NOT NULL,

                advance_days INT,

                cabin_class VARCHAR(30),

                total_fare DECIMAL(10,2),
                currency VARCHAR(10),

                self_transfer BOOLEAN,

                source VARCHAR(50)
            )
        """)

        connection.commit()

        print("Table 'fare_observations' is ready.")
        print("MySQL database setup completed successfully!")

    except Error as e:
        print("MySQL Error:", e)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    create_database()