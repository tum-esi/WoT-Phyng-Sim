from flask_restful import Resource, reqparse

from .exceptions import catch_error
from wopsimulator.loader import load_case, create_case, get_cases_names, save_case, remove_case

from wopsimulator.variables import CONFIG_TYPE_K, CONFIG_MESH_QUALITY_K, CONFIG_CLEAN_LIMIT_K, \
    CONFIG_PARALLEL_K, CONFIG_CORES_K, CONFIG_REALTIME_K, CONFIG_BACKGROUND_K, CONFIG_DEFAULTS, \
    CONFIG_END_TIME_K, CONFIG_BLOCKING_K


def auto_load_case(func):
    """
    WoP Flask auto case loading decorator
    :param func: function to decorate
    :return: Flask response
    """

    def wrapper(*args, **kwargs):
        if kwargs['case_name'] not in args[0].current_cases:
            print(f'Loading case {kwargs["case_name"]}...')
            args[0].current_cases[kwargs['case_name']] = load_case(kwargs['case_name'])
        return func(*args, **kwargs)

    return wrapper


class Case(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(CONFIG_TYPE_K, type=str, help='Web of Phyngs case type')
        self.reqparse.add_argument(CONFIG_MESH_QUALITY_K, type=int, help='Case mesh quality in percents')
        self.reqparse.add_argument(CONFIG_CLEAN_LIMIT_K, type=int,
                                   help='Case maximum amount of results before cleaning')
        self.reqparse.add_argument(CONFIG_BLOCKING_K, type=bool, help='Run case as blocking')
        self.reqparse.add_argument(CONFIG_PARALLEL_K, type=bool, help='Run case in parallel')
        self.reqparse.add_argument(CONFIG_CORES_K, type=int, help='Number of cores for parallel run', )
        self.reqparse.add_argument(CONFIG_REALTIME_K, type=bool,
                                   help='Case solving is done close to realtime if possible')
        self.reqparse.add_argument(CONFIG_BACKGROUND_K, type=str, help='CHT case background region material')
        self.reqparse.add_argument(CONFIG_END_TIME_K, type=int, help='Case simulation end time')
        super(Case, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name):
        return self.current_cases[case_name].dump_case()

    @catch_error
    def post(self, case_name):
        args = self.reqparse.parse_args()
        for key, default_value in CONFIG_DEFAULTS.items():
            if key in args.keys():
                args[key] = args[key] if args[key] else default_value
        case = create_case(case_name, args)
        self.current_cases[case_name] = case
        return '', 201

    @catch_error
    @auto_load_case
    def patch(self, case_name):
        args = self.reqparse.parse_args()
        for key, value in args.items():
            if value is not None:
                self.current_cases[case_name][key] = value
        save_case(case_name, self.current_cases[case_name])
        # Reload the case with new changes applied
        if not self.current_cases[case_name].initialized:
            self.current_cases[case_name].remove()
            del self.current_cases[case_name]
            self.current_cases[case_name] = load_case(case_name)

    @catch_error
    def delete(self, case_name):
        if case_name in self.current_cases:
            self.current_cases[case_name].remove()
            del self.current_cases[case_name]
        remove_case(case_name, remove_case_dir=True)


class CaseList(Resource):
    @catch_error
    def get(self):
        return get_cases_names()
