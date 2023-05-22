import logging
import random
import datetime
from abc import ABC, abstractmethod
from typing import List, Union

from .exceptions import PhyngNotFound
from .geometry.manipulator import combine_stls
from .phyngs.base import Phyng
from .phyngs.sensor import SensorPhyng
from .openfoam.common.filehandling import get_latest_time, get_latest_time_parallel
from .runtime_monitor import RunTimeMonitor
from .variables import CONFIG_TYPE_K, CONFIG_PATH_K, CONFIG_BLOCKING_K, CONFIG_PARALLEL_K, \
    CONFIG_CORES_K, CONFIG_INITIALIZED_K, CONFIG_MESH_QUALITY_K, CONFIG_CLEAN_LIMIT_K, CONFIG_PHYNG_DIMS_K, \
    CONFIG_PHYNG_ROT_K, CONFIG_PHYNG_LOC_K, CONFIG_PHYNG_STL_K, CONFIG_PHYNG_FIELD_K, CONFIG_PHYNG_NAME_K, \
    CONFIG_STARTED_TIMESTAMP_K, CONFIG_REALTIME_K, CONFIG_END_TIME_K, CONFIG_PHYNG_TYPE_K
from .openfoam.interface import OpenFoamInterface
from .openfoam.system.snappyhexmesh import SnappyRegion, SnappyPartitionedMesh, SnappyCellZoneMesh


logger = logging.getLogger('wop')
logger.setLevel(logging.DEBUG)


class OpenFoamCase(OpenFoamInterface, ABC):
    """OpenFOAM case base class"""
    case_type = ''

    def __init__(self, *args, loaded=False, initialized=False, **kwargs):
        """
        OpenFOAM case generic initializer
        :param args: OpenFOAM interface args
        :param loaded: case was loaded, i.e., was created in the past
        :param initialized: case was initialized (setup) in the past
        :param kwargs: OpenFOAM interface kwargs, i.e., case parameters
        """
        super(OpenFoamCase, self).__init__(*args, **kwargs)
        self.phyngs = {}
        self._partitioned_mesh = None
        self.sensors = {}
        self.start_time = kwargs[CONFIG_STARTED_TIMESTAMP_K] \
            if CONFIG_STARTED_TIMESTAMP_K in kwargs and kwargs[CONFIG_STARTED_TIMESTAMP_K] else 0
        runtime_enabled = kwargs[CONFIG_REALTIME_K] \
            if CONFIG_REALTIME_K in kwargs and kwargs[CONFIG_REALTIME_K] else False
        self._runtime_monitor = RunTimeMonitor(runtime_enabled, 5, self.run, self.stop, self.get_time_difference,
                                               lambda: self.solved)
        if loaded:
            if initialized:
                self._setup_initialized_case(kwargs)
            else:
                self._setup_uninitialized_case(kwargs)
        self.initialized = initialized

    def _setup_initialized_case(self, case_param: dict):
        """
        Setups the loaded initialized case
        :param case_param: loaded case parameters
        """
        logger.info('Setting up initialized case')
        try:
            if self.parallel:
                self.run_reconstruct(all_regions=True, latest_time=True)
        except Exception:
            pass
        self.extract_boundary_conditions()
        self.load_initial_phyngs(case_param)
        self.bind_boundary_conditions()
        self.set_initial_phyngs(case_param)

    def _setup_uninitialized_case(self, case_param: dict):
        """
        Setups the loaded uninitialized case
        :param case_param: loaded case parameters
        """
        logger.info('Setting up uninitialized case')
        self.clean_case()
        self.remove_geometry()

    def _get_mesh_dimensions(self) -> list:
        """
        Gets minimums and maximums of all axis
        :return: list of min and max, e.g., [(x_min, x_max), ...]
        """
        logger.debug('Getting mesh dimensions')
        all_x, all_y, all_z = set(), set(), set()
        for phyng in self.phyngs.values():
            phyng_x, phyng_y, phyng_z = phyng.model.geometry.get_used_coords()
            all_x = all_x | phyng_x
            all_y = all_y | phyng_y
            all_z = all_z | phyng_z
        min_coords = [min(all_x), min(all_y), min(all_z)]
        max_coords = [max(all_x), max(all_y), max(all_z)]
        logger.debug(f'Minimum coords: {min_coords}, Maximum coordinates {max_coords}')
        return list(zip(min_coords, max_coords))

    def _find_location_in_mesh(self, minmax_coords) -> [int, int, int]:
        """
        Finds a location in mesh, which is within the dimensions of the mesh
        and is not inside any cell zone mesh
        :param minmax_coords: dimensions of the mesh
        :return: x, y, z coordinates
        """
        logger.debug(f'Finding location in mesh: {minmax_coords}')
        # Find the forbidden coordinates, i.e., all cell zones' coordinates
        forbidden_coords = [{'min': phyng.model.location,
                             'max': [c1 + c2 for c1, c2 in zip(phyng.model.location, phyng.model.dimensions)]}
                            for phyng in self.phyngs.values() if type(phyng.snappy) == SnappyCellZoneMesh]
        logger.debug(f'Excluded coordinates: {forbidden_coords}')
        point_found = False
        coords_allowed = [False for _ in range(len(forbidden_coords))]
        # If there are no forbidden coordinates
        coords_allowed = [True] if not coords_allowed else coords_allowed
        x, y, z = 0, 0, 0
        # Loop while proper coordinates are found
        while not point_found:
            # Take a random point between the dimensions for each coordinate
            x = round(random.uniform(minmax_coords[0][0] + 0.1, minmax_coords[0][1] - 0.1), 3)
            y = round(random.uniform(minmax_coords[1][0] + 0.1, minmax_coords[1][1] - 0.1), 3)
            z = round(random.uniform(minmax_coords[2][0] + 0.1, minmax_coords[2][1] - 0.1), 3)
            # For each forbidden coordinate, check that it does not lie inside any forbidden zone
            for idx, coords in enumerate(forbidden_coords):
                coords_allowed[idx] = not (coords['min'][0] < x < coords['max'][0] and
                                           coords['min'][1] < y < coords['max'][1] and
                                           coords['min'][2] < z < coords['max'][2])
            point_found = all(coords_allowed)
        logger.debug(f'Found point [{x}, {y}, {z}]')
        return x, y, z

    def dump_case(self):
        """
        Dumps case parameters into dictionary
        :return: parameter dump dict
        """
        config = {
            CONFIG_TYPE_K: self.case_type,
            CONFIG_PATH_K: self.path,
            CONFIG_BLOCKING_K: self.blocking,
            CONFIG_PARALLEL_K: self.parallel,
            CONFIG_CORES_K: self._cores,
            CONFIG_INITIALIZED_K: self.initialized,
            CONFIG_MESH_QUALITY_K: self.blockmesh_dict.mesh_quality,
            CONFIG_CLEAN_LIMIT_K: self.clean_limit,
            CONFIG_STARTED_TIMESTAMP_K: self.start_time,
            CONFIG_REALTIME_K: self._runtime_monitor.enabled,
            CONFIG_END_TIME_K: self.end_time
        }
        return config

    def remove_initial_boundaries(self):
        """Removes initial boundary conditions directory"""
        super(OpenFoamCase, self).remove_initial_boundaries()
        self.initialized = False

    @abstractmethod
    def set_initial_phyngs(self, case_param: dict):
        """
        Method to set case phyngs parameters from case_param dict
        Must be implemented in all child classes
        :param case_param: loaded case parameters
        """
        pass

    @abstractmethod
    def load_initial_phyngs(self, case_param: dict):
        """
        Method to load case phyngs parameters from case_param dict
        Must be implemented in all child classes
        :param case_param: loaded case parameters
        """
        pass

    @abstractmethod
    def add_phyng(self, type: str, **kwargs):
        """
        Adds WoP phyng/sensor to a case
        """
        pass

    def get_phyng(self, phyng_name) -> Union[Phyng, SensorPhyng]:
        """
        Gets phyng/sensor by its name
        :param phyng_name: name of an phyng/sensor
        :return: phyng/sensor instance
        """
        logger.debug(f'Getting Phyng {phyng_name}')
        if phyng_name in self.phyngs:
            return self.phyngs[phyng_name]
        elif phyng_name in self.sensors:
            return self.sensors[phyng_name]
        raise PhyngNotFound(f'Object with name {phyng_name} was not found')

    def _reinit_sensor_from_parameters(self, sensor: SensorPhyng, params: dict):
        """
        Reinitializes sensor from given parameters
        :param sensor: sensor to reinitialize
        :param params: new parameters
        """
        new_params = {
            CONFIG_PHYNG_NAME_K: sensor.name,
            CONFIG_PHYNG_LOC_K: params[CONFIG_PHYNG_LOC_K] if params[CONFIG_PHYNG_LOC_K] else sensor.location,
            CONFIG_PHYNG_FIELD_K: params[CONFIG_PHYNG_FIELD_K] if params[CONFIG_PHYNG_FIELD_K] else sensor.field,
            CONFIG_PHYNG_TYPE_K: sensor.type_name
        }
        self.remove_phyng(sensor.name)
        self.add_phyng(**new_params)

    @staticmethod
    def _get_new_params(phyng: Phyng, params: dict):
        """
        Gets new parameters of a phyng according to present key - values
        :param phyng: WoP phyng
        :param params: new parameters
        :return: new parameters combined with old dict
        """
        return {
            CONFIG_PHYNG_NAME_K: phyng.name,
            CONFIG_PHYNG_DIMS_K: phyng.model.dimensions,
            CONFIG_PHYNG_LOC_K: params[CONFIG_PHYNG_LOC_K]
            if CONFIG_PHYNG_LOC_K in params and params[CONFIG_PHYNG_LOC_K] else phyng.model.location,
            CONFIG_PHYNG_ROT_K: params[CONFIG_PHYNG_ROT_K]
            if CONFIG_PHYNG_ROT_K in params and params[CONFIG_PHYNG_ROT_K] else phyng.model.rotation,
            CONFIG_PHYNG_STL_K: phyng.stl_name
        }

    def _add_phyng_from_parameters(self, phyng_name, params: dict):
        """
        Adds phyng from parameters
        :param phyng_name: phyng name
        :param params: phyng parameters
        """
        params = {**params, CONFIG_PHYNG_NAME_K: phyng_name}
        self.add_phyng(**params)

    def _reinit_phyng_from_parameters(self, phyng: Phyng, params: dict):
        """
        Reinitializes phyng from given parameters
        :param phyng: phyng to reinitialize
        :param params: new parameters
        """
        new_params = self._get_new_params(phyng, params)
        if CONFIG_PHYNG_DIMS_K in params and params[CONFIG_PHYNG_DIMS_K]:
            new_params[CONFIG_PHYNG_DIMS_K] = params[CONFIG_PHYNG_DIMS_K]
            new_params[CONFIG_PHYNG_STL_K] = ''
        elif CONFIG_PHYNG_STL_K in params and params[CONFIG_PHYNG_STL_K]:
            new_params[CONFIG_PHYNG_DIMS_K] = [0, 0, 0]
            new_params[CONFIG_PHYNG_STL_K] = params[CONFIG_PHYNG_STL_K]
        phyng_name = phyng.name
        self.remove_phyng(phyng.name)
        self._add_phyng_from_parameters(phyng_name, new_params)

    @staticmethod
    def _get_model_param_set():
        """
        Gets a set that defines model parameters
        :return: model parameters set
        """
        return {
            CONFIG_PHYNG_DIMS_K,
            CONFIG_PHYNG_ROT_K,
            CONFIG_PHYNG_LOC_K,
            CONFIG_PHYNG_STL_K,
            CONFIG_PHYNG_FIELD_K
        }

    def modify_phyng(self, phyng_name: str, params: dict):
        """
        Modifies phyng by recreating it with new parameters
        :param phyng_name: phyng name
        :param params: phyng parameters to change, e.g., dimensions
        """
        model_param_set = self._get_model_param_set()
        if not model_param_set.isdisjoint(params.keys()):
            self.stop()
            self.initialized = False
            phyng = self.get_phyng(phyng_name)
            if phyng.type_name == 'sensor':
                self._reinit_sensor_from_parameters(phyng, params)
            else:
                self._reinit_phyng_from_parameters(phyng, params)

    def remove_phyng(self, phyng_name):
        """
        Removes an phyng with a specified name from case
        :param phyng_name: phyng name to remove
        """
        phyng = self.get_phyng(phyng_name)
        type_name = phyng.type_name
        phyng.remove()
        if type_name == 'sensor':
            del self.sensors[phyng_name]
            self._probe_parser_thread.remove_unused()
        else:
            del self.phyngs[phyng_name]
        self.initialized = False

    def get_phyngs(self):
        """
        Gets all phyngs
        :return: phyngs dict
        """
        return {**self.phyngs, **self.sensors}

    def prepare_geometry(self):
        """Prepares each phyngs geometry"""
        logger.debug('Preparing Phyngs geometries')
        for phyng in self.phyngs.values():
            logger.debug(f'Preparing {phyng.name} Phyng')
            phyng.prepare()

    def partition_mesh(self, partition_name: str):
        """
        Partitions mesh by producing a partitioned mesh out of partition regions
        :param partition_name: partitioned mesh name
        """
        logger.debug(f'Partitioning mesh {partition_name}')
        regions = []
        for phyng in self.phyngs.values():
            if isinstance(phyng.snappy, list):
                snappies = [snappy for snappy in phyng.snappy if type(snappy) == SnappyRegion]
                regions.extend(snappies)
            elif type(phyng.snappy) == SnappyRegion:
                regions.append(phyng.snappy)
        region_paths = [f'{self.path}/constant/triSurface/{region.name}.stl' for region in regions]
        combine_stls(f'{self.path}/constant/triSurface/{partition_name}.stl', region_paths)
        self._partitioned_mesh = SnappyPartitionedMesh(partition_name, f'{partition_name}.stl')
        self._partitioned_mesh.add_regions(regions)

    def prepare_partitioned_mesh(self):
        """
        Prepares partitioned mesh, i.e., adds it to snappyHexMeshDict and
        adds background mesh to blockMeshDict
        """
        logger.debug('Preparing partioned mesh')
        # Get all partitions
        partitions = []
        for phyng in self.phyngs.values():
            if isinstance(phyng.snappy, list):
                snappies = [snappy for snappy in phyng.snappy if type(snappy) == SnappyCellZoneMesh]
                partitions.extend(snappies)
            elif type(phyng.snappy) == SnappyCellZoneMesh:
                partitions.append(phyng.snappy)
        partitions.insert(0, self._partitioned_mesh)
        for partition in partitions:
            logger.debug(f'Coupling partitions {partition.name} material')
            self.material_props.add_object(partition.name, partition.material_type, partition.material)
        # Add partitions to snappyHexMeshDict, get dimensions and find a location in mesh
        logger.debug(f'Adding partitions to snappyHexMeshDict')
        self.snappy_dict.add_meshes(partitions)
        minmax_coords = self._get_mesh_dimensions()
        self.snappy_dict.location_in_mesh = self._find_location_in_mesh(minmax_coords)
        # Create background mesh in blockMeshDict, which is bigger then the original dimensions
        blockmesh_min_coords = [coord[0] - 1 for coord in minmax_coords]
        blockmesh_max_coords = [coord[1] + 1 for coord in minmax_coords]
        self.blockmesh_dict.add_box(blockmesh_min_coords, blockmesh_max_coords, name=self._partitioned_mesh.name)
        # TODO: move it to more generalized function
        self.decompose_dict.divide_domain([j - i for i, j in minmax_coords])

    def bind_boundary_conditions(self):
        """Binds boundary conditions to phyngs"""
        for phyng in self.phyngs.values():
            phyng.bind_region_boundaries(self.boundaries)

    def get_simulation_time_ms(self):
        """
        Gets simulation time in datetime and epoch ms
        :return: epoch ms, datetime
        """
        simulation_timestamp = self.start_time + self._time_probe.time * 1000
        simulation_time = datetime.datetime.fromtimestamp(simulation_timestamp / 1000)
        return simulation_timestamp, simulation_time

    @staticmethod
    def get_current_time():
        """
        Gets current real time in datetime and epoch ms
        :return: epoch ms, datetime
        """
        time_now = datetime.datetime.now()
        timestamp_now = time_now.timestamp() * 1000
        return timestamp_now, time_now

    def get_time_difference(self, simulation_timestamp=None, timestamp_now=None):
        """
        Gets time difference in seconds
        :param simulation_timestamp: simulation time in epoch ms
        :param timestamp_now: real time in epoch ms
        :return: time difference in seconds
        """
        if bool(simulation_timestamp) != bool(timestamp_now):
            raise ValueError(f'Either both simulation time and now time or none should be specified')
        if not simulation_timestamp and not timestamp_now:
            simulation_timestamp, _ = self.get_simulation_time_ms()
            timestamp_now, _ = self.get_current_time()
        return round((simulation_timestamp - timestamp_now) / 1000, 3)

    def get_time(self) -> dict:
        """
        Gets real time, simulation time and
        a difference between real and simulation
        :return: dictionary
        """
        timestamp_now, time_now = self.get_current_time()
        times = {
            'real_time': time_now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'simulation_time': '0',
            'time_difference': 0
        }
        if self.start_time:
            simulation_timestamp, simulation_time = self.get_simulation_time_ms()
            times['simulation_time'] = simulation_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            times['time_difference'] = self.get_time_difference(simulation_timestamp, timestamp_now)
        return times

    def enable_realtime(self):
        """
        Enables runtime monitor that tries
        to keep simulation running at realtime
        """
        self._runtime_monitor.enabled = True
        if self._running:
            self._runtime_monitor.start()

    def disable_realtime(self):
        """Disables runtime monitor"""
        self._runtime_monitor.enabled = False

    @property
    def realtime(self):
        return self._runtime_monitor.enabled

    @realtime.setter
    def realtime(self, value):
        if value:
            self.enable_realtime()
        else:
            self.disable_realtime()

    @property
    def running(self):
        return super(OpenFoamCase, self).running or self._runtime_monitor.running

    def clean_case(self):
        """
        Removes old results and logs in the case directory.
        Resets start time
        """
        self.stop()
        self.start_time = 0
        super(OpenFoamCase, self).clean_case()
        for phyng in self.phyngs.values():
            phyng.reload_parameters()

    def run(self):
        """
        Runs solver and monitor threads
        Case must be setup before running
        """
        if self._running:
            return
        if not self.initialized:
            self.clean_case()
            self.setup()
        get_time = get_latest_time
        if self.parallel:
            get_time = get_latest_time_parallel
        if not self.start_time:
            self.start_time, _ = self.get_current_time()
        super(OpenFoamCase, self).run()
        self._runtime_monitor.start()

    def stop(self, runtime_checker=False, **kwargs):
        if not runtime_checker:
            self._runtime_monitor.stop()
        super(OpenFoamCase, self).stop(**kwargs)

    def __getitem__(self, item):
        """Allow to access attributes of a class as in dictionary"""
        return getattr(self, item)

    def __setitem__(self, key, value):
        """Allow to set attributes of a class as in dictionary"""
        if key not in (CONFIG_CLEAN_LIMIT_K, CONFIG_REALTIME_K, CONFIG_END_TIME_K):
            self.initialized = False
            self.stop()
        if key == CONFIG_MESH_QUALITY_K:
            self.blockmesh_dict.mesh_quality = value
        else:
            setattr(self, key, value)
        if key == CONFIG_END_TIME_K:
            self.control_dict.save()
        logger.info(f'Set "{key}" to {value}')

    def __iter__(self):
        """Allow to iterate over attribute names of a class"""
        for each in [b for b in dir(self) if '_' not in b[0]]:
            yield each

    def __delitem__(self, key):
        """Allow to delete individual attributes of a class"""
        del self.__dict__[key]

    def remove(self):
        for phyng_name in self.phyngs.keys():
            self.phyngs[phyng_name].remove()
        self.phyngs = None
        self._runtime_monitor.stop()
        self._runtime_monitor = None
        super(OpenFoamCase, self).remove()
