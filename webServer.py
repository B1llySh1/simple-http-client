from socket import *
from socket import *
import time
import os

import webbrowser

from datetime import datetime, timedelta

import threading
import secrets
import re

#global 
loggedInCookies = set()
def getCurrentCookie(request):
    requestLines = request.splitlines()
    cookie_line = None
    for line in requestLines:
        if "Cookie: " in line:
            cookie_line = line
    if (cookie_line):
        # Get rid of cookie header
        cookie_line = cookie_line.split("Cookie: ")[1]
        # Get the first cookie
        return cookie_line.split(";")[0]
    else:
        return None
def generate_random_cookie():
    # Generate a random 32-character hex string
    cookie_value = secrets.token_hex(16)
    return cookie_value
def protected(requestPath, request):
    protectedFiles = ["/secrect_web.html"]
    if requestPath in protectedFiles:
        if getCurrentCookie(request) and getCurrentCookie(request) in loggedInCookies:
            return False
        else:
            return True
    else:
        return False
def ifModifiedSince(request: str):
    # Extract if modified since line and its time
    header_lines = [line for line in request.splitlines() if line.startswith('If-Modified-Since')]
    if header_lines:
        print(header_lines)
        time = header_lines[0].split(": ", 1)[1]
        # Parse the If-Modified-Since header value
        return datetime.strptime(time, '%a, %d %b %Y %H:%M:%S %Z')
    return None

def send200Response(clientSocket, content_type="text/html"):
    # Send HTTP response header
    current_time_utc = datetime.utcnow()
    formatted_time = current_time_utc.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    response_header = f"HTTP/1.1 200 OK\r\nDate: {formatted_time}\r\Content-Type: {content_type}\r\n\r\n"
    # message_content = f"<h1>{message}</h1>"
    clientSocket.send(response_header.encode('utf-8'))
    print(f"Response: 200 OK")
    return 

def send304Response(clientSocket):
    # Send a 304 Not Modified response
    response_header = "HTTP/1.1 304 Not Modified\r\nContent-Type: text/html\r\n\r\n"
    not_modified_content = f"<h1>304 Not Modified</h1>"
    clientSocket.send(response_header.encode('utf-8') + not_modified_content.encode('utf-8'))
    print(f"Response: 304 Not Modified")
    return 

def send400Response(clientSocket):
    response_header = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n"
    bad_request_content = f"<h1>400 Bad Request</h1>"
    clientSocket.send(response_header.encode('utf-8') + bad_request_content.encode('utf-8'))
    print(f"Response: 400 Bad Request")
    return

def send403Response(clientSocket):
    response_header = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n"
    forbidden_content = f"<h1>403 Forbidden</h1>"
    clientSocket.send(response_header.encode('utf-8') + forbidden_content.encode('utf-8'))
    print(f"Response: 403 Forbidden")

def send404Response(clientSocket, file_path):
    response_header = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
    not_found_content = f"<h1>404 Not Found: {file_path}</h1>"
    clientSocket.send(response_header.encode('utf-8') + not_found_content.encode('utf-8'))
    print(f"Response: 404 Not Found")
    return

def getContentLength(request):
    content_length_pattern = re.compile(r'Content-Length:\s*(\d+)', re.IGNORECASE)
    match = content_length_pattern.search(request)

    if match:
        content_length = match.group(1)
        return int(content_length)
    else:
        return 0
    
    

def send411Response(clientSocket):
    # Send a 411 Length Required response
    # Send HTTP response header
    response_header = "HTTP/1.1 411 Length Required\r\nContent-Type: text/html\r\n\r\n"
    length_required_content = "<h1>411 Length Required</h1><p>Content is required for this request.</p>"
    # Send the response header and content to the client
    clientSocket.send(response_header.encode('utf-8') + length_required_content.encode('utf-8'))
    print(f"Response: 411 Length Required")

def getRequestParam(request):
    request_body = request.split("\r\n\r\n")[1]

    # Parse the form data
    form_data = dict(param.split("=") for param in request_body.split('&'))

    # Get the value of the "param" field
    param_value = form_data.get("param", "")

    return param_value

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
        
        # If the file needs authentication and user not authorized
        if protected(requestPath, request):
            send403Response(clientSocket)
            return

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

        # If the object is an image
        if (".jpg" in file_path):
            send200Response(clientSocket, content_type="image/jpeg")
        else:
            send200Response(clientSocket)

        # Send the content of the file to the client
        clientSocket.sendall(content)
        # print(f"File sent: {file_path}")
        return
    else:
        print(f"File not found: {file_path}")
        # Not found
        send404Response(clientSocket, file_path)
        return
    

def login(request, clientSocket):
    new_random_cookie = generate_random_cookie()
    loggedInCookies.add(new_random_cookie)
    print("logged cookie: ", new_random_cookie)
    # Set a cookie for the user when logging in
    # Set the expiration time in 1 hour
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    formatted_expiration_time = expiration_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    # Set a cookie for the user upon successful login
    response_header = (
        f"HTTP/1.1 200 OK\r\n"
        f"Set-Cookie: {new_random_cookie}; Expires={formatted_expiration_time}; Domain=localhost; Path=/; HttpOnly\r\n"
        f"Content-Type: text/html\r\n\r\n"
    )
    message_content = "<h1>Login successful</h1>"
    clientSocket.send(response_header.encode('utf-8') + message_content.encode('utf-8'))

def logout(request, clientSocket):
    if getCurrentCookie(request) and getCurrentCookie(request) in loggedInCookies:
        loggedInCookies.remove(getCurrentCookie(request))
        print("Removed cookie: ", getCurrentCookie(request))
        response_header = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        message_content = "<h1>Logout successful</h1>"
        clientSocket.send(response_header.encode('utf-8') + message_content.encode('utf-8'))
    else:
        send400Response(clientSocket)
    
def processHTMLrequest(request: str, clientSocket):
    requestLines = request.splitlines()
    if not requestLines:
        return
    requestLine = requestLines[0]
    print(f"Request: {requestLine}")

    requestCommands = requestLine.split(" ")

    if requestCommands[0] == "GET":
        getRequest(request, clientSocket)
        return

    elif requestCommands[0] == "POST":
        if "Content-Length" not in request:
            send411Response(clientSocket)
            return
        if (requestCommands[1] == "/login"):
            # Login action
            login(request, clientSocket)
            return
        if (requestCommands[1] == "/logout"):
            # Logout action
            logout(request, clientSocket)
            return
        if (getContentLength(request) == 0):
            send411Response(clientSocket)
            return
        
        else:
            send200Response(clientSocket)
            return

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
def processClient(clientSocket):
    request = clientSocket.recv(4096).decode()

    # For debgging the packets
    # print(request)
    processHTMLrequest(request, clientSocket)
    # print("\r\n")
    clientSocket.close()

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
    # webbrowser.open(f"http://localhost:{serverPort}/test.html", new=0, autoraise=True)

    while True:
        clientSocket, clientAddress = serverSocket.accept()
        # print("Client connected from " + str(clientAddress))
        
        # processClient(clientSocket)
        clientProcess = threading.Thread(target=processClient, args=(clientSocket,))
        clientProcess.start()
        
        # print("Client closed from " + str(clientAddress))



if __name__ == "__main__":
    main()
