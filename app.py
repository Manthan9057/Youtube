import streamlit as st
from flask import Flask, render_template_string, request, jsonify
import subprocess
import re
import threading
import time
import os
from streamlit.web import cli as stcli
import socket

# Flask App Initialization
app = Flask(__name__)

# HTML Template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Redirect</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #333;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #FF0000;
            font-size: 24px;
        }
        input[type="text"] {
            width: 80%;
            padding: 10px;
            font-size: 16px;
            margin-top: 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        button {
            background-color: #FF0000;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 20px;
            font-size: 16px;
        }
        button:hover {
            background-color: #cc0000;
        }
        .count-section {
            margin-top: 20px;
            font-size: 18px;
            color: #333;
        }
        .count-section span {
            font-weight: bold;
            font-size: 20px;
            color: #FF0000;
        }
    </style>
</head>
<body>

<div class="container" id="mainPage">
    <h1>YouTube Viewer</h1>
    <p>Enter the YouTube URL below:</p>
    <input type="text" id="youtubeUrl" placeholder="Paste YouTube URL here" />
    <br>
    <button onclick="redirectToVideo()">Open Video</button>

    <div class="count-section">
        <p>Click Count: <span id="countDisplay">0</span></p>
    </div>
</div>

<script>
    let count = 0;

    function redirectToVideo() {
        const url = document.getElementById('youtubeUrl').value;

        const youtubeRegex = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.be)\/.+$/;

        if (youtubeRegex.test(url)) {
            fetch('/redirect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            }).then(response => response.json()).then(data => {
                if (data.success) {
                    count++;
                    document.getElementById('countDisplay').textContent = count;
                } else {
                    alert(data.message);
                }
            });
        } else {
            alert('Please enter a valid YouTube URL');
        }
    }
</script>

</body>
</html>
"""

# Global variables for counting and locks
click_count = 0
click_count_lock = threading.Lock()

# Regular expression for YouTube URL validation
youtube_regex = re.compile(r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.be)\/.+$')

# Function to handle the redirection in the browser (incognito mode)
def open_video(url):
    if os.name == 'posix':  # Linux/macOS
        subprocess.Popen(["google-chrome", "--incognito", url])
    elif os.name == 'nt':  # Windows
        subprocess.Popen(["start", "chrome", "--incognito", url], shell=True)
    else:
        print("Unsupported OS for opening browser.")

    time.sleep(10)  # Simulate tab open duration
    subprocess.call(["pkill", "-f", url])  # Close the browser tab if supported

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/redirect', methods=['POST'])
def redirect_to_video():
    global click_count

    data = request.get_json()
    url = data.get('url', '')

    if youtube_regex.match(url):
        threading.Thread(target=open_video, args=(url,)).start()

        with click_count_lock:
            click_count += 1

        return jsonify(success=True, message="Video opened successfully!", count=click_count)
    else:
        return jsonify(success=False, message="Invalid YouTube URL.")

# Streamlit Integration
st.title("YouTube Video Redirect")
st.write("Enter the YouTube URL below:")
youtube_url = st.text_input("Paste YouTube URL here")

if st.button("Open Video"):
    if youtube_regex.match(youtube_url):
        threading.Thread(target=open_video, args=(youtube_url,)).start()
        st.success("Video opened successfully in incognito mode!")
    else:
        st.error("Invalid YouTube URL. Please enter a valid URL.")

# Helper function to get the local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

# Display network address
def display_network_info():
    local_ip = get_local_ip()
    st.write(f"Access this app on your local network at: http://{local_ip}:8501")

display_network_info()

# Run Flask App in a separate thread
def run_flask():
    app.run(debug=False, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start Streamlit App
    stcli.main()
