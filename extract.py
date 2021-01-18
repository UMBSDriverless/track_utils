import argparse
import numpy as np
import os
from src.ex_track_t.ex_track_t import *

track_dir = "tracks/"

parser = argparse.ArgumentParser(description="Convert an image of a track to a numpy array of waypoints.")

parser.add_argument("-t", "--track", help="Input track (image file).", default="", type=str)
parser.add_argument("-v", "--verbose", help="Set verbose.", default=False, action="store_true")
parser.add_argument("-f", "--filled", help="Track fill. Set if the track is not filled with black.", default=False, action="store_true")
parser.add_argument("-m", "--max", help="Resolution of the approximation: maximum points in the final result (default is 1000).", default=1000, type=int)
parser.add_argument("-q", "--quiet", help="Quiet mode. Set to turn plotting off.", default=False, action="store_true")

args = parser.parse_args()

if args.track:
    np.random.seed(0)
    if args.verbose:
        print("Loading image... ", end = "")
    img = load_image(args.track, args.filled)
    if args.verbose:
        print("Done")

    if args.verbose:
        print("Extracting contours... ", end = "")
    outside, inside = contours(img)
    # track_points = middle_lane(outside, inside)
    if args.verbose:
        print("Done")
    if args.verbose:
        print("removing excess points... ", end = "")

    # inner reduced line
    approx_inside = simplify(inside, args.max)
    # outer reduced line. reduce to exactly the inner approx size
    approx_outside = simplify(outside, len(approx_inside))
    approx = np.array([approx_inside, approx_outside])

    if args.verbose:
        print("Done")
    if args.verbose:
        print("Saving... ", end = "")
    file_name = args.track.split("/")[-1]
    file_name = track_dir + file_name.split(".")[0]
    np.save(file_name, approx)
    file_name = file_name + ".npy"
    if not args.quiet:
        os.system("python visualize.py -t" + file_name)

    if args.verbose:
        print("Done")
