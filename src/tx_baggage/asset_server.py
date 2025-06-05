#!/usr/bin/env python3
"""
Asset Player Server
HTTP server for web-based video and image player
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime
import logging
import mimetypes
import socket

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('asset_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AssetServer:
    def __init__(self):
        self.host = "0.0.0.0"  # Listen on all network interfaces
        self.port = 8080
        self.assets_folder = "./assets/"
        self.assets_played = 0
        self.last_asset_info = None
        
        os.makedirs(self.assets_folder, exist_ok=True)
        logger.info(f"Asset server initialized. Assets folder: {os.path.abspath(self.assets_folder)}")
    
    def get_asset_path(self, filename):
        """Get full path to asset file"""
        return os.path.join(self.assets_folder, filename)
    
    def play_asset(self, filename, card_id=""):
        """Play an asset file (video or image) and notify web clients"""
        asset_path = self.get_asset_path(filename)
        
        if not os.path.exists(asset_path):
            logger.error(f"Asset file not found: {asset_path}")
            return False
        
        asset_type = self.get_asset_type(filename)
        
        self.last_asset_info = {
            'asset_file': filename,
            'asset_type': asset_type,
            'card_id': card_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.assets_played += 1
        logger.info(f"Asset triggered: {filename} ({asset_type}) (Card: {card_id})")
        return True
    
    def get_asset_type(self, filename):
        """Determine if file is video or image"""
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v', '.webm')
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg')
        
        filename_lower = filename.lower()
        
        if filename_lower.endswith(video_extensions):
            return 'video'
        elif filename_lower.endswith(image_extensions):
            return 'image'
        else:
            return 'unknown'
    
    def list_assets(self):
        """List all asset files in the assets folder"""
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v', '.webm')
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg')
        all_extensions = video_extensions + image_extensions
        
        assets = []
        
        try:
            for file in os.listdir(self.assets_folder):
                if file.lower().endswith(all_extensions):
                    file_path = self.get_asset_path(file)
                    file_size = os.path.getsize(file_path)
                    asset_type = self.get_asset_type(file)
                    
                    assets.append({
                        "filename": file,
                        "type": asset_type,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
        except Exception as e:
            logger.error(f"Error listing assets: {e}")
        
        return assets

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, asset_server=None, **kwargs):
        self.asset_server = asset_server
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def send_safe_response(self, response_code, content_type="text/plain", content=""):
        """Safely send response, handling broken connections"""
        try:
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            self.send_response(response_code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if content:
                self.wfile.write(content)
                
        except (ConnectionResetError, BrokenPipeError, socket.error):
            logger.debug(f"Client disconnected during response")
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    def send_json_response(self, data):
        """Send JSON response safely"""
        try:
            response_data = json.dumps(data)
            self.send_safe_response(200, 'application/json', response_data)
        except Exception as e:
            logger.error(f"Error sending JSON response: {e}")
            self.send_safe_response(500, 'text/plain', 'Internal server error')
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/':
                self.serve_web_player()
            elif self.path == '/ping':
                self.send_json_response({"status": "ok", "timestamp": datetime.now().isoformat()})
            elif self.path == '/status':
                response = {
                    "status": "running",
                    "assets_played": self.asset_server.assets_played,
                    "assets_folder": os.path.abspath(self.asset_server.assets_folder),
                    "last_asset": self.asset_server.last_asset_info,
                    "timestamp": datetime.now().isoformat()
                }
                self.send_json_response(response)
            elif self.path == '/assets':
                assets = self.asset_server.list_assets()
                self.send_json_response({"assets": assets, "count": len(assets)})
            elif self.path.startswith('/assets/'):
                asset_filename = self.path[8:]  # Remove '/assets/'
                self.serve_asset_file(asset_filename)
            elif self.path == '/current-asset':
                if self.asset_server.last_asset_info:
                    self.send_json_response(self.asset_server.last_asset_info)
                else:
                    self.send_json_response({"asset_file": None})
            else:
                self.send_safe_response(404, 'text/plain', 'Not Found')
                
        except (ConnectionResetError, BrokenPipeError, socket.error):
            logger.debug("Client disconnected during GET request")
        except Exception as e:
            logger.error(f"Error handling GET request {self.path}: {e}")
            try:
                self.send_safe_response(500, 'text/plain', 'Internal server error')
            except:
                pass
    
    def serve_web_player(self):
        """Serve the web player HTML file"""
        try:
            web_player_path = os.path.join(os.path.dirname(__file__), 'web_player.html')
            with open(web_player_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_safe_response(200, 'text/html; charset=utf-8', content)
            
        except FileNotFoundError:
            self.send_safe_response(404, 'text/plain', 'Web player not found')
        except Exception as e:
            logger.error(f"Error serving web player: {e}")
            self.send_safe_response(500, 'text/plain', str(e))
    
    def serve_asset_file(self, filename):
        """Serve asset files for web player"""
        try:
            asset_path = self.asset_server.get_asset_path(filename)
            
            if not os.path.exists(asset_path):
                self.send_safe_response(404, 'text/plain', 'Asset not found')
                return
            
            file_size = os.path.getsize(asset_path)
            mime_type, _ = mimetypes.guess_type(asset_path)
            
            if not mime_type:
                if filename.lower().endswith(('.mp4', '.mov')):
                    mime_type = 'video/mp4'
                elif filename.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif filename.lower().endswith('.png'):
                    mime_type = 'image/png'
                else:
                    mime_type = 'application/octet-stream'
            
            # Handle range requests for video streaming
            range_header = self.headers.get('Range')
            if range_header and mime_type.startswith('video/'):
                self.handle_range_request(asset_path, file_size, mime_type, range_header)
            else:
                self.serve_full_file(asset_path, file_size, mime_type, filename)
                    
        except Exception as e:
            logger.error(f"Error serving asset {filename}: {e}")
            self.send_safe_response(500, 'text/plain', 'Error serving asset')
    
    def serve_full_file(self, asset_path, file_size, mime_type, filename):
        """Serve entire file"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(file_size))
            if mime_type.startswith('video/'):
                self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            
            with open(asset_path, 'rb') as f:
                chunk_size = 8192
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    
        except (ConnectionResetError, BrokenPipeError, socket.error):
            logger.debug(f"Client disconnected during asset transfer: {filename}")
    
    def handle_range_request(self, asset_path, file_size, mime_type, range_header):
        """Handle HTTP range requests for video streaming"""
        try:
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            start = max(0, start)
            end = min(file_size - 1, end)
            content_length = end - start + 1
            
            self.send_response(206)  # Partial Content
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(content_length))
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            
            with open(asset_path, 'rb') as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
                    
        except (ConnectionResetError, BrokenPipeError, socket.error):
            logger.debug("Client disconnected during range request")
        except Exception as e:
            logger.error(f"Error handling range request: {e}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            if self.path == '/play':
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    data = json.loads(post_data.decode('utf-8'))
                    asset_file = data.get('asset_file', '')
                    card_id = data.get('card_id', '')
                    
                    if not asset_file:
                        self.send_safe_response(400, 'text/plain', 'No asset file specified')
                        return
                    
                    logger.info(f"RFID Card {card_id} triggered asset: {asset_file}")
                    
                    success = self.asset_server.play_asset(asset_file, card_id)
                    
                    response = {
                        "success": success,
                        "asset_file": asset_file,
                        "card_id": card_id,
                        "message": f"Asset triggered: {asset_file}" if success else f"Failed to trigger {asset_file}",
                        "timestamp": datetime.now().isoformat(),
                        "web_player_url": f"http://{self.headers.get('Host', 'localhost')}/"
                    }
                    
                    self.send_json_response(response)
                    
                except json.JSONDecodeError:
                    self.send_safe_response(400, 'text/plain', 'Invalid JSON')
                except Exception as e:
                    logger.error(f"Error handling play request: {e}")
                    self.send_safe_response(500, 'text/plain', 'Internal server error')
            else:
                self.send_safe_response(404, 'text/plain', 'Not Found')
                
        except (ConnectionResetError, BrokenPipeError, socket.error):
            logger.debug("Client disconnected during POST request")
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")

def create_handler(asset_server):
    """Create request handler with asset server instance"""
    def handler(*args, **kwargs):
        return RequestHandler(*args, asset_server=asset_server, **kwargs)
    return handler

class RobustHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        """Handle server errors gracefully"""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        if isinstance(exc_value, (ConnectionResetError, BrokenPipeError)):
            logger.debug(f"Client {client_address} disconnected")
            return
            
        logger.error(f"Error handling request from {client_address}: {exc_value}")

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "localhost"

def main():
    print("Exhibition Asset Player Server")
    print("=" * 40)
    print("Simple HTTP server that plays videos and images")
    print("when triggered by RFID card scans from ReadPI")
    print()
    print("Setup:")
    print("1. Put your video/image files in the 'assets' folder")
    print("2. Update ReadPI client with this server's IP")
    print("3. Map RFID cards to asset filenames in client")
    print("=" * 40)
    
    asset_server = AssetServer()
    local_ip = get_local_ip()
    
    print(f"Server starting on: http://{local_ip}:{asset_server.port}")
    print(f"Assets folder: {os.path.abspath(asset_server.assets_folder)}")
    print("Waiting for RFID triggers...")
    
    handler = create_handler(asset_server)
    httpd = RobustHTTPServer((asset_server.host, asset_server.port), handler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        httpd.shutdown()

if __name__ == "__main__":
    main() 