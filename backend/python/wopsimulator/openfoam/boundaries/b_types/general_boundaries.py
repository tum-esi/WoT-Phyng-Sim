"""General boundaries type dataclasses"""
from dataclasses import dataclass


@dataclass
class FixedValue:
    value: float = None
    value_uniform: bool = None


@dataclass
class FixedGradient:
    gradient: float = None
    gradient_uniform: bool = None


@dataclass
class Mixed:
    refValue: float = None
    refValue_uniform: bool = None
    refGradient: float = None
    refGradient_uniform: bool = None
    valueFraction: float = None
    valueFraction_uniform: bool = None


@dataclass
class CodedFixedValue:
    value: float = None
    value_uniform: bool = None
    redirectType: str = None
    code: str = None


@dataclass
class UniformFixedValue:
    uniformValue: str = None

    def __post_init__(self):
        raise NotImplementedError('uniformValue is actually a table, so it should be implemented')


@dataclass
class ZeroGradient:
    pass


@dataclass
class Calculated:
    value: float = None
    value_uniform: bool = None
