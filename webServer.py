from socket import *
import time
import os

import webbrowser

from datetime import datetime
def getRequest(requestPath, clientSocket):
    file_path = '.' + requestPath
    if os.path.exists(file_path):
        # Read the file from path
        with open(file_path, 'rb') as file:
            content = file.read()

        # Send HTTP response header
        response_header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        clientSocket.send(response_header.encode('utf-8'))
        print(f"Response: {response_header}")

        # Send the content of the file to the client
        # TODO: Send useing round robin if mutiple objects are requested
        clientSocket.sendall(content)
        print(f"File sent: {file_path}")

        return
    else:
        print(f"File not found: {file_path}")
        
        # Send HTTP response header
        response_header = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
        not_found_content = f"<h1>404 Not Found: {file_path}</h1>"
        clientSocket.send(response_header.encode('utf-8') + not_found_content.encode('utf-8'))
        print(f"Response: {response_header}")
        return
def ifModifiedSince(request: str):
    # Extract if modified since line and its time
    header_lines = [line for line in request.splitlines() if line.startswith('If-Modified-Since')]
    if header_lines:
        print(header_lines)
        time = header_lines[0].split(": ", 1)[1]
        # Parse the If-Modified-Since header value
        return datetime.strptime(time, '%a, %d %b %Y %H:%M:%S %Z')
    return None

def send200Response(clientSocket):
    # Send HTTP response header
    current_time_utc = datetime.utcnow()
    formatted_time = current_time_utc.strftime("%a, %d %b %Y %H:%M:%S GMT")
    response_header = f"HTTP/1.1 200 OK\r\nDate: {formatted_time}\r\Content-Type: text/html\r\nn\r\n"
    clientSocket.send(response_header.encode('utf-8'))
    print(f"Response: 200 OK")
    return 

def send304Response(clientSocket):
    # Send a 304 Not Modified response
    response_header = "HTTP/1.1 304 Not Modified\r\n\r\n"
    clientSocket.send(response_header.encode('utf-8'))
    print(f"Response: 304 Not Modified")
    return 

def send404Response(clientSocket, file_path):
    response_header = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
    not_found_content = f"<h1>404 Not Found: {file_path}</h1>"
    clientSocket.send(response_header.encode('utf-8') + not_found_content.encode('utf-8'))
    print(f"Response: 404 Not Found")
    return

def send400Response(clientSocket):
    response_header = "HTTP/1.1 400 Bad Request\r\n\r\n"
    bad_request_content = f"<h1>400 Bad Request</h1>"
    clientSocket.send(response_header.encode('utf-8') + bad_request_content)
    print(f"Response: 400 Bad Request")
    return

def need411Response(request, clientSocket):
    if "Content-Length" not in request:
        # Send a 411 Length Required response
        # Send HTTP response header
        response_header = "HTTP/1.1 411 Length Required\r\nContent-Type: text/html\r\n\r\n"
        length_required_content = "<h1>411 Length Required</h1><p>A Content-Length header is required for this request.</p>"
        # Send the response header and content to the client
        clientSocket.send(response_header.encode('utf-8') + length_required_content.encode('utf-8'))
        return True
    return False

def getRequest(request, clientSocket):
    requestLines = request.splitlines()
    requestLine = requestLines[0]
    requestCommands = requestLine.split(" ")
    requestPath = requestCommands[1]
    
    # Default path if not request path
    if requestPath == "/":
        requestPath = "/test.html"

    file_path = '.' + requestPath
    if os.path.exists(file_path):

        # Get the If-Modified-Since header from the request
        if_modified_since_time = ifModifiedSince(request)

        # See if the file has not been modified since the If-Modified-Since header
        if if_modified_since_time:
            # Get the last modification time of the file
            last_modified_time = os.path.getmtime(file_path)
            last_modified_date = datetime.utcfromtimestamp(last_modified_time)
            # Compare the If-Modified-Since time with the last modification time
            if if_modified_since_time >= last_modified_date:
                # Not modified
                send304Response(clientSocket)
                return
            
        # Read the file from path
        with open(file_path, 'rb') as file:
            content = file.read()
        # OK
        send200Response(clientSocket)

        # Send the content of the file to the client
        # TODO: Send useing round robin if mutiple objects are requested
        clientSocket.sendall(content)
        # print(f"File sent: {file_path}")
        return
    else:
        print(f"File not found: {file_path}")
        # Not found
        send404Response(clientSocket, file_path)
        return
def processHTMLrequest(request: str, clientSocket):
    requestLines = request.splitlines()
    requestLine = requestLines[0]
    print(f"Request: {requestLine}")

    requestCommands = requestLine.split(" ")

    if requestCommands[0] == "GET":
        getRequest(request, clientSocket)
        return

    elif requestCommands[0] == "POST":
        if need411Response(request, clientSocket):
            return
        pass
    elif requestCommands[0] == "HEAD":
        pass
    else:
        # Bad request
        send400Response(clientSocket)
        return
    

def isPortInUse(port):
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.bind(("", port))
    except:
        return True
    return False


def main():
    serverPort = 12000

    # Select available port
    while (isPortInUse(serverPort)):
        serverPort += 1

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", serverPort))
    serverSocket.listen(1)


    print("Server is listening on: " + str(serverSocket.getsockname()))

    print(f"Connect to the server use: http://localhost:{serverPort}/test.html")

    # Optional: Open the webiste for the user
    webbrowser.open(f"http://localhost:{serverPort}/test.html", new=0, autoraise=True)

    while True:
        clientSocket, clientAddress = serverSocket.accept()
        # print("Client connected from " + str(clientAddress))

        request = clientSocket.recv(1024).decode()
        # print(request)
        processHTMLrequest(request, clientSocket)

        clientSocket.close()
        # print("Client closed from " + str(clientAddress))

if __name__ == "__main__":
    main()
