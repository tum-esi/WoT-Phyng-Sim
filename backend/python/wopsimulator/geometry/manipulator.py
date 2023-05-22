import logging
import os
import math
import re
from typing import Union, List

import gmsh
import numpy
from stl import mesh
from stl.stl import ASCII

from .primitives import Num, Point, Line, Loop, Surface

GMSH_INITIALIZED = False

logger = logging.getLogger('wop')
logger.setLevel(logging.DEBUG)


class TriSurface:
    """
    TriSurface class for models composed of multiple surfaces
    """

    def __init__(self):
        self.faces = []

    def produce(self, forced=False):
        """
        Produces faces using GMSH API
        :param forced: force produce the face
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        for face in faces:
            face.produce(forced)

    def withdraw(self):
        """
        Resets produced flag to allow to repopulate GMSH model
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        for face in faces:
            face.withdraw()

    def rotate(self, rotation: List[Num], center: List[Num]):
        """
        Rotates trisurface in space
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param center: center of rotation [x, y, z]
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        rotated_points = []
        for face in faces:
            face_points = []
            for loop in face.loops:
                for line in loop.lines:
                    face_points += [point for point in line.points if point not in face_points]
            for point in list(set(face_points) - set(rotated_points)):
                point.rotate(rotation, center)
                rotated_points.append(point)

    def translate(self, coords: List[Num]):
        """
        Translates trisurface by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        if isinstance(self.faces, dict):
            faces = self.faces.values()
        else:
            faces = self.faces
        translated_point = []
        for face in faces:
            face_points = []
            for loop in face.loops:
                for line in loop.lines:
                    face_points += [point for point in line.points if point not in face_points]
            for point in list(set(face_points) - set(translated_point)):
                point.translate(coords)
                translated_point.append(point)

    def remove(self):
        for face in self.faces:
            face.remove()


class Box(TriSurface):
    """
    Box class (trisurface)
    """

    def __init__(self, identifier: str, dimensions: List[Num], location: List[Num] = (0, 0, 0)):
        """
        Box class initialization function
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        """
        super(Box, self).__init__()
        self.dimensions = dimensions
        self.location = location
        self.faces = {}
        self._identifier = identifier
        self.create(dimensions, location)

    def create(self, dimensions, location):
        """
        Creates a box with certain dimensions and at a certain location
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        """
        p1 = Point(self._identifier, location[0], location[1], location[2])
        p2 = Point(self._identifier, location[0] + dimensions[0], location[1], location[2])
        p3 = Point(self._identifier, location[0] + dimensions[0], location[1] + dimensions[1], location[2])
        p4 = Point(self._identifier, location[0], location[1] + dimensions[1], location[2])
        p5 = Point(self._identifier, location[0], location[1], location[2] + dimensions[2])
        p6 = Point(self._identifier, location[0] + dimensions[0], location[1], location[2] + dimensions[2])
        p7 = Point(self._identifier, location[0] + dimensions[0], location[1] + dimensions[1],
                   location[2] + dimensions[2])
        p8 = Point(self._identifier, location[0], location[1] + dimensions[1], location[2] + dimensions[2])

        l1 = Line(self._identifier, p1, p2)
        l2 = Line(self._identifier, p2, p3)
        l3 = Line(self._identifier, p4, p3)
        l4 = Line(self._identifier, p1, p4)

        l5 = Line(self._identifier, p5, p6)
        l6 = Line(self._identifier, p6, p7)
        l7 = Line(self._identifier, p8, p7)
        l8 = Line(self._identifier, p5, p8)

        l9 = Line(self._identifier, p1, p5)
        l10 = Line(self._identifier, p2, p6)
        l11 = Line(self._identifier, p3, p7)
        l12 = Line(self._identifier, p4, p8)

        ll1 = Loop(self._identifier, [l1, l2, -l3, -l4])  # bottom
        ll2 = Loop(self._identifier, [l8, l7, -l6, -l5])  # top
        ll3 = Loop(self._identifier, [l4, l12, -l8, -l9])  # front
        ll4 = Loop(self._identifier, [l10, l6, -l11, -l2])  # back
        ll5 = Loop(self._identifier, [l9, l5, -l10, -l1])  # right
        ll6 = Loop(self._identifier, [l3, l11, -l7, -l12])  # left

        self.faces.update({'bottom': Surface(self._identifier, ll1)})
        self.faces.update({'top': Surface(self._identifier, ll2)})
        self.faces.update({'front': Surface(self._identifier, ll3)})
        self.faces.update({'back': Surface(self._identifier, ll4)})
        self.faces.update({'right': Surface(self._identifier, ll5)})
        self.faces.update({'left': Surface(self._identifier, ll6)})

    def cut_surface(self, other):
        """
        Finds a proper face to cut a surface from
        :param other: surface class to cut
        """
        if not isinstance(other, Surface):
            raise AttributeError('Subtraction of surfaces can only be done between surfaces')
        matching_face = None
        other_x, other_y, other_z = other.get_used_coords()
        for name, face in self.faces.items():
            face_x, face_y, face_z = face.get_used_coords()
            if face_x == other_x or face_y == other_y or face_z == other_z:
                matching_face = name
        if matching_face:
            self.faces[matching_face].cut(other)
        else:
            raise ValueError('Tried to cut surface from box with no matching coordinates')

    def get_used_coords(self):
        """
        Determines the coordinates used by the box
        :return: sets for each coordinate [x, y, z]
        """
        faces_x, faces_y, faces_z = set(), set(), set()
        for face in self.faces.values():
            face_x, face_y, face_z = face.get_used_coords()
            faces_x = faces_x | face_x
            faces_y = faces_y | face_y
            faces_z = faces_z | face_z
        return faces_x, faces_y, faces_z

    def remove(self):
        for face_name in self.faces.keys():
            self.faces[face_name].remove()


class STL:
    """
    STL class (trisurface) for imported STL models
    """

    def __init__(self, stl_path):
        """
        STL class initialization function
        :param stl_path: path to STL file
        """
        super(STL, self).__init__()
        self.path = stl_path
        self.mesh = mesh.Mesh.from_file(stl_path)

    def rotate(self, rotation: List[Num], center: List[Num]):
        """
        Rotates STL in space
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param center: center of rotation [x, y, z]
        """
        rot_mat = [1 if rot_deg else 0 for rot_deg in rotation]
        self.mesh.rotate([rot_mat[0], 0, 0], math.radians(rotation[0]), center)
        self.mesh.rotate([0, rot_mat[1], 0], math.radians(rotation[1]), center)
        self.mesh.rotate([0, 0, rot_mat[2]], math.radians(rotation[2]), center)

    def translate(self, coords: List[Num]):
        """
        Translates STL by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        for i in range(0, len(self.mesh.vectors)):
            for j in range(0, len(self.mesh.vectors[i])):
                self.mesh.vectors[i][j] = self.mesh.vectors[i][j] + numpy.array(coords)

    def get_location(self) -> list:
        """
        Returns location of the imported STL
        :return: [x, y, z] location
        """
        return [float(self.mesh.x.min()), float(self.mesh.y.min()), float(self.mesh.z.min())]

    def calculate_dimensions(self) -> list:
        """
        Calculates dimensions of the imported STL
        :return: [x, y, z] dimensions
        """
        minx = self.mesh.x.min()
        maxx = self.mesh.x.max()
        miny = self.mesh.y.min()
        maxy = self.mesh.y.max()
        minz = self.mesh.z.min()
        maxz = self.mesh.z.max()
        return [float(maxx - minx), float(maxy - miny), float(maxz - minz)]

    def get_used_coords(self):
        """
        Determines the coordinates used by the box
        :return: sets for each coordinate [x, y, z]
        """
        points = numpy.around(numpy.unique(self.mesh.vectors.reshape([int(self.mesh.vectors.size / 3), 3]), axis=0), 2)
        return set(points[:, 0].tolist()), set(points[:, 1].tolist()), set(points[:, 2].tolist())

    def remove(self):
        del self.mesh


class Model:
    """
    Geometric model class
    """
    _surface_type = 'surface'
    _box_type = 'box'
    _stl_type = 'stl'
    _model_types = [
        _surface_type,
        _box_type,
        _stl_type
    ]

    def __init__(self, name: str, model_type: str, dimensions: List[Num] = (0, 0, 0),
                 location: List[Num] = (0, 0, 0), rotation: List[Num] = (0, 0, 0),
                 facing_zero=True, stl_path: str = None, identifier: str = 'geometry'):
        """
        Initializes a Model class
        :param name: name of a model, used for file naming and boundaries
        :param model_type: ['surface', 'box', 'stl']
        :param dimensions: dimensions [x, y, z]
        :param location: location coordinates [x, y, z]
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        :param facing_zero: normal vector direction towards zero coordinates, used for model_type = 'surface'
        :param stl_path: path to STL model, used for model_type = 'stl'
        :param identifier: unique identifier associated with a case (if multiple cases are used)
        """
        if model_type not in self._model_types:
            raise TypeError(f'Geometry model type {model_type} is not defined. '
                            f'Available model types are: {self._model_types}')
        self.name = name
        self.model_type = model_type
        self.dimensions = dimensions if dimensions is not None else [0, 0, 0]
        self.location = location if location is not None else [0, 0, 0]
        self.rotation = rotation if rotation is not None else [0, 0, 0]
        self.facing_zero = facing_zero
        self.center = []
        self._initialized = False
        self._produced = False
        self._identifier = identifier
        self.geometry = self._create_geometry_from_type(facing_zero=facing_zero, stl_path=stl_path)

    def _init(self):
        """
        Initializes GMSH (if not initialized) and current GMSH model
        """
        global GMSH_INITIALIZED
        # FIXME: replace for a common class variable
        if not GMSH_INITIALIZED:
            GMSH_INITIALIZED = True
            gmsh.initialize()
            gmsh.clear()
        if not self._initialized:
            gmsh.model.add(self.name)
            self._initialized = True

    def _finilize(self):
        """
        Finalizes work with GMSH API and closes it and current model
        """
        global GMSH_INITIALIZED
        if self._initialized:
            self._initialized = False
            gmsh.clear()
            gmsh.model.remove()
            if self.geometry:
                self.geometry.withdraw()
            self._produced = False
        if GMSH_INITIALIZED:
            GMSH_INITIALIZED = False
            try:
                gmsh.finalize()
            except ValueError as e:
                # Do not handle this error as it occurs when
                #  gmsh was finalized from non-main thread
                print(e)

    def _produce(self):
        """
        Produces geometry using GMSH API
        :return:
        """
        if self._initialized:
            gmsh.model.set_current(self.name)
            if not self._produced:
                self.geometry.produce()
                # self.model.withdraw()
                gmsh.model.geo.synchronize()
                # Generate the coarsest mesh possible as it doesnt matter
                # for surface mesh
                gmsh.model.mesh.setSize(gmsh.model.getEntities(0), 1000)
                gmsh.model.mesh.generate(2)
                self._produced = True
            else:
                gmsh.model.remove()
                gmsh.model.add(self.name)
                self.geometry.withdraw()
                self._produced = False
                self._produce()
        else:
            self._init()
            self._produce()

    def _create_geometry_from_type(self, facing_zero, stl_path):
        """
        Creates geometry from a type provided
        :param facing_zero: normal vector direction towards zero coordinates, used for model_type = 'surface'
        :param stl_path: path to STL model, used for model_type = 'stl'
        :return: Geometry class, e.g., Surface, Box or STL
        """
        # TODO: split this ifs into separate method for code readability
        if self.model_type == self._surface_type:
            logger.info(f'Creating {self.name} surface')
            if all(self.dimensions) or len([dim for dim in self.dimensions if dim]) <= 1:
                raise ValueError(f'Model type {self._surface_type} must be 2D. Incorrect dimensions {self.dimensions}')
            else:
                d = self.dimensions
                l = self.location
                p1 = Point(self._identifier, l[0], l[1], l[2])
                if not d[0]:
                    p2 = Point(self._identifier, l[0], l[1], l[2] + d[2])
                    p3 = Point(self._identifier, l[0], l[1] + d[1], l[2] + d[2])
                    p4 = Point(self._identifier, l[0], l[1] + d[1], l[2])
                    c = [l[0], l[1] + d[1] / 2, l[2] + d[2] / 2]
                elif not d[1]:
                    p2 = Point(self._identifier, l[0] + d[0], l[1], l[2])
                    p3 = Point(self._identifier, l[0] + d[0], l[1], l[2] + d[2])
                    p4 = Point(self._identifier, l[0], l[1], l[2] + d[2])
                    c = [l[0] + d[0] / 2, l[1], l[2] + d[2] / 2]
                else:
                    p2 = Point(self._identifier, l[0], l[1] + d[1], l[2])
                    p3 = Point(self._identifier, l[0] + d[0], l[1] + d[1], l[2])
                    p4 = Point(self._identifier, l[0] + d[0], l[1], l[2])
                    c = [l[0] + d[0] / 2, l[1] + d[1] / 2, l[2]]
                l1, l2 = Line(self._identifier, p1, p2), Line(self._identifier, p2, p3)
                l3, l4 = Line(self._identifier, p3, p4), Line(self._identifier, p4, p1)
                if facing_zero:
                    ll = Loop(self._identifier, [l1, l2, l3, l4])
                else:
                    ll = Loop(self._identifier, [-l4, -l3, -l2, -l1])
                s = Surface(self._identifier, ll)
                s.rotate(self.rotation, c)
                self.center = c
                return s
        elif self.model_type == self._box_type:
            logger.info(f'Creating {self.name} box')
            if not all(self.dimensions):
                raise ValueError(f'Model type {self._box_type} must be 3D. Check your dimensions')
            else:
                b = Box(self._identifier, self.dimensions, self.location)
                self.center = [self.location[0] + self.dimensions[0] / 2,
                               self.location[1] + self.dimensions[1] / 2,
                               self.location[2] + self.dimensions[2] / 2]
                b.rotate(self.rotation, self.center)
                return b
        elif self.model_type == self._stl_type:
            logger.info(f'Importing {self.name} STL')
            inst = STL(stl_path)
            inst.translate(self.location)
            self.location = inst.get_location()
            self.dimensions = inst.calculate_dimensions()
            self.center = [self.location[0] + self.dimensions[0] / 2,
                           self.location[1] + self.dimensions[1] / 2,
                           self.location[2] + self.dimensions[2] / 2]
            return inst

    def rotate(self, rotation: List[Num]):
        """
        Rotates geometry
        :param rotation: rotation axis angles array [theta_x, theta_y, theta_z]
        """
        logger.info(f'Rotating {self.name} geometry')
        self.rotation = [x1 + x2 for (x1, x2) in zip(self.rotation, rotation)]
        self.geometry.rotate(rotation, self.center)

    def translate(self, coords: List[Num]):
        """
        Translates geometry by certain coordinates
        :param coords: coordinates [x, y, z]
        """
        logger.info(f'Moving {self.name} geometry')
        self.location = [x1 + x2 for (x1, x2) in zip(self.location, coords)]
        self.geometry.translate(coords)

    def show(self):
        """
        Display the geometry using GMSH
        """
        if self.model_type != 'stl':
            self._produce()
            gmsh.fltk.run()
            self._finilize()

    def save(self, dir_path: str):
        """
        Save a geometry as an STL file
        :param dir_path: path to directory to save to
        """
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        file_path = f'{dir_path}/{self.name}.stl'
        if self.model_type == 'stl':
            self.geometry.mesh.save(file_path, mode=ASCII)
        else:
            self._produce()
            gmsh.write(file_path)
            self._finilize()
        rename_solid_stl(file_path, self.name)

    def remove(self):
        self.geometry.remove()


def rename_solid_stl(stl_path: str, name: str):
    """
    Renames the solid in an STL file
    :param stl_path: path to STL file
    :param name: name of solids
    """
    stl_path = stl_path if '.stl' in stl_path else f'{stl_path}.stl'
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f'Path {stl_path} does not exist')
    with open(stl_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    solid_pattern = re.compile(r'((end)?solid)')
    for line in lines:
        match = solid_pattern.match(line)
        if match:
            line = f'{match.group(1)} {name}\n'
        new_lines.append(line)
    with open(stl_path, 'w') as f:
        f.writelines(new_lines)


def combine_stls(dest_path: str, other_paths: Union[List[str], str]):
    """
    Combines multiple STL files to one
    :param dest_path: path to destination STL file
    :param other_paths: paths to STL files
    """
    dest_path = dest_path if '.stl' in dest_path else f'{dest_path}.stl'
    open(dest_path, 'w').close()
    other_paths = other_paths if isinstance(other_paths, list) else [other_paths]
    other_paths = [stl_path if '.stl' in stl_path else f'{stl_path}.stl' for stl_path in other_paths]
    for path in other_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f'Path {path} does not exist')
    with open(dest_path, 'a') as dest_f:
        for other_path in other_paths:
            with open(other_path, 'r') as other_f:
                dest_f.write(other_f.read())


def main():
    # box = Model('box name', 'stl', stl_path='box name.stl')
    # box.show()
    box = Model('box name', 'box', [4, 4, 4], location=[10, 0, 0])
    surface_right = Model('surface_right', 'surface', [2, 0, 2], location=[11, 0, 1])
    surface_left = Model('surface_left', 'surface', [2, 0, 2], location=[11, 4, 1])
    # box.show()
    box.geometry.cut_surface(surface_right.geometry)
    box.geometry.cut_surface(surface_left.geometry)
    # box.geometry.faces['right'].cut(surface.geometry)
    # box.geometry.faces['front'].cut(surface.geometry)
    # # box.show()
    # # box.translate([0, 0, 100])
    # # box.show()
    # box.rotate([45, 45, 45])
    box.show()
    # # box.rotate([0, 0, -45])
    # # box.rotate([0, -45, 0])
    # # box.rotate([-45, 0, 0])
    # # box.show()
    # box.save()
    # combine_stls('box_1.stl', 'heater.stl')


if __name__ == '__main__':
    main()
