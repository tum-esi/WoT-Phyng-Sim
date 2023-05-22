import os
import re
import math
import time
from threading import Thread, Lock
from typing import Union, List

from ..common.filehandling import get_latest_time
from ..common.parsing import VECTOR_PATTERN, NUMBER_PATTERN

Num = Union[int, float, None]

PROBE_DICT_FILE_TEMPLATE = \
    r"""/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Version:  7
     \\/     M anipulation  |
-------------------------------------------------------------------------------
Description
    Writes out values of fields from cells nearest to specified locations.

\*---------------------------------------------------------------------------*/

#includeEtc "caseDicts/postProcessing/probes/probes.cfg"

fields (%s);
region %s;
functionObjectLibs ("libsampling.so");
probeLocations
(
%s
);
"""


def parse_probes_dict(dict_path: str,
                      on_field=lambda line, fields_str, fields: line,
                      on_region=lambda line, region: line,
                      on_location=lambda line, location_str, location: line,
                      on_location_end=lambda: ''):
    """
    A common function for parsing the probes dict
    Parses a probes dictionary at a specific location and calls the attached
    callbacks once it encounters field, region, location or end of location
    One can attach callbacks as arguments and change the lines provided
    to the callback and/or store the parsed data
    If a line is required to be skipped - return "" instead of the line in a callback and it would not be written
    :param dict_path: path to probes dictionary file
    :param on_field: on field found callback, must be of form: f(line, fields_str, fields): return line
    :param on_region: on region found callback, must be of form: f(line, region): return line
    :param on_location: on location found callback, must be of form: f(line, location_str, location): return line
    :param on_location_end: on location end found callback, must be of form: f(): return [str]
    :return: modified probes dictionary lines as a list
    """
    with open(dict_path, 'r') as f:
        lines = f.readlines()
    new_lines = []
    fields_pattern = re.compile(r'^\s*fields\s*\(([\w\s]*)\);\n*$')
    region_pattern = re.compile(r'^\s*region\s*([\w]+);\n*$')
    probe_loc_pattern = re.compile(f'{VECTOR_PATTERN}')
    probe_end_pattern = re.compile(r'^\);$')
    for line in lines:
        if '//' in line[:2]:
            continue
        fields_match = fields_pattern.search(line)
        if fields_match:
            line = on_field(line, fields_match.group(1), fields_match.group(1).split())
        region_match = region_pattern.search(line)
        if region_match:
            line = on_region(line, region_match.group(1))
        probe_loc_match = probe_loc_pattern.search(line)
        if probe_loc_match:
            cur_probe_loc = [float(probe_loc_match.group(i)) for i in range(1, 4)]
            line = on_location(line, probe_loc_match.group(), cur_probe_loc)
        if probe_end_pattern.match(line):
            new_line = on_location_end()
            if new_line:
                new_lines.append(new_line)
        if line != '':
            new_lines.append(line)
    return new_lines


class Probe:
    """
    Probe class that represents a single probe for a specific field in a specific location
    """
    _dict_path = {}
    _instances = {}
    _fields = {}
    _regions = {}
    _locations = {}

    def __new__(cls, case_dir: str, field: str, region: str, location: List[Num]):
        """
        Probe class creator
        Allows to remember all the existing instances of probes for the ProbeParser to use later
        If probe dictionary does not exist - creates it
        :param case_dir: case directory
        :param field: probe field (e.g., T)
        :param region: region to probe
        :param location: probe location
        """
        dict_path = f'{case_dir}/system/probes'
        if case_dir not in cls._dict_path.keys():
            cls._dict_path[case_dir] = dict_path
            cls._instances[case_dir] = []
            cls._fields[case_dir] = []
            cls._regions[case_dir] = []
            cls._locations[case_dir] = []
        if not os.path.exists(dict_path):
            location_str = f'{" " * 4}({" ".join([str(l) for l in location])})\n'
            with open(dict_path, 'w') as f:
                f.writelines(PROBE_DICT_FILE_TEMPLATE % (field, region, location_str))
        instance, _ = cls._get_instance_and_idx(case_dir, field, region, location)
        if not instance:
            instance = super(Probe, cls).__new__(cls)
            cls._fields[case_dir].append(field)
            cls._regions[case_dir].append(region)
            cls._locations[case_dir].append(location)
            cls._instances[case_dir].append(instance)
        return instance

    @classmethod
    def _get_instance_and_idx(cls, case_dir, field, region, location):
        in_fields = True if field in cls._fields[case_dir] else False
        in_regions = True if region in cls._regions[case_dir] else False
        in_locations = True if location in cls._locations[case_dir] else False
        if all([in_fields, in_regions, in_locations]):
            values = list(zip(cls._fields[case_dir], cls._regions[case_dir], cls._locations[case_dir]))
            idx = values.index((field, region, location))
            return cls._instances[case_dir][idx], idx
        return None, None

    @classmethod
    def get_instances(cls, case_dir: str) -> list:
        return cls._instances[case_dir] if case_dir in cls._instances else None

    @classmethod
    def get_fields(cls, case_dir: str) -> set:
        return set(cls._fields[case_dir]) if case_dir in cls._fields else None

    @classmethod
    def get_regions(cls, case_dir: str) -> set:
        return set(cls._regions[case_dir]) if case_dir in cls._regions else None

    @classmethod
    def get_locations(cls, case_dir: str) -> set:
        return set(cls._locations[case_dir]) if case_dir in cls._locations else None

    def __init__(self, case_dir: str, field: str, region: str, location: List[Num]):
        """
        Probe class initialization function
        :param case_dir: case directory
        :param field: probe field (e.g., T)
        :param region: region to probe
        :param location: probe location
        """
        self._case_dir = case_dir
        self._added = False
        self.field = field
        self.region = region
        self._location = location
        self._value = 0
        self._time = 0
        self._add_probe_to_dict()
        self._lock = Lock()

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, value):
        with self._lock:
            self._value = value

    @property
    def time(self):
        with self._lock:
            return self._time

    @time.setter
    def time(self, value):
        with self._lock:
            self._time = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        _, idx = self._get_instance_and_idx(self._case_dir, self.field, self.region, self.location)
        self.__class__._locations[self._case_dir][idx] = location
        self._location = location

    def _on_region_callback(self, line, region):
        """
        Callback for a probe parsing function, which is called when a region is found
        Used to change a region if it doesn't correspond to probe's region
        :param line: document line string
        :param region: region (e.g., 'fluid')
        :return: document line string
        """
        # FIXME: potential error if some probes use other regions
        if region != self.region:
            # TODO: check if one can append different regions (probably not)
            line.replace(region, self.region)
        return line

    def _on_field_callback(self, line, fields_str, fields):
        """
        Callback for a probe parsing function, which is called when a field is found
        Used to add a current probe's field to probes dictionary
        :param line: document line string
        :param fields_str: fields match string (e.g., '("T" "U")')
        :param fields: fields as list (e.g., ['T', 'U', ...]
        :return: document line string
        """
        if self.field not in fields:
            fields.append(self.field)
            line = line.replace(fields_str, ' '.join(fields))
        return line

    def _on_location_callback(self, line, location_str, location):
        """
        Callback for a probe parsing function, which is called when a location is found
        Used to check whether a current probe's location is added to probes dictionary
        :param line: document line string
        :param location_str: location match string
        :param location: location as coordinates [x, y, z]
        :return: document line string
        """
        if all([1 if math.isclose(probe1, probe2, abs_tol=0.5) else 0
                for probe1, probe2 in zip(self._location, location)]):
            self.location = location
            self._added = True
        return line

    def _on_location_end_callback(self):
        """
        Callback for a probe parsing function, which is called when a location end is found
        Used to add current probe's location to probes dictionary if it was not there
        :return: document line string
        """
        string = ''
        if not self._added:
            string = f'{" " * 4}({" ".join([str(l) for l in self.location])})\n'
        return string

    def _add_probe_to_dict(self):
        """
        Adds probe to probe dict
        """
        new_lines = parse_probes_dict(self.__class__._dict_path[self._case_dir],
                                      on_field=self._on_field_callback,
                                      on_region=self._on_region_callback,
                                      on_location=self._on_location_callback,
                                      on_location_end=self._on_location_end_callback)
        with open(self.__class__._dict_path[self._case_dir], 'w') as f:
            f.writelines(new_lines)

    def remove(self):
        """Removes probe from known instances"""
        _, idx = self._get_instance_and_idx(self._case_dir, self.field, self.region, self.location)
        self.__class__._regions[self._case_dir].pop(idx)
        self.__class__._fields[self._case_dir].pop(idx)
        self.__class__._locations[self._case_dir].pop(idx)
        self.__class__._instances[self._case_dir].pop(idx)


class ProbeParser(Thread):
    """
    Probe parser class, which represents a probe
    results parsing thread
    """

    def __init__(self, case_dir, period: int = 0.01):
        """
        Probe parser initialization function
        :param case_dir: case directory
        :param period: parsing period
        """
        self._case_dir = case_dir
        self.running = False
        self._mutex = Lock()
        self._num_of_probes = 0
        self.parsing_period = period
        super(ProbeParser, self).__init__(daemon=True)

    def _on_location_count(self, line, location_str, location):
        """
        Callback for a probe parsing function, which is called when a location is found
        Used for counting the probes used in probe dictionary
        :param line: document line string
        :param location_str: location match string
        :param location: location as coordinates [x, y, z]
        :return: document line string
        """
        self._num_of_probes += 1
        return line

    def _get_number_of_probes(self):
        """
        Reads probe dictionary if it exists and returns number of probes in it
        This number doesn't have to necessarily match the number of probes defined
        in the scripts as some locations might be unused in the code
        """
        self._num_of_probes = 0
        probe_dict = f'{self._case_dir}/system/probes'
        if os.path.exists(probe_dict):
            parse_probes_dict(probe_dict, on_location=self._on_location_count)

    def _parse_region(self, region):
        """
        Checks the postProcessing folder for probes data
        Opens the corresponding fields data, parses last line
        and saves it to corresponding probe.
        """
        path_to_probes_data = f'{self._case_dir}/postProcessing/probes/{region}'
        scalar_pattern = re.compile(NUMBER_PATTERN)
        vector_pattern = re.compile(VECTOR_PATTERN)
        region_probes = [[num, probe] for num, probe in enumerate(Probe.get_instances(self._case_dir), 0)
                         if probe.region == region]
        for field in Probe.get_fields(self._case_dir):
            try:
                latest_result = get_latest_time(path_to_probes_data)
            except FileNotFoundError:
                latest_result = '0'
            path_to_probes_field = f'{path_to_probes_data}/{latest_result}/{field}'
            if os.path.exists(path_to_probes_field):
                field_probes = [[num, probe] for num, probe in region_probes if probe.field == field]
                with open(path_to_probes_field, 'rb') as f:
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                    last_line = f.readline().decode()
                scalar_match = re.findall(scalar_pattern, last_line)
                vector_match = vector_pattern.findall(last_line)
                for number, probe in field_probes:
                    if vector_match:
                        probe.time = float(scalar_match[0])
                        probe.value = [float(v) for v in vector_match[number]]
                    elif scalar_match:
                        scalar_match = [float(match) for match in scalar_match]
                        probe.time = scalar_match[0]
                        probe.value = scalar_match[number + 1]

    @staticmethod
    def _on_field_remove(line, fields_str, fields, used_fields):
        """
        Callback for a probe parsing function, which is called when a field is found
        Used to replace the fields in probe dictionary with used fields
        :param line: document line string
        :param fields_str: fields match string (e.g., '("T" "U")')
        :param fields: fields as list (e.g., ['T', 'U', ...]
        :param used_fields: used fields as list (e.g., ['T', 'U', ...]
        :return: document line string
        """
        return line.replace(fields_str, ' '.join(used_fields))

    @staticmethod
    def _on_location_remove(line, location_str, location, used_locations):
        """
        Callback for a probe parsing function, which is called when a location is found
        Used to remove unused locations from probes dictionary
        :param line: document line string
        :param location_str: location match string
        :param location: location as coordinates [x, y, z]
        :param used_locations: used probe locations [[x, y, z], [x, y, z], ...]
        :return: document line string
        """
        if location not in used_locations:
            line = ''
        return line

    def remove_unused(self):
        """
        Removes unused probes and fields from a probe dictionary,
        counts the amount of used probes
        """
        probe_dict = f'{self._case_dir}/system/probes'
        if not os.path.exists(probe_dict):
            self._num_of_probes = 0
            return
        probe_locations = [probe.location for probe in Probe.get_instances(self._case_dir)]
        new_lines = parse_probes_dict(
            probe_dict,
            on_field=lambda line, fields_str, fields: self._on_field_remove(line, fields_str, fields,
                                                                            Probe.get_fields(self._case_dir)),
            on_location=lambda line, loc_str, loc: self._on_location_remove(line, loc_str, loc, probe_locations)
        )
        with open(probe_dict, 'w') as f:
            f.writelines(new_lines)
        self._num_of_probes = len(probe_locations)

    def parse_probe(self, probe: Probe):
        """
        Parses data for initialized case with previous results
        :param probe: probe to parse
        """
        if probe not in Probe.get_instances(self._case_dir) or \
                not os.path.exists(f'{self._case_dir}/postProcessing/probes/{probe.region}'):
            return
        self._parse_region(probe.region)

    def run(self):
        """Thread function to parse data"""
        if not Probe.get_instances(self._case_dir):
            # No probes were initialized
            return
        self.running = True
        self.remove_unused()
        self._mutex.acquire()
        while self.running:
            for region in Probe.get_regions(self._case_dir):
                self._parse_region(region)
            time.sleep(self.parsing_period)
        self._mutex.release()

    def start(self) -> None:
        super(ProbeParser, self).__init__(daemon=True)
        super(ProbeParser, self).start()

    def stop(self):
        """Stops parsing thread"""
        self.running = False
        self._mutex.acquire()
        self._mutex.release()


if __name__ == '__main__':
    case = '.'
    temperature_probe = Probe(case, 'T', 'fluid', [1, 2, 1])
    parser = ProbeParser(case)
    parser.remove_unused()
    parser.start()
