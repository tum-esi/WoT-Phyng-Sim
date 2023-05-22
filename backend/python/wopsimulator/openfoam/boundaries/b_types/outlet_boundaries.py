"""Outlet boundaries type dataclasses"""
from dataclasses import dataclass


@dataclass
class InletOutlet:
    inletValue: float = None
    inletValue_uniform: bool = None
    value: float = None
    value_uniform: bool = False
    phi: float = None


@dataclass
class PressureInletOutletVelocity:
    tangentialVelocity: float = None
    tangentialVelocity_uniform: bool = None
    value: float = None
    value_uniform: bool = None
    phi: str = None


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
class TotalPressure:
    rho: str = None
    p0: float = None
    p0_uniform: bool = None
    value: float = None
    value_uniform: bool = None
    U: str = None
    phi: str = None


@dataclass
class TotalTemperature:
    rho: str = None
    gamma: float = None
    T0: float = None
    T0_uniform: bool = None
    U: str = None
    phi: str = None
    psi: str = None
