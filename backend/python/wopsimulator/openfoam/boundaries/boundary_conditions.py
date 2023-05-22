"""Boundary conditions script with corresponding field classes"""
import re
import os
import logging
from dataclasses import dataclass
from typing import Union, List, Callable

from ..common.parsing import INTERNAL_FIELD_PATTERN, BOUNDARY_FIELD_PATTERN, LIST_OR_VALUE_PATTERN, \
    SPECIFIC_FIELD_PATTERN, SPECIFIC_FIELD_VALUES_PATTERN, SPECIAL_CHARACTERS
from ..common.parsing import NUMBER_PATTERN, VECTOR_PATTERN, FIELD_NAME_PATTERN
from .boundary_types import Boundary, BoundaryBase

BOUNDARY_CONDITION_FILE_TEMPLATE = \
    r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    class       %s;
    object      %s;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      %s;

boundaryField
{
    #includeEtc "caseDicts/setConstraintTypes"
}

// ************************************************************************* //
"""

logger = logging.getLogger('openfoam')


@dataclass
class InternalField(BoundaryBase):
    """Internal field dataclass, individual for each boundary conditions file"""
    value: Union[float, str, List[float]]
    value_uniform: bool = False
    _save_callback: Callable = None
    _modified: bool = False

    def save(self):
        """Save an internal field via callback"""
        if self._modified:
            self._save_callback()
            self._modified = False

    def __str__(self):
        """Internal field string representation"""
        value = self.value if not isinstance(self.value, list) else f'({" ".join(self.value)})'
        return f'internalField {"uniform " if self.value_uniform else ""}{value};\n'


class BoundaryConditionBase:
    """
    Boundary condition base class. Provides common
    functionality to all boundary condition classes
    of all fields (e.g. T)
    """
    _case_dir = ''

    def __init__(self, case_dir, field, field_class, dimensions, region=None):
        """
        Boundary condition base initialization function
        :param case_dir: case directory
        :param field: probe field (e.g., T)
        :param region: region to probe
        :param field_class: field class (volScalarField or volVectorField),
        specified in the file header
        :param dimensions: field dimensions specified in the file [kg m s K mol A cd]
        :param region: region for multiregion case (e.g. CHT)
        """
        self._case_dir = case_dir
        self._filepath = f'{case_dir}/%s/{(region + "/") if region else ""}{field}'
        self._field = field
        self._region = region
        self._time = '0'
        # Parse file if exists or create a new one
        if os.path.exists(self._filepath % '0'):
            logger.debug(f'Found {field} boundary{" in " + region + " region" if region else ""}')
            self._file_parse()
        else:
            logger.debug(f'Creating {field} boundary{" in " + region + " region" if region else ""}')
            self._file_create(field_class, dimensions)
        logger.debug(f'{field} boundary{" in " + region + " region" if region else ""} was initialized')

    @staticmethod
    def _get_internal_field(lines_str: str):
        """
        Function to get internal field and it's parameters from a file converted to one string
        :param lines_str: file lines as one string
        :return: internalField dictionary
        """
        # Find an internal field pattern
        internal_field_match = re.search(INTERNAL_FIELD_PATTERN, lines_str, flags=re.MULTILINE)
        if not internal_field_match:
            return {}
        # Check if parsed internal field is a list or a value
        # Note that only the LAST VALUE from the list is taken and NOT the WHOLE LIST!
        if lst_type := internal_field_match.group(7):
            lst_str = internal_field_match.group(9)
            lst_size = int(internal_field_match.group(8))
            if lst_type == 'vector':
                values = re.findall(VECTOR_PATTERN, lst_str, flags=re.MULTILINE)
                value = [float(val) for val in values[-1]]
            else:
                value = float(re.findall(f'\\s({NUMBER_PATTERN})\\n', lst_str, flags=re.MULTILINE)[-1])
            value = {
                'value': value
            }
        else:
            if internal_field_match.group(4):
                value = [float(internal_field_match.group(i)) for i in range(4, 7)]
            else:
                if (val := internal_field_match.group(3)).isnumeric():
                    value = float(val)
                else:
                    value = val
            value = {
                'value': value,
                'value_uniform': True if internal_field_match.group(2) else False
            }
        return {'internalField': value}

    @staticmethod
    def _get_boundary_fields(lines_str: str):
        """
        Function to get boundary fields and their parameters from a file converted to one string
        :param lines_str: file lines as one string
        :return: dictionary of boundary type dictionaries
        """
        # Find boundary fields and separate them into separate strings
        fields = re.search(BOUNDARY_FIELD_PATTERN, lines_str, flags=re.MULTILINE).group(1)
        fields = re.findall(f'{FIELD_NAME_PATTERN}{{\\s*([^}}]*)}}\\s*', fields, flags=re.MULTILINE)
        boundary_fields = {}
        for name, val_str in fields:
            f_contents = re.findall(f'^(?!\\/\\/)\\s*{FIELD_NAME_PATTERN}{LIST_OR_VALUE_PATTERN}', val_str,
                                    flags=re.MULTILINE)
            boundary_fields.update({name: {}})
            for f_content in f_contents:
                val_name = f_content[0]
                # Check if parsed field is a list or a value
                # Note that only the LAST VALUE from the list is taken and NOT the WHOLE LIST!
                if lst_type := f_content[7]:
                    if lst_type == 'vector':
                        vectors = re.findall(VECTOR_PATTERN, f_content[9], flags=re.MULTILINE)
                        val = [float(val) for val in vectors[-1]]
                    else:
                        temp = re.findall(f'\\s({NUMBER_PATTERN})\\n', f_content[9], flags=re.MULTILINE)
                        if temp and temp[-1]:
                            val = float(temp[-1])
                else:
                    if f_content[4]:
                        val = [float(f_content[i]) for i in range(4, 7)]
                    else:
                        if f_content[3].isnumeric():
                            val = float(f_content[3])
                        else:
                            val = f_content[3]
                if f_content[2]:
                    boundary_fields[name].update({f'{val_name}_uniform': True})
                boundary_fields[name].update({val_name: val})

        return boundary_fields

    def _file_parse(self):
        """Parses boundary condition file"""
        filepath = self._filepath % self._time
        if not os.path.exists(filepath):
            raise FileNotFoundError(f'File {filepath} does not exist')
        with open(filepath, 'r') as f:
            lines = f.readlines()
        lines_str = ''.join(lines)
        # Parse and initialize internal field if it exists
        internal_field_dict = self._get_internal_field(lines_str)
        if internal_field_dict:
            self.__dict__.update({'internalField': InternalField(**internal_field_dict['internalField'])})
            self['internalField'].attach_callback(self._file_update_internal_field)
        # Parse boundary fields and initialize them
        boundary_fields_dict = self._get_boundary_fields(lines_str)
        boundary_fields = {}
        for name, fields in boundary_fields_dict.items():
            if 'type' in fields:
                field_type = fields['type']
                del fields['type']
                boundary_fields.update({name: Boundary(field_type, **fields)})
                boundary_fields[name].attach_callback(self.save_boundary)
        self.__dict__.update(boundary_fields)

    def _file_create(self, field_class, dimensions):
        """Create a new field boundary condition file"""
        filepath = self._filepath % self._time
        with open(filepath, 'w') as f:
            f.writelines(BOUNDARY_CONDITION_FILE_TEMPLATE % (field_class, self._field, dimensions))

    def _file_write_decorator(func):
        """
        File write decorator, used to decorate function that do changes to file
        Declared as inside a class in order to have access to class specific functions
        """

        def wrapper(self, *args, **kwargs):
            filepath = self._filepath % self._time
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                lines_str = ''.join(lines)
                lines_str = func(self, *args, **kwargs, lines_str=lines_str)
                with open(filepath, 'w') as f:
                    f.writelines(lines_str)

        return wrapper

    @_file_write_decorator
    def _file_add_internal_field(self, lines_str=None):
        """
        Adds internalField to file
        Should only be used if internal field is not present in file
        :param lines_str: file lines as one string
        :return: modified file lines as one string
        """
        if 'internalField' not in self.__dict__:
            raise Exception(f'Internal field is not defined')
        return re.sub(r'boundaryField', f'{self["internalField"]}\nboundaryField', lines_str)

    @_file_write_decorator
    def _file_update_internal_field(self, lines_str=None):
        """
        Update internalField in file
        Should only be used if internal field is present in file
        :param lines_str: file lines as one string
        :return: modified file lines as one string
        """
        internal_field_match = re.search(INTERNAL_FIELD_PATTERN, lines_str, flags=re.MULTILINE)
        string_orig = internal_field_match.group()
        string_new = string_orig[:]
        if lst_type := internal_field_match.group(7):
            lst_str = internal_field_match.group(9)
            value = self['internalField'].value
            if lst_type == 'vector':
                lst_str_new = re.sub(VECTOR_PATTERN, f'({value[0]} {value[1]} {value[2]})\n', lst_str)
            else:
                lst_str_new = re.sub(f'\\s*{NUMBER_PATTERN}\\n', f'\n{value}', lst_str) + '\n'
            string_new = string_new.replace(lst_str, lst_str_new)
        else:
            value = self['internalField'].value
            if not internal_field_match.group(2) and self['internalField'].value_uniform:
                string_new = string_new.replace('internalField', 'internalField uniform')
            elif internal_field_match.group(2) and not self['internalField'].value_uniform:
                string_new = string_new.replace('internalField uniform', 'internalField')
            if internal_field_match.group(4):
                string = f'({value[0]} {value[1]} {value[2]})'
            else:
                string = f'{value}'
            string_new = string_new.replace(internal_field_match.group(3), string)
        return lines_str.replace(string_orig, string_new)

    @_file_write_decorator
    def _file_add_boundary(self, name, lines_str=None):
        """
        Adds boundary with a specified name to file
        :param name: boundary name to add
        :param lines_str: file lines as one string
        :return: modified file lines as one string
        """
        if name not in self.__dict__:
            raise Exception(f'Boundary {name} is not in use')
        string = str(self[name]).replace('\n', f'\n{" " * 4}')
        return re.sub(r'boundaryField\s*{', f'boundaryField\n{{\n{" " * 4}{name}{string}\n', lines_str)

    @_file_write_decorator
    def _file_remove_boundary(self, name, lines_str=None):
        """
        Removes boundary with a specified name from file
        :param name: boundary name to remove
        :param lines_str: file lines as one string
        :return: modified file lines as one string
        """
        find_name = ''.join([f'\\{c}' if c in SPECIAL_CHARACTERS else c for c in name])
        field_pattern = f'{SPECIFIC_FIELD_PATTERN % find_name}\n*'
        return re.sub(field_pattern, '', lines_str)

    @_file_write_decorator
    def _file_update_boundary(self, name, lines_str=None):
        """
        Updates boundary with a specified name in file
        :param name: boundary name to update
        :param lines_str: file lines as one string
        :return: modified file lines as one string
        """
        field_pattern = SPECIFIC_FIELD_VALUES_PATTERN % name
        boundary_field_str = re.search(field_pattern, lines_str, flags=re.MULTILINE).group()
        values = re.findall(f'{FIELD_NAME_PATTERN}{LIST_OR_VALUE_PATTERN}', boundary_field_str, flags=re.MULTILINE)
        new_boundary_field_str = boundary_field_str[:]
        for value in values:
            val_name = value[0]
            if lst_type := value[7]:
                new_value = self[name][val_name]
                if lst_type == 'vector':
                    lst_str_new = re.sub(VECTOR_PATTERN, f'({new_value[0]} {new_value[1]} {new_value[2]})\n', value[9])
                else:
                    lst_str_new = re.sub(f'\\s*{NUMBER_PATTERN}\\n', f'\n{new_value}', value[9]) + '\n'
                lines_str = lines_str.replace(value[9], lst_str_new)
            else:
                new_value = self[name][val_name]
                append_uniform = False
                old_value_line = re.search(f'.*{val_name}.*', boundary_field_str, flags=re.MULTILINE).group()
                if value[2] and f'{val_name}_uniform' in self[name] and not self[name][f'{val_name}_uniform']:
                    old_value_line = old_value_line.replace('uniform ', '')
                elif not value[2] and f'{val_name}_uniform' in self[name] and self[name][f'{val_name}_uniform']:
                    append_uniform = True
                string = f'{"uniform " if append_uniform else ""}'
                if value[4]:
                    string += f'({new_value[0]} {new_value[1]} {new_value[2]})'
                    new_value_line = re.sub(VECTOR_PATTERN, string, old_value_line)
                else:
                    string += f'{new_value}'
                    if value[3].isnumeric():
                        new_value_line = re.sub(f'{NUMBER_PATTERN};', f'{string};', old_value_line)
                    else:
                        new_value_line = old_value_line.replace(value[3], string)
                new_boundary_field_str = new_boundary_field_str.replace(old_value_line, new_value_line)
        return lines_str.replace(boundary_field_str, new_boundary_field_str)

    def save_boundary(self, name=None, inst=None):
        """
        Saves boundary with a specified name or instance in file
        Either a boundary name or directly a boundary instance must be provided
        :param name: boundary name to save
        :param inst: boundary instance to save
        """
        if inst and not name:
            name = [name for name in self.__dict__ if self[name] == inst][0]
        else:
            raise AttributeError('Either name or instance has to be specified')
        self._file_update_boundary(name)

    def update_time(self, current_time):
        """
        Updates boundary conditions according to provided time
        :param current_time: time, must correspond to a timed result folder
        """
        if self._time != current_time:
            self._time = current_time
            self._file_parse()

    def save(self):
        """Saves all modified boundaries of a boundary condition"""
        for b_condition_name in self:
            self[b_condition_name].save()

    def __getitem__(self, item):
        """Allow to access attributes of a class as in dictionary"""
        return self.__dict__[item]

    def __setitem__(self, key, value):
        """
        Allow to set attributes of a class as in dictionary
        If a boundary is redefine with new boundary type class
        and the types are different - a boundary is replaced and
        rewritten in the file. Otherwise, the boundary values
        are simply updated with new values
        """
        if key == 'internalField':
            need_add = False
            if 'internalField' not in self.__dict__:
                need_add = True
            self.__dict__['internalField'] = value
            self['internalField'].attach_callback(self._file_update_internal_field)
            if need_add:
                self._file_add_internal_field()
            else:
                self._file_update_internal_field()
        else:
            if key in self.__dict__:
                if self[key].type == value.type:
                    # If type is the same - simply update values with new once
                    for value_name in self[key]:
                        if value[value_name] is not None:
                            self[key][value_name] = value[value_name]
                    return
                self._file_remove_boundary(key)
            else:
                if self._time != '0':
                    raise Exception('New boundaries can only be added on time 0 (initial)')
            self.__dict__[key] = value
            self[key].attach_callback(self.save_boundary)
            self._file_add_boundary(key)

    def __iter__(self):
        """Allow to iterate over attribute names of a class"""
        for each in [b for b in self.__dict__ if '_' not in b[0]]:
            yield each

    def __delitem__(self, key):
        """
        Allow to delete individual attributes of a class
        An internal field cannot be deleted
        """
        if key != 'internalField':
            del self.__dict__[key]
            self._file_remove_boundary(key)


class BoundaryConditionT(BoundaryConditionBase):
    """Temperature boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionT, self).__init__(case_dir, 'T', 'volScalarField',
                                                 '[0 0 0 1 0 0 0]', region)


class BoundaryConditionAlphat(BoundaryConditionBase):
    """Turbulent Thermal Diffusivity boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionAlphat, self).__init__(case_dir, 'alphat', 'volScalarField',
                                                      '[1 -1 -1 0 0 0 0]', region)


class BoundaryConditionEpsilon(BoundaryConditionBase):
    """Turbulent Kinetic Energy Dissipation Rate boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionEpsilon, self).__init__(case_dir, 'epsilon', 'volScalarField',
                                                       '[0 2 -3 0 0 0 0]', region)


class BoundaryConditionK(BoundaryConditionBase):
    """Turbulent Kinetic Energy boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionK, self).__init__(case_dir, 'k', 'volScalarField',
                                                 '[0 2 -2 0 0 0 0]', region)


class BoundaryConditionNut(BoundaryConditionBase):
    """Turbulent Viscosity boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionNut, self).__init__(case_dir, 'nut', 'volScalarField',
                                                   '[0 2 -1 0 0 0 0]', region)


class BoundaryConditionOmega(BoundaryConditionBase):
    """Turbulence Specific Dissipation Rate boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionOmega, self).__init__(case_dir, 'omega', 'volScalarField',
                                                     '[0 0 -1 0 0 0 0]', region)


class BoundaryConditionP(BoundaryConditionBase):
    """Pressure boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionP, self).__init__(case_dir, 'p', 'volScalarField',
                                                 '[1 -1 -2 0 0 0 0]', region)


class BoundaryConditionPrgh(BoundaryConditionBase):
    """Dynamic Pressure (p_rgh = p - rho*g*h) boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionPrgh, self).__init__(case_dir, 'p_rgh', 'volScalarField',
                                                    '[1 -1 -2 0 0 0 0 ]', region)


class BoundaryConditionU(BoundaryConditionBase):
    """Velocity boundary condition"""

    def __init__(self, case_dir, region=None):
        super(BoundaryConditionU, self).__init__(case_dir, 'U', 'volVectorField',
                                                 '[0 1 -1 0 0 0 0]', region)


BOUNDARY_CONDITION_CLASSES = {
    'T': BoundaryConditionT,
    'U': BoundaryConditionU,
    'p_rgh': BoundaryConditionPrgh,
    'p': BoundaryConditionP,
    'omega': BoundaryConditionOmega,
    'alphat': BoundaryConditionAlphat,
    'epsilon': BoundaryConditionEpsilon,
    'k': BoundaryConditionK,
    'nut': BoundaryConditionNut,
}


class BoundaryCondition:
    """
    Generic Boundary Condition type class that automatically determines
    the class according to passed field name string
    """

    def __new__(cls, field, case_dir, region=None):
        """
        Instantiates a required class according to passed field name
        :param field: probe field (e.g., T)
        :param case_dir: case directory
        :param region: region to probe
        """
        if field in BOUNDARY_CONDITION_CLASSES:
            field_class = BOUNDARY_CONDITION_CLASSES[field]
            field_inst = field_class.__new__(field_class)
            field_inst.__init__(case_dir, region)
            return field_inst
        return None
