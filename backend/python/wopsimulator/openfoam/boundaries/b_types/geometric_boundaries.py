"""Geometric boundaries type dataclasses"""
from dataclasses import dataclass


@dataclass
class Empty:
    pass


@dataclass
class Processor:
    pass


@dataclass
class SymmetryPlane:
    pass


@dataclass
class Wedge:
    pass
