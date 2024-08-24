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
from dotenv import load_dotenv
from datetime import datetime
from threading import Thread
import dotenv
import socket
import json
import time
import os

import psycopg2
from psycopg2 import OperationalError


class Endpoints:
    def __init__(self, conn, client_mac, ip, ident, user,
                 client_version, os_release, boot_time, connection_time,
                 is_vm, hardware, hdd, external_ip, wifi):
        self.wifi = wifi
        self.external_ip = external_ip
        self.hardware = hardware
        self.hdd = hdd
        self.is_vm = is_vm
        self.boot_time = boot_time
        self.conn = conn
        self.client_mac = client_mac
        self.ip = ip
        self.ident = ident
        self.user = user
        self.client_version = client_version
        self.os_release = os_release
        self.connection_time = connection_time

    # def __repr__(self):
    #     return f"Endpoint({self.conn}, {self.client_mac}, " \
    #            f"{self.ip}, {self.ident}, {self.user}, " \
    #            f"{self.client_version}, {self.os_release}, {self.boot_time}, " \
    #            f"{self.connection_time}, {self.is_vm}, {self.hardware}, " \
    #            f"{self.hdd}, {self.external_ip}, {self.wifi})"
    
    def to_dict(self):
        return {
            "conn": f"{self.conn}",  # Convert socket object to a string representation
            "client_mac": self.client_mac,
            "ip": self.ip,
            "ident": self.ident,
            "user": self.user,
            "client_version": self.client_version,
            "os_release": self.os_release,
            "boot_time": self.boot_time,
            "connection_time": self.connection_time,
            "is_vm": self.is_vm,
            "hardware": {
                "memory": {
                    "total": self.hardware['memory']['total'],
                    "available": self.hardware['memory']['available']
                },
                "hard_drives": [
                    {
                        "device": drive['device'],
                        "mountpoint": drive['mountpoint'],
                        "filesystem_type": drive['filesystem_type'],
                        "total_size": drive['total_size'],
                        "used_space": drive['used_space'],
                        "free_space": drive['free_space'],
                        "errors": drive['errors']  # List of errors
                    } for drive in self.hardware['hard_drives']
                ]
            },
            "hdd": [
                {
                    "Drive Type": hdd['Drive Type'],
                    "Model": hdd['Model'],
                    "Media Type": hdd['Media Type']
                } for hdd in self.hdd
            ],
            "external_ip": self.external_ip,
            "wifi": self.wifi
        }
    

class Server:
    def __init__(self, ip, port, log_path):
        self.log_path = log_path
        self.port = port
        self.serverIP = ip
        self.hostname = socket.gethostname()
        self.logger = init_logger(self.log_path, __name__)

        load_dotenv()
        self.user = os.getenv('USER')
        self.password = os.getenv('PASSWORD')

        self.conn = None
        self.ip = None
        self.handshake = None
        self.fresh_endpoint = None
        self.endpoints = []
        self.connHistory = {}

        self.connect_to_db()

    def connect_to_db(self):
        self.logger.debug("Connecting to database...")
        try:
            self.db_conn = psycopg2.connect(
                dbname="hands_off",
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            self.db_cursor = self.db_conn.cursor()
            self.logger.info("Connected to DB!")

        except OperationalError as e:
            self.logger.error(f"Error connecting to DB: {e}")
            self.db_conn = None

    def listener(self) -> None:
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.logger.debug(f'Binding {self.serverIP}, {self.port}...')
        self.server.bind((self.serverIP, int(self.port)))
        self.server.listen()

        self.logger.info(f'Running run...')
        self.logger.debug(f'Starting connection thread...')
        self.connectThread = Thread(target=self.connect, daemon=True, name=f"Connect Thread")
        self.connectThread.start()

    def connect(self) -> None:
        self.logger.info(f'Running connect...')
        while True:
            if self.process_connection():
                self.logger.info(f'connect completed.')

            else:
                self.logger.error(f'Connection failed.')

    def process_connection(self) -> bool:
        try:
            self.dt = self.get_date()
            self.logger.debug(f'Accepting connection...')
            self.conn, (self.ip, self.port) = self.server.accept()
            self.logger.debug(f'Connection from {self.ip} accepted.')
            self.send_welcome_message()
            self.logger.debug(f'Waiting for handshake data...')

            self.gate_keeper = self.conn.recv(1024).decode()
            if self.gate_keeper.lower()[:6] != 'client':
                self.logger.error(f'GATE-KEEPER: {self.conn} failed.')
                self.conn.close()
                return False

            self.logger.info("Handshake completed.")
            self.logger.debug("Waiting for client data...")
            received_data = self.conn.recv(4096).decode()
            self.logger.debug(f"Client data: {received_data}")
            try:
                self.logger.debug("Loading data to JSON...")
                self.handshake = json.loads(received_data)

            except Exception as e:
                self.logger.error(e)
                return False

            self.update_data()
            return True

        except ConnectionResetError as e:
            self.logger.error(e)
            self.conn.close()
            return False

    def send_welcome_message(self) -> None:
        welcome = "Connection Established!"
        self.logger.debug(f'Sending welcome message...')
        self.conn.send(f"@Server: {welcome}".encode())
        self.logger.debug(f'"{welcome}" sent to {self.ip}.')

    def update_data(self) -> None:
        self.logger.debug(f'Defining fresh endpoint data...')
        self.logger.debug(f'Getting VM value...')
        is_vm = self.handshake.get('is_vm', False)
        try:
            is_vm_value = is_vm.get('true', 'false')
            self.logger.debug(f"VM Value: {is_vm_value}")

        except (AttributeError, TypeError) as e:
            self.logger.error(e)
            is_vm_value = "N/A"

        self.logger.debug("Compiling endpoint repr...")
        self.fresh_endpoint = Endpoints(
            self.conn, self.handshake['mac_address'], self.ip,
            self.handshake['hostname'], self.handshake['current_user'],
            self.handshake['client_version'], self.handshake['os_platform'],
            self.handshake['boot_time'], self.get_date(),
            is_vm_value, self.handshake.get('hardware'),
            self.handshake.get('hdd'), self.handshake.get('ex_ip'),
            self.handshake.get('wifi')
        )

        self.logger.info(f"Fresh Endpoint: {self.fresh_endpoint}")
        if self.fresh_endpoint not in self.endpoints:
            self.logger.debug(f'{self.fresh_endpoint} not in endpoints list.')
            self.endpoints.append(self.fresh_endpoint)

        self.logger.debug(f"Total Endpoints: {self.endpoints}")
        self.logger.debug(f'Updating connection history dict...')
        self.connHistory.update({self.fresh_endpoint: self.dt})
        self.logger.info(f'Connection history updated with: {self.fresh_endpoint}:{self.dt}')

        self.insert_into_db()

    def insert_into_db(self) -> None:
        self.logger.debug(f'Inserting endpoint data into the database...')
        try:
            insert_query = """
            INSERT INTO endpoints (
                client_mac, ip, ident, user, client_version,
                os_release, boot_time, connection_time, is_vm,
                hardware, hdd, external_ip, wifi
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            if self.db_conn is not None:
                self.db_cursor.execute(insert_query, (
                    self.fresh_endpoint.client_mac,
                    self.fresh_endpoint.ip,
                    self.fresh_endpoint.ident,
                    self.fresh_endpoint.user,
                    self.fresh_endpoint.client_version,
                    self.fresh_endpoint.os_release,
                    datetime.strptime(self.fresh_endpoint.boot_time, "%d/%b/%y %H:%M:%S"),
                    datetime.strptime(self.fresh_endpoint.connection_time, "%d/%b/%y %H:%M:%S"),
                    self.fresh_endpoint.is_vm,
                    json(self.fresh_endpoint.hardware),
                    json(self.fresh_endpoint.hdd),
                    self.fresh_endpoint.external_ip,
                    json(self.fresh_endpoint.wifi)
                ))

                self.db_conn.commit()
                self.logger.info("Endpoint data inserted into the database successfully.")

        except Exception as e:
            self.logger.error(f"Failed to insert data into the database: {e}")
            if self.db_conn is not None:
                self.db_conn.rollback()

    def get_date(self) -> str:
        d = datetime.now().replace(microsecond=0)
        dt = str(d.strftime("%d/%b/%y %H:%M:%S"))
        return dt

    def check_vital_signs(self, endpoint):
        self.callback = 'yes'
        self.logger.debug(f'Checking {endpoint.ip}...')

        try:
            endpoint.conn.send('alive'.encode())
            ans = endpoint.conn.recv(1024).decode()

        except (Exception, socket.error, UnicodeDecodeError) as e:
            self.logger.debug(f'removing {endpoint}...')
            self.remove_lost_connection(endpoint)
            return

        if str(ans) == str(self.callback):
            try:
                self.logger.debug(f'Station IP: {endpoint.ip} | Station Name: {endpoint.ident} - ALIVE!')
            except (IndexError, RuntimeError):
                return

        else:
            try:
                self.logger.debug(f'removing {endpoint}...')
                self.remove_lost_connection(endpoint)

            except (IndexError, RuntimeError):
                return

    def vital_signs(self) -> bool:
        self.logger.info(f'Running vital_signs...')
        if not self.endpoints:
            self.logger.debug(f'No endpoints.')
            return False

        self.callback = 'yes'
        threads = []
        for endpoint in self.endpoints:
            thread = Thread(target=self.check_vital_signs, args=(endpoint,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        self.logger.info(f'=== End of vital_signs() ===')
        return True

    def remove_lost_connection(self, endpoint) -> bool:
        self.logger.info(f'Running remove_lost_connection({endpoint})...')
        try:
            self.logger.debug(f'Removing {endpoint.ip}...')
            endpoint.conn.close()
            self.endpoints.remove(endpoint)

            self.logger.info(f'=== End of remove_lost_connection({endpoint}) ===')
            return True

        except (ValueError, RuntimeError) as e:
            self.logger.error(f'Error: {e}.')
