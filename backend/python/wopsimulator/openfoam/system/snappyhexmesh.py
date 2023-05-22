from typing import List, Union

SNAPPY_DICT_FILE_TEMPLATE = r"""/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2106                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

#includeEtc "caseDicts/mesh/generation/snappyHexMeshDict.cfg"

castellatedMesh %s;
snap            %s;
addLayers       %s;

geometry
{
%s}

castellatedMeshControls
{
    refinementSurfaces
    {
%s    }

    nCellsBetweenLevels %s;

    refinementRegions
    {
        // Note: for better mesh quality utilize this refinement region
        %s
    }
    locationInMesh (%f %f %f);
}

addLayersControls
{
    relativeSizes       %s;
    minThickness        %d;
    finalLayerThickness %d;
    expansionRatio      %d;
    layers
    {}
}

// ************************************************************************* //
"""


class SnappyRegion:
    """Class representation of a partitioned mesh region in snappyHexMeshDict"""

    def __init__(self, name: str, region_type: str, refinement_level: int = 0):
        """
        Snappy region base initialization function
        :param name: name of a partitioned mesh region
        :param region_type: region type (wall or patch)
        :param refinement_level: mesh region refinement level (0, 1, 2, 3)
        """
        self.name = name
        self.region_type = region_type
        self.refinement_level = refinement_level

    def get_geometry_str(self) -> str:
        """
        Mesh region representation for geometry in snappyHexMeshDict
        :return: string, e.g., '{ name walls; }'
        """
        return f'{{ name {self.name}; }}'

    def get_ref_surfaces_str(self) -> str:
        """
        Mesh region representation for refinementSurfaces in snappyHexMeshDict
        :return: string, e.g., 'walls  { level (0 0); patchInfo { type wall; } }'
        """
        return f'{{ level ({self.refinement_level} {self.refinement_level}); ' \
               f'patchInfo {{ type {self.region_type}; }} }}'


class SnappyPartitionedMesh:
    """Class representation of a partitioned mesh in snappyHexMeshDict"""

    def __init__(self, name: str, stl_name: str, refinement_level: int = 0,
                 material_type: str = 'fluid', material: str = 'air'):
        """
        Snappy region base initialization function
        :param name: name of a partitioned mesh
        :param stl_name: name of an partitioned mesh STL located in triSurfaceMesh
        :param refinement_level: mesh region refinement level (0, 1, 2, 3)
        """
        self.name = name
        self.refinement_level = refinement_level
        self.regions = {}
        self.material_type = material_type
        self.material = material
        self._stl_file = stl_name if '.stl' in stl_name else f'{stl_name}.stl'
        self._max_name_len = 0

    def add_regions(self, regions: List[SnappyRegion]):
        """
        Add mesh region to a partitioned mesh
        :param regions: list of regions
        """
        for region in regions:
            self.regions.update({region.name: region})
            self._max_name_len = 1 + len(region.name) if len(region.name) >= self._max_name_len else self._max_name_len

    def get_geometry_str(self) -> str:
        """
        Partitioned mesh representation for geometry in snappyHexMeshDict
        :return: string, e.g.,
            'fluid
            {
                type triSurfaceMesh;
                file "fluid.stl";

                regions
                {
                    { name walls; }
                }
            }'
        """
        geo_str = f'{self.name}\n' \
                  f'{{\n' \
                  f'{" " * 4}type triSurfaceMesh;\n' \
                  f'{" " * 4}file "{self._stl_file}";\n' \
                  f'\n' \
                  f'{" " * 4}regions\n' \
                  f'{" " * 4}{{\n' \
                  f'%s{" " * 4}}}\n' \
                  f'}}'
        region_str = ''
        for name, region in self.regions.items():
            region_str += f'{" " * 8}{name}{" " * (self._max_name_len - len(name))}{region.get_geometry_str()}\n'
        return geo_str % region_str

    def get_ref_surfaces_str(self) -> str:
        """
        Partitioned mesh representation for refinementSurfaces in snappyHexMeshDict
        :return: string, e.g.,
                'fluid
                {
                    level (0 0);
                    regions
                    {
                        walls  { level (0 0); patchInfo { type wall; } }
                    }
                }'
        """
        ref_str = f'{self.name}\n' \
                  f'{{\n' \
                  f'{" " * 4}level ({self.refinement_level} {self.refinement_level});\n' \
                  f'{" " * 4}regions\n' \
                  f'{" " * 4}{{\n' \
                  f'%s{" " * 4}}}\n' \
                  f'}}'
        region_str = ''
        for r_name, region in self.regions.items():
            region_str += f'{" " * 8}{r_name}{" " * (self._max_name_len - len(r_name))}' \
                          f'{region.get_ref_surfaces_str()}\n'
        return ref_str % region_str


class SnappyCellZoneMesh:
    """Class representation of a cell zone mesh in snappyHexMeshDict"""

    def __init__(self, name: str, stl_name: str, refinement_level: int = 0, face_zone: str = None,
                 cell_zone: str = None, cell_zone_inside: str = 'inside', inside_point: List[float] = None,
                 material_type: str = 'solid', material: str = 'copper'):
        """
        Snappy cell zone base initialization function
        :param name: cell zone name
        :param stl_name: name of an partitioned mesh STL located in triSurfaceMesh
        :param refinement_level: mesh region refinement level (0, 1, 2, 3)
        :param face_zone: face zone name
        :param cell_zone: cell zone name
        :param cell_zone_inside: cell zone inside type
        :param inside_point: cell zone inside point
        """
        self.name = name
        self._stl_name = stl_name
        self.refinement_level = refinement_level
        self.face_zone = name if not face_zone else face_zone
        self.cell_zone = name.split('To')[-1].lower() if not cell_zone else cell_zone
        self.cell_zone_inside = cell_zone_inside
        if cell_zone_inside == 'insidePoint' and not inside_point:
            raise AttributeError('Cell zone specified as inside point, but the point is not specified')
        self.inside_point = inside_point
        self.material_type = material_type
        self.material = material

    def get_geometry_str(self) -> str:
        """
        Cell zone mesh representation for geometry in snappyHexMeshDict
        :return: string, e.g.,
            'heater
            {
                type triSurfaceMesh;
                file "heater.stl";
            }'
        """
        return f'{self.name}\n' \
               f'{{\n' \
               f'{" " * 4}type triSurfaceMesh;\n' \
               f'{" " * 4}file "{self._stl_name}";\n' \
               f'}}'

    def get_ref_surfaces_str(self) -> str:
        """
        Cell zone mesh representation for refinementSurfaces in snappyHexMeshDict
        :return: string, e.g.,
                'heater
                {
                    level          (2 2);
                    faceZone       heater;
                    cellZone       heater;
                    cellZoneInside inside;
                }'
        """
        data = f'{self.name}\n' \
               f'{{\n' \
               f'{" " * 4}level          ({self.refinement_level} {self.refinement_level});\n' \
               f'{" " * 4}faceZone       {self.face_zone};\n' \
               f'{" " * 4}cellZone       {self.cell_zone};\n' \
               f'{" " * 4}cellZoneInside {self.cell_zone_inside};\n'
        if self.cell_zone_inside == 'insidePoint':
            data += f'{" " * 4}insidePoint    ({" ".join([str(val) for val in self.inside_point])});\n'
        data += r'}'
        return data


class SnappyHexMeshDict:
    """SnappyHexMesh dictionary file representation as a class"""

    def __init__(self, case_dir):
        """
        SnappyHexMeshDict class initialization function
        :param case_dir: case directory
        """
        self.castellated_mesh = True
        self.snap = False
        self.add_layers = False
        self.meshes = {}
        self.n_cells_between_levels = 1
        self.refinement_regions = ''
        self.location_in_mesh = []
        self.relative_sizes = True
        self.min_thickness = 1
        self.final_layer_thickness = 1
        self.expansion_ratio = 1
        self.layers = {}
        self._case_dir = case_dir
        self._of_bool = lambda x: 'true' if x else 'false'  # function to convert bool to OpenFOAM boolean string

    def add_meshes(self, meshes: List[Union[SnappyPartitionedMesh, SnappyCellZoneMesh]]):
        """
        Adds meshes to a snappy hex mesh class to be later accessed for saving the file
        :param meshes: PartitionedMesh or CellZoneMesh
        """
        for mesh in meshes:
            self.meshes.update({mesh.name: mesh})

    def save(self):
        """Saves a class as snappyHexMeshDict"""
        geometries_str = ''
        ref_surfaces_str = ''
        for m_name, mesh in self.meshes.items():
            geometries_str += ' ' * 4 + mesh.get_geometry_str().replace('\n', f'\n{" " * 4}') + '\n'
            ref_surfaces_str += ' ' * 8 + mesh.get_ref_surfaces_str().replace('\n', f'\n{" " * 8}') + '\n'
        file_output = SNAPPY_DICT_FILE_TEMPLATE % (
            self._of_bool(self.castellated_mesh), self._of_bool(self.snap), self._of_bool(self.add_layers),
            geometries_str, ref_surfaces_str, self.n_cells_between_levels, self.refinement_regions,
            self.location_in_mesh[0], self.location_in_mesh[1], self.location_in_mesh[2],
            self._of_bool(self.relative_sizes), self.min_thickness, self.final_layer_thickness, self.expansion_ratio
        )
        with open(f'{self._case_dir}/system/snappyHexMeshDict', 'w') as f:
            f.writelines(file_output)

    def remove(self, name):
        try:
            del self.meshes[name]
        except KeyError:
            print(f'Mesh {name} does not exist in snappyHexMeshDict, thus not deleted')


def main():
    walls = SnappyRegion('walls', 'wall')
    inlet = SnappyRegion('inlet', 'patch', 1)
    outlet = SnappyRegion('outlet', 'patch', 1)
    fluid = SnappyPartitionedMesh('fluid', 'fluid.stl')
    fluid.add_regions([walls, inlet, outlet])
    geo_str = fluid.get_geometry_str()
    print(geo_str)
    ref_str = fluid.get_ref_surfaces_str()
    print(ref_str)
    heater = SnappyCellZoneMesh('fluidToHeater', 'heater.stl', refinement_level=1, inside_point=[1.5, 0.21, 0.2])
    print(heater.get_geometry_str())
    print(heater.get_ref_surfaces_str())
    snappy_dict = SnappyHexMeshDict('.')
    snappy_dict.add_meshes([fluid, heater])
    snappy_dict.location_in_mesh = [1, 2, 3]
    snappy_dict.save()
    inlet.region_type = 'wall'
    snappy_dict.save()


if __name__ == '__main__':
    main()
