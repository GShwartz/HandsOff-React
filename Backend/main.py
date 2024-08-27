from Modules import init_logger, Server, Backend, Handlers, Startup
import threading


def main(**kwargs):
    logger = init_logger(kwargs.get('log_path'), __name__)

    startup.manage_server_files(**kwargs)

    logger.info(f"Initializing Server...")
    server = Server(kwargs.get('server_ip'), kwargs.get('server_port'), kwargs.get('log_path'))
    logger.debug(f"Server: {server}")

    logger.info(f"Initializing Backend...")
    backend = Backend(kwargs.get('main_path'), kwargs.get('log_path'),
                      server, kwargs.get('server_version'), kwargs.get('server_ip'), kwargs.get('web_port'))
    logger.debug(f"Backend: {backend}")

    logger.info(f"Starting backend thread...")
    backend_thread = threading.Thread(target=backend.run)
    backend_thread.start()

    logger.info(f"Starting server listener...")
    server.listener()


if __name__ == '__main__':
    startup = Startup()
    web_port, server_port, main_path, server_ip, server_version, local_download_path = startup.load_cfg()
    handler = Handlers(main_path=main_path, log_path=None)
    main_path, log_path = handler.check_platform()
    

    kwargs = {
        'web_port': web_port,
        'server_port': server_port,
        'main_path': main_path,
        'log_path': log_path,
        'server_ip': server_ip,
        'server_version': server_version,
        'download_dir': local_download_path
    }

    main(**kwargs)
