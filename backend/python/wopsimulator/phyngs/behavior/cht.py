from typing import List

from ...openfoam.boundaries.boundary_types import Boundary


def update_boundaries(boundary: dict, time: str):
    """
    Updates selected boundaries with latest time
    :param boundary: boundary region dict
    :param time: time to update from
    """
    boundary['alphat'].update_time(time)
    boundary['omega'].update_time(time)
    boundary['k'].update_time(time)
    boundary['nut'].update_time(time)
    boundary['p'].update_time(time)
    boundary['p_rgh'].update_time(time)
    boundary['T'].update_time(time)
    boundary['U'].update_time(time)


def set_boundary_to_wall(boundary_name: str, boundary: dict, temperature: float, time: str = '0', bg_name: str = None,
                         of_interface=None):
    """
    Sets boundary to wall type
    :param boundary_name: name of the boundary (e.g., inlet)
    :param boundary: boundary region dict
    :param temperature: temperature to set on wall, K
    :param time: time to update from
    :param bg_name: background region name
    :param of_interface: OpenFOAM interface
    """
    update_boundaries(boundary, time)
    alphat = boundary['alphat']
    epsilon = boundary['epsilon']
    k = boundary['k']
    nut = boundary['nut']
    omega = boundary['omega']
    p = boundary['p']
    p_rgh = boundary['p_rgh']
    t = boundary['T']
    u = boundary['U']
    alphat[boundary_name] = Boundary('compressible::alphatWallFunction', value=0, value_uniform=True)
    epsilon[boundary_name] = Boundary('compressible::epsilonWallFunction', value=0.001, value_uniform=True)
    k[boundary_name] = Boundary('kqRWallFunction', value=0.02, value_uniform=True)
    nut[boundary_name] = Boundary('nutkWallFunction', value=0, value_uniform=True)
    omega[boundary_name] = Boundary('omegaWallFunction', value=10, value_uniform=True)
    p[boundary_name] = Boundary('calculated', value=1e5, value_uniform=True)
    p_rgh[boundary_name] = Boundary('fixedFluxPressure', value=1e5, value_uniform=True)
    t[boundary_name] = Boundary('fixedValue', value=temperature, value_uniform=True)
    u[boundary_name] = Boundary('noSlip')
    if of_interface and bg_name:
        of_interface.run_foam_dictionary(f'constant/{bg_name}/polyMesh/boundary',
                                         f'entry0.{boundary_name}.type', 'wall')


def set_boundary_to_inlet(boundary_name: str, boundary: dict, velocity: List[float], temperature: float,
                          time: str = '0', bg_name: str = None, of_interface=None):
    """
    Sets boundary to inlet type
    :param boundary_name: name of the boundary (e.g., inlet)
    :param boundary: boundary region dict
    :param velocity: velocity to set on inlet, m/s [0, 1, 0]
    :param temperature: temperature to set on inlet, K
    :param time: time to update from
    :param bg_name: background region name
    :param of_interface: OpenFOAM interface
    """
    update_boundaries(boundary, time)
    alphat = boundary['alphat']
    epsilon = boundary['epsilon']
    k = boundary['k']
    nut = boundary['nut']
    omega = boundary['omega']
    p = boundary['p']
    p_rgh = boundary['p_rgh']
    t = boundary['T']
    u = boundary['U']
    alphat[boundary_name] = Boundary('calculated', value=0, value_uniform=True)
    epsilon[boundary_name] = Boundary('turbulentMixingLengthDissipationRateInlet', mixingLength=0.007,
                                      value=0.001, value_uniform=True)
    k[boundary_name] = Boundary('turbulentIntensityKineticEnergyInlet', intensity=0.01,
                                value=0.02, value_uniform=True)
    nut[boundary_name] = Boundary('zeroGradient')
    omega[boundary_name] = Boundary('turbulentMixingLengthFrequencyInlet', mixingLength=0.0035,
                                    value=10, value_uniform=True)
    p[boundary_name] = Boundary('calculated', value=1e5, value_uniform=True)
    p_rgh[boundary_name] = Boundary('fixedFluxPressure', value=1e5, value_uniform=True)
    t[boundary_name] = Boundary('fixedValue', value=temperature, value_uniform=True)
    u[boundary_name] = Boundary('fixedValue', value=velocity, value_uniform=True)
    if of_interface and bg_name:
        of_interface.run_foam_dictionary(f'constant/{bg_name}/polyMesh/boundary',
                                         f'entry0.{boundary_name}.type', 'patch')


def set_boundary_to_outlet(boundary_name: str, boundary: dict, velocity: List[float], temperature: float,
                           time: str = '0', bg_name: str = None, of_interface=None):
    """
    Sets boundary to outlet type
    :param boundary_name: name of the boundary (e.g., inlet)
    :param boundary: boundary region dict
    :param velocity: velocity to set on outlet, m/s [0, 1, 0]
    :param temperature: temperature to set on outlet, K
    :param time: time to update from
    :param bg_name: background region name
    :param of_interface: OpenFOAM interface
    """
    update_boundaries(boundary, time)
    alphat = boundary['alphat']
    epsilon = boundary['epsilon']
    k = boundary['k']
    nut = boundary['nut']
    omega = boundary['omega']
    p = boundary['p']
    p_rgh = boundary['p_rgh']
    t = boundary['T']
    u = boundary['U']
    p[boundary_name] = Boundary('calculated', value=1e5, value_uniform=True)
    p_rgh[boundary_name] = Boundary('fixedValue', value=1e5, value_uniform=True)
    alphat[boundary_name] = Boundary('calculated', value=0, value_uniform=True)
    k[boundary_name] = Boundary('zeroGradient')
    nut[boundary_name] = Boundary('zeroGradient')
    omega[boundary_name] = Boundary('zeroGradient')
    t[boundary_name] = Boundary('inletOutlet', value=temperature, value_uniform=True, inletValue=temperature)
    u[boundary_name] = Boundary('pressureInletOutletVelocity', value=velocity, value_uniform=True)
    epsilon[boundary_name] = Boundary('inletOutlet', value=0.001, value_uniform=True,
                                      inletValue=0.001, inletValue_uniform=True)
    if of_interface and bg_name:
        of_interface.run_foam_dictionary(f'constant/{bg_name}/polyMesh/boundary',
                                         f'entry0.{boundary_name}.type', 'patch')


def set_boundary_to_heater(boundary_name: str, background_region_name: str, boundaries: dict, temperature: float,
                           time: str = '0'):
    """
    Sets boundary to heater type
    :param boundary_name: name of the boundary (e.g., inlet)
    :param background_region_name: background region name (e.g., fluid)
    :param boundaries: boundary regions dict
    :param temperature: temperature to set on heater, K
    :param time: time to update from
    """
    boundaries[boundary_name]['p'].update_time(time)
    boundaries[boundary_name]['T'].update_time(time)
    update_boundaries(boundaries[background_region_name], time)
    heater_boundary_name = f'{boundary_name}_to_{background_region_name}'
    bg_boundary_name = f'{background_region_name}_to_{boundary_name}'
    p = boundaries[boundary_name]['p']
    t = boundaries[boundary_name]['T']
    bg_alphat = boundaries[background_region_name]['alphat']
    bg_epsilon = boundaries[background_region_name]['epsilon']
    bg_k = boundaries[background_region_name]['k']
    bg_nut = boundaries[background_region_name]['nut']
    bg_omega = boundaries[background_region_name]['omega']
    bg_p = boundaries[background_region_name]['p']
    bg_p_rgh = boundaries[background_region_name]['p_rgh']
    bg_t = boundaries[background_region_name]['T']
    bg_u = boundaries[background_region_name]['U']
    p[heater_boundary_name] = Boundary('calculated', value=1e5, value_uniform=True)
    t[heater_boundary_name] = Boundary('compressible::turbulentTemperatureCoupledBaffleMixed',
                                       value='$internalField', kappaMethod='solidThermo', kappa='kappa', Tnbr='T')

    bg_alphat[bg_boundary_name] = Boundary('compressible::alphatWallFunction', value=0, value_uniform=True)
    bg_epsilon[bg_boundary_name] = Boundary('compressible::epsilonWallFunction', value=0.001, value_uniform=True)
    bg_k[bg_boundary_name] = Boundary('kqRWallFunction', value=0.02, value_uniform=True)
    bg_nut[bg_boundary_name] = Boundary('nutkWallFunction', value=0, value_uniform=True)
    bg_omega[bg_boundary_name] = Boundary('omegaWallFunction', value=10, value_uniform=True)
    bg_p[bg_boundary_name] = Boundary('calculated', value=1e5, value_uniform=True)
    bg_p_rgh[bg_boundary_name] = Boundary('fixedFluxPressure', value=1e5, value_uniform=True)
    bg_t[bg_boundary_name] = Boundary('compressible::turbulentTemperatureCoupledBaffleMixed',
                                      value='$internalField', kappaMethod='fluidThermo', kappa='kappa', Tnbr='T')
    bg_u[bg_boundary_name] = Boundary('noSlip')

    t.internalField.value = temperature
    if time != '0':
        t[heater_boundary_name].value = temperature
