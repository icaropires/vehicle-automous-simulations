# RFID Data


## Summary

There are four activators positioned like corners from a square in a frame of size
1800px X 1800px, (0,0) is on the top left corner, activators are always 400px from
top (or bottom) and 400px from left (or right).

## Columns

**timestamp:** not reliable yet

**id_activator [1,4]:** id from the activator, numbered clockwise

**rssi (decibels) [0,31]:** received signal strength indicator

**estimated_x (pixels) [0,1800]:** estimated position in X axis

**estimated_y (pixels): [0,1800]** estimated position in Y axis
