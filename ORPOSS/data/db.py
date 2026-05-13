import mysql.connector

try:
    # 1. Establish the connection
    db_connection = mysql.connector.connect(
        host="localhost",
        user="your_username",
        password="your_password",
        database="pos_system"
    )

    if db_connection.is_connected():
        print("Connected to MySQL database!")
        
        # 2. Create a cursor object (this executes the SQL)
        cursor = db_connection.cursor()
        
        # 3. Example: Create a Products table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                price DECIMAL(10, 2),
                stock INT
            )
        """)

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    # Always close the connection when done!
    if 'db_connection' in locals() and db_connection.is_connected():
        cursor.close()
        db_connection.close()