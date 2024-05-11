import mysql.connector
from mysql.connector import Error

def create_connection():
    """Create a database connection to the MySQL server."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',        # or your host, e.g., '127.0.0.1'
            user='root',    # your mysql username
            password='Ememno96.' # your mysql password
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection

def execute_query(connection, query):
    """Execute a single query."""
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")

def main():
    return None
if __name__ == "__main__":
    main()
