#!/bin/bash
echo "Executing '$@'"
sudo chmod -R 0777 /wop/cases
source /opt/openfoam7/etc/bashrc
exec "$@"
