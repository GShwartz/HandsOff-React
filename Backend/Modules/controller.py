from .logger import init_logger
from .commands import Commands
from .utils import Handlers
import subprocess
import threading
import platform
import json
import time
import sys
import os


class Controller:
    def __init__(self, main_path, log_path, server, reload):
        self.main_path = main_path
        self.log_path = log_path
        self.server = server
        self.reload = reload

        self.handlers = Handlers(self.log_path, self.main_path)
        self.logger = init_logger(self.log_path, __name__)

    def browse_local_files(self, ident) -> subprocess:
        self.logger.info(f'Running browse_local_files_command...')
        directory = os.path.join('static', 'images', ident)
        self.logger.debug(fr'Opening {directory}...')
        if os.path.isdir(directory):
            if platform.system() == 'Windows':
                return subprocess.Popen(rf"explorer {directory}")

            elif platform.system() == 'Linux':
                files = os.listdir(directory)
                for file_name in files:
                    file_path = os.path.join(directory, file_name)
                    files.append(file_path)

                return print(files)

            else:
                print("Unsupported operating system.")
                sys.exit(1)

    def count_files(self, matching_endpoint):
        self.logger.info("Running count_files()...")
        self.commands.shell_target = matching_endpoint.conn
        dir_path = os.path.join('static', 'images', matching_endpoint.ident)
        file_list = os.listdir(dir_path)
        return len(file_list)

    def multi_command(self, cmd, matching_endpoint, restarted, updated):
        if cmd == 'restart':
            self.logger.debug(f"Restarting {matching_endpoint.ip} | {matching_endpoint.ident}...")
            if self.commands.call_restart(matching_endpoint.conn):
                restarted.append(matching_endpoint)
                self.server.remove_lost_connection(matching_endpoint)
                self.logger.info('Restart completed.')

        if cmd == 'update':
            self.logger.debug(f"Updating {matching_endpoint.ip} | {matching_endpoint.ident}...")
            if self.commands.call_update(matching_endpoint.conn):
                updated.append(matching_endpoint)
                self.server.remove_lost_connection(matching_endpoint)
                self.logger.info(f"Update completed.")

    def handle_screenshot(self, matching_endpoint):
        self.logger.debug(f"Calling self.commands.call_screenshot()...")
        if self.commands.call_screenshot(matching_endpoint):
            self.logger.info(f"Screenshot completed.")
            message = 'Screenshot complete!'
            return True, message

        self.logger.debug(f"Screenshot failed.")
        message = 'Screenshot failed!'
        return False, message

    def handle_anydesk(self, matching_endpoint):
        self.logger.debug(f"Calling self.commands.call_anydesk()...")
        if not self.commands.call_anydesk(matching_endpoint):
            self.logger.debug(f"Anydesk missing.")
            return False, 'Anydesk missing'

        self.logger.debug(f"Anydesk running.")
        return True, 'Anydesk running.'

    def handle_teamviewer(self, matching_endpoint):
        self.logger.debug(f"Calling self.commands.call_teamviewer()...")
        if not self.commands.call_teamviewer(matching_endpoint):
            self.logger.debug(f"teamviewer missing.")
            return False, 'Teamviewer is missing.'

        else:
            self.logger.debug(f"TeamViewer running.")
            return True, 'TeamViewer running.'

    def handle_sysinfo(self, matching_endpoint):
        latest_file = self.commands.call_sysinfo(matching_endpoint)
        if latest_file:
            count = self.count_files(matching_endpoint)
            try:
                with open(latest_file, 'r') as file:
                    file_content = file.read()

                data = {
                    'type': 'system',
                    'fileName': f'{latest_file}',
                    'fileContent': f'{file_content}',
                    'notificationCount': f'{count}',
                }

                return True, data

            except Exception as e:
                return False, e

        else:
            return False, 'local dir not found'

    def handle_tasks(self, matching_endpoint):
        latest_file = self.commands.call_tasks(matching_endpoint)
        count = self.count_files(matching_endpoint)
        try:
            with open(latest_file, 'r') as file:
                file_content = file.read()

            data = {
                'type': 'tasks',
                'fileName': f'{latest_file}',
                'fileContent': f'{file_content}',
                'notificationCount': f'{count}',
            }

            return True, data

        except Exception as e:
            return False, data

    def handle_task_kill(self, matching_endpoint):
        self.commands = Commands(self.main_path, self.log_path,
                                 matching_endpoint, self.server.remove_lost_connection)

        result, message = self.commands.tasks_post_run(matching_endpoint)
        return message

    def handle_view(self, matching_endpoint):
        self.logger.debug(f"<Handle View>")
        self.logger.debug(f"{matching_endpoint}")
        self.browse_local_files(matching_endpoint.ident)
        return True, 'View message sent.'

    def handle_controller_action(self, data, restarted, updated, matching_endpoint):
        self.commands = Commands(self.main_path, self.log_path,
                                 matching_endpoint, self.server.remove_lost_connection)

        if data['action'] == 'screenshot':
            self.logger.info(f"<Screenshot>")
            result, message = self.handle_screenshot(matching_endpoint)
            self.logger.debug(f"{result} | {message}")

            if result:
                return True, message

            return False, message

        if data['action'] == 'anydesk':
            self.logger.info(f"<Anydesk>")
            result, message = self.handle_anydesk(matching_endpoint)
            self.logger.debug(f"{result} | {message}")

            if result:
                return result, message

            return False, message

        if data['action'] == 'teamviewer':
            self.logger.info(f"<Teamviewer>")
            result, message = self.handle_teamviewer(matching_endpoint)
            self.logger.debug(f"{result} | {message}")

            if result:
                return True, message

            return False, message

        if data['action'] == 'sysinfo':
            self.logger.info(f"<System Information>")
            result, message = self.handle_sysinfo(matching_endpoint)
            self.logger.debug(f"{result} | {message}")

            if result:
                return True, message

            return False, message

        if data['action'] == 'tasks':
            self.logger.info(f"<Tasks>")
            result, message = self.handle_tasks(matching_endpoint)
            self.logger.debug(f"{result} | {message}")

            if result:
                return result, message

            return False, 'Tasks failed.'

        if data['action'] == 'view':
            self.logger.info(f"<View Local Files>")
            result, message = self.handle_view(matching_endpoint)
            self.logger.debug(f"{result} | {message}")

            if result:
                return True, message

            return False, message

        if data['action'] == 'clear_local':
            self.logger.info("<Clear Local Files>")
            if self.handlers.clear_local(matching_endpoint):
                message = 'Files cleared.'
                return True, message

            else:
                message = 'Error while clearing.'
                return False, message

        if data['action'] == 'restart':
            self.logger.info("<Restart>")
            threads = []

            self.logger.debug(f"Checked items: {data.get('checkedItems')}")
            for item in data.get('checkedItems', []):
                dicted = json.loads(item)
                for endpoint in self.server.endpoints:
                    if endpoint.client_mac == dicted.get('id'):
                        thread = threading.Thread(target=self.multi_command,
                                                  args=('restart', endpoint, restarted, updated),
                                                  name=f'Restart {endpoint.conn}')
                        threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            time.sleep(1)
            self.logger.debug(f"Restarted {restarted}.")
            self.logger.debug("Reloading app...")
            self.reload()
            message = f'Multi restart sent to {restarted}.'
            return True, message

        if data['action'] == 'update':
            self.logger.info("<Update>")
            threads = []

            self.logger.debug(f"Checked items: {data.get('checkedItems')}")
            for item in data.get('checkedItems', []):
                dicted = json.loads(item)
                for endpoint in self.server.endpoints:
                    if endpoint.client_mac == dicted.get('id'):
                        thread = threading.Thread(target=self.multi_command,
                                                  args=('update', endpoint, restarted, updated),
                                                  name=f'Update {endpoint.conn}')
                        threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            self.logger.info(f"Updated {updated}.")
            self.logger.debug(f"Reloading app...")
            self.reload()
            message = f'Multi Update sent to {updated}!'
            return True, message
