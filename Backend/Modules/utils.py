from Modules.logger import init_logger
import platform
import sys
import os


class Handlers:
    def __init__(self,  log_path, app_path):
        self.log_path = log_path
        self.app_path = app_path
        self.logger = init_logger(self.log_path, __name__)

    def handle_local_dir(self, matching_endpoint):
        self.ident_path = os.path.join(self.app_path, matching_endpoint.ident)
        paths = [f"{self.ident_path}", "images", "tasks", "sysinfo"]
        if not os.path.isdir(self.ident_path):
            for path in paths:
                try:
                    os.makedirs(str(path), exist_ok=True)

                except Exception as e:
                    print(f"Failed to create directory '{self.local_dir}': {e}")
                    sys.exit(1)

        return self.ident_path

    def clear_local(self, matching_endpoint):
        def remove_files_from_path(path):
            if os.path.isdir(path):
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    self.remove_file(file_path)
                return True
            return False

        path = os.path.join('static', 'images', matching_endpoint.ident)
        if remove_files_from_path(path):
            return True

        return False

    def remove_file(self, file_path):
        if platform.system() == 'Windows':
            try:
                os.remove(file_path)

            except OSError as e:
                print(f"Error deleting file: {e}")
                return False

        elif platform.system() == 'Linux' or platform.system() == 'Darwin':
            try:
                os.unlink(file_path)

            except OSError as e:
                print(f"Error deleting file: {e}")
                return False
        else:
            print("Unsupported platform")
            return False
