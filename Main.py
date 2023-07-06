from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import threading
from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime

HOST_NAME = 'localhost'
PORT_NUMBER = 3000
SOCKET_HOST = 'localhost'
SOCKET_PORT = 5000
DATA_FILE = 'storage/data.json'


class WebHandler(BaseHTTPRequestHandler):
    ROUTES = {
        '/': {'content_type': 'text/html', 'resource': 'index.html'},
        '/message.html': {'content_type': 'text/html', 'resource': 'message.html'},
        '/style.css': {'content_type': 'text/css', 'resource': 'style.css'},
        '/logo.png': {'content_type': 'image/png', 'resource': 'logo.png'}
    }

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path in self.ROUTES:
            route = self.ROUTES[path]
            self._send_response(200, route['content_type'], self._load_static(route['resource']))
        else:
            self._send_response(404, 'text/html', self._load_template('error.html'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_qs = parse_qs(post_data)

        if self.path == '/message':
            self._save_web_message(parsed_qs)
            self._send_response(302, 'text/html', self._load_template('message.html'), {'Location': '/message.html'})
        else:
            self._send_response(404, 'text/html', self._load_template('error.html'))

    def _send_response(self, status_code, content_type, data, headers=None):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))

    def _load_static(self, resource):
        with open(resource, 'rb') as file:
            return file.read()

    def _load_template(self, template):
        with open(template, 'r') as file:
            return file.read()

    def _send_message_to_socket_server(self, message):
        sock = socket(AF_INET, SOCK_DGRAM)
        message_bytes = json.dumps(message).encode('utf-8')
        sock.sendto(message_bytes, (SOCKET_HOST, SOCKET_PORT))

    def _save_web_message(self, message_data):
        data = {
            'username': message_data.get('username', [''])[0],
            'message': message_data.get('message', [''])[0]
        }
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        new_message = {timestamp: data}

        with open(DATA_FILE, 'r+') as file:
            messages = json.load(file)
            messages.update(new_message)
            file.seek(0)
            json.dump(messages, file, indent=4)

        self._send_message_to_socket_server(new_message)


class ThreadedHTTPServer(threading.Thread, HTTPServer):
    def __init__(self, address, handler_class):
        threading.Thread.__init__(self)
        self.http_server = HTTPServer(address, handler_class)

    def run(self):
        self.http_server.serve_forever()





class SocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind((self.host, self.port))

        while True:
            data, _ = sock.recvfrom(1024)
            message = json.loads(data.decode('utf-8'))
            self._save_socket_message(message)

    def _save_socket_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        new_message = {timestamp: message}

        with open(DATA_FILE, 'r+') as file:
            data = json.load(file)
            data.update(new_message)
            file.seek(0)
            file.write(json.dumps(data, indent=4))
            file.truncate()


def run_servers():
    while True:
        pass

if __name__ == '__main__':
    web_server = ThreadedHTTPServer((HOST_NAME, PORT_NUMBER), WebHandler)
    socket_server = SocketServer(SOCKET_HOST, SOCKET_PORT)

    print(f'Starting web server on http://{HOST_NAME}:{PORT_NUMBER}')
    print(f'Starting socket server on {SOCKET_HOST}:{SOCKET_PORT}')

    try:
        web_server.start()
        socket_server_thread = threading.Thread(target=socket_server.start)

        socket_server_thread.daemon = True
        socket_server_thread.start()

        run_servers()

    except KeyboardInterrupt:
        print('\nStopping servers...')
        web_server.shutdown()
        socket_server_thread.join()
        print('Servers stopped.')



