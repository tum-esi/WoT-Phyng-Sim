import logging
import time
from typing import List

from .exceptions import WrongPhyngType
from .openfoam.common.filehandling import get_latest_time
from .openfoam.constant.material_properties import FLUID_MATERIALS
from .case_base import OpenFoamCase
from .phyngs.door import DoorPhyng
from .phyngs.walls import WallsPhyng
from .phyngs.window import WindowPhyng
from .phyngs.heater import HeaterPhyng
from .phyngs.sensor import SensorPhyng
from .phyngs.ac import AcPhyng
from .phyngs.base import Phyng
from .variables import (CHT_PHYNG_TYPES, CONFIG_BACKGROUND_K, CONFIG_WALLS_K, CONFIG_HEATERS_K, CONFIG_WINDOWS_K,
                        CONFIG_DOORS_K, CONFIG_SENSORS_K, CONFIG_PHYNG_TEMPER_K, CONFIG_PHYNG_VEL_K, CONFIG_PHYNG_MAT_K,
                        CONFIG_PHYNG_NAME_K, CASE_DIR_K, CONFIG_PHYNG_REGION_K, CONFIG_PHYNG_TYPE_K, OF_INTERFACE_K,
                        BG_REGION_K, CONFIG_ACS_K, CONFIG_PHYNG_EN_K, CONFIG_PHYNG_ANGLE_K)


logger = logging.getLogger('wop')
logger.setLevel(logging.DEBUG)


class ChtCase(OpenFoamCase):
    """Conjugate Heat Transfer (CHT) OpenFOAM case"""
    case_type = 'cht'

    def __init__(self, *args, background='air', **kwargs):
        """
        Conjugate Heat Transfer case initialization function
        :param args: OpenFOAM base case args
        :param kwargs: OpenFOAM base case kwargs
        """
        self.heaters = {}
        self.windows = {}
        self.doors = {}
        self.acs = {}
        self.furniture = {}
        self.walls = None
        self.background_name = 'fluid'
        self._background_material = background
        self.background = background
        super(ChtCase, self).__init__('chtMultiRegionFoam', *args, **kwargs)

    def _setup_initialized_case(self, case_param: dict):
        super(ChtCase, self)._setup_initialized_case(case_param)
        self._add_time_probe('T', 'fluid')

    def _setup_uninitialized_case(self, case_param: dict):
        """
        Sets up the loaded uninitialized CHT case
        :param case_param: loaded case parameters
        """
        super(ChtCase, self)._setup_uninitialized_case(case_param)
        self.remove_initial_boundaries()
        self.load_initial_phyngs(case_param)
        self.set_initial_phyngs(case_param)

    def _get_model_param_set(self):
        return super(ChtCase, self)._get_model_param_set() | {CONFIG_PHYNG_MAT_K}

    def _get_new_params(self, phyng: Phyng, params: dict):
        new_params = super(ChtCase, self)._get_new_params(phyng, params)
        if CONFIG_PHYNG_MAT_K in phyng:
            new_params.update({
                CONFIG_PHYNG_MAT_K: params[CONFIG_PHYNG_MAT_K]
                if CONFIG_PHYNG_MAT_K in params and params[CONFIG_PHYNG_MAT_K] else phyng.material
            })
        return new_params

    def prepare_partitioned_mesh(self):
        super(ChtCase, self).prepare_partitioned_mesh()
        self._partitioned_mesh.material = self._background_material

    @property
    def background(self):
        return self._background_material

    @background.setter
    def background(self, background_material):
        if background_material not in FLUID_MATERIALS:
            raise ValueError(f'Background material cannot be "{background_material}", '
                             f'possible values are: {", ".join(FLUID_MATERIALS)}')
        self._background_material = background_material

    def dump_case(self):
        """
        Dumps CHT case parameters into dictionary
        :return: parameter dump dict
        """
        config = super(ChtCase, self).dump_case()
        config[CONFIG_BACKGROUND_K] = self.background
        config[CONFIG_HEATERS_K] = {}
        config[CONFIG_WINDOWS_K] = {}
        config[CONFIG_DOORS_K] = {}
        config[CONFIG_SENSORS_K] = {}
        config[CONFIG_WALLS_K] = {}
        config[CONFIG_ACS_K] = {}
        if self.walls:
            config[CONFIG_WALLS_K] = self.walls.dump_settings()
        for name, heater in self.heaters.items():
            config[CONFIG_HEATERS_K].update(heater.dump_settings())
        for name, window in self.windows.items():
            config[CONFIG_WINDOWS_K].update(window.dump_settings())
        for name, door in self.doors.items():
            config[CONFIG_DOORS_K].update(door.dump_settings())
        for name, ac in self.acs.items():
            config[CONFIG_ACS_K].update(ac.dump_settings())
        for name, sensor in self.sensors.items():
            config[CONFIG_SENSORS_K].update(sensor.dump_settings())
        return config

    def set_initial_phyngs(self, case_param: dict):
        """
        Sets CHT case phyngs parameters from case_param dict
        :param case_param: loaded case parameters
        """
        if CONFIG_HEATERS_K in case_param and case_param[CONFIG_HEATERS_K]:
            for name, heater in case_param[CONFIG_HEATERS_K].items():
                self.heaters[name].temperature = heater[CONFIG_PHYNG_TEMPER_K]
        if CONFIG_WINDOWS_K in case_param and case_param[CONFIG_WINDOWS_K]:
            for name, window in case_param[CONFIG_WINDOWS_K].items():
                self.windows[name].temperature = window[CONFIG_PHYNG_TEMPER_K]
                self.windows[name].is_open = any(window[CONFIG_PHYNG_VEL_K])
                self.windows[name].velocity = window[CONFIG_PHYNG_VEL_K]
        if CONFIG_DOORS_K in case_param and case_param[CONFIG_DOORS_K]:
            for name, door in case_param[CONFIG_DOORS_K].items():
                self.doors[name].temperature = door[CONFIG_PHYNG_TEMPER_K]
                self.doors[name].is_open = any(door[CONFIG_PHYNG_VEL_K])
                self.doors[name].velocity = door[CONFIG_PHYNG_VEL_K]
        if CONFIG_ACS_K in case_param and case_param[CONFIG_ACS_K]:
            for name, ac in case_param[CONFIG_ACS_K].items():
                self.acs[name].temperature = ac[CONFIG_PHYNG_TEMPER_K]
                self.acs[name].enabled = ac[CONFIG_PHYNG_EN_K]
                self.acs[name].velocity = ac[CONFIG_PHYNG_VEL_K]
                self.acs[name].angle = ac[CONFIG_PHYNG_ANGLE_K]

    def load_initial_phyngs(self, case_param: dict):
        """
        Loads CHT case phyngs parameters from case_param dict
        :param case_param: loaded case parameters
        """
        logger.debug(f'Loading initial CHT case Phyngs')
        # self.background = case_param[CONFIG_BACKGROUND_K]
        if CONFIG_WALLS_K in case_param and case_param[CONFIG_WALLS_K]:
            walls = case_param[CONFIG_WALLS_K]
            params = {**walls, CONFIG_PHYNG_TYPE_K: WallsPhyng.type_name}
            self.add_phyng(**params)
        if CONFIG_HEATERS_K in case_param and case_param[CONFIG_HEATERS_K]:
            for name, heater in case_param[CONFIG_HEATERS_K].items():
                params = {**heater, CONFIG_PHYNG_NAME_K: name, CONFIG_PHYNG_TYPE_K: HeaterPhyng.type_name}
                self.add_phyng(**params)
        if CONFIG_WINDOWS_K in case_param and case_param[CONFIG_WINDOWS_K]:
            for name, window in case_param[CONFIG_WINDOWS_K].items():
                params = {**window, CONFIG_PHYNG_NAME_K: name, CONFIG_PHYNG_TYPE_K: WindowPhyng.type_name}
                self.add_phyng(**params)
        if CONFIG_DOORS_K in case_param and case_param[CONFIG_DOORS_K]:
            for name, door in case_param[CONFIG_DOORS_K].items():
                params = {**door, CONFIG_PHYNG_NAME_K: name, CONFIG_PHYNG_TYPE_K: DoorPhyng.type_name}
                self.add_phyng(**params)
        if CONFIG_SENSORS_K in case_param and case_param[CONFIG_SENSORS_K]:
            for name, sensor in case_param[CONFIG_SENSORS_K].items():
                params = {**sensor, CONFIG_PHYNG_NAME_K: name, CONFIG_PHYNG_TYPE_K: SensorPhyng.type_name}
                self.add_phyng(**params)
        if CONFIG_ACS_K in case_param and case_param[CONFIG_ACS_K]:
            for name, ac in case_param[CONFIG_ACS_K].items():
                params = {**ac, CONFIG_PHYNG_NAME_K: name, CONFIG_PHYNG_TYPE_K: AcPhyng.type_name}
                self.add_phyng(**params)

    def setup(self):
        """Setups CHT case"""
        logger.debug(f'Setting up CHT case')
        self.prepare_geometry()
        self.partition_mesh(self.background_name)
        self.prepare_partitioned_mesh()
        self.clean_case()
        self.run_block_mesh(waiting=True)
        self.run_snappy_hex_mesh(waiting=True)
        self.run_split_mesh_regions(cell_zones_only=True, waiting=True)
        self.run_setup_cht(waiting=True)
        self.extract_boundary_conditions()
        self._add_time_probe('T', 'fluid')
        self.bind_boundary_conditions()
        self.initialized = True

    def add_phyng(self, type: str, **kwargs):
        """
        Adds Phyng to a CHT case
        :param name: name of the phyng
        :param type: type of a phyng, one of: 'heater', 'walls', 'door', 'window'
        :param url: phyng URL
        :param custom: phyng was created from URL
        :param template: phyng template
        :param dimensions: phyng dimensions
        :param location: phyng location
        :param rotation: phyng rotation
        :param sns_field: field to monitor for sensor
        :param material: material of an phyng
        """
        # TODO: check if name contains spaces
        params = {
            **kwargs,
            OF_INTERFACE_K: self,
            BG_REGION_K: self.background_name,
            CASE_DIR_K: self.path,
            CONFIG_PHYNG_REGION_K: self.background_name,
        }
        if type == HeaterPhyng.type_name:
            phyng = HeaterPhyng(**params)
            phyng.bind_snappy(self.snappy_dict, 'cell_zone', refinement_level=2)
            self.heaters.update({phyng.name: phyng})
        elif type == WindowPhyng.type_name:
            phyng = WindowPhyng(**params)
            phyng.bind_snappy(self.snappy_dict, 'region', 'wall', refinement_level=2)
            self.windows.update({phyng.name: phyng})
            if self.walls:
                self.walls.model.geometry.cut_surface(phyng.model.geometry)
        elif type == DoorPhyng.type_name:
            phyng = DoorPhyng(**params)
            phyng.bind_snappy(self.snappy_dict, 'region', 'wall', refinement_level=2)
            self.doors.update({phyng.name: phyng})
            if self.walls:
                self.walls.model.geometry.cut_surface(phyng.model.geometry)
        elif type == WallsPhyng.type_name:
            phyng = WallsPhyng(**params)
            phyng.bind_snappy(self.snappy_dict, 'region', 'wall')
            self.walls = phyng
            for window in self.windows.values():
                phyng.model.geometry.cut_surface(window.model.geometry)
            for door in self.windows.values():
                phyng.model.geometry.cut_surface(door.model.geometry)
        elif type == AcPhyng.type_name:
            phyng = AcPhyng(**params)
            phyng.bind_snappy(self.snappy_dict, 'region', 'wall', refinement_level=2)
            self.acs.update({phyng.name: phyng})
        elif type == SensorPhyng.type_name:
            sensor = SensorPhyng(**params)
            self.sensors.update({sensor.name: sensor})
            self.initialized = False
            return
        else:
            raise WrongPhyngType(f'Wrong phyng type {type}! Possible types are {CHT_PHYNG_TYPES}')
        self.initialized = False
        self.phyngs.update({phyng.name: phyng})

    def remove_phyng(self, phyng_name):
        """
        Removes a phyng with a specified name from case
        :param phyng_name: phyng name to remove
        """
        type_name = self.get_phyng(phyng_name).type_name
        super(ChtCase, self).remove_phyng(phyng_name)
        type_name = f'{type_name}s' if 's' not in type_name[-1] else type_name
        if type_name != 'sensors':
            del self[type_name][phyng_name]


def main():
    is_run_parallel = True
    timestep = 5
    case_dir = '../my_room.case'

    room_dimensions = [3, 4, 2.5]
    window_dimension = [1.5, 0, 1.25]
    door_dimension = [1.5, 0, 2]
    heater_dimensions = [1, 0.2, 0.7]

    window_location = [(room_dimensions[0] - window_dimension[0]) / 2,
                       0,
                       (room_dimensions[2] - window_dimension[2]) / 2]
    door_location = [(room_dimensions[0] - door_dimension[0]) / 2,
                     room_dimensions[1],
                     (room_dimensions[2] - door_dimension[2]) / 2]
    heater_location = [1, 1, 0.2]
    sensor_location = [1.5, 2, 1]

    room = ChtCase(case_dir, blocking=False, parallel=is_run_parallel, cores=4)
    room.add_phyng(name='walls', phyng_type='walls', dimensions=room_dimensions)
    room.add_phyng('inlet', 'window', dimensions=window_dimension, location=window_location)
    room.add_phyng('outlet', 'door', dimensions=door_dimension, location=door_location)
    room.add_phyng('heater', 'heater', dimensions=heater_dimensions, location=heater_location)
    room.add_phyng('temp_sensor', 'sensor', location=sensor_location, sns_field='T')

    # room.get_boundary_conditions()
    # current_time = get_latest_time(room.case_dir)
    # room.boundaries['fluid']['alphat'].update(current_time)
    # room.boundaries['fluid']['omega'].update(current_time)
    # room.boundaries['fluid']['k'].update(current_time)
    # room.boundaries['fluid']['nut'].update(current_time)
    # room.boundaries['fluid']['p'].update(current_time)
    # room.boundaries['fluid']['p_rgh'].update(current_time)
    # room.boundaries['fluid']['T'].update(current_time)
    # room.boundaries['fluid']['U'].update(current_time)
    # room.boundaries['heater']['p'].update(current_time)
    # room.boundaries['heater']['T'].update(current_time)

    room.setup()

    room.heaters['heater'].temperature = 450
    room.walls.temperature = 293.15

    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.heaters['heater'].temperature = room.walls.temperature
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.heaters['heater'].temperature = 450
    room.doors['outlet'].open = True
    room.doors['outlet'].velocity = [0, 0.1, 0]
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.doors['outlet'].open = False
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.windows['inlet'].open = True
    room.windows['inlet'].velocity = [0, 0.1, 0]
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.windows['inlet'].open = False
    room.run()
    time.sleep(timestep)
    room.stop()

    print(f'{room.sensors["temp_sensor"].value=}')
    print(f'Latest time: {get_latest_time(room.path)}')
    room.windows['inlet'].open = True
    room.windows['inlet'].velocity = [0, -0.1, 0]
    room.doors['outlet'].open = True
    room.doors['outlet'].velocity = [0, 0, 0]
    room.run()
    time.sleep(timestep)
    room.stop()


if __name__ == '__main__':
    main()
