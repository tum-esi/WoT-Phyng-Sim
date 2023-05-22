"""
OpenFOAM python interface
"""
import os
import time
import subprocess
import multiprocessing as mp
import threading as thr
from abc import ABC, abstractmethod
import logging
from numpy import arange

from .boundaries.boundary_conditions import BoundaryCondition
from .common.filehandling import remove_iterable_dirs, remove_dirs_with_pattern, \
    force_remove_dir, remove_files_in_dir_with_pattern, copy_tree, get_latest_time, get_latest_time_parallel
from .constant.material_properties import MaterialProperties
from .probes.probes import ProbeParser, Probe
from .pyfoam_runner import PyFoamCmd, PyFoamSolver, check_runner_errors
from .system.blockmesh import BlockMeshDict
from .system.controldict import ControlDict
from .system.decomposepar import DecomposeParDict
from .system.snappyhexmesh import SnappyHexMeshDict


logging.basicConfig(
    format='%(asctime)s %(name)-10s %(levelname)-8s %(message)s',
    level=logging.INFO
)

logger = logging.getLogger('openfoam')
logger.setLevel(logging.DEBUG)


class OpenFoamInterface(ABC):
    """
    OpenFOAM Interface class. Serves as a wrapper of OpenFOAM commands
    """

    def __init__(self, solver_type, path='.', blocking=False, parallel=False, cores=1, mesh_quality=50,
                 clean_limit=0, end_time=10000, **kwargs):
        """
        OpenFOAM Interface initialization function
        :param solver_type: solver type, e.g., chtMultiRegionFoam TODO: check for solver type
        :param path: path to case dir
        :param blocking: flag for solver blocking the main thread
        :param parallel: flag for parallel run
        :param cores: number of cores used for parallel run
        :param mesh_quality: mesh quality in percents [0 - 100]
        :param clean_limit: maximum number of results before cleaning, cleans if > 0
        :param kwargs: keys used by children and not by this class
        """
        self.path = path
        self.control_dict = ControlDict(self.path, solver_type)
        self.decompose_dict = DecomposeParDict(self.path, cores, 'hierarchical')
        self.blockmesh_dict = BlockMeshDict(self.path)
        self.snappy_dict = SnappyHexMeshDict(self.path)
        self.material_props = MaterialProperties(self.path)
        self.regions = []
        self.boundaries = {}
        self.is_decomposed = os.path.exists(f'{path}/processor0')
        self._solver_type = solver_type
        self._solver_thread = None
        self._solver_lock = thr.Lock()
        self._stop_lock = thr.Lock()
        self._probe_parser_thread = ProbeParser(self.path)
        self._time_probe = None
        self.parallel = parallel
        self.blocking = blocking
        self.cores = cores
        self.clean_limit = clean_limit
        self.control_dict.end_time = end_time
        self.blockmesh_dict.mesh_quality = mesh_quality
        self._running = False
        logger.debug('Interface initialized')

    @property
    def cores(self):
        """
        Number of cores getter
        """
        return self._cores

    @cores.setter
    def cores(self, cores):
        """
        Number of cores setter
        :param cores: number of cores
        """
        if self.parallel:
            available_cores = mp.cpu_count()
            if available_cores >= cores > 0:
                if cores == 1:
                    self.parallel = False
                self._cores = cores
            else:
                self._cores = available_cores
            if self._cores != 1 and self._cores % 2:
                self._cores //= 2
        else:
            self._cores = 1
        self.decompose_dict.num_of_domains = self._cores
        logger.info(f'Number of cores are set to {self._cores}')

    @property
    def running(self):
        return self._running

    @property
    def end_time(self):
        return self.control_dict.end_time

    @end_time.setter
    def end_time(self, value):
        self.control_dict.end_time = value

    def remove_processor_dirs(self):
        """
        Removes processors folder
        :return: None
        """
        self.is_decomposed = False
        remove_iterable_dirs(self.path, prepend_str='processor')
        logger.debug('Processors removed')

    def remove_solution_dirs(self):
        """
        Removes solution directories folder
        :return: None
        """
        remove_iterable_dirs(self.path, exception='0')
        logger.debug('Solutions removed')

    def remove_mesh_dirs(self):
        """
        Removes Mesh folders in all folders (e.g. polyMesh)
        :return: None
        """
        remove_dirs_with_pattern(self.path, suffix='Mesh', is_recursive=True)
        logger.debug('Mesh dirs removed')

    def remove_tri_surface_dir(self):
        """
        Removes tri surface folder
        :return: None
        """
        force_remove_dir(f'{self.path}/constant/triSurface')
        logger.debug('Triangulated surfaces removed')

    def remove_geometry(self):
        """Removes geometry and mesh related files"""
        logger.debug('Removing geometry')
        self.remove_mesh_dirs()
        self.remove_tri_surface_dir()
        logger.debug('Geometries removed')

    def remove_solutions(self):
        """Removes solutions from directory"""
        logger.debug('Removing solutions')
        self.remove_processor_dirs()
        self.remove_solution_dirs()
        force_remove_dir(f'{self.path}/postProcessing')
        logger.debug('Removed post-processing')
        logger.debug('Solutions removed')

    def remove_logs(self):
        """Removes logs and foam files"""
        remove_files_in_dir_with_pattern(self.path, prefix='PyFoamState.')
        remove_files_in_dir_with_pattern(self.path, prefix='log.')
        remove_files_in_dir_with_pattern(self.path, suffix='.logfile')
        remove_files_in_dir_with_pattern(self.path, suffix='.foam')
        remove_files_in_dir_with_pattern(self.path, suffix='.OpenFOAM')

    def remove_initial_boundaries(self):
        """Removes initial boundary conditions directory"""
        logger.debug('Removing initial boundaries')
        force_remove_dir(f'{self.path}/0')

    def clean_case(self):
        """
        Removes old results and logs in the case directory
        :return: None
        """
        logger.debug('Cleaning the case')
        self.remove_solutions()
        self.remove_logs()
        if self._time_probe:
            self._time_probe.time = 0
        logger.debug('Case is clean')

    def copy_stls(self, src_sub_dir: str = 'geometry', dst_sub_dir: str = 'constant/triSurface'):
        """
        Copy STLs from geometry dir to constant/triSurface or user prefered location
        TODO: move this function to other class later!
        :param src_sub_dir: source subdirectory
        :param dst_sub_dir:
        :return: None
        """
        logger.debug('Copying STLs')
        stls_path = f'{self.path}/{src_sub_dir}'
        path_to_copy = f'{self.path}/{dst_sub_dir}'
        copy_tree(stls_path, path_to_copy)

    def run_decompose(self, all_regions: bool = False, copy_zero: bool = False, latest_time: bool = False,
                      force: bool = False, waiting: bool = False):
        """
        Runs OpenFOAM case decomposition for parallel run, described in system/decomposeParDict
        :param all_regions: flag to decompose all regions (used for multi-region cases like cht)
        :param copy_zero: copy zero state
        :param latest_time: flag to only decompose from the latest time
        :param force: flag to clear processor folders before decomposing
        :return: None
        """
        logger.info('Running decompose')
        if self.is_decomposed:
            latest_time = True
            force = True
        else:
            self.decompose_dict.save()
        cmd = 'decomposePar'
        argv = [cmd, '-case', self.path]
        if all_regions:
            argv.insert(1, '-allRegions')
        if copy_zero:
            argv.insert(1, '-copyZero')
        if latest_time:
            argv.insert(1, '-latestTime')
        if force:
            argv.insert(1, '-force')
        command = PyFoamCmd(argv)
        command.start()
        while waiting and command.running:
            time.sleep(0.001)
        self.is_decomposed = True
        logger.info('Case decomposed')

    def run_reconstruct(self, all_regions: bool = False, latest_time: bool = False, fields: list = None,
                        region: str = '', waiting: bool = False):
        """
        Runs OpenFOAM case reconstruction after a parallel run, described in system/decomposeParDict
        :param all_regions: flag to reconstruct all regions (used for multi-region cases like cht)
        :param latest_time: flag to only reconstruct from the latest time
        :param fields: fields to be reconstructed, e.g., ['U', 'T', 'p']
        :param region: region to reconstruct
        :return: None
        """
        logger.debug('Removing old solutions')
        self.remove_solution_dirs()  # Hope no bug is implemented by this, be aware
        logger.info('Running reconstruct')
        if not self.is_decomposed:
            logger.info('Case is not decomposed, skipping reconstruction')
            return
        cmd = 'reconstructPar'
        argv = [cmd, '-newTimes', '-case', self.path]
        if all_regions:
            argv.insert(1, '-allRegions')
        elif region:
            argv.insert(1, f'-region {region}')
        if latest_time:
            argv.insert(1, '-latestTime')
        if fields:
            argv.insert(1, f'-fields \'({" ".join(fields)})\'')
        command = PyFoamCmd(argv)
        command.start()
        while waiting and command.running:
            time.sleep(0.001)
        logger.info('Case reconstructed')

    def run_block_mesh(self, waiting: bool = False):
        """
        Runs OpenFOAM command to create a mesh as described in system/blockMeshDict
        :return: None
        """
        logger.info('Running blockMesh')
        self.blockmesh_dict.save()
        cmd = 'blockMesh'
        argv = [cmd, '-case', self.path]
        command = PyFoamCmd(argv)
        command.start()
        while waiting and command.running:
            time.sleep(0.001)
        logger.info('Block mesh created')

    def run_snappy_hex_mesh(self, waiting: bool = False):
        """
        Runs OpenFOAM command to snap additional mesh to a background mesh as described in system/snappyHexMeshDict
        :return: None
        """
        logger.info('Running snappyHexMesh')
        self.snappy_dict.save()
        cmd = 'snappyHexMesh'
        argv = [cmd, '-case', self.path, '-overwrite']
        command = PyFoamCmd(argv)
        command.start()
        while waiting and command.running:
            time.sleep(0.001)
        logger.info('Surfaces snapped')

    def run_split_mesh_regions(self, cell_zones: bool = False, cell_zones_only: bool = False,
                               waiting: bool = False):
        """
        Runs OpenFOAM command to split mesh regions for a produced mesh
        :param cell_zones: split additionally cellZones off into separate regions
        :param cell_zones_only: use cellZones only to split mesh into regions; do not use walking
        :return: None
        """
        logger.info('Splitting mesh')
        cmd = 'splitMeshRegions'
        argv = [cmd, '-case', self.path, '-overwrite']
        if cell_zones:
            argv.insert(1, '-cellZones')
        if cell_zones_only:
            argv.insert(1, '-cellZonesOnly')
        command = PyFoamCmd(argv)
        command.start()
        while waiting and command.running:
            time.sleep(0.001)
        logger.info('Mesh was split')

    def run_setup_cht(self, waiting: bool = False):
        """
        Runs OpenFOAM command to setup CHT, which copies data from case/templates folder
        :return: None
        """
        logger.info('Setting up CHT')
        self.material_props.save()
        cmd = 'foamSetupCHT'
        argv = [cmd, '-case', self.path]
        command = PyFoamCmd(argv)
        command.start()
        while waiting and command.running:
            time.sleep(0.001)
        logger.info('CHT case is setup')

    def run_foam_dictionary(self, path: str, entry: str, set_value: str):
        """
        Runs OpenFOAM command to change dictionary specified in the path
        :param path: path to dictionary
        :param entry: field to change
        :param set_value: value to set
        :return: None
        """
        logger.debug(f'Setting a value of {path} field {entry} to {set_value}')
        cmd = 'foamDictionary'
        argv = [cmd, f'{self.path}/{path}', '-entry', entry, '-set', set_value]
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        p.wait()
        if err or b'ERROR' in output:
            raise Exception(err)
        logger.debug('Value changed')

    def _add_time_probe(self, field, region):
        self._time_probe = Probe(self.path, field, region, [0, 0, 0])
        self._probe_parser_thread.parse_probe(self._time_probe)

    def extract_boundary_conditions(self):
        """
        Extracts initial boundary conditions for current case from files
        :return: None
        """
        logger.debug('Extracting boundaries')
        fields_dir = os.listdir(f'{self.path}/0')
        region_dirs = [obj for obj in fields_dir if os.path.isdir(f'{self.path}/0/{obj}')]
        # Check if there are any folders in initial boundary dir
        # If there folders there, then the case is multi-regional
        if any(region_dirs):
            self.regions = region_dirs
            for region in region_dirs:
                self.boundaries.update({region: {}})
                region_dir = os.listdir(f'{self.path}/0/{region}')
                for field in region_dir:
                    cls_instance = BoundaryCondition(field, self.path, region=region)
                    if cls_instance:
                        self.boundaries[region].update({field: cls_instance})
        else:
            for field in fields_dir:
                cls_instance = BoundaryCondition(field, self.path)
                if cls_instance:
                    self.boundaries.update({field: cls_instance})
        self.decompose_dict.regions = self.regions
        logger.debug('Boundaries were extracted')

    @abstractmethod
    def setup(self):
        """
        Setups case, should be overridden by child classes
        :return: None
        """
        raise NotImplementedError('Setup method is not implemented!')

    def save_boundaries(self):
        """Saves all boundary conditions"""
        logger.info('Saving boundaries')
        if self.regions:
            for region in self.regions:
                for field in self.boundaries[region].values():
                    field.save()
        else:
            for field in self.boundaries.values():
                field.save()
        logger.info('Boundaries were saved')

    @property
    def solved(self):
        if self.parallel:
            latest_time = get_latest_time_parallel(self.path)
        else:
            latest_time = get_latest_time(self.path)
        latest_time = float(latest_time)
        if (self.control_dict.write_interval + latest_time) > self.control_dict.end_time:
            return True
        return False

    def start_solving(self):
        """
        Starts OpenFOAM solver thread or process
        :return:
        """
        self.control_dict.save()
        self.save_boundaries()
        cleaner_thread = thr.Thread(target=self.result_cleaner, daemon=True)
        if self.parallel:
            self.run_decompose(all_regions=True, latest_time=True, force=True, waiting=True)
        self._solver_thread = PyFoamSolver(self._solver_type, self.path, self._solver_lock, self.parallel, self.cores)
        self._solver_thread.start()
        self._running = True
        cleaner_thread.start()

    def stop_solving(self):
        """
        Stops OpenFOAM solver
        :return: None
        """
        if not self._running:
            return
        self._solver_thread.stop(int(self.control_dict.stop_at_write_now_signal))
        self._solver_thread = None
        self._running = False

    def result_cleaner(self):
        """Thread to clean the results periodically"""
        if not self.clean_limit:
            return
        logger.debug('Starting case cleaner')
        time_getter = get_latest_time_parallel if self.parallel else get_latest_time
        deletion_time = 0
        margin = self.clean_limit / 2 // self.control_dict.write_interval * self.control_dict.write_interval
        while self._running:
            latest_time = float(time_getter(self.path))
            if latest_time != deletion_time and not latest_time % self.clean_limit:
                time.sleep(0.05)
                exceptions = '|'.join([str(int(val) if val.is_integer() else val)
                                       for val in arange(latest_time - margin, latest_time + margin,
                                                         self.control_dict.write_interval)])
                exceptions = exceptions.replace('.', r'\.')
                if self.parallel:
                    for core in range(0, self.cores):
                        remove_dirs_with_pattern(f'{self.path}/processor{core}', f'^(?!(?:0|{exceptions})$)\\d+')
                else:
                    remove_dirs_with_pattern(self.path, f'^(?!(?:0|{exceptions})$)\\d+')
                deletion_time = latest_time
            time.sleep(0.01)
        logger.debug('Case cleaner stopped')

    def run(self):
        """
        Runs solver and monitor threads
        :return: None
        """
        if self._running:
            logger.debug('Case is already being solved')
            return
        with self._stop_lock:
            logger.info('Starting to solve the case')
            self.start_solving()
            self._probe_parser_thread.start()
        if self.blocking:
            self._solver_lock.acquire()
            self._solver_lock.release()
            if self._solver_thread.solver:
                check_runner_errors(self._solver_type, self._solver_thread.solver)
        logger.info('Stopped solving the case')

    def stop(self, stop_solver=True, **kwargs):
        """
        Stops solver and monitor threads
        :return: None
        """
        if not self._running:
            logger.debug('Case is already stopped')
            return
        with self._stop_lock:
            logger.debug('Stopping probe parsers')
            self._probe_parser_thread.stop()
            if stop_solver:
                logger.info('Stopping the case solver')
                self.stop_solving()

    def remove(self):
        self.blockmesh_dict.remove()
        self._probe_parser_thread.stop()
        self._probe_parser_thread = None
