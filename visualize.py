import argparse
import matplotlib.pyplot as plt
import numpy as np
import os

def read_points(data):
    xs = []
    ys = []
    for q in data:
        xs.append(q[0])
        ys.append(q[1])
    return xs, ys

def plot(data, name, width):
    xs, ys = read_points(data)
    fig, axs = plt.subplots(1, 1, constrained_layout=True)
    axs.plot(xs, ys, c="k", lw=width)
    plt.gca().set_aspect('equal', adjustable='box')
    fig.suptitle("name: " + str(name))
    plt.show()

parser = argparse.ArgumentParser(description="Visualize a track previously stored in a file.")

parser.add_argument("-t", "--track", help="Input file from where to load the track data.", default="", type=str)
parser.add_argument("-w", "--width", type=int, help="Width of the track (default: 2)", default=2)

args = parser.parse_args()
if args.track:
    file = args.track
    name = file.split("/")[-1].split(".")[0]
else:
    print("No input file. Quitting...")
    exit()
try:
    if not os.path.exists(file):
        raise IOError()
except IOError:
    print("The input file does not exist. Quitting...")
    exit()

points = np.load(file)
plot(points, name, args.width)
