import psycopg2
from psycopg2 import sql, Error
from dotenv import load_dotenv
import os
if os.path.exists("config.env"):
    load_dotenv("config.env")
    print("Loaded environment variables from config.env (local testing).")
else:
    print("Using Vercel environment variables.")

# def get_db_connection():
#     """
#     Establishes and returns a connection to the PostgreSQL database.
#     Ensure you update the credentials to match your database configuration.

#     Returns:
#         connection (psycopg2.connection): Connection object to the PostgreSQL database.
#     Raises:
#         psycopg2.Error: If there is an issue connecting to the database.
#     """
#     # Replace with your database credentials
#     HOST = "127.0.0.1"       # Host address, e.g., localhost or IP
#     PORT = "5432"            # Port number
#     DATABASE = "postgres"    # Database name
#     USER = "postgres"        # Database user
#     PASSWORD = "your_new_password"  # Database password

#     try:
#         # Establish the connection
#         connection = psycopg2.connect(
#             host=HOST,
#             port=PORT,
#             database=DATABASE,
#             user=USER,
#             password=PASSWORD
#         )
  
#         print("Database connection established successfully!")
#         return connection
#     except psycopg2.Error as e:
#         print("Error while connecting to PostgreSQL:", e)
#         raise

# import psycopg2

def get_db_connection():
    """
    Establish a connection to the PostgreSQL database.
    """
    DATABASE_URL =os.getenv("DATABASE_URL")#"postgresql://postgres:CFAnD4HXqeADzkbWV72O@database-1.cbeegwck4wyg.us-east-1.rds.amazonaws.com:5432/postgres"# os.getenv("DATABASE_URL")  # Use environment variable
    try:
        print(DATABASE_URL)
        connection = psycopg2.connect(DATABASE_URL)
        print("Database connection established successfully!")
        return connection
    except psycopg2.Error as e:
        print("Error while connecting to PostgreSQL:", e)
        raise
def add_reset_token_column():
    """
    Adds the 'reset_token' column to the 'users' table in the database if it does not exist.

    Raises:
        psycopg2.Error: If there is an issue executing the SQL command.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Add the 'reset_token' column if it doesn't exist
        cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'reset_token'
            ) THEN
                ALTER TABLE users
                ADD COLUMN reset_token VARCHAR(255);
            END IF;
        END $$;
        """)

        connection.commit()
        print("Column 'reset_token' added to the 'users' table successfully (if it didn't already exist).")
    except psycopg2.Error as e:
        print("Error while adding 'reset_token' column to the 'users' table:", e)
        raise
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

def fetch_all_users():
    """
    Fetches all records from the 'users' table.

    Returns:
        list: A list of dictionaries where each dictionary represents a user.
    Raises:
        psycopg2.Error: If there is an issue executing the SQL query.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Execute the SQL query to fetch all records
        cursor.execute("SELECT * FROM users;")
        
        # Fetch all rows from the query
        rows = cursor.fetchall()
        print(rows)
        # Get column names for better representation
        column_names = [desc[0] for desc in cursor.description]
        
        # Convert rows to a list of dictionaries
        users = [dict(zip(column_names, row)) for row in rows]

        print("Fetched all users successfully!")
        return users
    except psycopg2.Error as e:
        print("Error while fetching users from the 'users' table:", e)
        raise
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

def delete_all_users():
    """
    Deletes all records from the 'users' table.

    Raises:
        psycopg2.Error: If there is an issue executing the SQL query.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Execute the SQL query to delete all records
        cursor.execute("DELETE FROM users;")
        
        # Commit the changes to the database
        connection.commit()

        print("All users deleted successfully!")
    except psycopg2.Error as e:
        print("Error while deleting users from the 'users' table:", e)
        raise
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.") 

def create_users_table():
    """
    Creates a 'users' table in the connected PostgreSQL database.
    """
    
    try:
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Define the SQL statement to create the table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            reset_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Execute the query
        cursor.execute(create_table_query)
        connection.commit()

        print("Table 'users' created successfully!")
    except psycopg2.Error as e:
        print(f"Error while creating the 'users' table: {e}")
    finally:
        # Close the connection
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")

# Call the function to create the table
# create_users_table()            


# delete_all_users()                     

# # Example usage
if __name__ == "__main__":
    users = fetch_all_users()
    for user in users:
        print(user)

# get_db_connection()
 


       
       
        