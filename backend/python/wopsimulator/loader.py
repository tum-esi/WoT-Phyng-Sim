"""
Case loader
"""
import os
import json
from pathlib import Path
from typing import Union, Type

from .case_base import OpenFoamCase
from .cht_case import ChtCase
from .exceptions import CaseTypeError, CaseNotFound, CaseAlreadyExists
from .openfoam.common.filehandling import force_remove_dir, copy_tree
from .variables import CASES_STORAGE, CONFIG_PATH_K, CONFIG_TYPE_K, CUR_FILE_DIR, CONFIG_DEFAULTS, WOP_CONFIG_FILE

CASE_TYPES = {
    ChtCase.case_type: ChtCase,
}

CASE_CLS_TYPES = Union[
    Type[ChtCase],
    # Add your custom case types here
]

CASE_INST_TYPE = Union[
    ChtCase,
    # Add your custom case types here
]


def load_case(case_name: str, config_path: str = f'{CASES_STORAGE}/{WOP_CONFIG_FILE}') -> CASE_INST_TYPE:
    """
    Loads case from wop.config.json
    :param case_name: name of the loaded case
    :param config_path: path to a wop.config.json. A __main__ script directory is taken by default
    :return: WoP Simulator class instance
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    case_name = case_name if '.case' in case_name else f'{case_name}.case'
    if case_name in config.keys():
        if not (CONFIG_PATH_K in config[case_name] and os.path.exists(path := config[case_name][CONFIG_PATH_K])):
            raise CaseNotFound(f'Path for case "{case_name}" is not defined')
        if CONFIG_TYPE_K in config[case_name] and \
                (case_type_name := config[case_name][CONFIG_TYPE_K]) in CASE_TYPES.keys():
            case_cls: CASE_CLS_TYPES = CASE_TYPES[case_type_name]
        else:
            raise CaseTypeError(f'Case type is wrong or not specified! Expected one of: {", ".join(CASE_TYPES)}')
        case = case_cls(**config[case_name], loaded=True)
        return case
    raise CaseNotFound(f'Case "{case_name}" is not defined in the config "{config_path}"')


def create_case(case_name: str, case_param: dict, case_dir_path: str = CASES_STORAGE,
                config_path: str = f'{CASES_STORAGE}/{WOP_CONFIG_FILE}', replace_old: bool = False) -> CASE_INST_TYPE:
    """
    Creates a new WoP Simulator case by finding a OpenFOAM case template by a specified type, copying it to a path
    specified, and adding all this data to a wop.config.json.
    :param case_name: name of the project to name a new copied case and to refer to from wop.config.json
    :param case_param: WoP Simulator case parameters
    :param case_dir_path: OpenFOAM case creation folder path. A __main__ script directory is taken by default
    :param config_path: path to a wop.config.json. A __main__ script directory is taken by default
    :param replace_old: flag to replace the old project. Active -> files will be overwritten. Otherwise -> error
    :return: WoP Simulator class instance
    """
    if case_param[CONFIG_TYPE_K] not in CASE_TYPES.keys():
        raise CaseTypeError(f'Case type is wrong or not specified! '
                            f'Got "{case_param[CONFIG_TYPE_K]}", expected one of: {", ".join(CASE_TYPES)}')
    case_cls: CASE_CLS_TYPES = CASE_TYPES[case_param[CONFIG_TYPE_K]]

    # Load/Create config
    Path(config_path).touch(exist_ok=True)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.decoder.JSONDecodeError:
        config = {}

    # Get the case path, check if it already exists and the copy case
    case_name = case_name if '.case' in case_name else f'{case_name}.case'
    case_path = f'{case_dir_path}{"/" if case_dir_path[-1] != "/" else ""}{case_name}'
    if case_name in config.keys() or os.path.exists(case_path):
        if replace_old:
            del config[case_name]
            force_remove_dir(case_path)
        else:
            raise CaseAlreadyExists(f'Project with name "{case_name}" already exists!')
    copy_tree(f'{CUR_FILE_DIR}/openfoam/cases/{case_param[CONFIG_TYPE_K]}', case_path)

    # TODO: JSON schema validation

    case_config = CONFIG_DEFAULTS.copy()
    for key, value in case_param.items():
        case_config[key] = value
    case_config[CONFIG_PATH_K] = case_path
    config[case_name] = case_config

    with open(config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    case = case_cls(**config[case_name])
    return case


def save_case(case_name: str, case: OpenFoamCase, config_path: str = f'{CASES_STORAGE}/{WOP_CONFIG_FILE}'):
    """
    Saves WoP Simulator case parameters into wop.config.json.
    :param case_name: name of the project to name a new copied case and to refer to from wop.config.json
    :param case: name of the project to name a new copied case and to refer to from wop.config.json
    :param config_path: path to a wop.config.json. A __main__ script directory is taken by default
    """
    if (case_type := type(case)) not in CASE_TYPES.values():
        raise CaseTypeError(f'Case type is wrong or not specified! '
                            f'Got "{case_type}", expected one of: {", ".join(CASE_TYPES)}')
    config = case.dump_case()
    case_name = case_name if '.case' in case_name else f'{case_name}.case'
    with open(config_path, 'r') as f:
        config_old = json.load(f)

    config_old[case_name] = config

    with open(config_path, 'w') as f:
        json.dump(config_old, f, ensure_ascii=False, indent=2)


def remove_case(case_name: str, config_path: str = f'{CASES_STORAGE}/{WOP_CONFIG_FILE}', remove_case_dir: bool = False):
    """
    Removes case from wop.config.json (optionally OpenFOAM case dir as well)
    :param case_name: name of the case to remove
    :param config_path: path to a wop.config.json. A __main__ script directory is taken by default
    :param remove_case_dir: flag to remove a case dir by its path
    :return: None
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    case_name = case_name if '.case' in case_name else f'{case_name}.case'
    if remove_case_dir and case_name in config and os.path.exists(case_path := config[case_name][CONFIG_PATH_K]):
        force_remove_dir(case_path)
    else:
        raise CaseNotFound(f'Case "{case_name}" is not defined in the config "{config_path}"')
    del config[case_name]

    with open(config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def get_cases_names(config_path: str = f'{CASES_STORAGE}/{WOP_CONFIG_FILE}'):
    """
    Retrieve all available cases
    :param config_path: path to a wop.config.json. A __main__ script directory is taken by default
    :return: None
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return list(config.keys())
    except FileNotFoundError:
        with open(config_path, 'w') as f:
            f.write('{}\n')
    return []


def main():
    print(CUR_FILE_DIR)


if __name__ == '__main__':
    main()
