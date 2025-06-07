import socket
import sys

print("Testing basic TCP connection to 172.28.69.148:5432...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)

try:
    print("Attempting connection...")
    result = sock.connect(('172.28.69.148', 5432))
    print("Connected successfully!")
    sock.close()
except socket.timeout:
    print("Connection timed out after 5 seconds")
except Exception as e:
    print(f"Connection failed: {e}")
