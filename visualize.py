import argparse
import matplotlib.pyplot as plt
import numpy as np
import os


def read_points(data):
    data_inner = data[0]
    data_outer = data[1]
    xi = []
    yi = []
    xo = []
    yo = []
    for q in data_inner:
        xi.append(q[0])
        yi.append(q[1])
    for q in data_outer:
        xo.append(q[0])
        yo.append(q[1])
    return xi, yi, xo, yo


def plot(data, name, width):
    xi, yi, xo, yo = read_points(data)
    fig, axs = plt.subplots(1, 1, constrained_layout=True)
    axs.plot(xi[1:], yi[1:], c="yellow", lw=width)
    axs.plot(xo[1:], yo[1:], c="blue", lw=width)
    axs.plot(xi[0], yi[0], xo[0], yo[0], c="orange", marker='o')
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

points = np.load(file, allow_pickle=True)
plot(points, name, args.width)
