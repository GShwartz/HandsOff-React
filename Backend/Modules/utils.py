from Modules.logger import init_logger
import platform
import sys
import os


class Handlers:
    def __init__(self,  log_path, main_path):
        self.log_path = log_path
        self.main_path = main_path
        self.logger = init_logger(self.log_path, __name__)

    def handle_local_dir(self, matching_endpoint):
        self.ident_path = os.path.join(self.main_path, matching_endpoint.ident)
        self.logger.debug(f"Ident Path: {self.ident_path}")

        paths = ["images"]
        if not os.path.isdir(self.ident_path):
            self.logger.info(f"Directory '{self.ident_path}' does not exist.")

            try:
                self.logger.debug(f"Creating Directory '{self.ident_path}'...")
                os.makedirs(self.ident_path, exist_ok=True)
                self.logger.debug(f"Directory '{self.ident_path}' created successfully.")

            except Exception as e:
                self.logger.error(f"Error creating {self.ident_path}. {e}")

            for path in paths:
                sub_dir_path = os.path.join(self.ident_path, path)
                self.logger.debug(f"Subdir path: {sub_dir_path}")

                if not os.path.isdir(sub_dir_path):
                    self.logger.debug(f"Subdir path '{sub_dir_path}' does not exist.")

                    try:
                        self.logger.debug(f"Creating Subdir '{sub_dir_path}'...")
                        os.makedirs(sub_dir_path, exist_ok=True)
                        self.logger.debug(f"Successfully created subdir '{sub_dir_path}'.")

                    except Exception as e:
                        self.logger.error(f"Failed to create subdir '{sub_dir_path}': {e}")
                        sys.exit(1)
        
        return self.ident_path

    def clear_local(self, matching_endpoint):
        self.logger.info(f"Running 'clear_local'...")
        
        def remove_files_from_path(path):
            if os.path.isdir(path):
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    if os.path.islink(file_path):
                        # Remove symbolic link
                        self.logger.debug(f"Removing symbolic link '{file_path}'...")
                        os.unlink(file_path)
                        self.logger.debug(f"'{file_path}' removed successfully.")

                    elif os.path.isdir(file_path):
                        # Recursively handle the subdirectory but do not remove it
                        remove_files_from_path(file_path)

                    else:
                        # Remove the file
                        self.logger.debug(f"Removing file '{file_path}'...")
                        self.remove_file(file_path)
                        self.logger.debug(f"File '{file_path}' removed successfully.")

                return True
            
            return False

        path = os.path.join(self.main_path, matching_endpoint.ident)
        self.logger.debug(f"Clear path: {path}")
        
        if remove_files_from_path(path):
            return True

        return False
