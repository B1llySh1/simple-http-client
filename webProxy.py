from socket import *
import time
import os

import webbrowser

from datetime import datetime

import threading
import socket
import threading

cache = {}

def handle_client(client_socket):
    request_data = client_socket.recv(4096)

    print(request_data)

    # Check if the request is in the cache
    if request_data in cache:
        # Serve the cached response
        response_data = cache[request_data]
        print("Cache hit!")
    else:
        # Forward the request to the target server
        target_host = "www.google.com"
        target_port = 80

        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_host, target_port))
        target_socket.send(request_data)

        # Receive the response from the target server
        response_data = target_socket.recv(4096)

        # Cache the response for future use
        cache[request_data] = response_data
        print("Cached the response!")

        # Close the target socket
        target_socket.close()

    # Forward the response to the client
    client_socket.send(response_data)

    # Close the client socket
    client_socket.close()

def start_proxy_server(proxy_port):
    # Create a server socket
    server_socket = socket.socket(AF_INET, SOCK_STREAM)
    server_socket.bind(("", proxy_port))
    server_socket.listen(1)

    print(f"Proxy server listening on port {proxy_port}")

    while True:
        # Accept incoming connections
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")

        # Handle the client in a separate thread
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    # Set the proxy server port
    proxy_port = 8000

    # Start the proxy server
    start_proxy_server(proxy_port)
