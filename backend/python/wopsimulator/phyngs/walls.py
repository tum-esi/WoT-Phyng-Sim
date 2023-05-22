from ..exceptions import PhyngSetValueFailed
from ..openfoam.common.filehandling import get_latest_time
from .behavior.cht import set_boundary_to_wall
from .base import Phyng
from .common import MIN_TEMP, MAX_TEMP


class WallsPhyng(Phyng):
    """
    Web of Phyngs Walls phyng class
    Combines everything what walls phyng have (wall geometry, properties, etc)
    """
    type_name = 'walls'

    def __init__(self, stl_name='', **kwargs):
        """
        Web of Phyngs walls phyng initialization function
        :param name: name of the walls phyng
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param stl_name: STL geometry name
        :param of_interface: OpenFoam interface
        """
        model_type = 'box'
        templates_dir = 'walls'
        super(WallsPhyng, self).__init__(stl_name=stl_name, model_type=model_type,
                                         templates_dir=templates_dir, **kwargs)
        self._temperature = self.environment.temperature
        self._fields = ['T']

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a room"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)

    def dump_settings(self) -> dict:
        settings = super(WallsPhyng, self).dump_settings()
        settings[self.name].update({'temperature': self._temperature})
        settings[self.name].update({'name': self.name})
        return list(settings.values())[0]

    @property
    def temperature(self):
        """Room temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets room temperature by modifying the latest results
        :param temperature: temperature in K
        """
        temperature = float(temperature)
        if temperature <= MIN_TEMP or temperature >= MAX_TEMP:
            raise PhyngSetValueFailed(f'Temperature can only be between {MIN_TEMP} and {MAX_TEMP}, '
                                      f'not {self._temperature}')
        self._temperature = temperature
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            self.environment.temperature = temperature
            self._boundary_conditions['T'].update_time(latest_result)
            self._boundary_conditions['T'].internalField.value = temperature
        except Exception as e:
            raise PhyngSetValueFailed(e)


def main():
    case_dir = 'test.case'
    heater = WallsPhyng('heater', case_dir, 'fluid', [1, 2, 3])
    heater.model.show()


if __name__ == '__main__':
    main()
