import os
import shutil
import re

from .parsing import NUMBER_PATTERN


def force_remove_dir(src_dir):
    shutil.rmtree(src_dir, ignore_errors=True)


def force_merge_flat_dir(src_dir, dst_dir):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    for item in os.listdir(src_dir):
        src_file = os.path.join(src_dir, item)
        dst_file = os.path.join(dst_dir, item)
        force_copy_file(src_file, dst_file)


def force_copy_file(s_file, d_file):
    if os.path.isfile(s_file):
        # st = os.stat(s_file)
        shutil.copy2(s_file, d_file)
        # os.chown(d_file, st.st_uid, st.st_gid)


def is_flat_dir(s_dir):
    for item in os.listdir(s_dir):
        s_item = os.path.join(s_dir, item)
        if os.path.isdir(s_item):
            return False
    return True


def copy_tree(src, dst):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            if not os.path.exists(dst):
                os.makedirs(dst)
            force_copy_file(s, d)
        if os.path.isdir(s):
            is_recursive = not is_flat_dir(s)
            if is_recursive:
                copy_tree(s, d)
            else:
                force_merge_flat_dir(s, d)


def create_pattern(prefix: str = '', suffix: str = ''):
    prefix_re = r''
    suffix_re = r''
    symbols = ['\\', '/', '.', '$', '(', ')']
    if prefix:
        for symbol in symbols:
            if symbol in prefix:
                prefix.replace(symbol, f'\\{symbol}')
        prefix_re = f'^{prefix}'
    if suffix:
        for symbol in symbols:
            if symbol in suffix:
                suffix = suffix.replace(symbol, f'\\{symbol}')
        suffix_re = f'{suffix}.*'
    return re.compile('%s%s' % (prefix_re, suffix_re))


def remove_files_in_dir_with_pattern(directory: str, prefix: str = '', suffix: str = '', exception: str = ''):
    pattern = create_pattern(prefix, suffix)
    dir_as_list = os.listdir(directory)
    parsed_dir = list(filter(pattern.search, dir_as_list))
    for item in parsed_dir:
        if not (exception and exception in item):
            os.remove(f'{directory}/{item}')


def get_numerated_dirs(directory: str, prepend_str: str = '', exception: str = ''):
    pattern = re.compile(f'^{prepend_str}{NUMBER_PATTERN}$')
    dir_as_list = os.listdir(directory)
    return [item for item in filter(pattern.match, dir_as_list) if item != exception]


def remove_iterable_dirs(directory: str, prepend_str: str = '', exception: str = ''):
    parsed_dir = get_numerated_dirs(directory, prepend_str, exception)
    for item in parsed_dir:
        if os.path.isdir(f'{directory}/{item}'):
            force_remove_dir(f'{directory}/{item}')


def remove_dirs_with_pattern(directory: str,
                             prefix: str = '',
                             suffix: str = '',
                             exception: str = '',
                             is_recursive=False):
    pattern = create_pattern(prefix, suffix)
    dir_as_list = os.listdir(directory)
    for item in dir_as_list:
        item_path = f'{directory}/{item}'
        if os.path.isdir(item_path):
            if pattern.search(item):
                if not (exception and exception in item):
                    force_remove_dir(item_path)
            elif is_recursive:
                remove_dirs_with_pattern(item_path, prefix, suffix, exception, is_recursive)


def get_latest_time(case_dir: str) -> str:
    """
    Returns latest time of the simulation that
    correspond to latest time result folder name
    :param case_dir: case directory
    :return: latest simulation time
    """
    try:
        return sorted(get_numerated_dirs(case_dir, exception='0'), key=lambda x: float(x))[-1]
    except (IndexError, FileNotFoundError):
        return '0'


def get_latest_time_parallel(case_dir: str) -> str:
    """
    Returns latest time of the simulation that
    correspond to latest time result folder name
    in parallel run
    :param case_dir: case directory
    :return: latest simulation time
    """
    try:
        return sorted(get_numerated_dirs(f'{case_dir}/processor0', exception='0'), key=lambda x: float(x))[-1]
    except (IndexError, FileNotFoundError):
        return '0'
