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

from Modules.logger import init_logger
from Modules.utils import Handlers
import socket
import shutil
import sys
import os


class Tasks:
    def __init__(self, path, log_path, endpoint, remove_connection):
        self.endpoint = endpoint
        self.path = path
        self.log_path = log_path
        self.remove_connection = remove_connection
        self.tasks_file_path = os.path.join(self.path, self.endpoint.ident)
        if not os.path.exists(self.tasks_file_path):
            os.makedirs(self.tasks_file_path, exist_ok=True)

        self.logger = init_logger(self.log_path, __name__)
        self.handlers = Handlers(self.log_path, self.path)
        self.local_dir = self.handlers.handle_local_dir(self.endpoint)

    def bytes_to_number(self, b: int) -> int:
        res = 0
        for i in range(4):
            res += b[i] << (i * 8)
        return res

    def kill_task(self, taskname):
        self.logger.debug(f"Running kill_task...")
        try:
            self.logger.debug(f"Sending kill command to {self.endpoint.ip}...")
            self.endpoint.conn.send('kill'.encode())

        except (Exception, socket.error) as e:
            self.handle_error(e)
            return False

        try:
            self.logger.debug(f"Sending {str(taskname)} to {self.endpoint.ip}...")
            self.endpoint.conn.send(str(taskname).encode())

        except (Exception, socket.error) as e:
            self.handle_error(e)
            return False

        try:
            self.logger.debug(f"Waiting for confirmation from {self.endpoint.ip}...")
            msg = self.endpoint.conn.recv(1024).decode()
            self.logger.debug(f"{self.endpoint.ip}: {msg}")
            return True

        except (Exception, socket.error) as e:
            self.handle_error(e)
            return False

    def get_file_name(self):
        self.logger.info(f"Running get_file_name...")
        self.logger.debug(f"Waiting for filename from {self.endpoint.ip}...")
        try:
            self.endpoint.conn.settimeout(10)
            self.filenameRecv = self.endpoint.conn.recv(1024).decode()
            self.full_file_path = os.path.join(self.tasks_file_path, self.filenameRecv)
            self.endpoint.conn.settimeout(None)
            self.logger.debug(f"Filename: {self.filenameRecv}")

        except (Exception, socket.error) as e:
            self.handle_error(e)
            return False

    def get_file_size(self):
        self.logger.info(f"Running get_file_size...")
        self.logger.debug(f"Waiting for file size from {self.endpoint.ip}...")
        try:
            self.endpoint.conn.settimeout(10)
            self.size = self.endpoint.conn.recv(4)
            self.endpoint.conn.settimeout(None)
            self.size = self.bytes_to_number(self.size)
            self.logger.debug(f"Size: {self.size}")

        except (Exception, socket.error) as e:
            self.handle_error(e)
            return False

    def get_file_content(self):
        self.logger.info(f"Running get_file_content...")
        current_size = 0
        buffer = b""
        self.logger.debug(f"Writing content to {self.full_file_path}...")
        with open(self.full_file_path, 'wb') as tsk_file:
            try:
                self.endpoint.conn.settimeout(60)
                while current_size < self.size:
                    data = self.endpoint.conn.recv(1024)
                    if not data:
                        break
                    if len(data) + current_size > self.size:
                        data = data[:self.size - current_size]
                    buffer += data
                    current_size += len(data)
                    tsk_file.write(data)

                self.endpoint.conn.settimeout(None)

            except (Exception, socket.error) as e:
                self.handle_error(e)
                return False

    def confirm(self):
        self.logger.info(f"Running confirm...")
        self.logger.debug(f"Sending confirmation to {self.endpoint.ip}...")
        try:
            self.endpoint.conn.send(f"Received file: {self.filenameRecv}\n".encode())
            return True

        except (Exception, socket.error) as e:
            self.handle_error(e)
            return False

    def handle_error(self, error):
        self.logger.debug(f"Error: {error}")
        self.logger.debug(f"Calling self.remove_connection({self.endpoint})...")
        self.remove_connection(self.endpoint)
        return False

    def run(self):
        self.logger.info(f"Running tasks.run()...")
        try:
            self.logger.debug(f"Sending tasks command to {self.endpoint.ip}...")
            self.endpoint.conn.send('tasks'.encode())

        except (Exception, socket.error) as e:
            self.handle_error(e)
            return False

        self.logger.debug(f"Calling get_file_name...")
        self.get_file_name()
        self.logger.debug(f"Calling get_file_size...")
        self.get_file_size()
        self.logger.debug(f"Calling get_file_content...")
        self.get_file_content()
        self.logger.debug(f"Calling confirm...")
        self.confirm()

        src = os.path.join(self.tasks_file_path, self.filenameRecv)
        try:
            shutil.move(src, self.local_dir)

        except shutil.Error as file_error:
            self.logger.error(file_error)
            return False, file_error

        self.logger.info(f"Tasks run completed.")
        return True, 'Tasks run completed.'
