import os

from .phyngs.door import DoorPhyng
from .phyngs.heater import HeaterPhyng
from .phyngs.walls import WallsPhyng
from .phyngs.window import WindowPhyng
from .phyngs.sensor import SensorPhyng
from .phyngs.ac import AcPhyng

CUR_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
CASES_STORAGE = os.getenv('CASES_STORAGE', os.path.realpath(f'{CUR_FILE_DIR}/../'))

WOP_CONFIG_FILE = 'wop.config.json'

# Cases
CONFIG_TYPE_K = 'type'
CONFIG_PATH_K = 'path'
CONFIG_BLOCKING_K = 'blocking'
CONFIG_PARALLEL_K = 'parallel'
CONFIG_MESH_QUALITY_K = 'mesh_quality'
CONFIG_CLEAN_LIMIT_K = 'clean_limit'
CONFIG_CORES_K = 'cores'
CONFIG_INITIALIZED_K = 'initialized'
CONFIG_STARTED_TIMESTAMP_K = 'started_timestamp'
CONFIG_REALTIME_K = 'realtime'
CONFIG_END_TIME_K = 'end_time'

CONFIG_CASE_KEYS = [
    CONFIG_TYPE_K,
    CONFIG_MESH_QUALITY_K,
    CONFIG_CLEAN_LIMIT_K,
    CONFIG_PARALLEL_K,
    CONFIG_CORES_K,
    CONFIG_REALTIME_K,
    CONFIG_END_TIME_K
]

DEFAULT_MESH_QUALITY = 50
DEFAULT_CLEAN_LIMIT = 0
DEFAULT_PARALLEL = True
DEFAULT_CORES = 4
DEFAULT_REALTIME = True
DEFAULT_END_TIME = 1000

CONFIG_DEFAULTS = {
    CONFIG_MESH_QUALITY_K: DEFAULT_MESH_QUALITY,
    CONFIG_CLEAN_LIMIT_K: DEFAULT_CLEAN_LIMIT,
    CONFIG_PARALLEL_K: DEFAULT_PARALLEL,
    CONFIG_CORES_K: DEFAULT_CORES,
    CONFIG_REALTIME_K: DEFAULT_REALTIME,
    CONFIG_END_TIME_K: DEFAULT_END_TIME
}

# Phyngs
CASE_DIR_K = 'case_dir'
OF_INTERFACE_K = 'of_interface'
BG_REGION_K = 'bg_region'
CONFIG_PHYNG_NAME_K = 'name'
CONFIG_PHYNG_REGION_K = 'region'
CONFIG_PHYNG_TYPE_K = 'type'
CONFIG_PHYNG_DIMS_K = 'dimensions'
CONFIG_PHYNG_ROT_K = 'rotation'
CONFIG_PHYNG_MAT_K = 'material'
CONFIG_PHYNG_FIELD_K = 'field'
CONFIG_PHYNG_LOC_K = 'location'
CONFIG_PHYNG_STL_K = 'stl_name'
CONFIG_PHYNG_TEMPER_K = 'temperature'
CONFIG_PHYNG_VEL_K = 'velocity'
CONFIG_PHYNG_EN_K = 'enabled'
CONFIG_PHYNG_ANGLE_K = 'angle'

# Specific cases data
CHT_PHYNG_TYPES = [
    HeaterPhyng.type_name,
    WindowPhyng.type_name,
    WallsPhyng.type_name,
    DoorPhyng.type_name,
    SensorPhyng.type_name,
    AcPhyng.type_name,
    # TODO:
    'furniture',
]
CONFIG_BACKGROUND_K = 'background'
DEFAULT_BACKGROUND = 'air'
CONFIG_CASE_KEYS.append(CONFIG_BACKGROUND_K)
CONFIG_DEFAULTS.update({CONFIG_BACKGROUND_K: DEFAULT_BACKGROUND})

CONFIG_WALLS_K = 'walls'
CONFIG_HEATERS_K = 'heaters'
CONFIG_WINDOWS_K = 'windows'
CONFIG_DOORS_K = 'doors'
CONFIG_SENSORS_K = 'sensors'
CONFIG_ACS_K = 'acs'
