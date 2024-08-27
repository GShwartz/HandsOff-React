from flask import request, jsonify, url_for
from datetime import datetime
from .logger import init_logger
import psutil
import os


class Operations:
    def __init__(self, backend):
        self.backend = backend
        self.main_path = backend.main_path
        self.log_path = backend.log_path
        self.logger = init_logger(self.log_path, __name__)

    def control(self):
        self.logger.info(f"<Control>")

        restarted = []
        updated = []

        data = request.get_json()
        self.logger.debug(f"Command: {data}")

        matching_endpoint = self.backend.find_matching_endpoint(data)
        self.logger.debug(f"Matching Endpoint: {matching_endpoint}.")
        if matching_endpoint:
            handler, message = self.backend.controller.handle_controller_action(
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
    
    def get_files(self):
        directory = request.args.get('directory')
        self.logger.debug(f"Get Files: Directory: {directory}")
        if not directory:
            return jsonify({'error': 'Directory parameter is missing'}), 400

        images_dir = os.path.join(self.main_path, directory, 'images')
        self.logger.debug(f"Images Dir: {images_dir}")

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

    def count_files(self):
        self.logger.info("Running count_files()...")
        folder_details = {}

        try:
            selected_id = self.backend.selected_row_data['client_mac']
            matching_endpoints = [ep for ep in self.backend.server.endpoints if ep.client_mac == selected_id]

            if not matching_endpoints:
                return {'error': 'No matching endpoints found'}

            endpoint = matching_endpoints[0]
            self.backend.commands.shell_target = endpoint.conn
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

    def get_ex_ip(self):
        matching_endpoint = self.backend.find_matching_endpoint(data=None)
        self.logger.info(f"Calling commands.get_ex_ip({matching_endpoint})...")
        ip = self.backend.commands.ex_ip(matching_endpoint)
        return jsonify({'ip': ip})

    def get_wifi(self):
        matching_endpoint = self.backend.find_matching_endpoint(data=None)
        if not matching_endpoint:
            return jsonify({'wifi': 'No endpoint found.'})

        self.logger.info(f"Calling commands.get_nearby_wifi({matching_endpoint})...")
        networks_data, files = self.backend.commands.get_nearby_wifi(matching_endpoint)
        return jsonify({'wifi': networks_data, 'files': files})

    def clear_local(self):
        matching_endpoint = self.backend.find_matching_endpoint(data=None)
        isLocalCleared = self.backend.handlers.clear_local(matching_endpoint)
        if isLocalCleared:
            return jsonify({'message': f'Local dir cleared'})

        return jsonify({'error': f'Something went wrong'})

    def task_kill(self):
        matching_endpoint = self.backend.find_matching_endpoint(data=None)
        message = self.backend.controller.handle_task_kill(matching_endpoint)
        return jsonify({'message': message}) 

    def discover(self):
        matching_endpoint = self.backend.find_matching_endpoint(data=None)
        self.logger.debug(f"Calling self.commands.discover({matching_endpoint})...")
        netMap = self.backend.commands.call_discover(matching_endpoint)
        files = self.count_files()
        self.logger.info(f"Netmap: {netMap}\nFiles: {files}\n")
        return jsonify({'map': netMap, 'files': files})

    def last_boot(self, format_str='%d/%b/%y %H:%M:%S %p'):
            last_reboot = psutil.boot_time()
            last_reboot_str = datetime.fromtimestamp(last_reboot).strftime(format_str)
            return last_reboot_str