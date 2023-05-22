import logging
from dataclasses import dataclass
from typing import List, Union

END_OF_FILE = '// ************************************************************************* //'

MATERIAL_DICT_FILE_TEMPLATE = r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    object      materialProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

%s
"""
MATERIAL_DICT_FILE_TEMPLATE += END_OF_FILE

TYPES = [
    'fluid',
    'solid'
]

FLUID_MATERIALS = [
    'air',
    'water'
]

SOLID_MATERIALS = [
    'aluminium',
    'copper'
]

MATERIALS = FLUID_MATERIALS + SOLID_MATERIALS

logger = logging.getLogger('openfoam')


@dataclass
class ObjectMaterial:
    name: str
    _type: str
    _material: str

    def __post_init__(self):
        self.type = self._type
        self.material = self._material

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, m_type):
        if m_type not in TYPES:
            raise ValueError(f'Incorrect material type {self.name}. Available types are {TYPES}')
        self._type = m_type

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, material):
        if material not in MATERIALS:
            raise ValueError(f'Incorrect material for {self.name}. Available types are {MATERIALS}')
        self._material = material

    def __str__(self):
        tabs = " " * 4
        params = self.__dict__.keys()
        max_len = max([len(param) for param in params]) + 1
        strings = []
        for val_name, value in self.__dict__.items():
            if val_name == 'name':
                continue
            val_name = val_name[1:] if val_name[0] == '_' else val_name
            strings.append(f'{tabs}{val_name}{" " * (max_len - len(val_name))}{value};\n')
        return f'{self.name}\n{{\n{"".join(strings)}}}\n'


class MaterialProperties:
    def __init__(self, case_dir):
        """
        MaterialProperties class initialization function
        :param case_dir: case directory
        """
        self._case_dir = case_dir
        self.materials = {}

    def add_object(self, name=None, m_type=None, material=None,
                   materials: Union[List[ObjectMaterial], ObjectMaterial] = None):
        """
        Adds object material to material properties
        :param name: object name
        :param m_type: object type
        :param material: object material
        :param materials: object material as an instance or list of instances
        """
        if materials:
            if isinstance(materials, list):
                for material in materials:
                    self.materials.update({material.name: material})
            else:
                self.materials.update({materials.name: materials})
        elif name and m_type and material:
            self.materials.update({name: ObjectMaterial(name, m_type, material)})
        else:
            raise ValueError('Either material name, type material or materials must be provided')
        logging.debug(f'Set {name} material to {material}')

    def save(self):
        """Saves materialProperties file to constant folder"""
        file_output = MATERIAL_DICT_FILE_TEMPLATE % ''.join([str(material) for material in self.materials.values()])
        with open(f'{self._case_dir}/constant/materialProperties', 'w+') as f:
            f.writelines(file_output)

    def remove(self, name):
        """
        Removes an object material with a specified name
        :param name: object name
        """
        del self.materials[name]


def main():
    material_props = MaterialProperties('./')
    material_props.add_object('heater', 'solid', 'copper')
    material_props.save()


if __name__ == '__main__':
    main()
