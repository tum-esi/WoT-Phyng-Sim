from flask_restful import Resource, reqparse

from paraview_server import PvServer

PP_START = 'start'
PP_STOP = 'stop'
PP_HELP = 'help'
PP_COMMANDS = [PP_START, PP_STOP, PP_HELP]

PP_HELP_STRING = f'Make a POST request with command "{PP_START}" to start postprocessing server.\n' \
                 f'Make a POST request with command "{PP_STOP}" to stop.\n' \
                 f'Make a PUT request with parameters in body to update postprocessing server parameters.\n' \
                 f'Make a GET request to get current postprocessing server parameters.\n' \
                 f'To run a server - following the steps described in link. Current server address is %s.'


class Postprocess(Resource):
    pvserver = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('hostname', type=str, default='opt',
                                   help='Override the hostname to be used to connect to this process. By default, the '
                                        'hostname is determined using appropriate system calls')
        self.reqparse.add_argument('server_port', type=int, default=11111,
                                   help='What port should the combined server use to connect to the client. (default '
                                        '11111)')
        self.reqparse.add_argument('multi_clients', type=bool, default=False,
                                   help='Allow server to keep listening for several clients to connect to it and share '
                                        'the same visualization session')
        self.reqparse.add_argument('client_host', type=str, default='opt',
                                   help='Tell the data|render server the host name of the client, use with -rc')
        self.reqparse.add_argument('connection_id', type=str, default='opt',
                                   help='Set the ID of the server and client to make sure they match. 0 is reserved to '
                                        'imply none specified')
        self.reqparse.add_argument('cslog', type=str, default='opt',
                                   help='ClientServerStream log file')
        self.reqparse.add_argument('disable_further_connections', type=bool, default=False,
                                   help='Disable further connections after the first client connects.Does nothing '
                                        'without --multi-clients enabled')
        self.reqparse.add_argument('disable_registry', type=bool, default=False,
                                   help='Do not use registry when running ParaView (for testing)')
        self.reqparse.add_argument('disable_xdisplay_test', type=bool, default=False,
                                   help='When specified, all X-display tests and OpenGL version checks are skipped. '
                                        'Use this option if you are getting remote-rendering disabled errors and you '
                                        'are positive that the X environment is set up properly and your OpenGL '
                                        'support is adequate (experimental)')
        self.reqparse.add_argument('enable_bt', type=bool, default=False,
                                   help='Enable stack trace signal handler')
        self.reqparse.add_argument('enable_satellite_message_ids', type=bool, default=False,
                                   help='When specified, server side messages shown on client show rank of originating '
                                        'process')
        self.reqparse.add_argument('enable_streaming', type=bool, default=False,
                                   help='EXPERIMENTAL: When specified, view-based streaming is enabled for certain '
                                        'views and representation types')
        self.reqparse.add_argument('force_offscreen_rendering', type=bool, default=False,
                                   help='If supported by the build and platform, create headless (offscreen) render '
                                        'windows for rendering results')
        self.reqparse.add_argument('force_onscreen_rendering', type=bool, default=False,
                                   help='If supported by the build and platform, create on-screen render windows for '
                                        'rendering results')
        self.reqparse.add_argument('multi_clients_debug', type=bool, default=False,
                                   help='Allow server to keep listening for several clients toconnect to it and share '
                                        'the same visualization session.While keeping the error macro on the server '
                                        'session for debug')
        self.reqparse.add_argument('print_monitors', type=bool, default=False,
                                   help='Print detected monitors and exit (Windows only)')
        self.reqparse.add_argument('reverse_connection', type=bool, default=False,
                                   help='Have the server connect to the client')
        self.reqparse.add_argument('test_plugin', type=str, default='opt',
                                   help='Specify the name of the plugin to load for testing')
        self.reqparse.add_argument('test_plugin_path', type=str, default='opt',
                                   help='Specify the path where more plugins can be found.This is typically used when '
                                        'testing plugins')
        self.reqparse.add_argument('test_dimensions_x', type=str, default='opt',
                                   help='Size of tile display in the number of displays in each row of the display')
        self.reqparse.add_argument('test_dimensions_y', type=str, default='opt',
                                   help='Size of tile display in the number of displays in each column of the display')
        self.reqparse.add_argument('tile_mullion_x', type=str, default='opt',
                                   help='Size of the gap between columns in the tile display, in pixels')
        self.reqparse.add_argument('tile_mullion_y', type=str, default='opt',
                                   help='Size of the gap between rows in the tile display, in pixels')
        self.reqparse.add_argument('timeout', type=str, default='opt',
                                   help='Time (in minutes) since connecting with a client after which the server may '
                                        'timeout. The client typically shows warning messages before the server times '
                                        'out')
        self.reqparse.add_argument('use_offscreen_rendering', type=str, default='opt',
                                   help='Render offscreen on the satellite processes. This option only works with '
                                        'software rendering or mangled Mesa on Unix')
        super(Postprocess, self).__init__()

    def post(self, command=None):
        if not command or command not in PP_COMMANDS:
            return f'Invalid command "{command}". Valid commands are {", ".join(PP_COMMANDS)}', 400
        args = self.reqparse.parse_args()
        if command == PP_START:
            if self.__class__.pvserver.running:
                return 'Postprocessing server is already running', 208
            if self.__class__.pvserver:
                self.__class__.pvserver = None
            self.__class__.pvserver = PvServer(**args)
            self.__class__.pvserver.start()
        elif command == PP_STOP:
            self.__class__.pvserver.stop()
            self.__class__.pvserver = None

    def put(self, command=None):
        args = self.reqparse.parse_args()
        self.__class__.pvserver.update_parameters(**args)

    def get(self, command=None):
        if not self.__class__.pvserver:
            self.__class__.pvserver = PvServer()
        if not command:
            return self.__class__.pvserver.dump()
        if command == PP_HELP:
            return PP_HELP_STRING % f'{self.__class__.pvserver.hostname}:{self.__class__.pvserver.server_port}'
