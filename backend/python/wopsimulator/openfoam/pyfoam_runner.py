import traceback
import logging
from signal import SIGINT
from threading import Thread, Lock

import PyFoam.Error
import psutil


def default_error_catcher(text):
    raise Exception(text)


PyFoam.Error.debug = lambda *text: None
PyFoam.Error.warning = lambda *text: None
PyFoam.Error.error = default_error_catcher

from PyFoam.Execution.BasicRunner import BasicRunner
from PyFoam.Execution.ParallelExecution import LAMMachine


logger = logging.getLogger('openfoam')


class RunFailed(Exception):
    pass


def error_callback(error: BaseException):
    """OpenFoam commands error callback"""
    pass
    # tb = error.__traceback__
    # traceback.print_exception(type(error), error, tb)


def run_error_catcher(func):
    """
    OpenFOAM interface error catching decorator
    Calls attached callback if error was caught
    :param func: function to decorate
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (RunFailed, Exception) as e:
            error = e
        error_callback(error)
        raise error

    return wrapper


def check_runner_errors(command, solver):
    """Check if errors appeared after running command"""
    if not solver.runOK():
        if solver.fatalError:
            error = f'fatal error'
        elif solver.fatalFPE:
            error = f'fatal FPE'
        elif solver.fatalStackdump:
            error = f'fatal stack dump'
        else:
            error = 'unknown error'
        error_message = f'{command} run failed with {error}' \
                        f'{(":" + solver.data["errorText"]) if "errorText" in solver.data else ""}'
        logger.error(error_message)
        raise RunFailed(error_message)


class BasicRunnerWrapper(BasicRunner):
    def __init__(self, *args, **kwargs):
        self.running = False
        super(BasicRunnerWrapper, self).__init__(*args, **kwargs)

    def kill(self, *args, **kwargs):
        """Kills a thread if it is stuck"""
        try:
            self.run.run.send_signal(SIGINT)
            self.run._stop()
        except AssertionError:
            pass

    def start(self):
        """Starts executing command"""
        self.running = True
        try:
            super(BasicRunnerWrapper, self).start()
        finally:
            self.running = False


class PyFoamCmd(BasicRunnerWrapper):
    def __init__(self, argv, silent=True, is_parallel: bool = False, cores: int = 1, **kwargs):
        self.logname = argv[0]
        self.silent = silent
        self.argv = argv
        if is_parallel:
            self.argv = ['mpirun', '-np', str(cores)] + argv + ['-parallel']
        super(PyFoamCmd, self).__init__(argv=self.argv, silent=self.silent, logname=self.logname, **kwargs)

    @run_error_catcher
    def start(self):
        """Starts executing command"""
        super(PyFoamCmd, self).start()
        check_runner_errors(self.logname, self)


class PyFoamSolver(Thread):
    def __init__(self, solver_type: str, case_dir: str, lock: Lock, is_parallel: bool = False, cores: int = 1,
                 silent=True, **kwargs):
        argv = [solver_type, '-case', case_dir]
        lam = None
        if is_parallel:
            lam = LAMMachine(nr=cores)
        self._solve = False
        self._lock = lock
        self._parallel = is_parallel
        self._solver_type = solver_type
        self.solver = BasicRunnerWrapper(argv=argv, silent=silent, logname=solver_type, lam=lam, **kwargs)
        super(PyFoamSolver, self).__init__(daemon=True)

    @run_error_catcher
    def run(self):
        """Solving thread"""
        with self._lock:
            logger.debug('Entering solver thread')
            try:
                self.solver.start()
            except Exception:
                pass
            check_runner_errors(self._solver_type, self.solver)
            logger.debug('Quiting solver thread')
            self.solver = None

    def stop(self, signal):
        """Stops solving"""
        try:
            if not self.solver:
                return
            pid = self.solver.run.run.pid
            process = psutil.Process(pid)
            process.children()[0].send_signal(signal)
            process.send_signal(signal)
        except psutil.NoSuchProcess:
            pass
        acquired = self._lock.acquire(timeout=1)
        self._lock.release()
        if not acquired:
            logger.warning('Could not obtain the lock, killing the solving thread')
            self.kill()

    def kill(self):
        """Kill solving thread"""
        try:
            pid = self.solver.run.run.pid
            process = psutil.Process(pid)
            process.send_signal(SIGINT)
            process.children()[0].send_signal(SIGINT)
        except psutil.NoSuchProcess:
            pass
        self.solver = None
        acquired = self._lock.acquire(timeout=10)
        self._lock.release()
        if not acquired:
            logger.warning('Solver was not killed within 10 ms')
            raise Exception('Case solving could not be stopped')
