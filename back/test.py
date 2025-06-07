import socket

# Test port connectivity
print("Testing port 5432...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
result = sock.connect_ex(('172.28.69.148', 5432))
if result == 0:
    print("✓ Port 5432 is open")
else:
    print(f"✗ Port 5432 is closed or filtered: {result}")
sock.close()

# Test PostgreSQL connection
print("\nTesting PostgreSQL connection...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='172.28.69.148',
        user='cropapi',
        password='cropapi123',
        database='crop_recommendations',
        port=5432,
        connect_timeout=10
    )
    print("✓ PostgreSQL connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prediction_logs")
    count = cursor.fetchone()[0]
    print(f"✓ Found {count} prediction logs in database")
    conn.close()
except Exception as e:
    print(f"✗ PostgreSQL connection error: {e}")
