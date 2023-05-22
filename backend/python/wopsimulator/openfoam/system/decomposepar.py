import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import List

from ..common.parsing import SPECIFIC_FIELD_PATTERN

END_OF_FILE = '// ************************************************************************* //'

DECOMPOSE_DICT_FILE_TEMPLATE = r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  7
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
numberOfSubdomains  %d;

method %s;

%s
%s
"""
DECOMPOSE_DICT_FILE_TEMPLATE += END_OF_FILE

DECOMPOSE_METHODS = [
    'simple',
    'hierarchical',
    # TODO: implement:
    #  'scotch',
    #  'ptscotch',
    #  'metis',
    #  'manual'
]


@dataclass
class SimpleCoeffs:
    n: List[int] = (1, 1, 1)
    delta: float = 0.001

    @classmethod
    def get_name(cls):
        """Get class name in camel case"""
        return cls.__name__[0].lower() + cls.__name__[1:]

    def __str__(self):
        tabs = " " * 4
        name = self.get_name()
        params = self.__dict__.keys()
        max_len = max([len(param) for param in params]) + 1
        strings = []
        for val_name, value in self.__dict__.items():
            if not isinstance(value, str) and isinstance(value, Iterable):
                value = f'({" ".join([str(val) for val in value])})'
            strings.append(f'{tabs}{val_name}{" " * (max_len - len(val_name))}{value};\n')
        return f'{name}\n{{\n{"".join(strings)}}}\n'


@dataclass
class HierarchicalCoeffs(SimpleCoeffs):
    order: str = 'xyz'


class DecomposeParDict:
    _num_of_domains_str = 'numberOfSubdomains'
    _method_str = 'method'
    _simple_coeffs_str = SimpleCoeffs.get_name()
    _hierarchical_coeffs_str = HierarchicalCoeffs.get_name()

    def __init__(self, case_dir, num_of_domains, method, regions: List[str] = None, n=(1, 1, 1), delta=0.001,
                 order='xyz'):
        """
        DecomposeParDict class initialization function
        :param case_dir: case directory
        :param num_of_domains: number of decomposed domains
        :param method: decomposition method
        :param regions: decomposed regions
        :param n: decomposition parts in each direction [x, y, z]
        :param delta: cell skew factor
        :param order: decomposition order (for hierarchical), e.g., "xyz"
        """
        self._case_dir = case_dir
        self.num_of_domains = num_of_domains
        if method not in DECOMPOSE_METHODS:
            raise ValueError(f'Method {method} does not exist. '
                             f'Available methods are: {DECOMPOSE_METHODS}')
        self.method = method
        self.regions = regions if regions else []
        self.simple_coeffs = SimpleCoeffs(n, delta)
        self.hierarchical_coeffs = HierarchicalCoeffs(n, delta, order)
        # self._parse()

    def _parse(self):
        """Parses decomposeParDict"""
        if os.path.exists(path := f'{self._case_dir}/system/decomposeParDict'):
            with open(path, 'r') as f:
                lines = f.readlines()
            lines_str = ''.join(lines)
            self.num_of_domains = int(re.search(f'{self._num_of_domains_str}\\s+(\\d+);', lines_str,
                                                flags=re.MULTILINE).group(1))
            self.method = re.search(f'{self._method_str}\\s+(\\w+);', lines_str, flags=re.MULTILINE).group(1)
            result = re.search(SPECIFIC_FIELD_PATTERN % SimpleCoeffs.get_name(), lines_str,
                               flags=re.MULTILINE).group(0)
            if result:
                n_str = re.search(r' *n\s+\s*\(([^;]*)\)', result, flags=re.MULTILINE).group(1)
                self.simple_coeffs.n = [int(s) for s in n_str.split(' ')]
                self.simple_coeffs.delta = float(re.search(r' *delta\s+\s*([^;]*)', result,
                                                           flags=re.MULTILINE).group(1))
            result = re.search(SPECIFIC_FIELD_PATTERN % HierarchicalCoeffs.get_name(), lines_str,
                               flags=re.MULTILINE).group(0)
            if result:
                n_str = re.search(r' *n\s+\s*\(([^;]*)\)', result, flags=re.MULTILINE).group(1)
                self.hierarchical_coeffs.n = [int(s) for s in n_str.split(' ')]
                self.hierarchical_coeffs.delta = float(re.search(r' *delta\s+\s*([^;]*)', result,
                                                                 flags=re.MULTILINE).group(1))
                self.hierarchical_coeffs.order = re.search(r' *order\s+\s*([^;]*)', result,
                                                           flags=re.MULTILINE).group(1)

    def _save(self, data: str, rel_path: str):
        """
        Saves file to relative path from case system folder
        :param data: data to save
        :param rel_path: relative path
        """
        with open(f'{self._case_dir}/system/{rel_path}', 'w+') as f:
            f.writelines(data)

    def save(self):
        """
        Saves decomposeParDict to system and
        to regions (if available)
        """
        file_output = DECOMPOSE_DICT_FILE_TEMPLATE % (self.num_of_domains, self.method, str(self.simple_coeffs),
                                                      str(self.hierarchical_coeffs))
        for region in self.regions:
            path = f'{region}/decomposeParDict'
            self._save(file_output, path)
        self._save(file_output, 'decomposeParDict')

    def divide_domain(self, dimensions: List[float]):
        """
        Divides domain on the longest side
        :param dimensions: domain dimensions, [x, y, z]
        """
        if 2 > (dim_length := len(dimensions)) > 3:
            raise ValueError(f'Exactly 3 dimensions should be provided, not {dim_length}')
        max_length_idx = dimensions.index(max(dimensions))
        n = [1, 1, 1]
        n[max_length_idx] = self.num_of_domains
        self.simple_coeffs.n = n
        self.hierarchical_coeffs.n = n


def main():
    decompose_dict = DecomposeParDict('./case', 4, 'simple')
    decompose_dict.save()
    simple = HierarchicalCoeffs()
    print(f'{simple}')


if __name__ == '__main__':
    main()
