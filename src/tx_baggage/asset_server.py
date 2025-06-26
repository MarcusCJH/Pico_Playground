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
    # Supported file extensions (centralized)
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v', '.webm')
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg')
    ALL_EXTENSIONS = VIDEO_EXTENSIONS + IMAGE_EXTENSIONS
    
    def __init__(self):
        self.host = "0.0.0.0"  # Listen on all network interfaces
        self.port = 8080
        self.assets_folder = "./assets/"
        self.assets_played = 0
        self.last_asset_info = None
        
        # RFID card tracking
        self.scanned_cards = {}  # card_id -> {first_seen, last_seen, scan_count, mapped}
        self.unknown_cards = {}  # card_id -> {first_seen, last_seen, scan_count}
        
        # Multi-asset support per card
        self.card_asset_indices = {}  # card_id -> current_asset_index
        self.current_card_id = None
        self.card_removal_timestamp = None  # Track when card was removed
        
        os.makedirs(self.assets_folder, exist_ok=True)
        logger.info(f"Asset server initialized. Assets folder: {os.path.abspath(self.assets_folder)}")
    
    def get_asset_path(self, filename):
        """Get full path to asset file"""
        return os.path.join(self.assets_folder, filename)
    
    def get_card_assets(self, card_id):
        """Get all assets for a specific card"""
        try:
            from importlib import reload
            import config
            reload(config)
            
            card_assets = getattr(config, 'CARD_ASSETS', {})
            assets = card_assets.get(card_id, [])
            
            # Handle both old format (string) and new format (list)
            if isinstance(assets, str):
                return [assets]
            elif isinstance(assets, list):
                return assets
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting card assets: {e}")
            return []
    
    def play_card_asset(self, card_id, asset_index=None):
        """Play asset for a card, optionally specifying index"""
        assets = self.get_card_assets(card_id)
        
        if not assets:
            logger.error(f"No assets found for card: {card_id}")
            return False
        
        # Initialize or get current index for this card
        if card_id not in self.card_asset_indices:
            self.card_asset_indices[card_id] = 0
        
        # Use specified index or current index
        if asset_index is not None:
            if 0 <= asset_index < len(assets):
                self.card_asset_indices[card_id] = asset_index
            else:
                logger.error(f"Invalid asset index {asset_index} for card {card_id}")
                return False
        
        current_index = self.card_asset_indices[card_id]
        filename = assets[current_index]
        
        # Set current card
        self.current_card_id = card_id
        
        return self.play_asset(filename, card_id, current_index, len(assets))
    
    def navigate_card_assets(self, card_id, direction):
        """Navigate through assets of a specific card"""
        assets = self.get_card_assets(card_id)
        
        if not assets or len(assets) <= 1:
            return False
        
        if card_id not in self.card_asset_indices:
            self.card_asset_indices[card_id] = 0
        
        current_index = self.card_asset_indices[card_id]
        
        if direction == 'next':
            new_index = (current_index + 1) % len(assets)
        elif direction == 'prev':
            new_index = (current_index - 1) % len(assets)
        else:
            return False
        
        self.card_asset_indices[card_id] = new_index
        filename = assets[new_index]
        
        logger.info(f"Navigating card {card_id} assets: {direction} to index {new_index} ({filename})")
        
        return self.play_asset(filename, card_id, new_index, len(assets))
    
    def remove_card(self, card_id):
        """Handle card removal - reset to splash screen"""
        self.current_card_id = None
        self.card_removal_timestamp = datetime.now().isoformat()
        self.last_asset_info = {
            'action': 'card_removed',
            'card_id': card_id,
            'timestamp': self.card_removal_timestamp
        }
        
        logger.info(f"Card {card_id} removed - returning to splash screen")
        return True

    def play_asset(self, filename, card_id="", asset_index=0, total_assets=1):
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
            'asset_index': asset_index,
            'total_assets': total_assets,
            'timestamp': datetime.now().isoformat()
        }
        
        # Track the card scan as mapped
        if card_id:
            self.track_card_scan(card_id, is_mapped=True)
        
        self.assets_played += 1
        logger.info(f"Asset triggered: {filename} ({asset_type}) (Card: {card_id}, {asset_index + 1}/{total_assets})")
        return True
    
    def get_asset_type(self, filename):
        """Determine if file is video or image"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith(self.VIDEO_EXTENSIONS):
            return 'video'
        elif filename_lower.endswith(self.IMAGE_EXTENSIONS):
            return 'image'
        else:
            return 'unknown'
    
    def list_assets(self):
        """List all asset files in the assets folder"""
        assets = []
        
        try:
            for file in os.listdir(self.assets_folder):
                if file.lower().endswith(self.ALL_EXTENSIONS):
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
    
    def track_card_scan(self, card_id, is_mapped=True):
        """Track RFID card scan for management purposes"""
        current_time = datetime.now().isoformat()
        
        if card_id not in self.scanned_cards:
            self.scanned_cards[card_id] = {
                'first_seen': current_time,
                'last_seen': current_time,
                'scan_count': 1,
                'mapped': is_mapped
            }
        else:
            self.scanned_cards[card_id]['last_seen'] = current_time
            self.scanned_cards[card_id]['scan_count'] += 1
            self.scanned_cards[card_id]['mapped'] = is_mapped
        
        # Also track unknown cards separately
        if not is_mapped:
            if card_id not in self.unknown_cards:
                self.unknown_cards[card_id] = {
                    'first_seen': current_time,
                    'last_seen': current_time,
                    'scan_count': 1
                }
            else:
                self.unknown_cards[card_id]['last_seen'] = current_time
                self.unknown_cards[card_id]['scan_count'] += 1

    def update_card_mapping_status(self):
        """Update card mapping status based on current config"""
        try:
            # Get current card mappings from config
            from importlib import reload
            import config
            reload(config)  # Reload to get latest changes
            
            current_mappings = getattr(config, 'CARD_ASSETS', {})
            
            # Update mapping status for all tracked cards
            for card_id in self.scanned_cards:
                is_mapped = card_id in current_mappings
                self.scanned_cards[card_id]['mapped'] = is_mapped
                
                # Remove from unknown_cards if now mapped
                if is_mapped and card_id in self.unknown_cards:
                    del self.unknown_cards[card_id]
                    
            logger.info(f"Updated card mapping status. {len(current_mappings)} cards mapped.")
            
        except Exception as e:
            logger.error(f"Error updating card mapping status: {e}")

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
    
    def handle_client_disconnect(self, operation="request"):
        """Handle client disconnection gracefully"""
        logger.debug(f"Client disconnected during {operation}")
    
    def handle_server_error(self, error, operation="operation"):
        """Handle server errors consistently"""
        logger.error(f"Error during {operation}: {error}")
        try:
            self.send_safe_response(500, 'text/plain', 'Internal server error')
        except:
            pass
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/':
                self.serve_web_player()
            elif self.path == '/manage':
                self.serve_management_interface()
            elif self.path == '/config':
                self.get_config()
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
            elif self.path == '/scanned-cards':
                # Return all scanned cards (both mapped and unknown)
                response = {
                    "scanned_cards": self.asset_server.scanned_cards,
                    "unknown_cards": self.asset_server.unknown_cards,
                    "total_scanned": len(self.asset_server.scanned_cards),
                    "total_unknown": len(self.asset_server.unknown_cards)
                }
                self.send_json_response(response)
            elif self.path == '/unknown-cards':
                # Return only unknown cards
                self.send_json_response({
                    "unknown_cards": self.asset_server.unknown_cards,
                    "count": len(self.asset_server.unknown_cards)
                })
            else:
                self.send_safe_response(404, 'text/plain', 'Not Found')
                
        except (ConnectionResetError, BrokenPipeError, socket.error):
            self.handle_client_disconnect()
        except Exception as e:
            self.handle_server_error(e)
    
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
                    card_id = data.get('card_id', '')
                    asset_file = data.get('asset_file', '')  # Optional - for backward compatibility
                    asset_index = data.get('asset_index', None)  # Optional - to specify which asset
                    
                    if not card_id:
                        self.send_safe_response(400, 'text/plain', 'No card_id specified')
                        return
                    
                    logger.info(f"RFID Card {card_id} scanned")
                    
                    # Use new multi-asset method
                    success = self.asset_server.play_card_asset(card_id, asset_index)
                    
                    if success:
                        asset_info = self.asset_server.last_asset_info
                        response = {
                            "success": True,
                            "card_id": card_id,
                            "asset_file": asset_info['asset_file'],
                            "asset_index": asset_info['asset_index'],
                            "total_assets": asset_info['total_assets'],
                            "message": f"Asset triggered: {asset_info['asset_file']} ({asset_info['asset_index'] + 1}/{asset_info['total_assets']})",
                            "timestamp": datetime.now().isoformat(),
                            "web_player_url": f"http://{self.headers.get('Host', 'localhost')}/"
                        }
                    else:
                        response = {
                            "success": False,
                            "card_id": card_id,
                            "message": f"Failed to trigger assets for card {card_id}",
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    self.send_json_response(response)
                    
                except json.JSONDecodeError:
                    self.send_safe_response(400, 'text/plain', 'Invalid JSON')
                except Exception as e:
                    logger.error(f"Error handling play request: {e}")
                    self.send_safe_response(500, 'text/plain', 'Internal server error')
            elif self.path == '/upload':
                self.handle_file_upload()
            elif self.path == '/update-config':
                self.handle_config_update()
            elif self.path == '/rename-file':
                self.handle_file_rename()
            elif self.path == '/delete-file':
                self.handle_file_delete()
            elif self.path == '/unknown-card':
                self.handle_unknown_card()
            elif self.path == '/navigate':
                self.handle_navigation()
            elif self.path == '/card-removed':
                self.handle_card_removal()
            else:
                self.send_safe_response(404, 'text/plain', 'Not Found')
                
        except (ConnectionResetError, BrokenPipeError, socket.error):
            self.handle_client_disconnect()
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")

    def serve_management_interface(self):
        """Serve the management interface HTML file"""
        try:
            web_manager_path = os.path.join(os.path.dirname(__file__), 'web_manager.html')
            with open(web_manager_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_safe_response(200, 'text/html; charset=utf-8', content)
            
        except FileNotFoundError:
            self.send_safe_response(404, 'text/plain', 'Management interface not found')
        except Exception as e:
            logger.error(f"Error serving management interface: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def get_config(self):
        """Get the current config.py contents"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.py')
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            response = {
                "config": config_content,
                "card_assets": self.get_card_assets()
            }
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error reading config: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def get_card_assets(self):
        """Get the current CARD_ASSETS mapping"""
        try:
            from config import CARD_ASSETS
            return CARD_ASSETS
        except:
            return {}

    def handle_file_upload(self):
        """Handle file upload requests"""
        try:
            content_type = self.headers['Content-Type']
            if not content_type.startswith('multipart/form-data'):
                self.send_safe_response(400, 'text/plain', 'Invalid content type')
                return

            # Get the boundary
            boundary = content_type.split('=')[1].encode()
            remainbytes = int(self.headers['Content-Length'])
            line = self.rfile.readline()
            remainbytes -= len(line)

            if not boundary in line:
                self.send_safe_response(400, 'text/plain', 'Invalid boundary')
                return

            # Get filename from Content-Disposition header
            line = self.rfile.readline()
            remainbytes -= len(line)
            filename = line.decode().split('filename=')[1].strip().strip('"')

            # Skip headers
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if line == b'\r\n':
                    break

            # Write file
            filepath = os.path.join(self.asset_server.assets_folder, filename)
            with open(filepath, 'wb') as f:
                while remainbytes > 0:
                    line = self.rfile.readline()
                    remainbytes -= len(line)
                    if boundary in line:
                        break
                    f.write(line)

            self.send_json_response({"status": "success", "filename": filename})
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def handle_config_update(self):
        """Handle config.py update requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            config_path = os.path.join(os.path.dirname(__file__), 'config.py')
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(data['config'])
            
            # Update card mapping status after config change
            self.asset_server.update_card_mapping_status()
            
            self.send_json_response({"status": "success"})
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def handle_file_rename(self):
        """Handle file rename requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            old_filename = data.get('old_filename')
            new_filename = data.get('new_filename')
            
            if not old_filename or not new_filename:
                self.send_safe_response(400, 'text/plain', 'Missing filename parameters')
                return
            
            old_path = os.path.join(self.asset_server.assets_folder, old_filename)
            new_path = os.path.join(self.asset_server.assets_folder, new_filename)
            
            if not os.path.exists(old_path):
                self.send_safe_response(404, 'text/plain', 'File not found')
                return
            
            if os.path.exists(new_path):
                self.send_safe_response(409, 'text/plain', 'File with new name already exists')
                return
            
            # Rename the file
            os.rename(old_path, new_path)
            
            self.send_json_response({
                "status": "success", 
                "old_filename": old_filename,
                "new_filename": new_filename
            })
            
        except Exception as e:
            logger.error(f"Error renaming file: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def handle_file_delete(self):
        """Handle file deletion requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            filename = data.get('filename')
            
            if not filename:
                self.send_safe_response(400, 'text/plain', 'Missing filename parameter')
                return
            
            file_path = os.path.join(self.asset_server.assets_folder, filename)
            
            if not os.path.exists(file_path):
                self.send_safe_response(404, 'text/plain', 'File not found')
                return
            
            # Delete the file
            os.remove(file_path)
            
            self.send_json_response({
                "status": "success", 
                "filename": filename,
                "message": f"File '{filename}' deleted successfully"
            })
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def handle_unknown_card(self):
        """Handle unknown card scan requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            card_id = data.get('card_id')
            
            if not card_id:
                self.send_safe_response(400, 'text/plain', 'Missing card_id parameter')
                return
            
            logger.info(f"Unknown card {card_id} scanned")
            
            self.asset_server.track_card_scan(card_id, is_mapped=False)
            
            self.send_json_response({
                "status": "success",
                "card_id": card_id,
                "message": f"Card {card_id} marked as unknown"
            })
            
        except Exception as e:
            logger.error(f"Error handling unknown card scan: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def handle_navigation(self):
        """Handle navigation through card assets"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            card_id = data.get('card_id')
            direction = data.get('direction')
            
            if not card_id:
                self.send_safe_response(400, 'text/plain', 'Missing card_id parameter')
                return
                
            if direction not in ['next', 'prev']:
                self.send_safe_response(400, 'text/plain', 'Invalid direction (must be "next" or "prev")')
                return
            
            success = self.asset_server.navigate_card_assets(card_id, direction)
            
            if success:
                asset_info = self.asset_server.last_asset_info
                response = {
                    "success": True,
                    "card_id": card_id,
                    "direction": direction,
                    "asset_file": asset_info['asset_file'],
                    "asset_index": asset_info['asset_index'],
                    "total_assets": asset_info['total_assets'],
                    "message": f"Navigated {direction} to {asset_info['asset_file']} ({asset_info['asset_index'] + 1}/{asset_info['total_assets']})"
                }
            else:
                response = {
                    "success": False,
                    "card_id": card_id,
                    "direction": direction,
                    "message": "Navigation failed or no multiple assets for this card"
                }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling navigation: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

    def handle_card_removal(self):
        """Handle card removal requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            card_id = data.get('card_id')
            
            if not card_id:
                self.send_safe_response(400, 'text/plain', 'Missing card_id parameter')
                return
            
            success = self.asset_server.remove_card(card_id)
            
            response = {
                "success": success,
                "card_id": card_id,
                "action": "card_removed",
                "message": f"Card {card_id} removed - returning to splash screen",
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling card removal: {e}")
            self.send_safe_response(500, 'text/plain', str(e))

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
    print("when triggered by RFID card scans from Exhibition device")
    print()
    print("Setup:")
    print("1. Put your video/image files in the 'assets' folder")
    print("2. Update Exhibition client with this server's IP")
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