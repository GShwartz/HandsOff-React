"""
    HandsOff
    A C&C for IT Admins
    Copyright (C) 2023 Gil Shwartz

    This work is licensed under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    You should have received a copy of the GNU General Public License along with this work.
    If not, see <https://www.gnu.org/licenses/>.
"""

from flask import Flask, request, jsonify, send_from_directory, url_for, redirect, session
from dotenv import load_dotenv
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime, timezone
import threading
import platform
import argparse
import psutil
import sys
import os

from Modules.logger import init_logger
from Modules.commands import Commands
from Modules.server import Server
from Modules.utils import Handlers
from Modules.controller import Controller


class Backend:
    def __init__(self, logger, main_path, log_path, server, version, server_ip, port):
        self.logger = logger
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.version = version
        self.server_ip = server_ip
        self.port = port

        self.station = False
        self.images = {}
        self.rows = []
        self.temp = []
        self.temp_rows = []
        self.files_info = ""

        self.app = Flask(__name__)
        CORS(self.app)

        self.app.secret_key = os.getenv('SECRET_KEY')
        self.app.config['SESSION_TIMEOUT'] = 3600
        self.sio = SocketIO(self.app)

        self.controller = Controller(self.main_path, self.log_path, self.server,
                                     self.reload)
        self.handlers = Handlers(self.log_path, self.main_path)

        self._routes()

    def _routes(self):
        self.logger.info(f"Defining app routes...")
        self.sio.event('event')(self.on_event)
        self.sio.event('connect')(self.handle_connect)

        self.app.route('/images/<machine_name>/<path:filename>')(self.serve_images)
        self.app.route('/get_files', methods=['GET'])(self.get_files)

        self.app.errorhandler(404)(self.page_not_found)
        self.app.route('/')(self.index)

        self.app.route('/reload')(self.reload)
        self.app.route('/get_file_content', methods=['GET'])(self.get_file_content)
        self.app.route('/control', methods=['POST'])(self.control)
        self.app.route('/shell_data', methods=['POST', 'GET'])(self.shell_data)
        self.app.route('/kill_task', methods=['POST'])(self.task_kill)
        self.app.route('/clear_local', methods=['POST'])(self.clear_local)
        self.app.route('/discover', methods=['POST'])(self.discover)
        self.app.route('/ex_ip', methods=['GET'])(self.get_ex_ip)
        self.app.route('/wifi', methods=['POST'])(self.get_wifi)

    def on_event(self, data):
        self.logger.debug(f"Event data: {data}")
        pass

    def handle_connect(self):
        self.logger.debug(f"Connect event")
        pass

    def serve_images(self, machine_name, filename):
        # Construct the full path to the images directory
        images_dir = os.path.join(os.getenv('MAIN_PATH'), machine_name, 'images')
        return send_from_directory(images_dir, filename)

    def download_file(self, filename):
        self.logger.info(f"Serving file: {filename}...")
        return send_from_directory('static', filename, as_attachment=True)

    def page_not_found(self, error) -> jsonify:
        self.logger.error(fr'Error 404: Directory not found.')
        return jsonify({'error': 'Directory not found'}), 404

    def find_matching_endpoint(self, data) -> str:
        self.logger.debug("Finding matching endpoint...")
        try:
            matching_endpoints = [endpoint for endpoint in self.server.endpoints if
                                  endpoint.conn == self.commands.shell_target]
            return next(iter(matching_endpoints), None)

        except AttributeError as e:
            self.logger.error(f"Error while matching endpoints: {e}")
            return data['checkedItems']

    def get_files(self):
        directory = request.args.get('directory')
        self.logger.debug(f"Get Files: Directory: {directory}")
        if not directory:
            return jsonify({'error': 'Directory parameter is missing'}), 400

        images_dir = os.path.join(self.main_path, directory, 'images')
        self.logger.debug(f"Get Files: Images Dir: {images_dir}")

        try:
            # Get file names
            image_files = os.listdir(images_dir) if os.path.exists(images_dir) else []

            self.logger.debug(f"Get Files: Compiling images urls...")
            image_urls = [
                url_for('serve_images', machine_name=directory, filename=f, _external=True) for f in image_files
            ]

            return jsonify({
                'images': image_urls
            })

        except Exception as e:
            self.logger.error(f"Error while retreiving files: {e}")
            return jsonify({'error': str(e)}), 500

    def get_file_content(self):
        self.logger.info("Running get_file_content()...")
        filename = request.args.get('filename')
        with open(filename, 'r') as file:
            file_content = file.read()

        return jsonify({'fileContent': file_content})

    def count_files(self):
        self.logger.info("Running count_files()...")
        folder_details = {}

        try:
            selected_id = self.selected_row_data['client_mac']
            matching_endpoints = [ep for ep in self.server.endpoints if ep.client_mac == selected_id]

            if not matching_endpoints:
                return {'error': 'No matching endpoints found'}

            endpoint = matching_endpoints[0]
            self.commands.shell_target = endpoint.conn
            dir_path = os.path.join(self.main_path, endpoint.ident)

            for root, dirs, files in os.walk(dir_path):
                normalized_path = os.path.normpath(root)
                folder_details[normalized_path] = {
                    'numOfFiles': len(files),
                    'fileList': [os.path.join(root, file) for file in files],
                    'subFolders': dirs
                }

            self.logger.debug(f"Folder Details: {folder_details}")

        except Exception as e:
            self.logger.error(f"Error: {e}")
            return {'error': str(e)}

        return folder_details

    def control(self):
        self.logger.info(f"<Control>")

        restarted = []
        updated = []

        data = request.get_json()
        self.logger.debug(f"Command: {data}")

        matching_endpoint = self.find_matching_endpoint(data)
        self.logger.debug(f"Matching Endpoint: {matching_endpoint}.")
        if matching_endpoint:
            handler, message = self.controller.handle_controller_action(
                data, restarted, updated, matching_endpoint)
            self.logger.debug(f"Handler: {handler} | Message: {message}\n")

            if handler:
                try:
                    if message['type']:
                        return jsonify(message)

                except TypeError:
                    return jsonify({'message': message})

            self.logger.error(f"Unknown command: {data}")
            return jsonify({'message': f'Unknown command: {data}'})

        return jsonify({'message:': 'No matching endpoint found.'})

    def discover(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        self.logger.debug(f"Calling self.commands.discover({matching_endpoint})...")
        netMap = self.commands.call_discover(matching_endpoint)
        files = self.count_files()
        self.logger.info(f"Netmap: {netMap}\nFiles: {files}\n")
        return jsonify({'map': netMap, 'files': files})

    def get_ex_ip(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        self.logger.info(f"Calling commands.get_ex_ip({matching_endpoint})...")
        ip = self.commands.ex_ip(matching_endpoint)
        return jsonify({'ip': ip})

    def get_wifi(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        if not matching_endpoint:
            return jsonify({'wifi': 'No endpoint found.'})

        self.logger.info(f"Calling commands.get_nearby_wifi({matching_endpoint})...")
        networks_data, files = self.commands.get_nearby_wifi(matching_endpoint)
        return jsonify({'wifi': networks_data, 'files': files})

    def clear_local(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        isLocalCleared = self.handlers.clear_local(matching_endpoint)
        if isLocalCleared:
            return jsonify({'message': f'Local dir cleared'})

        return jsonify({'error': f'Something went wrong'})

    def task_kill(self):
        matching_endpoint = self.find_matching_endpoint(data=None)
        message = self.controller.handle_task_kill(matching_endpoint)
        return jsonify({'message': message})

    def last_boot(self, format_str='%d/%b/%y %H:%M:%S %p'):
        last_reboot = psutil.boot_time()
        last_reboot_str = datetime.fromtimestamp(last_reboot).strftime(format_str)
        return last_reboot_str

    def reload(self):
        self.logger.info("Reloading...")
        self.temp.clear()
        self.temp_rows.clear()
        self.rows.clear()
        return redirect(url_for('index'))

    def shell_data(self) -> jsonify:
        self.logger.info(f'Running shell_data...')
        if self.server.endpoints:
            self.station = True

        self.selected_row_data = request.get_json()
        self.logger.debug(f"Selected Row Data: {self.selected_row_data}")
        
        checked_value = self.selected_row_data.get('checked')
        row_value = self.selected_row_data.get('message')
        self.logger.debug(f"Checked Value: {checked_value} | Row Value: {row_value}")
        
        if row_value == 'clear_shell':
            self.station = False
            self.files_info = ""

            return jsonify({
                "data": {
                    'message': 'Shell cleared.'
                    },
                "Status": 200
            })

        if 'conn' in self.selected_row_data:
            self.logger.debug(f"Found 'conn'!")

            if self.server.endpoints:
                time_now = datetime.now(timezone.utc)
                self.logger.debug(f"Settting session login time...")
                session['login_time'] = time_now

                for endpoint in self.server.endpoints:
                    try:
                        self.logger.debug(f"Endpoint.client_mac: {endpoint.client_mac}")
                        if endpoint.client_mac == self.selected_row_data['client_mac']:
                            self.logger.debug(f"Match found!")

                            dir_path = os.path.join(self.main_path, endpoint.ident)
                            self.logger.debug(f"Dir Path: {dir_path}")

                            if not os.path.exists(dir_path):
                                self.logger.info(f"Calling 'self.handlers.handle_local_dir(endpoint)'...")
                                self.handlers.handle_local_dir(endpoint)

                            self.files_info = self.count_files()
                            self.subdirs = os.listdir(dir_path)

                    except KeyError as k:
                        self.logger.debug(f"Key error caught: {k}")
                        pass

                try:
                    self.logger.info(
                        f'row: {self.selected_row_data}\n'
                        f'station: {self.station}\n'
                        f'files_info: {self.files_info}\n'
                        f'subdirs: {self.subdirs}'
                    )
                    
                except AttributeError as a:
                    self.logger.debug(f"Attribute error caught: {a}")
                    pass

                return jsonify({
                    "data": {
                        'row': self.selected_row_data,
                        'station': self.station,
                        'files_info': self.files_info,
                        'subdirs': self.subdirs,
                        'checked': checked_value
                    },
                    "Status": 200
                })

            self.commands.shell_target = []
            self.station = False
            self.logger.info(f"No connected stations.")

            return jsonify({
                "data": {
                    "message": "No connected stations."
                },
                "Status": 200
            })

        else:
            return jsonify({
                "data": {
                    "station": self.station
                },
                "Status": 200
            })

    def index(self):
        self.logger.info(f'INDEX: User {os.getenv("USER")} logged in successfully')
        matching_endpoint = None
        self.commands = Commands(self.main_path, self.log_path, matching_endpoint,
                                self.server.remove_lost_connection)
        self.logger.debug(f'shell_target: {matching_endpoint}')

        for endpoint in self.server.endpoints:
            self.server.check_vital_signs(endpoint)

        endpoints_data = [endpoint.to_dict() for endpoint in self.server.endpoints]

        res = {
            "data": {
                "serving_on": f"{os.getenv('SERVER_URL')}:{os.getenv('WEB_PORT')}",
                "server_ip": f"{os.getenv('SERVER_IP')}",
                "server_port": f"{os.getenv('SERVER_PORT')}",
                "boot_time": f"{self.last_boot()}",
                "connected_stations": f"{len(self.server.endpoints)}",
                "endpoints": endpoints_data,
                "history": f"{self.server.connHistory}",
                "history_rows": f"{len(self.server.connHistory)}",
                "server_version": f"{self.version}"
            },
            "Status": 200
        }

        return jsonify(res)

    def run(self):
        self.sio.run(self.app, host=self.server_ip, port=self.port)


def main(**kwargs):
    logger = init_logger(kwargs.get('log_path'), __name__)

    try:
        os.makedirs(str(kwargs.get('main_path')), exist_ok=True)

    except Exception as e:
        print(f"Failed to create directory '{kwargs.get('main_path')}': {e}")
        sys.exit(1)

    try:
        with open(kwargs.get('log_path'), 'w'):
            pass

    except IOError as e:
        print(f"Failed to open file '{kwargs.get('log_path')}': {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An error occurred while trying to open file '{kwargs.get('log_path')}': {e}")
        sys.exit(1)

    server = Server(kwargs.get('server_ip'), kwargs.get('server_port'), kwargs.get('log_path'))
    backend = Backend(logger, kwargs.get('main_path'), kwargs.get('log_path'),
                      server, kwargs.get('server_version'), kwargs.get('server_ip'), kwargs.get('web_port'))

    backend_thread = threading.Thread(target=backend.run)
    backend_thread.start()
    server.listener()


def check_platform(main_path):
    if platform.system() == 'Windows':
        main_path = main_path.replace('/', '\\')
        log_path = os.path.join(main_path, os.getenv('LOG_FILE'))
        return main_path, log_path

    elif platform.system() == 'Linux':
        log_path = os.path.join(main_path, os.getenv('LOG_FILE'))
        return main_path, log_path

    else:
        print("Unsupported operating system.")
        sys.exit(1)


def load_config_from_args_and_env():
    parser = argparse.ArgumentParser(description='HandsOff-Server')
    parser.add_argument('-wp', '--web_port', type=int, help='Web port')
    parser.add_argument('-sp', '--server_port', type=int, help='Server port')
    parser.add_argument('-mp', '--main_path', type=str, help='Main path')
    parser.add_argument('-ip', '--server_ip', type=str, help='Server IP')
    args = parser.parse_args()

    load_dotenv()

    web_port = args.web_port if args.web_port else int(os.getenv('WEB_PORT'))
    server_port = args.server_port if args.server_port else int(os.getenv('SERVER_PORT'))
    main_path = args.main_path if args.main_path else str(os.getenv('MAIN_PATH'))
    server_ip = args.server_ip if args.server_ip else str(os.getenv('SERVER_IP'))
    server_version = os.getenv('SERVER_VERSION')

    local_download_path = os.path.join(main_path, 'LocalFiles')
    if not os.path.isdir(local_download_path):
        try:
            os.makedirs(local_download_path)
        except Exception as e:
            print(f"Error creating '{local_download_path}': {e}")

    return web_port, server_port, main_path, server_ip, server_version, local_download_path


if __name__ == '__main__':
    web_port, server_port, main_path, server_ip, server_version, local_download_path = load_config_from_args_and_env()
    main_path, log_path = check_platform(main_path)

    kwargs = {
        'web_port': web_port,
        'server_port': server_port,
        'main_path': main_path,
        'log_path': log_path,
        'server_ip': server_ip,
        'server_version': server_version,
    }

    main(**kwargs)
