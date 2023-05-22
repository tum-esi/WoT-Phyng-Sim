"""Inlet boundaries type dataclasses"""
import sys
from dataclasses import dataclass
from typing import List

sys.path.append('..')
from .outlet_boundaries import InletOutlet
from .general_boundaries import FixedValue


@dataclass
class OutletInlet:
    outletValue: float = None
    outletValue_uniform: bool = None
    value: float = None
    value_uniform: bool = None
    phi: float = None


@dataclass
class FlowRateInletVelocity:
    value: float = None
    value_uniform: bool = None
    volumetricFlowRate: str = None
    massFlowRate: str = None


@dataclass
class TurbulentDigitalFilterInlet(FixedValue):
    n: List[float] = None
    L: List[float] = None
    R: List[float] = None
    R_uniform: bool = False
    Umean: List[float] = None
    Umean_uniform: bool = False
    Ubulk: float = 0
    fsm: bool = None
    Gaussian: bool = None
    fixSeed: bool = None
    continuous: bool = None
    correctFlowRate: bool = None
    mapMethod: str = None
    perturb: float = None
    C1: float = None
    C1FSM: float = None
    C2FSM: float = None


@dataclass
class TurbulentDFSEMInlet:
    delta: float = None
    nCellPerEddy: float = None
    mapMethod: str = None
    value: float = None
    value_uniform: bool = None


@dataclass
class FanPressure:
    file: str = None
    outOfBounds: str = None
    direction: str = None
    p0: float = None
    p0_uniform: bool = None
    value: float = None
    value_uniform: bool = None
    U: str = None
    phi: str = None


@dataclass
class TurbulentIntensityKineticEnergyInlet:
    intensity: float = None
    value: float = None
    value_uniform: bool = None
    U: str = None
    phi: str = None


@dataclass
class TurbulentMixingLengthDissipationRateInlet:
    mixingLength: float = None
    value: float = None
    value_uniform: bool = None
    k: str = None
    phi: str = None


@dataclass
class TurbulentMixingLengthFrequencyInlet:
    mixingLength: float = None
    value: float = None
    value_uniform: bool = None
    Cmu: float = None
    k: str = None
    phi: str = None
    # mixingLengthInlet: float = None


@dataclass
class AtmBoundaryLayer(InletOutlet):
    flowDir: List[float] = None
    zDir: List[float] = None
    Uref: float = None
    Zref: float = None
    z0: float = None
    z0_uniform: bool = None
    d: float = None
    d_uniform: bool = None
    kappa: float = None
    Cmu: float = None
    initABL: bool = None
    C1: float = None
    C2: float = None


@dataclass
class AtmBoundaryLayerInletEpsilonInlet(AtmBoundaryLayer):
    pass


@dataclass
class AtmBoundaryLayerInletK(AtmBoundaryLayer):
    pass


@dataclass
class AtmBoundaryLayerInletOmega(AtmBoundaryLayer):
    pass


@dataclass
class AtmBoundaryLayerInletVelocity(AtmBoundaryLayer):
    pass
