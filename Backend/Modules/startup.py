from dotenv import load_dotenv
import argparse
import sys
import os


class Startup:
    def load_cfg(self):
        parser = argparse.ArgumentParser(description='HandsOff-Server')
        parser.add_argument('-wp', '--web_port', type=int, help='Web port')
        parser.add_argument('-sp', '--server_port', type=int, help='Server port')
        parser.add_argument('-mp', '--main_path', type=str, help='Main path')
        parser.add_argument('-ip', '--server_ip', type=str, help='Server IP')
        parser.add_argument('-dd', '--download-dir', type=str, help='Store files to download from the server')
        args = parser.parse_args()

        try:
            load_dotenv()

            web_port = args.web_port if args.web_port else int(os.getenv('WEB_PORT'))
            server_port = args.server_port if args.server_port else int(os.getenv('SERVER_PORT'))
            main_path = args.main_path if args.main_path else str(os.getenv('MAIN_PATH'))
            server_ip = args.server_ip if args.server_ip else str(os.getenv('SERVER_IP'))
            download_dir = args.download_dir if args.download_dir else str(os.getenv('DOWNLOAD_DIR'))
            download_path = os.path.join(main_path, download_dir)
            server_version = os.getenv('SERVER_VERSION')
        
        except Exception as e:
            print(f"Error while loading environment: {e}")
            exit(1)

        return web_port, server_port, main_path, server_ip, server_version, download_path


    def manage_server_files(self, **kwargs):
        try:
            os.makedirs(str(kwargs.get('main_path')), exist_ok=True)

        except Exception as e:
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

        if not os.path.isdir(kwargs.get('download_dir')):
            try:
                os.makedirs(kwargs.get('download_dir'))

            except Exception as e:
                print(f"Error creating '{kwargs.get('download_dir')}': {e}")
