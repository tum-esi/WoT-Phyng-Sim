import re
import PyFoam.Execution.FoamThread

filepath = PyFoam.Execution.FoamThread.__file__

with open(filepath, 'r') as file:
    content = file.read()

regex = r'(?<=def getLinuxMem\(thrd\):\n)((.|\n)+?(?=class))'

content = re.sub(regex, '    pass\n\n', content, flags=re.MULTILINE)

with open(filepath, 'w') as file:
    file.write(content)
