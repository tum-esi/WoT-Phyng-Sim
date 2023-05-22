import os
import json
import traceback
from datetime import datetime

from flask_restful import Resource

import wopsimulator.openfoam.pyfoam_runner
from wopsimulator.exceptions import CaseTypeError, CaseNotFound, CaseAlreadyExists, WrongPhyngType, PhyngNotFound

ERROR_FILE = 'errors.json'
ERROR_FILEPATH = os.path.abspath(f'{os.path.dirname(os.path.abspath(__file__))}/../{ERROR_FILE}')

ERR_TEXT_KEY = 'texts'
ERR_TRACE_KEY = 'traces'

simulator_exceptions = {
    ERR_TEXT_KEY: [],
    ERR_TRACE_KEY: []
}


def load_exceptions():
    """Loads exceptions from error file"""
    global simulator_exceptions
    if os.path.exists(ERROR_FILEPATH):
        try:
            with open(ERROR_FILEPATH, 'r') as f:
                error_json = dict(json.load(f))
            if ERR_TEXT_KEY in error_json and ERR_TRACE_KEY in error_json:
                simulator_exceptions[ERR_TEXT_KEY] = error_json[ERR_TEXT_KEY][:]
                simulator_exceptions[ERR_TRACE_KEY] = error_json[ERR_TRACE_KEY][:]
        except Exception:
            pass


load_exceptions()


def dump_exceptions():
    """Dumps exceptions to error file"""
    global simulator_exceptions
    with open(ERROR_FILEPATH, 'w') as f:
        json.dump(simulator_exceptions, f, ensure_ascii=False, indent=2)


def log_error(error: BaseException):
    """Error logger function"""
    global simulator_exceptions
    time_now = datetime.now()
    error_text = f'{time_now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}: {error}'
    tb = error.__traceback__
    traceback.print_exception(type(error), error, tb)
    error_traceback = traceback.format_exception(type(error), error, tb)
    simulator_exceptions[ERR_TEXT_KEY].insert(0, error_text)
    simulator_exceptions[ERR_TRACE_KEY].insert(0, error_traceback)
    dump_exceptions()


wopsimulator.openfoam.pyfoam_runner.error_callback = log_error


def catch_error(func):
    """
    WoP Flask error catching decorator
    :param func: function to decorate
    :return: Flask response
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (CaseTypeError, CaseAlreadyExists, WrongPhyngType,) as e:
            error, status = e, 400
        except (CaseNotFound, PhyngNotFound) as e:
            error, status = e, 404
        except Exception as e:
            error, status = e, 500
        log_error(error)
        return str(error), status

    return wrapper


class ErrorList(Resource):

    @staticmethod
    def get():
        global simulator_exceptions
        temp = dict(simulator_exceptions)
        for key, lst in temp.items():
            temp[key] = list(lst)
        return temp

    @staticmethod
    def delete():
        global simulator_exceptions
        simulator_exceptions[ERR_TEXT_KEY].clear()
        simulator_exceptions[ERR_TRACE_KEY].clear()
        dump_exceptions()
