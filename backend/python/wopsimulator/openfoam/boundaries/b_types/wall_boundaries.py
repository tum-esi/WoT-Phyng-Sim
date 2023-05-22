"""Wall boundaries type dataclasses"""
import sys
from dataclasses import dataclass

sys.path.append('..')
from .general_boundaries import FixedGradient, FixedValue


@dataclass
class NoSlip:
    pass


@dataclass
class TranslatingWallVelocity:
    U: str = None

    def __post_init__(self):
        raise NotImplementedError(f'Boundary type {self.__class__.__name__} is not implemented!')


@dataclass
class MovingWallVelocity:
    value: float = None
    value_uniform: bool = None


@dataclass
class AtmTurbulentHeatFluxTemperature(FixedGradient):
    heatSource: str = None
    alphaEff: str = None
    Cp0: float = None
    q: float = None
    q_uniform: bool = None


@dataclass
class AtmAlphatkWallFunction(FixedValue):
    Pr: float = None
    Prt: float = None
    Prt_uniform: bool = None
    z0: float = None
    z0_uniform: bool = None
    Cmu: float = None
    kappa: float = None


@dataclass
class EpsilonWallFunction(FixedValue):
    lowReCorrection: bool = None
    blending: str = None
    n: float = None


@dataclass
class AtmEpsilonWallFunction(EpsilonWallFunction):
    z0: float = None
    z0_uniform: bool = None
    Cmu: float = None
    kappa: float = None
    lowReCorrection: bool = None


@dataclass
class NutWallFunction(FixedValue):
    Cmu: float = None
    kappa: float = None
    E: float = None
    blending: float = None
    n: float = None
    U: float = None


@dataclass
class NutkWallFunction(NutWallFunction):
    pass


@dataclass
class NutUWallFunction(NutWallFunction):
    pass


@dataclass
class NutUSpaldingWallFunction(NutWallFunction):
    maxIter: float = None
    tolerance: float = None


@dataclass
class AtmNutkWallFunction(NutkWallFunction):
    z0: float = None
    z0_uniform: bool = None
    boundNut: bool = None
    Cmu: float = None
    kappa: float = None


@dataclass
class AtmNutUWallFunction(NutUWallFunction):
    z0: float = None
    z0_uniform: bool = None
    boundNut: bool = None
    kappa: float = None


@dataclass
class AtmNutWallFunction(NutkWallFunction):
    z0Min: float = None
    z0: float = None
    z0_uniform: bool = None
    kappa: float = None


@dataclass
class OmegaWallFunction(FixedValue):
    beta1: float = None
    blended: float = None
    blending: str = None
    n: float = None


@dataclass
class AtmOmegaWallFunction(OmegaWallFunction):
    z0Min: float = None
    z0: float = None
    z0_uniform: bool = None
    Cmu: float = None
    kappa: float = None


@dataclass
class KLowReWallFunction(FixedValue):
    Ceps2: float = None
    Ck: float = None
    Bk: float = None
    C: float = None


@dataclass
class KqRWallFunction:
    value: float = None
    value_uniform: bool = None


@dataclass
class NutkRoughWallFunction(NutkWallFunction):
    Ks: float = None
    Ks_uniform: bool = None
    Cs: float = None
    Cs_uniform: bool = None


@dataclass
class NutLowReWallFunction(NutWallFunction):
    pass


@dataclass
class NutUBlendedWallFunction(NutWallFunction):
    n: float = None


@dataclass
class NutURoughWallFunction(NutWallFunction):
    roughnessHeight: float = None
    roughnessConstant: float = None
    roughnessFactor: float = None
    maxIter: float = None
    tolerance: float = None


@dataclass
class NutUTabulatedWallFunction(NutWallFunction):
    uPlusTable: str = None

    def __post_init__(self):
        raise NotImplementedError(f'Boundary type {self.__class__.__name__} is not implemented!')


@dataclass
class CompressibleAlphatWallFunction:
    Prt: float = None
    value: float = None
    value_uniform: bool = None


@dataclass
class CompressibleEpsilonWallFunction:
    value: float = None
    value_uniform: bool = None


@dataclass
class FixedFluxPressure:
    gradient: float = None
    gradient_uniform: bool = None
    value: float = None
    value_uniform: bool = None
