import argparse
from src.ex_track_t.ex_track_t import *

track_dir = "tracks/"

parser = argparse.ArgumentParser(description="Convert an image of a track to a numpy array of waypoints.")

parser.add_argument("-t", "--track", help="Input track (image file).", default="", type=str)
parser.add_argument("-f", "--filled", help="Track fill. Set if the track is not filled with black.", default=False, action="store_true")
parser.add_argument("-e", "--epsilon", help="Resolution of the approximation: maximum distance between original track and Appriximate polygon.", default=0.5, type=int)

args = parser.parse_args()

if args.track:
    img = load_image(args.track, args.filled)
    track_points = extract(img, args.epsilon)
    filename = args.track.split("/")[-1]
    np.save(track_dir + filename.split(".")[0], track_points)
