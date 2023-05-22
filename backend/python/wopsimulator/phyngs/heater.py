from ..exceptions import PhyngSetValueFailed
from ..openfoam.system.snappyhexmesh import SnappyHexMeshDict
from ..openfoam.common.filehandling import get_latest_time
from ..openfoam.constant.material_properties import SOLID_MATERIALS
from .behavior.cht import set_boundary_to_heater
from .base import Phyng
from .common import MIN_TEMP


class HeaterPhyng(Phyng):
    """
    Web of Phyngs Heater phyng class
    Combines everything what a heater phyng has (geometry, properties, etc)
    """
    type_name = 'heater'

    def __init__(self, name, material='copper', stl_name='', **kwargs):
        """
        Web of Phyngs heater phyng initialization function
        :param name: name of the heater phyng
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param material: heater phyng material
        :param stl_name: STL geometry name
        :param of_interface: OpenFoam interface
        """
        model_type = 'box'
        templates_dir = 'heaters'
        super(HeaterPhyng, self).__init__(name=name, model_type=model_type, stl_name=stl_name,
                                          templates_dir=templates_dir, **kwargs)
        self._temperature = self.environment.temperature
        self._region = name
        self._fields = ['T']
        self._material = material

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a heater phyng"""
        set_boundary_to_heater(self.name, self._bg_region, self._boundary_conditions, self.temperature)
        self._boundary_conditions[self.name]['T'].internalField.value = self._temperature

    def bind_snappy(self, snappy_dict: SnappyHexMeshDict, snappy_type: str, region_type='wall', refinement_level=0):
        super(HeaterPhyng, self).bind_snappy(snappy_dict, snappy_type, region_type, refinement_level)
        self.material = self._material

    def bind_region_boundaries(self, region_boundaries: dict):
        """
        Binds the thing boundary conditions to a class
        Binding regions can only be performed once a case is setup,
        i.e., the boundary files are produced
        :param region_boundaries: dict of a region boundary conditions
        """
        if region_boundaries:
            self._boundary_conditions = region_boundaries
            self._add_initial_boundaries()

    def dump_settings(self) -> dict:
        settings = super(HeaterPhyng, self).dump_settings()
        settings[self.name].update({'temperature': self._temperature})
        settings[self.name].update({'material': self.material})
        return settings

    @property
    def material(self):
        return self.snappy.material

    @material.setter
    def material(self, material):
        if material not in SOLID_MATERIALS:
            raise ValueError(f'Phyng material cannot be {material}, '
                             f'possible values are {", ".join(SOLID_MATERIALS)}')
        self.snappy.material = material

    @property
    def temperature(self):
        """Temperature getter"""
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        """
        Sets heater phyng temperature by modifying the latest results
        :param temperature: temperature in K
        """
        if temperature <= MIN_TEMP:
            raise PhyngSetValueFailed(f'Heater temperature can only be higher than {MIN_TEMP}, '
                                      f'not {self._temperature}')
        self._temperature = temperature
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            self._boundary_conditions[self.name]['T'].update_time(latest_result)
            if latest_result != '0':
                heater_boundary_name = f'{self.name}_to_{self._bg_region}'
                t = self._boundary_conditions[self.name]['T']
                t.internalField.value = temperature
                t[heater_boundary_name].value = temperature
            else:
                set_boundary_to_heater(self.name, self._bg_region, self._boundary_conditions, self._temperature,
                                       latest_result)
        except Exception as e:
            raise PhyngSetValueFailed(e)


def main():
    case_dir = 'test.case'
    heater = HeaterPhyng('heater', case_dir, 'fluid', [1, 2, 3])
    heater.model.show()


if __name__ == '__main__':
    main()
