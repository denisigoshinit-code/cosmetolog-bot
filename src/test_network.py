import socket
import os

def test_connection():
    try:
        host = 'db'
        port = 5432
        
        print(f'Testing connection to {host}:{port}...')
        
        # Проверяем DNS resolution
        try:
            ip = socket.gethostbyname(host)
            print(f'DNS resolution: {host} -> {ip}')
        except Exception as e:
            print(f'DNS resolution failed: {e}')
            return False
        
        # Проверяем порт
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(' Port 5432 is open and accessible')
            return True
        else:
            print(f' Port 5432 is closed or unreachable (error code: {result})')
            return False
            
    except Exception as e:
        print(f'Error: {e}')
        return False

if __name__ == '__main__':
    test_connection()
