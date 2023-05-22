import json

import werkzeug.datastructures
from flask_restful import Resource, reqparse

from .case import auto_load_case
from .exceptions import catch_error
from wopsimulator.loader import save_case
from wopsimulator.exceptions import PhyngNotFound

from wopsimulator.variables import CONFIG_PHYNG_NAME_K, CONFIG_PHYNG_TYPE_K, CONFIG_PHYNG_DIMS_K, CONFIG_PHYNG_LOC_K, \
    CONFIG_PHYNG_ROT_K, CONFIG_PHYNG_STL_K, CONFIG_PHYNG_MAT_K, CONFIG_PHYNG_FIELD_K


class PhyngList(Resource):
    current_cases = None

    @catch_error
    @auto_load_case
    def get(self, case_name):
        obj_list = []
        for obj in self.current_cases[case_name].get_phyngs().values():
            dump = obj.dump_settings()
            if CONFIG_PHYNG_NAME_K not in dump.keys():
                name = list(dump.keys())[0]
                dump = list(dump.values())[0]
                dump[CONFIG_PHYNG_NAME_K] = name
            dump[CONFIG_PHYNG_TYPE_K] = obj.type_name
            obj_list.append(dump)
        return obj_list


class Phyng(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(CONFIG_PHYNG_NAME_K, type=str, help='Phyng name')
        self.reqparse.add_argument(CONFIG_PHYNG_TYPE_K, type=str, help='Phyng type')
        self.reqparse.add_argument(CONFIG_PHYNG_DIMS_K, type=list, help='Phyng dimensions', location='json')
        self.reqparse.add_argument(CONFIG_PHYNG_LOC_K, type=list, help='Phyng location', location='json')
        self.reqparse.add_argument(CONFIG_PHYNG_ROT_K, type=list, help='Phyng rotation', location='json')
        self.reqparse.add_argument(CONFIG_PHYNG_STL_K, type=str, help='Phyng geometry STL name (uploaded or template)')
        self.reqparse.add_argument(CONFIG_PHYNG_MAT_K, type=str, help='Phyng material')
        self.reqparse.add_argument(CONFIG_PHYNG_FIELD_K, type=str, help='Sensor field')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_DIMS_K}_in', type=list, help='Phyng dimensions', location='json')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_LOC_K}_in', type=list, help='Phyng location', location='json')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_ROT_K}_in', type=list, help='Phyng rotation', location='json')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_STL_K}_in', type=str,
                                   help='Phyng geometry STL name (uploaded or template)')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_DIMS_K}_out', type=list, help='Phyng dimensions', location='json')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_LOC_K}_out', type=list, help='Phyng location', location='json')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_ROT_K}_out', type=list, help='Phyng rotation', location='json')
        self.reqparse.add_argument(f'{CONFIG_PHYNG_STL_K}_out', type=str,
                                   help='Phyng geometry STL name (uploaded or template)')
        super(Phyng, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name, phyng_name):
        obj = self.current_cases[case_name].get_phyng(phyng_name)
        return obj.dump_settings()

    @catch_error
    @auto_load_case
    def post(self, case_name, phyng_name):
        args = self.reqparse.parse_args()
        params = {**args, CONFIG_PHYNG_NAME_K: phyng_name}
        self.current_cases[case_name].add_phyng(**params)
        save_case(case_name, self.current_cases[case_name])
        return '', 201

    @catch_error
    @auto_load_case
    def patch(self, case_name, phyng_name):
        params = self.reqparse.parse_args()
        if phyng_name in self.current_cases[case_name].phyngs or phyng_name in self.current_cases[case_name].sensors:
            self.current_cases[case_name].modify_phyng(phyng_name, params)
            save_case(case_name, self.current_cases[case_name])
            return '', 200
        raise PhyngNotFound(f'Phyng {phyng_name} does not exist in case {case_name}')

    @catch_error
    @auto_load_case
    def delete(self, case_name, phyng_name):
        if phyng_name in self.current_cases[case_name].phyngs or phyng_name in self.current_cases[case_name].sensors:
            self.current_cases[case_name].remove_phyng(phyng_name)
            save_case(case_name, self.current_cases[case_name])
            return '', 200
        raise PhyngNotFound(f'Phyng {phyng_name} does not exist in case {case_name}')


class PhyngValue(Resource):
    current_cases = None

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('value', type=str, help='Phyng value')
        super(PhyngValue, self).__init__()

    @catch_error
    @auto_load_case
    def get(self, case_name, phyng_name, phyng_value):
        obj = self.current_cases[case_name].get_phyng(phyng_name)
        if phyng_value in obj:
            return obj[phyng_value]
        # TODO: move this error
        raise KeyError(f'Property "{phyng_value}" for phyng "{phyng_name} does not exist')

    @catch_error
    @auto_load_case
    def post(self, case_name, phyng_name, phyng_value):
        value = self.reqparse.parse_args(strict=True)['value']
        phyng = self.current_cases[case_name].get_phyng(phyng_name)
        if phyng_value in phyng:
            phyng[phyng_value] = json.loads(value)
            return '', 200
        # TODO: move this error
        raise KeyError(f'Property "{phyng_value}" for phyng "{phyng_name} does not exist')
