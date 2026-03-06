import pyodbc

# Database connection parameters
server = 'YOUR_SERVER'  # replace with your server name
database = 'YOUR_DATABASE'  # replace with your database name
username = 'YOUR_USERNAME'  # replace with your username
password = 'YOUR_PASSWORD'  # replace with your password

# Create a connection string
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

try:
    # Establishing the connection
    with pyodbc.connect(conn_str) as conn:
        print('Connection successful!')

except pyodbc.Error as ex:
    # Print detailed error message
    sqlstate = ex.args[0]
    error_message = ex.args[1]
    print(f'Error occurred: SQLState: {sqlstate}, Message: {error_message}')