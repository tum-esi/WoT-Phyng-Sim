import logging
import subprocess
import time
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK
from threading import Thread, Lock

import psutil


logger = logging.getLogger('paraview')
logger.setLevel(logging.DEBUG)


class PvServer(Thread):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PvServer, cls).__new__(cls)
        return cls._instance

    def __init__(self,
                 hostname: str = '0.0.0.0',
                 server_port: int = 11111,
                 multi_clients: bool = True,
                 client_host: str = 'opt',
                 connection_id: str = 'opt',
                 cslog: str = 'opt',
                 disable_further_connections: bool = False,
                 disable_registry: bool = False,
                 disable_xdisplay_test: bool = False,
                 enable_bt: bool = False,
                 enable_satellite_message_ids: bool = False,
                 enable_streaming: bool = False,
                 force_offscreen_rendering: bool = False,
                 force_onscreen_rendering: bool = False,
                 multi_clients_debug: bool = False,
                 print_monitors: bool = False,
                 reverse_connection: bool = False,
                 test_plugin: str = 'opt',
                 test_plugin_path: str = 'opt',
                 test_dimensions_x: str = 'opt',
                 test_dimensions_y: str = 'opt',
                 tile_mullion_x: str = 'opt',
                 tile_mullion_y: str = 'opt',
                 timeout: str = 'opt',
                 use_offscreen_rendering: str = 'opt'):
        """
        Paraview postprocessing server thread
        :param hostname: Override the hostname to be used to connect to this process. By default, the hostname is
        determined using appropriate system calls
        :param server_port: What port should the combined server use to connect to the client. (default 11111)
        :param multi_clients: Allow server to keep listening for several clients to connect to it and share the same
        visualization session
        :param client_host: Tell the data|render server the host name of the client, use with -rc
        :param connection_id: Set the ID of the server and client to make sure they match. 0 is reserved to imply none
        specified
        :param cslog: ClientServerStream log file
        :param disable_further_connections: Disable further connections after the first client connects.Does nothing
        without --multi-clients enabled
        :param disable_registry: Do not use registry when running ParaView (for testing)
        :param disable_xdisplay_test: When specified, all X-display tests and OpenGL version checks are skipped. Use
        this option if you are getting remote-rendering disabled errors and you are positive that the X environment is
        set up properly and your OpenGL support is adequate (experimental)
        :param enable_bt: Enable stack trace signal handler
        :param enable_satellite_message_ids: When specified, server side messages shown on client show rank of
        originating process
        :param enable_streaming: EXPERIMENTAL: When specified, view-based streaming is enabled for certain views and
        representation types
        :param force_offscreen_rendering: If supported by the build and platform, create headless (offscreen) render
        windows for rendering results
        :param force_onscreen_rendering: If supported by the build and platform, create on-screen render windows for
        rendering results
        :param multi_clients_debug: Allow server to keep listening for several clients to connect to it and share the
        same visualization session.While keeping the error macro on the server session for debug
        :param print_monitors: Print detected monitors and exit (Windows only)
        :param reverse_connection: Have the server connect to the client
        :param test_plugin: Specify the name of the plugin to load for testing
        :param test_plugin_path: Specify the path where more plugins can be found.This is typically used when testing
        plugins
        :param test_dimensions_x: Size of tile display in the number of displays in each row of the display
        :param test_dimensions_y: Size of tile display in the number of displays in each column of the display
        :param tile_mullion_x: Size of the gap between columns in the tile display, in pixels
        :param tile_mullion_y: Size of the gap between rows in the tile display, in pixels
        :param timeout: Time (in minutes) since connecting with a client after which the server may timeout. The client
        typically shows warning messages before the server times out
        :param use_offscreen_rendering: Render offscreen on the satellite processes. This option only works with
        software rendering or mangled Mesa on Unix
        """
        self.hostname = hostname
        self.server_port = server_port
        self.multi_clients = multi_clients
        self.client_host = client_host
        self.connection_id = connection_id
        self.cslog = cslog
        self.disable_further_connections = disable_further_connections
        self.disable_registry = disable_registry
        self.disable_xdisplay_test = disable_xdisplay_test
        self.enable_bt = enable_bt
        self.enable_satellite_message_ids = enable_satellite_message_ids
        self.enable_streaming = enable_streaming
        self.force_offscreen_rendering = force_offscreen_rendering
        self.force_onscreen_rendering = force_onscreen_rendering
        self.multi_clients_debug = multi_clients_debug
        self.print_monitors = print_monitors
        self.reverse_connection = reverse_connection
        self.test_plugin = test_plugin
        self.test_plugin_path = test_plugin_path
        self.test_dimensions_x = test_dimensions_x
        self.test_dimensions_y = test_dimensions_y
        self.tile_mullion_x = tile_mullion_x
        self.tile_mullion_y = tile_mullion_y
        self.timeout = timeout
        self.use_offscreen_rendering = use_offscreen_rendering
        self.running = False
        self._process = None
        self._lock = Lock()
        super(PvServer, self).__init__(daemon=True)

    @staticmethod
    def _to_kebab(string: str):
        """Transforms snake_case to kebab-case"""
        return string.replace('_', '-')

    def update_parameters(self, **kwargs):
        """Update server parameters"""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def dump(self) -> dict:
        """Dumps paraview simulation variables"""
        variables = {key: value for key, value in self.__dict__.items()
                     if value is not None and key[0] != '_' and key not in
                     ('running', 'additional_info', 'stop_reason', 'ident', 'name', 'native_id')}
        return variables

    def run(self) -> None:
        argv = ['/opt/paraviewopenfoam56/bin/pvserver', ]
        variables = self.dump()
        for var_name, var_val in variables.items():
            if not var_val or var_val == 'opt':
                continue
            if isinstance(var_val, bool):
                argv.append(f'--{self._to_kebab(var_name)}')
                continue
            argv.append(f'--{self._to_kebab(var_name)} {var_val}')
        self._process = subprocess.Popen(argv,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         shell=True)
        # Read stdout/stderr non-blocking
        flags = fcntl(self._process.stdout, F_GETFL)
        fcntl(self._process.stdout, F_SETFL, flags | O_NONBLOCK)
        flags = fcntl(self._process.stderr, F_GETFL)
        fcntl(self._process.stderr, F_SETFL, flags | O_NONBLOCK)
        while True:
            with self._lock:
                if line := self._process.stdout.readline():
                    text = line.rstrip().decode()
                    logger.info(text)
                    if 'Exiting' in text:
                        self.running = False
                if line := self._process.stderr.readline():
                    text = line.rstrip().decode()
                    logger.error(text)
                    if 'Broken pipe' in text:
                        self.running = False
                if not self.running:
                    break
            time.sleep(0.1)
        logger.info('PV Server exited')
        self.running = False

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        super(PvServer, self).start()

    def stop(self) -> None:
        """Stops paraview server"""
        with self._lock:
            self.running = False
        process = psutil.Process(self._process.pid)
        for proc in process.children(recursive=True):
            proc.kill()
        process.kill()

    def kill(self) -> None:
        self.stop()
        try:
            self._stop()
        except AssertionError:
            pass
