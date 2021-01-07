# track_utils
Set of scripts to generate/extract track in form of arrays of waypoints.

## extrack.py
Takes a image of the stylized version of a track and converts it in a list of waypoints (nupy array).

Usage:

```python extract.py -t <track image file> [-f|--filled] [-m|--max <maximum points>]```

## generate.py
Highly customizable random track generation.

Usage:

```python generate.py [-s|--seed <seed>] [--npoints <complexity>] [--softness <corner softnening, from (0, 100)>] [...]```

## visualize.py
Plot a generated track

Usage:

```python visualize.py -t <track numpy file>```
