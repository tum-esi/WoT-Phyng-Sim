import atexit
import os
import signal
import configparser

from flask import Flask
from flask_restful import Api

from server_resources.exceptions import ErrorList
from server_resources.case import Case, CaseList
from server_resources.commands import Command
from server_resources.phyng import Phyng, PhyngList, PhyngValue
from server_resources.postprocess import Postprocess


class Server:
    def __init__(self, host, port, debug):
        self.host = host
        self.port = port
        self.debug = debug
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.current_cases = {}
        Case.current_cases = self.current_cases
        Command.current_cases = self.current_cases
        PhyngList.current_cases = self.current_cases
        Phyng.current_cases = self.current_cases
        PhyngValue.current_cases = self.current_cases
        self.api.add_resource(Command, '/case/<string:case_name>/<string:command>', endpoint='command')
        self.api.add_resource(CaseList, '/case', endpoint='cases')
        self.api.add_resource(Case, '/case/<string:case_name>', endpoint='case')
        self.api.add_resource(PhyngList, '/case/<string:case_name>/phyng/', endpoint='phyngs')
        self.api.add_resource(Phyng, '/case/<string:case_name>/phyng/<string:phyng_name>', endpoint='phyng')
        self.api.add_resource(PhyngValue, '/case/<string:case_name>/phyng/<string:phyng_name>/<string:phyng_value>',
                              endpoint='phyng_value')
        self.api.add_resource(ErrorList, '/errors')
        self.api.add_resource(Postprocess, '/postprocess', '/postprocess/<string:command>')

    def run(self):
        self.app.run(self.host, self.port, self.debug)


def atexit_handler():
    try:
        os.killpg(os.getpid(), signal.SIGINT)
    except ProcessLookupError:
        pass


def main():
    # Kill all spawned processes before exiting
    atexit.register(atexit_handler)
    config = configparser.ConfigParser()
    config.read(f'{os.path.dirname(os.path.abspath(__file__))}/server.ini')
    server = Server(host=config['DEFAULT']['Host'],
                    port=config.getint('DEFAULT', 'Port'),
                    debug=config.getboolean('DEFAULT', 'Debug'))
    server.run()


if __name__ == '__main__':
    main()
