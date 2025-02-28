from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

class RESTHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/backup':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'message': 'do backup'}
            self.wfile.write(json.dumps(response).encode())
        else:
            super().do_GET()

def run(server_class=HTTPServer, handler_class=RESTHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print('Starting server...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
