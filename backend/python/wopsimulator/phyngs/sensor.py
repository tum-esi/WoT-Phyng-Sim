from ..openfoam.probes.probes import Probe


class SensorPhyng:
    """Web of Phyngs Sensor base class"""
    type_name = 'sensor'

    def __init__(self, name, case_dir, field, region, location, **kwargs):
        """
        Web of Phyngs sensor initialization function
        :param name: name of the sensor
        :param case_dir: case dictionary
        :param field: sensor field to monitor (e.g., T)
        :param region: region to sense
        :param location: sensor location
        """
        self.name = name
        self.location = location
        self.field = field
        self._case_dir = case_dir
        self._probe = Probe(case_dir, field, region, location)

    def dump_settings(self):
        return {self.name: {
            'location': self.location,
            'field': self.field
        }}

    @property
    def value(self):
        """Sensor value getter"""
        return self._probe.value

    def destroy(self):
        """Destroys a Phyng Sensor by deleting a probe"""
        self._probe.remove()
        del self._probe

    def remove(self):
        self.destroy()

    def __getitem__(self, item):
        """Allow to access attributes of a class as in dictionary"""
        return getattr(self, item)

    def __setitem__(self, key, value):
        """Allow to set attributes of a class as in dictionary"""
        setattr(self, key, value)

    def __iter__(self):
        """Allow to iterate over attribute names of a class"""
        for each in [b for b in dir(self) if '_' not in b[0]]:
            yield each

    def __delitem__(self, key):
        """Allow to delete individual attributes of a class"""
        del self.__dict__[key]
