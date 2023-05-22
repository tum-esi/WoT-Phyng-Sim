import numpy as np

from ..openfoam.common.filehandling import get_latest_time
from ..openfoam.system.snappyhexmesh import SnappyHexMeshDict, SnappyRegion
from ..geometry.manipulator import Model
from .base import Phyng
from .common import MIN_TEMP, MAX_TEMP, MIN_VEL, MAX_VEL
from .behavior.cht import set_boundary_to_wall, set_boundary_to_outlet, set_boundary_to_inlet, update_boundaries
from ..exceptions import PhyngSetValueFailed


class AcPhyng(Phyng):
    """
    Web of Phyngs Air Conditioner phyng class
    Combines everything what an AC phyng has (geometry, properties, etc)
    """
    type_name = 'ac'

    def __init__(self, name, stl_name='',
                 dimensions_in=(0, 0, 0), location_in=(0, 0, 0), rotation_in=(0, 0, 0),
                 dimensions_out=(0, 0, 0), location_out=(0, 0, 0), rotation_out=(0, 0, 0),
                 **kwargs):
        """
        Web of Phyngs heater phyng initialization function
        :param name: name of the heater phyng
        :param case_dir: case directory
        :param bg_region: background region name
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param template: template name
        :param of_interface: OpenFoam interface
        """
        self._velocity_in = [0, 0, -MIN_VEL]
        self._velocity_out = [np.sqrt(MIN_VEL), 0, -np.sqrt(MIN_VEL)]
        self._angle_out = 45
        self._enabled = False

        self.name_in = f'{name}_in'
        self.name_out = f'{name}_out'
        self.model_type_in = 'surface'
        self.model_type_out = 'surface'
        self.path_in = ''
        self.path_out = ''
        self.stl_name_in = ''
        self.stl_name_out = ''

        model_type = 'box'
        templates_dir = 'acs'
        super(AcPhyng, self).__init__(name=name, stl_name=stl_name, model_type=model_type,
                                      templates_dir=templates_dir, **kwargs)
        self._temperature = self.environment.temperature

        if self.model_type == 'stl':
            self.model_type_in = 'stl'
            self.model_type_out = 'stl'
            self.stl_name_in = f'{stl_name}_in'
            self.stl_name_out = f'{stl_name}_out'
            self.path_in = self._get_stl(f'{self.stl_name_in}{"" if stl_name[-4:] == ".stl" else ".stl"}',
                                         templates_dir)
            self.path_out = self._get_stl(f'{self.stl_name_out}{"" if stl_name[-4:] == ".stl" else ".stl"}',
                                          templates_dir)

        self.model_in = Model(
            self.name_in,
            self.model_type_in,
            dimensions_in,
            location_in,
            rotation_in,
            True,
            self.path_in,
            self._case_dir
        )
        self.model_out = Model(
            self.name_out,
            self.model_type_out,
            dimensions_out,
            location_out,
            rotation_out,
            True,
            self.path_out,
            self._case_dir
        )

        if self.model_type != 'stl':
            self.model.geometry.cut_surface(self.model_in.geometry)
            self.model.geometry.cut_surface(self.model_out.geometry)

        self._fields = 'all'

    def _add_initial_boundaries(self):
        """Adds initial boundaries of a door phyng"""
        set_boundary_to_wall(self.name, self._boundary_conditions, self._temperature)
        set_boundary_to_wall(self.name_in, self._boundary_conditions, self._temperature)
        set_boundary_to_wall(self.name_out, self._boundary_conditions, self._temperature)

    def dump_settings(self) -> dict:
        dump = {self.name: {
            'dimensions': self.model.dimensions,
            'location': self.model.location,
            'rotation': self.model.rotation,
            'stl_name': self.stl_name,
            'dimensions_in': self.model_in.dimensions,
            'location_in': self.model_in.location,
            'rotation_in': self.model_in.rotation,
            'stl_name_in': self.stl_name_in,
            'dimensions_out': self.model_out.dimensions,
            'location_out': self.model_out.location,
            'rotation_out': self.model_out.rotation,
            'stl_name_out': self.stl_name_out,
            'enabled': self.enabled,
            'velocity': self.velocity,
            'temperature': self.temperature,
            'angle': self.angle,
        }}
        return dump

    def set_dimensions(self, dimensions: list):
        raise NotImplementedError('Changing dimensions of an AC is not yet implemented')

    def prepare(self):
        """Saves the model of an instance to a proper location (constant/triSurface)"""
        super(AcPhyng, self).prepare()
        self.path_in = f'{self._case_dir}/constant/triSurface/{self.name_in}.stl'
        self.path_out = f'{self._case_dir}/constant/triSurface/{self.name_out}.stl'
        self.model_in.save(f'{self._case_dir}/constant/triSurface')
        self.model_out.save(f'{self._case_dir}/constant/triSurface')

    def bind_snappy(self, snappy_dict: SnappyHexMeshDict, snappy_type: str, region_type='wall', refinement_level=0):
        """
        Binds a snappyHexMeshDict and Phyng type for it
        Must be called before the case is setup
        :param snappy_dict: snappyHexMeshDict class instance
        :param snappy_type: type of phyng representation in snappyHexMeshDict
        :param region_type: initial region type
        :param refinement_level: mesh refinement level
        """
        super(AcPhyng, self).bind_snappy(snappy_dict, snappy_type, 'wall', refinement_level)
        snappy_in = SnappyRegion(self.name_in, region_type, refinement_level)
        snappy_out = SnappyRegion(self.name_out, region_type, refinement_level)
        self.snappy = [self.snappy, snappy_in, snappy_out]

    def destroy(self):
        super(AcPhyng, self).destroy()
        self._destroy_by_name(self.name_in)
        self._destroy_by_name(self.name_out)

    def remove(self):
        super(AcPhyng, self).remove()
        self.model_in.remove()
        self.model_out.remove()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self._snappy_dict is None or self._boundary_conditions is None:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            if value:
                set_boundary_to_outlet(self.name_in, self._boundary_conditions, self._velocity_in, self._temperature,
                                       latest_result, bg_name=self._bg_region, of_interface=self._of_interface)
                set_boundary_to_inlet(self.name_out, self._boundary_conditions, self._velocity_out,
                                      self.environment.temperature, latest_result,
                                      bg_name=self._bg_region, of_interface=self._of_interface)
            else:
                set_boundary_to_wall(self.name_in, self._boundary_conditions, self.environment.temperature,
                                     latest_result, bg_name=self._bg_region, of_interface=self._of_interface)
                set_boundary_to_wall(self.name_out, self._boundary_conditions, self.environment.temperature,
                                     latest_result, bg_name=self._bg_region, of_interface=self._of_interface)
                self._velocity_in = [0, 0, -0.01]
                self._velocity_out = [0.001, 0, -0.001]
                self._angle_out = 45
                self._temperature = self.environment.temperature
        except Exception as e:
            raise PhyngSetValueFailed(e)
        self._enabled = value

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        temperature = float(temperature)
        if not (MIN_TEMP <= temperature and temperature <= MAX_TEMP):
            raise PhyngSetValueFailed(f'Temperature can only be between {MIN_TEMP} and {MAX_TEMP}, '
                                      f'not {temperature}')
        self._temperature = temperature
        if self._temperature <= MIN_TEMP or self._temperature >= MAX_TEMP:
            raise PhyngSetValueFailed(f'Temperature can only be between {MIN_TEMP} and {MAX_TEMP}, '
                                      f'not {self._temperature}')
        if self._snappy_dict is None or self._boundary_conditions is None or not self._enabled:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            self._boundary_conditions['T'].update_time(latest_result)
            self._boundary_conditions['T'][self.name_in].value = self.environment.temperature
            self._boundary_conditions['T'][self.name_out].value = self._temperature
        except Exception as e:
            raise PhyngSetValueFailed(e)

    @property
    def velocity(self):
        return -self._velocity_in[2]

    @velocity.setter
    def velocity(self, value):
        value = float(value)
        if not (MIN_VEL <= value <= MAX_VEL):
            raise PhyngSetValueFailed(f'Velocity can only be between {MIN_VEL} and {MAX_VEL} m/s, '
                                      f'not {value}')
        self._velocity_in = [0, 0, -value]
        vel_x, vel_y = 0, 0
        vel_z = -value * np.cos(np.deg2rad(abs(self._angle_out)))
        vel_side = value * np.sin(np.deg2rad(self._angle_out))
        if self.model.dimensions[0] > self.model.dimensions[1]:
            vel_y = vel_side
        else:
            vel_x = vel_side
        self._velocity_out = [vel_x, vel_y, vel_z]
        if self._snappy_dict is None or self._boundary_conditions is None or not self._enabled:
            return
        latest_result = get_latest_time(self._case_dir)
        try:
            update_boundaries(self._boundary_conditions, latest_result)
            self._boundary_conditions['U'][self.name_in].value = self._velocity_in
            self._boundary_conditions['U'][self.name_out].value = self._velocity_out
            self._boundary_conditions['U'][self.name_in].save()
            self._boundary_conditions['U'][self.name_out].save()
        except Exception as e:
            raise PhyngSetValueFailed(e)

    @property
    def angle(self):
        return self._angle_out

    @angle.setter
    def angle(self, value):
        value = float(value)
        if value > 45 or value < -45:
            raise PhyngSetValueFailed(f'Angle can only be between -45 and 45 degrees')
        self._angle_out = value
        self.velocity = self.velocity

    def reload_parameters(self):
        self.enabled = self._enabled
