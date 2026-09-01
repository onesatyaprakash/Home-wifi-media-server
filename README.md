# Home Wi-Fi Media Server
A lightweight, secure, and modern local file-sharing server built with Python, Flask, and Waitress. Designed to run on a local network, allowing devices on the same Wi-Fi to upload, view, stream, and download media seamlessly.

## Features
* **Production-Ready Server:** Powered by Waitress for stable, multi-threaded local performance.
* **Secure Authentication:** Basic Auth implemented using environment variables (`.env`) to keep credentials safe.
* **Modern UI:** A responsive, mobile-friendly interface featuring CSS variables, soft shadows, and dynamic file icons.
* **Native Media Playback:** Stream `.mp4` video, `.mp3` audio, and view images or PDFs directly in the browser without downloading.
* **Upload Security:** Enforces a 50MB file size limit and restricts uploads to a whitelist of safe media and document extensions.

## Prerequisites
* Python 3.x installed on your host machine.

## Installation
1. Clone the repository:
```bash
git clone [https://github.com/onesatyaprakash/Home-wifi-media-server.git](https://github.com/onesatyaprakash/Home-wifi-media-server.git)
cd Home-wifi-media-server

```
2. Install the required dependencies:
pip install -r requirements.txt

```
3. Password Configuration:
APP_USERNAME=your_custom_username
APP_PASSWORD=your_secure_password

```
4. Start the server by running the application:
python app.py

```
5 Access your server
IP address http://192.168.x.x:8000
