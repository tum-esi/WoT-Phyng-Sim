from ..exceptions import PhyngSetValueFailed
from ..openfoam.common.filehandling import get_latest_time
from .behavior.cht import set_boundary_to_wall, set_boundary_to_inlet, update_boundaries
from .base import Phyng
from .common import MIN_TEMP, MAX_TEMP, MIN_VEL, MAX_VEL


class WindowPhyng(Phyng):
    """
    Web of Phyngs Window phyng class
    Combines everything what a window phyng has (geometry, properties, etc)
    """
    type_name = 'window'

    def __init__(self, stl_name='', **kwargs):
        """
        Web of Phyngs window phyng initialization function
        :param name: name of the window phyng
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param stl_name: STL geometry name
        :param of_interface: OpenFoam interface
        """
        self._open = False
        model_type = 'surface'
        templates_dir = 'windows'
        super(WindowPhyng, self).__init__(stl_name=stl_name, model_type=model_type,
                                          templates_dir=templates_dir, **kwargs)
        self._temperature = self.environment.temperature
        self._velocity = [MIN_VEL if dim else 0 for dim in self.model.dimensions]
        self._velocity[2] = 0
        self._fields = 'all'

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a window phyng"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)

    def dump_settings(self) -> dict:
        settings = super(WindowPhyng, self).dump_settings()
        settings[self.name].update({'temperature': self._temperature, 'velocity': self._velocity})
        return settings

    @property
    def open(self):
        """Window phyng open status getter"""
        return self._open

    @open.setter
    def open(self, is_open):
        """
        Sets window phyng type by modifying the latest results
        :param is_open: window phyngs status
        :return:
        """
        self._open = is_open
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            if is_open:
                set_boundary_to_inlet(self.name, self._boundary_conditions, self._velocity, self._temperature,
                                      latest_result, bg_name=self._bg_region, of_interface=self._of_interface)
            else:
                set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature, latest_result,
                                     bg_name=self._bg_region, of_interface=self._of_interface)
                self._velocity = [MIN_VEL if dim else 0 for dim in self.model.dimensions]
                self._velocity[2] = 0
                self._temperature = self.environment.temperature
        except Exception as e:
            raise PhyngSetValueFailed(e)

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, wind_speed):
        wind_speed_check = [True if (MIN_VEL <= v <= MAX_VEL) or (-MIN_VEL >= v >= -MAX_VEL) else False
                            for v in wind_speed]
        if not any(wind_speed_check):
            raise PhyngSetValueFailed(f'Velocity can only be between {MIN_VEL} and {MAX_VEL} m/s, '
                                      f'not {wind_speed}')
        self._velocity = wind_speed
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            if self._open:
                update_boundaries(self._boundary_conditions, latest_result)
                self._boundary_conditions['U'][self.name].value = self._velocity
                self._boundary_conditions['U'][self.name].save()
        except Exception as e:
            raise PhyngSetValueFailed(e)

    @property
    def temperature(self):
        """Window phyng temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets window phyng temperature by modifying the latest results
        :param temperature: temperature in K
        """
        if not (MIN_TEMP <= temperature <= MAX_TEMP):
            raise PhyngSetValueFailed(f'Temperature can only be between {MIN_TEMP} and {MAX_TEMP}, '
                                      f'not {temperature}')
        self._temperature = temperature
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            self._boundary_conditions['T'].update_time(latest_result)
            self._boundary_conditions['T'][self.name].value = self._temperature
        except Exception as e:
            raise PhyngSetValueFailed(e)

    def reload_parameters(self):
        self.open = self._open


def main():
    case_dir = 'test.case'
    door = WindowPhyng('outlet', case_dir, 'fluid', [2, 0, 2])
    door.model.show()


if __name__ == '__main__':
    main()
