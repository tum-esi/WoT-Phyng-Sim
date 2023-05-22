"""Boundary types script. Used to instantiate various types of boundary conditions"""
from typing import Callable

from .b_types.general_boundaries import *
from .b_types.geometric_boundaries import *
from .b_types.inlet_boundaries import *
from .b_types.outlet_boundaries import *
from .b_types.wall_boundaries import *
from .b_types.coupled_boundaries import *

# Dict of available geometric boundary types and their corresponding classes
GEOMETRIC_BOUNDARY_TYPES = {
    'empty': Empty,
    'processor': Processor,
    'symmetryPlane': SymmetryPlane,
    'wedge': Wedge
}

# Dict of available general boundary types and their corresponding classes
GENERAL_BOUNDARY_TYPES = {
    'fixedValue': FixedValue,
    'fixedGradient': FixedGradient,
    'mixed': Mixed,
    'codedFixedValue': CodedFixedValue,
    'uniformFixedValue': UniformFixedValue,
    'zeroGradient': ZeroGradient,
    'calculated': Calculated
}

# Dict of available inlet boundary types and their corresponding classes
INLET_BOUNDARY_TYPES = {
    'outletInlet': OutletInlet,
    'flowRateInletVelocity': FlowRateInletVelocity,
    'turbulentDigitalFilterInlet': TurbulentDigitalFilterInlet,
    'turbulentDFSEMInlet': TurbulentDFSEMInlet,
    'fanPressure': FanPressure,
    'turbulentIntensityKineticEnergyInlet': TurbulentIntensityKineticEnergyInlet,
    'turbulentMixingLengthDissipationRateInlet': TurbulentMixingLengthDissipationRateInlet,
    'turbulentMixingLengthFrequencyInlet': TurbulentMixingLengthFrequencyInlet,
    'atmBoundaryLayerInletEpsilon': AtmBoundaryLayerInletEpsilonInlet,
    'atmBoundaryLayerInletK': AtmBoundaryLayerInletK,
    'atmBoundaryLayerInletOmega': AtmBoundaryLayerInletOmega,
    'atmBoundaryLayerInletVelocity': AtmBoundaryLayerInletVelocity,
    'atmBoundaryLayer': AtmBoundaryLayer
}

# Dict of available outlet boundary types and their corresponding classes
OUTLET_BOUNDARY_TYPES = {
    'inletOutlet': InletOutlet,
    'pressureInletOutletVelocity': PressureInletOutletVelocity,
    'fanPressure': FanPressure,
    'totalPressure': TotalPressure,
    'totalTemperature': TotalTemperature
}

# Dict of available wall boundary types and their corresponding classes
WALL_BOUNDARY_TYPES = {
    'noSlip': NoSlip,
    'translatingWallVelocity': TranslatingWallVelocity,
    'movingWallVelocity': MovingWallVelocity,
    'atmTurbulentHeatFluxTemperature': AtmTurbulentHeatFluxTemperature,
    'atmAlphatkWallFunction': AtmAlphatkWallFunction,
    'atmEpsilonWallFunction': AtmEpsilonWallFunction,
    'atmNutkWallFunction': AtmNutkWallFunction,
    'atmNutUWallFunction': AtmNutUWallFunction,
    'atmNutWallFunction': AtmNutWallFunction,
    'atmOmegaWallFunction': AtmOmegaWallFunction,
    'epsilonWallFunction': EpsilonWallFunction,
    'kLowReWallFunction': KLowReWallFunction,
    'kqRWallFunction': KqRWallFunction,
    'nutkRoughWallFunction': NutkRoughWallFunction,
    'nutkWallFunction': NutkWallFunction,
    'nutLowReWallFunction': NutLowReWallFunction,
    'nutUBlendedWallFunction': NutUBlendedWallFunction,
    'nutURoughWallFunction': NutURoughWallFunction,
    'nutUSpaldingWallFunction': NutUSpaldingWallFunction,
    'nutUTabulatedWallFunction': NutUTabulatedWallFunction,
    'nutUWallFunction': NutUWallFunction,
    'nutWallFunction': NutWallFunction,
    'omegaWallFunction': OmegaWallFunction,
    'compressible::alphatWallFunction': CompressibleAlphatWallFunction,
    'compressible::epsilonWallFunction': CompressibleEpsilonWallFunction,
    'fixedFluxPressure': FixedFluxPressure,
}

# Dict of available coupled boundary types and their corresponding classes
COUPLED_BOUNDARY_TYPES = {
    'cyclicAMI': CyclicAMI,
    'cyclic': Cyclic,
    'fan': Fan,
    'compressible::turbulentTemperatureCoupledBaffleMixed': CompressibleTurbulentTemperatureCoupledBaffleMixed
}


class BoundaryBase:
    """
    Boundary type base class. Provides common
    functionality to all boundary type classes
    """

    def __init__(self, boundary_type, subclass, *args, **kwargs):
        """
        Boundary base initialization function
        :param boundary_type: type of boundary, string
        :param subclass: boundary type subclass, extends the current
        instance to provide variables required for this boundary type
        :param args: boundary type subclass arguments
        :param kwargs: boundary type subclass key-value pairs
        """
        self.type = boundary_type
        self._save_callback = lambda inst: None
        instance = subclass(*args, **kwargs)
        for key, value in instance.__dict__.items():
            setattr(self, key, value)
        self._modified = False

    def attach_callback(self, callback: Callable):
        """
        Attaches a callback for a saving function
        :param callback: callable function
        """
        self._save_callback = callback

    def save(self):
        """Save a current boundary type via callback"""
        if self._modified:
            self._save_callback(inst=self)
            self._modified = False

    def is_modified(self):
        """Indicates if the boundary type was modified or not"""
        return self._modified

    def __str__(self):
        """Boundary type string representation"""
        output_str = '\n{'
        list_of_attr = ['type']  # make it first in the list
        list_of_attr += [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))
                         and a != 'type' and 'uniform' not in a and '_' not in a[0]]
        # Find a maximum string length to make the string look prettier
        max_length = len(max(list_of_attr, key=len)) + 1

        for name in list_of_attr:
            value = self.__getattribute__(name)
            # Do not represent a None value in string
            if value is None:
                continue
            # If instance is list - format it in OF style (e.g. (0 1 0))
            if isinstance(value, list):
                value = f'({" ".join([str(val) for val in value])})'
            # If uniform flag is present and is true - attach a uniform string
            uniform = 'uniform ' if (u_name := f'{name}_uniform') in self.__dict__ and self[u_name] else ''
            output_str += f'\n{" " * 4}{name}{" " * (max_length - len(name))}{uniform}{value};'
        output_str += '\n}'
        return output_str

    def __setattr__(self, key, value):
        """Check if the class attributes were modified or not"""
        if '_' not in key[0]:
            if key in self.__dict__ and self.__dict__[key] != value:
                self.__dict__['_modified'] = True
        self.__dict__[key] = value

    def __getitem__(self, item):
        """Allow to access attributes of a class as in dictionary"""
        return self.__dict__[item]

    def __setitem__(self, key, value):
        """Allow to set attributes of a class as in dictionary"""
        self.__dict__[key] = value

    def __iter__(self):
        """Allow to iterate over attribute names of a class"""
        for each in [b for b in self.__dict__ if '_' not in b[0]]:
            yield each

    def __delitem__(self, key):
        """Allow to delete individual attributes of a class"""
        del self.__dict__[key]


class GeometricBoundary(BoundaryBase):
    """Geometric boundary type class"""

    def __init__(self, boundary_type, subclass, *args, **kwargs):
        super(GeometricBoundary, self).__init__(boundary_type, subclass, *args, **kwargs)


class GeneralBoundary(BoundaryBase):
    """General boundary type class"""

    def __init__(self, boundary_type, subclass, *args, **kwargs):
        super(GeneralBoundary, self).__init__(boundary_type, subclass, *args, **kwargs)


class InletBoundary(BoundaryBase):
    """Inlet boundary type class"""

    def __init__(self, boundary_type, subclass, *args, **kwargs):
        super(InletBoundary, self).__init__(boundary_type, subclass, *args, **kwargs)


class OutletBoundary(BoundaryBase):
    """Outlet boundary type class"""

    def __init__(self, boundary_type, subclass, *args, **kwargs):
        super(OutletBoundary, self).__init__(boundary_type, subclass, *args, **kwargs)


class WallBoundary(BoundaryBase):
    """Wall boundary type class"""

    def __init__(self, boundary_type, subclass, *args, **kwargs):
        super(WallBoundary, self).__init__(boundary_type, subclass, *args, **kwargs)


class CoupledBoundary(BoundaryBase):
    """Coupled boundary type class"""

    def __init__(self, boundary_type, subclass, *args, **kwargs):
        super(CoupledBoundary, self).__init__(boundary_type, subclass, *args, **kwargs)


class Boundary:
    """
    Generic Boundary type class that automatically determines
    the class according to passed boundary type string
    """

    def __new__(cls, boundary_type, *args, **kwargs):
        """Instantiates a required class according to passed boundary type"""
        # Check which type of instance needs to be created (e.g. WallBoundary) and
        # which class should it be extended with (e.g. NutWallFunction)
        if boundary_type in GEOMETRIC_BOUNDARY_TYPES.keys():
            subclass_1 = GeometricBoundary
            subclass_2 = GEOMETRIC_BOUNDARY_TYPES[boundary_type]
        elif boundary_type in GENERAL_BOUNDARY_TYPES.keys():
            subclass_1 = GeneralBoundary
            subclass_2 = GENERAL_BOUNDARY_TYPES[boundary_type]
        elif boundary_type in INLET_BOUNDARY_TYPES.keys():
            subclass_1 = InletBoundary
            subclass_2 = INLET_BOUNDARY_TYPES[boundary_type]
        elif boundary_type in OUTLET_BOUNDARY_TYPES.keys():
            subclass_1 = OutletBoundary
            subclass_2 = OUTLET_BOUNDARY_TYPES[boundary_type]
        elif boundary_type in WALL_BOUNDARY_TYPES.keys():
            subclass_1 = WallBoundary
            subclass_2 = WALL_BOUNDARY_TYPES[boundary_type]
        elif boundary_type in COUPLED_BOUNDARY_TYPES.keys():
            subclass_1 = CoupledBoundary
            subclass_2 = COUPLED_BOUNDARY_TYPES[boundary_type]
            boundary_type = 'cyclic' if boundary_type == 'fan' else boundary_type
        else:
            raise ValueError(f'Incorrect boundary type {boundary_type}')
        # Create an instance of a class
        obj = subclass_1.__new__(subclass_1)
        # Initialize the instance with its boundary type and subclass with arguments
        obj.__init__(boundary_type, subclass_2, *args, **kwargs)
        return obj


def main():
    test = Boundary('fixedValue', 15, True)
    test.is_modified()
    test1 = Boundary('fixedGradient')
    test2 = Boundary('inletOutlet')
    print(1)


if __name__ == '__main__':
    main()
