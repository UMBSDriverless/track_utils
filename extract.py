import argparse
from src.ex_track_t.ex_track_t import *

track_dir = "tracks/"

parser = argparse.ArgumentParser(description="Convert an image of a track to a numpy array of waypoints.")

parser.add_argument("-t", "--track", help="Input track (image file).", default="", type=str)
parser.add_argument("-v", "--verbose", help="Set verbosity.", default=False, action="store_true")
parser.add_argument("-f", "--filled", help="Track fill. Set if the track is not filled with black.", default=False, action="store_true")
parser.add_argument("-m", "--max", help="Resolution of the approximation: maximum points in the final result (default is 1000).", default=1000, type=int)

args = parser.parse_args()

if args.track:

    if args.verbose:
        print("Loading image... ", end = "")
    img = load_image(args.track, args.filled)
    if args.verbose:
        print("Done")

    if args.verbose:
        print("Extracting contours... ", end = "")
    outside, inside = contours(img)
    track_points = middle_lane(outside, inside)
    if args.verbose:
        print("Done")

    if args.verbose:
        print("removing excess points... ", end = "")
    approx = simplify(track_points, args.max)
    if args.verbose:
        print("Done")

    if args.verbose:
        print("Saving... ", end = "")
    filename = args.track.split("/")[-1]
    np.save(track_dir + filename.split(".")[0], approx)
    if args.verbose:
        print("Done")
