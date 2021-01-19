import random as rand
import scipy
import math
from collections import deque
import matplotlib.pyplot as plt
import json
import time
import sys
import copy

from src.voronoiTrack.generator.voronoi import *
from src.voronoiTrack.generator.utils import *
from src.voronoiTrack.generator.sectors import *

BOUNDARY_DEFAULT_SCALE = 0.1

class Track:

    # straights = dequeue of obj corner
    # corners = dequeue of obj corner

    def __init__(self, boundary, npoints, seed, verbose=False, scale=BOUNDARY_DEFAULT_SCALE):
        self.track_points = []
        self.straights = deque()
        self.corners = deque()
        self.seed = seed
        random.seed(seed)
        self.boundary = Boundary(boundary[0],boundary[1], scale)
        self.figure = Vor(npoints, self.boundary, seed)
        for v_key in self.figure.vertices.keys():
            if(self.figure.vertices.get(v_key)._is_out_of_bounds(self.boundary)):
                self.figure.delete_element(v_key, False)
        self.figure.cleanup()
        np.set_printoptions(threshold=sys.maxsize)

    def _get_by_ID(self, id, L):
    	for el in L:
    		if el.id == id:
    			return el
    	return None

    def _element(self, ID):
        if ID is None:
            print("ID of _element is None")
            return None
        element = self._get_by_ID(ID, self.straights)
        if element is not None:
            return element
        element = self._get_by_ID(ID, self.corners)
        if element is not None:
            return element
        print("Found nothing")
        return None

    def select_bfs(self, perc):
        """
        Acts as a breadth first visit and adds new cells to the selected area
        starting from a random cell. (deprecated)
        """
        areaTot = sum([self.figure._area(c) for c in list(self.figure.cells.values())])
        toCover = areaTot * perc
        covered = 0
        #start from a random cell
        q = deque([rand.choice(list(self.figure.cells.values()))])
        q[0].flag_center()
        while len(q) > 0:
            el = q.popleft()
            #update the area with the added region
            covered = covered + self.figure._area(el)
            if toCover < covered:
                #ugly (and wrong) way to patch possible holes
                for el in q:
                    if all([c.selected for c in self.figure._adjacent_cells(el)]):
                        el.flag_selected()
                break
            else:
                el.flag_selected()
                for adj in self.figure._adjacent_cells(el):
                    if adj not in q and not adj.selected:        #does not enqueue already enqueued and already selected
                        q.append(adj)

    def _in_hull(self, p, hull):
        from scipy.spatial import Delaunay
        if not isinstance(hull,Delaunay):
            hull = Delaunay(hull)
        return hull.find_simplex(p)>=0

    def select_by_hull(self, perc, n = 5):
        """
        Draws a random n-edged hull over the voronoi diagram; only the cells that
        have at least one vertex inside the hull get included in the selected area.
        """
        figurePoints = []
        #generate a random point centered in the middle of the boundary
        randPoint = lambda : np.array((random.randint(0, self.boundary.x+1) * perc - 50 * perc + 50, random.randint(0, self.boundary.y+1) * perc - 50 * perc +50))
        figurePoints.append(randPoint())
        figurePoints.append(randPoint())
        figurePoints.append(randPoint())
        convex = scipy.spatial.ConvexHull(figurePoints, incremental=True)
        #add n vertices to the hull
        while len(convex.vertices) < n:
            p = randPoint()
            figurePoints.append(p)
            convex.add_points([p])
        convex.close()
        #scans for vertices inside the hull
        v_counter = 0
        for v in self.figure.vertices.values():
            if self._in_hull([[v.x,v.y]], [convex.points[i] for i in convex.vertices])[0]:
                v_counter = v_counter + 1
                for c in v.cells:
                    (self.figure.cells.get(c)).flag_selected()
        if v_counter < 1:
            return False
        return True

    def select(self, perc, method = "hull", n = 5):
        if method == "hull":
            #repeat until no cell is selected
            while not self.select_by_hull(perc, n):
                pass
        else:
            self.select_bfs(perc)
        vertices = []
        out_edges = self.figure._filter_outside_edges()
        for e in out_edges:
            if (e.v1 not in vertices):
                vertices.append(e.v1)
            if (e.v2 not in vertices):
                vertices.append(e.v2)
        #single cell representing the track
        track_cell = Cell([self.figure.vertices.get(v) for v in vertices], 0)
        for e in out_edges:
            track_cell.connect_edge(e)
        sorted_edges, sorted_vertices = self.figure.sort(track_cell)
        t1 = Corner(sorted_vertices[-1].x,sorted_vertices[-1].y)
        t0 = Corner(sorted_vertices[0].x,sorted_vertices[0].y)
        self.corners.append(t1)
        self.straights.append(Straight(t1,t0))
        for i in range(1, len(sorted_edges)-1):
            t1 = Corner(sorted_vertices[i].x,sorted_vertices[i].y)
            self.corners.append(t0)
            self.straights.append(Straight(t0,t1))
            t0 = t1
        self.corners.append(t1)
        self.straights.append(Straight(t1,self.corners[0]))
        for i in range(len(self.straights)):
            self.straights[0].setPreviousStraight(self.straights[-1])
            self.straights[0].setNextStraight(self.straights[1])
            self.corners[0].setPreviousStraight(self.straights[-1])
            self.corners[0].setNextStraight(self.straights[0])
            self.straights.rotate(1)
            self.corners.rotate(1)

    def _avg_straight_length(self):
        return sum([distance(self._element(s.start_node), self._element(s.end_node)) for s in self.straights])/len(self.straights)

    def starting_line(self):
        max_straight = max(self.straights, key=lambda s : distance(self._element(s.start_node), self._element(s.end_node))).id
        # scans the queue and sets the first straight as the start
        while self.straights[0].id != max_straight:
            self.straights.rotate(1)
            self.corners.rotate(1)
        self.straights[0].flagStart()

    def flag_dense_corners(self, tol=0.6, min_p=3):
        """
        the ways to choose between basic rounding and spline of corners is by grouping
        corners close to one another and mark them for spline.
        tol: tolerance relative to the average straight length as minimum distance between corners to be splined
        min_p: minumum corners to be found grouped
        (deprecated)
        """
        max_d = tol*self._avg_straight_length()
        i = 0
        while i < len(self.corners):
            next_straight = self._element(self.corners[i].next_straight)
            # saving current state
            c = i
            while distance(self._element(next_straight.start_node), self._element(next_straight.end_node)) < max_d:
                if i + 1 >= len(self.corners):
                    i = i + 1
                    break
                # the found corners are more than the minimum target (+1 because two corners for each straight)
                if i + 1 - c >= min_p:
                    self._element(next_straight.start_node).flagSpline()
                    self._element(next_straight.end_node).flagSpline()
                i = i + 1
                next_straight = self._element(self.corners[i].next_straight)
            else:
                i = i + 1

    def plot_out(self, points=None, orderedCorners=False, orderedStraights = False):
        ext = self.straights
        plt.xlim(left=self.boundary._x_min(), right=self.boundary._x_max())
        plt.ylim(bottom=self.boundary._y_min(), top=self.boundary._y_max())
        if orderedCorners:
            i = 0
            for c in self.corners:
                label = str(i)
                c.id2 = i
                plt.annotate(label, (c.x, c.y))
                i = i + 1
        j = 0
        for e in ext:
            v1 = self._element(e.start_node)
            v2 = self._element(e.end_node)
            plt.plot([v1.x,v2.x],[v1.y,v2.y], c="r")
            if orderedStraights:
                label = str(j)
                plt.annotate(label, ((v1.x + v2.x)/2., (v1.y + v2.y)/2.))
                j = j + 1
                # if v1.spline:
                #     plt.plot([v1.x, v2.x], [v1.y, v2.y], "ro")
                # else:
                #     plt.plot([v1.x, v2.x], [v1.y, v2.y], "ko")
        plt.show()

    def _track2points(self, plot_step = 0.01):
        p = []
        for s in self.straights:
            v1 = self._element(s.start_node)
            v2 = self._element(s.end_node)
            q1 = v1.arc_finish
            q2 = v2.arc_start
            p.append(q1)
            st = lambda x: (q2[1]-q1[1])/(q2[0]-q1[0])*(x - q1[0]) + q1[1]
            nsteps = int(abs(q2[0]-q1[0])/plot_step)
            for x in np.linspace(q1[0],q2[0],nsteps,endpoint=False):
                p.append([x,st(x)])
            p.append(q2)
            for ap in v2.arc_points:
                p.append(ap)
        return p

    def store(self,filename):
        # with open(filename, "w") as f:
        #     f.write(str(self.seed))
        #     f.write("\n")
        #     f.write(str())
        np.save(filename, self.track_points)

    def plot_track(self, width=4):
        plt.xlim(left=self.boundary._x_min(), right=self.boundary._x_max())
        plt.ylim(bottom=self.boundary._y_min(), top=self.boundary._y_max())
        p = self._track2points()
        xs = []
        ys = []
        for q in p:
            xs.append(q[0])
            ys.append(q[1])
        plt.plot(xs, ys, c="k", lw=width)
        plt.plot(xs, ys, c="r", lw=1)
        plt.show()

    def plot_fill(self):
        ax = plt.axes()
        xs = [v.x for v in self.corners]
        ys = [v.y for v in self.corners]
        ax.fill(xs,ys,color="r")
        plt.show()

    def round(self, corner, v, previous_f=None, min_radius=0.15):
        if previous_f and previous_f > 0.1:
            f = 1-previous_f
        else:
            f = random.uniform(min_radius, 0.5)
        A = self._element(self._element(corner.prev_straight).start_node)
        B = corner
        C = self._element(self._element(corner.next_straight).end_node)
        m1 = float(B.y-A.y)/float(B.x-A.x)
        m2 = float(B.y-C.y)/float(B.x-C.x)
        l1 = distance(A, B)
        l2 = distance(B, C)
        alfa = angle_3_points(A,B,C)
        r = f*math.tan(alfa/2.0)*min(l1, l2)
        t = float(r)/float(math.tan(alfa/2.0))
        costan = lambda x: math.cos(math.atan(x))
        sintan = lambda x: math.sin(math.atan(x))
        if A.x > B.x:
            T1 = [B.x+t*costan(m1), B.y+t*sintan(m1)]
        elif A.x < B.x:
            T1 = [B.x-t*costan(m1), B.y-t*sintan(m1)]
        else:
            raise Exception("Two consecutive points were aligned vertically")
        if C.x > B.x:
            T2 = [B.x+t*costan(m2), B.y+t*sintan(m2)]
        elif C.x < B.x:
            T2 = [B.x-t*costan(m2), B.y-t*sintan(m2)]
        else:
            raise Exception("Two consecutive points were aligned vertically")
        C = [float(m2*T1[0] + m1*m2*T1[1] - m1*T2[0] - m1*m2*T2[1])/float(m2-m1), float(T2[0]+m2*T2[1] - T1[0] - m1*T1[1])/float(m2-m1)]
        corner.radius = r
        corner.center = C
        corner.arc_start = T1
        corner.arc_finish = T2
        corner.flagBlend()
        corner.roundify(v)

    def double_line(self, track_width):
        # TODO make this code efficient
        initial_points = np.array(self._track2points())
        while True:
            inner_points = []
            outer_points = []
            in_maxy = 0
            out_maxy = 0
            for i in range(len(initial_points)):
                cp = initial_points[i]
                if i > 0:
                    pp = initial_points[i - 1]
                else:
                    pp = initial_points[-1]
                x_vect = cp[0] - pp[0]
                y_vect = cp[1] - pp[1]
                modulo = np.linalg.norm(cp - pp)
                if modulo != 0:
                    ort_vector = [- y_vect * track_width / modulo, x_vect * track_width / modulo]
                    outer_points.append([cp[0] + ort_vector[0], cp[1] + ort_vector[1]])
                    if cp[1] + ort_vector[1] > out_maxy:
                        out_maxy = cp[1] + ort_vector[1]
                    inner_points.append([cp[0], cp[1]])
                    if cp[1] > in_maxy:
                        in_maxy = cp[1]
            if out_maxy > in_maxy:
                break
            track_width = track_width * -1
        self.track_points = np.array(self.correct_mismatches(np.array(inner_points), np.array(outer_points), abs(track_width)))

    def orientation(self, p, q, r):
        val = ((q[1] - p[1]) * (r[0] - q[0])) - ((q[0] - p[0]) * (r[1] - q[1]))
        if val == 0:
            return 0
        return 1 if val > 0 else -1

    def do_intersects(self, p1, q1, p2, q2):
        o1 = self.orientation(p1, q1, p2)
        o2 = self.orientation(p1, q1, q2)
        o3 = self.orientation(p2, q2, p1)
        o4 = self.orientation(p2, q2, q1)
        if o1 != o2 and o3 != o4:
            return True
        return False

    def correct_mismatches(self, in_points, out_points, track_width):
        """"
        for i in range(len(in_points)):
            p1 = in_points[i]
            q1 = out_points[i]
            if i > 0:
                p2 = in_points[i - 1]
                q2 = out_points[i - 1]
            else:
                p2 = in_points[-1]
                q2 = out_points[-1]
            if self.do_intersects(p1, q1, p2, q2):
                if i > 0:
                    out_points[i], out_points[i - 1] = out_points[i - 1], out_points[i]
                else:
                    out_points[0], out_points[-1] = out_points[-1], out_points[0]
        # removing external points too close to the internal ones
        """
        error_count = 0
        toll = track_width * 0.98
        radius = 400
        outer_points = []
        for i in range(len(out_points)):
            q = out_points[i]
            miss_detect = False
            for j in range(0, 2 * radius, 1):
                p = in_points[(i + j - 1 - radius + len(in_points)) % len(in_points)]
                if np.linalg.norm(q-p) < toll:
                    miss_detect = True
                    error_count += 1
                    break
            if not miss_detect:
                outer_points.append(q)
        # remove mis_count random points from the internal line
        inner_points = []
        for i in range(len(in_points) - error_count):
            inner_points.append(in_points[i])
        print(len(in_points))
        print(len(out_points))
        print(error_count)
        inner_points = np.array(inner_points)
        outer_points = np.array(outer_points)
        print(inner_points.shape)
        print(outer_points.shape)
        return [inner_points, outer_points]
