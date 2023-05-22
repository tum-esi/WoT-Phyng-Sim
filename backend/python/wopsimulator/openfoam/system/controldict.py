import os
import re

from ..common.parsing import SPECIFIC_VALUE_PATTERN, NUMBER_PATTERN

END_OF_FILE = '// ************************************************************************* //'

CONTROL_DICT_FILE_TEMPLATE = r"""/*--------------------------------*- C++ -*----------------------------------*\
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
    object      controlDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application       %s;

startFrom         %s;

startTime         %d;

endTime           %d;

runTimeModifiable %s;

stopAt            %s;

deltaT            %d;

writeControl      %s;

writeInterval     %d;

purgeWrite        %d;

writeFormat       %s;

writePrecision    %d;

writeCompression  %s;

timeFormat        %s;

timePrecision     %d;

adjustTimeStep    %s;

maxCo             %d;

maxDi             %d;

OptimisationSwitches
{
    fileModificationChecking %s;
    fileHandler              %s;
    maxThreadFileBufferSize  %d;
    maxMasterFileBufferSize  %d;
    commsType                %s;
    writeNowSignal           %d;
    stopAtWriteNowSignal     %d;
}

functions
{
    #includeFunc  probes
}

"""
CONTROL_DICT_FILE_TEMPLATE += END_OF_FILE


def to_camel_case(s: str) -> str:
    s = re.sub(r'(_|-)+', ' ', s).title().replace(' ', '')
    return ''.join([s[0].lower(), s[1:]])


def to_snake_case(s: str) -> str:
    s = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s).lower()


class ControlDict:

    def __init__(self, case_dir: str, solver_type: str = ''):
        """
        ControlDict class initialization function
        :param case_dir: case directory
        """
        self._case_dir = case_dir
        self.application = solver_type
        self.start_from = 'latestTime'
        self.start_time = 0
        self.end_time = 1e6
        self.run_time_modifiable = True
        self.stop_at = 'endTime'
        self.delta_t = 1
        self.write_control = 'adjustableRunTime'
        self.write_interval = 1
        self.purge_write = 0
        self.write_format = 'ascii'
        self.write_precision = 8
        self.write_compression = 'off'
        self.time_format = 'general'
        self.time_precision = 6
        self.adjust_time_step = 'yes'
        self.max_co = 1.0
        self.max_di = 10.0
        self.file_modification_checking = 'timeStampMaster'
        self.file_handler = 'uncollated'
        self.max_thread_file_buffer_size = 2e9
        self.max_master_file_buffer_size = 2e9
        self.comms_type = 'blocking'
        self.write_now_signal = -1
        self.stop_at_write_now_signal = 10
        self._camel = lambda s: to_camel_case(s)
        self._snake = lambda s: to_snake_case(s)
        self._of_bool = lambda x: 'true' if x else 'false'  # function to convert bool to OpenFOAM boolean string
        self._bool = lambda x: True if x == 'true' else False
        self._parse()

    def _parse(self):
        """Parses controlDict"""
        if os.path.exists(path := f'{self._case_dir}/system/controlDict'):
            with open(path, 'r') as f:
                lines = f.readlines()
            lines_str = ''.join(lines)
            for name in self.__dict__.keys():
                if name[0] == '_':
                    continue
                dict_name = self._camel(name)
                found_value = re.search(SPECIFIC_VALUE_PATTERN % dict_name, lines_str, flags=re.MULTILINE)
                if found_value and (value := found_value.group(1)):
                    if re.match(NUMBER_PATTERN, value):
                        self.__dict__[name] = float(value)
                    elif value == 'false' or value == 'true':
                        self.__dict__[name] = self._bool(value)
                    else:
                        self.__dict__[name] = value

    def save(self):
        """
        Saves decomposeParDict to system and
        to regions (if available)
        """
        write_values = (self.application,
                        self.start_from,
                        self.start_time,
                        self.end_time,
                        self._of_bool(self.run_time_modifiable),
                        self.stop_at,
                        self.delta_t,
                        self.write_control,
                        self.write_interval,
                        self.purge_write,
                        self.write_format,
                        self.write_precision,
                        self.write_compression,
                        self.time_format,
                        self.time_precision,
                        self.adjust_time_step,
                        self.max_co,
                        self.max_di,
                        self.file_modification_checking,
                        self.file_handler,
                        self.max_thread_file_buffer_size,
                        self.max_master_file_buffer_size,
                        self.comms_type,
                        self.write_now_signal,
                        self.stop_at_write_now_signal)
        file_output = CONTROL_DICT_FILE_TEMPLATE % write_values
        with open(f'{self._case_dir}/system/controlDict', 'w+') as f:
            f.writelines(file_output)


def main():
    control_dict = ControlDict('.', 'chtMultiRegionFoam')
    control_dict.save()


if __name__ == '__main__':
    main()
