import os
import werkzeug.datastructures
from flask_restful import Resource, reqparse

from .case import auto_load_case
from .exceptions import catch_error
from wopsimulator.loader import save_case

COMMAND_HELP = 'help'
COMMAND_LIST = 'list'
COMMAND_CREATE = 'create'
COMMAND_LOAD = 'load'
COMMAND_MOD = 'modify'
COMMAND_SAVE = 'save'
COMMAND_CLEAN = 'clean'
COMMAND_SETUP = 'setup'
COMMAND_RUN = 'run'
COMMAND_STOP = 'stop'
COMMAND_PROCESS = 'postprocess'
COMMAND_SIMULATION_TIME = 'time'
COMMAND_UPLOAD_STL = 'uploadSTL'

COMMANDS = {
    COMMAND_HELP: 'Returns this JSON',
    COMMAND_SAVE: 'Saves case configuration',
    COMMAND_CLEAN: 'Cleans case',
    COMMAND_SETUP: 'Setups case',
    COMMAND_RUN: 'Runs case',
    COMMAND_STOP: 'Stops case',
    COMMAND_PROCESS: 'Post-process case',
    COMMAND_SIMULATION_TIME: 'Current real, simulation time of a case and their difference',
    COMMAND_UPLOAD_STL: 'Upload STL geometry of a Phyng'
}


class Command(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('fields', type=list, help='Fields to post-process', location='json')
        self.reqparse.add_argument('region', type=str, help='Region to post-process')
        self.reqparse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files',
                                   help="Custom STL geometry")
        self.reqparse.add_argument('stl_name', type=str, help='Custom STL geometry name')
        super(Command, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name, command):
        if command not in COMMANDS:
            return f'Command {command} is not defined', 400
        elif command == COMMAND_SIMULATION_TIME:
            return self.current_cases[case_name].get_time()
        return COMMANDS[command]

    @catch_error
    @auto_load_case
    def post(self, case_name, command):
        if command == COMMAND_HELP:
            return COMMANDS
        if command == COMMAND_SAVE:
            save_case(case_name, self.current_cases[case_name])
        elif command == COMMAND_CLEAN:
            self.current_cases[case_name].clean_case()
            save_case(case_name, self.current_cases[case_name])
        elif command == COMMAND_SETUP:
            self.current_cases[case_name].setup()
            save_case(case_name, self.current_cases[case_name])
        elif command == COMMAND_RUN:
            self.current_cases[case_name].run()
            save_case(case_name, self.current_cases[case_name])
        elif command == COMMAND_STOP:
            self.current_cases[case_name].stop()
            save_case(case_name, self.current_cases[case_name])
        elif command == COMMAND_PROCESS:
            args = self.reqparse.parse_args()
            print(args)
            if self.current_cases[case_name].running:
                self.current_cases[case_name].stop()
            if self.current_cases[case_name].parallel:
                if not args['region']:
                    self.current_cases[case_name].run_reconstruct(all_regions=True)
                else:
                    self.current_cases[case_name].run_reconstruct(region=args['region'], fields=args['fields'])
        elif command == COMMAND_UPLOAD_STL:
            args = self.reqparse.parse_args()
            file = args['file']
            if file and '.stl' in file.filename:
                geometry_path = f'{self.current_cases[case_name].path}/geometry'
                os.makedirs(geometry_path, exist_ok=True)
                file.save(f'{geometry_path}/{file.filename}')
                return '', 200
        else:
            return 'Command not found', 404
        return '', 200
