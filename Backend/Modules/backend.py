from flask import Flask, request, jsonify, send_from_directory, url_for, redirect, session
from datetime import datetime, timezone
from flask_socketio import SocketIO
from flask_cors import CORS
import os

from .controller import Controller
from .operations import Operations
from .logger import init_logger
from .commands import Commands
from .utils import Handlers


class Backend:
    def __init__(self, main_path, log_path, server, version, server_ip, port):
        self.main_path = main_path
        self.log_path = log_path
        self.logger = init_logger(self.log_path, __name__)

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
        self.operations = Operations(self)

        self._routes()

    def __str__(self):
        return (f"Backend(version={self.version}, server_ip={self.server_ip}, port={self.port}, "
                f"server={self.server}, main_path={self.main_path})")

    def __repr__(self):
        return (f"Backend(version={self.version}, server_ip={self.server_ip}, port={self.port}, "
                f"server={self.server}, main_path={self.main_path}, "
                f"station={self.station}, images_count={len(self.images)}, "
                f"rows_count={len(self.rows)}, temp_rows_count={len(self.temp_rows)})")
    
    def _routes(self):
        self.logger.info(f"Defining app routes...")

        self.app.route('/')(self.index)

        self.app.route('/control', methods=['POST'])(self.operations.control)
        self.app.route('/get_files', methods=['GET'])(self.operations.get_files)
        self.app.route('/kill_task', methods=['POST'])(self.operations.task_kill)
        self.app.route('/clear_local', methods=['POST'])(self.operations.clear_local)
        self.app.route('/discover', methods=['POST'])(self.operations.discover)
        self.app.route('/ex_ip', methods=['GET'])(self.operations.get_ex_ip)
        self.app.route('/wifi', methods=['POST'])(self.operations.get_wifi)

        self.app.route('/images/<machine_name>/<path:filename>')(self.serve_images)
        self.app.errorhandler(404)(self.page_not_found)

        self.app.route('/reload')(self.reload)
        self.app.route('/shell_data', methods=['POST', 'GET'])(self.shell_data)

    def serve_images(self, machine_name, filename):
        images_dir = os.path.join(os.getenv('MAIN_PATH'), machine_name, 'images')
        return send_from_directory(images_dir, filename)

    def download_file(self, filename):
        self.logger.info(f"Serving file: {filename}...")
        return send_from_directory('static', filename, as_attachment=True)

    def page_not_found(self, error) -> jsonify:
        self.logger.error(fr'Error 404: Directory not found.')
        return jsonify({'error': 'Directory not found'}), 404

    def find_matching_endpoint(self, data) -> str:
        self.logger.info("Finding matching endpoint...")
        try:
            matching_endpoints = [endpoint for endpoint in self.server.endpoints if
                                  endpoint.conn == self.commands.shell_target]
            return next(iter(matching_endpoints), None)

        except AttributeError as e:
            self.logger.error(f"Error while matching endpoints: {e}")
            return data['checkedItems']

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
        self.logger.debug(f"Checkboxes Value: {checked_value} | Row: {row_value}")
        
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
            self.logger.debug(f"Conn matched: {self.selected_row_data['conn']}")

            if self.server.endpoints:
                ''' Future User Management '''
                time_now = datetime.now(timezone.utc)
                self.logger.info(f"Settting session login time...")
                session['login_time'] = time_now

                for endpoint in self.server.endpoints:
                    try:
                        if endpoint.client_mac == self.selected_row_data['client_mac']:
                            self.logger.info(f"Match found: {endpoint.client_mac}")

                            dir_path = os.path.join(self.main_path, endpoint.ident)
                            self.logger.debug(f"Dir Path: {dir_path}")

                            if not os.path.exists(dir_path):
                                self.logger.info(f"Calling 'self.handlers.handle_local_dir(endpoint)'...")
                                self.handlers.handle_local_dir(endpoint)

                            self.files_info = self.operations.count_files()
                            self.subdirs = os.listdir(dir_path)

                    except KeyError as k:
                        self.logger.error(f"Key error caught: {k}")
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
        matching_endpoint = None
        self.commands = Commands(self.main_path, self.log_path, matching_endpoint,
                                 self.server.remove_lost_connection)
        self.logger.debug(f'shell_target: {matching_endpoint}')

        for endpoint in self.server.endpoints:
            self.logger.info(f"Checking vital signs on {endpoint.client_mac}...")
            self.server.check_vital_signs(endpoint)

        endpoints_data = [endpoint.to_dict() for endpoint in self.server.endpoints]
        self.logger.debug(f"Endpoints data: {endpoints_data}")

        res = {
            "data": {
                "serving_on": f"{os.getenv('SERVER_URL')}:{os.getenv('WEB_PORT')}",
                "server_ip": f"{os.getenv('SERVER_IP')}",
                "server_port": f"{os.getenv('SERVER_PORT')}",
                "boot_time": f"{self.operations.last_boot()}",
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
