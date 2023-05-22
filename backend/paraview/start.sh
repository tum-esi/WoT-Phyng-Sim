#!/bin/bash

while true; do

    /opt/paraview/bin/pvserver --force-offscreen-rendering \
    && wait

done
