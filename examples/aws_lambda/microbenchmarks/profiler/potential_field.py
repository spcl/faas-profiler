"""

Potential Field based path planner

author: Atsushi Sakai (@Atsushi_twi)

Ref:
https://www.cs.cmu.edu/~motionplanning/lecture/Chap4-Potential-Field_howie.pdf

"""
import faas_profiler_python as fp
import numpy as np

from collections import deque

OSCILLATIONS_DETECTION_LENGTH = 3


def calc_potential_field(
        gx,
        gy,
        ox,
        oy,
        reso,
        rr,
        sx,
        sy,
        area_width,
        kp,
        eta):
    minx = min(min(ox), sx, gx) - area_width / 2.0
    miny = min(min(oy), sy, gy) - area_width / 2.0
    maxx = max(max(ox), sx, gx) + area_width / 2.0
    maxy = max(max(oy), sy, gy) + area_width / 2.0
    xw = int(round((maxx - minx) / reso))
    yw = int(round((maxy - miny) / reso))

    # calc each potential
    pmap = [[0.0 for i in range(yw)] for i in range(xw)]

    for ix in range(xw):
        x = ix * reso + minx

        for iy in range(yw):
            y = iy * reso + miny
            ug = calc_attractive_potential(x, y, gx, gy, kp)
            uo = calc_repulsive_potential(x, y, ox, oy, rr, eta)
            uf = ug + uo
            pmap[ix][iy] = uf

    return pmap, minx, miny


def calc_attractive_potential(x, y, gx, gy, kp):
    return 0.5 * kp * np.hypot(x - gx, y - gy)


def calc_repulsive_potential(x, y, ox, oy, rr, eta):
    # search nearest obstacle
    minid = -1
    dmin = float("inf")
    for i, _ in enumerate(ox):
        d = np.hypot(x - ox[i], y - oy[i])
        if dmin >= d:
            dmin = d
            minid = i

    # calc repulsive potential
    dq = np.hypot(x - ox[minid], y - oy[minid])

    if dq <= rr:
        if dq <= 0.1:
            dq = 0.1

        return 0.5 * eta * (1.0 / dq - 1.0 / rr) ** 2
    else:
        return 0.0


def get_motion_model():
    # dx, dy
    motion = [[1, 0],
              [0, 1],
              [-1, 0],
              [0, -1],
              [-1, -1],
              [-1, 1],
              [1, -1],
              [1, 1]]

    return motion


def oscillations_detection(previous_ids, ix, iy):
    previous_ids.append((ix, iy))

    if (len(previous_ids) > OSCILLATIONS_DETECTION_LENGTH):
        previous_ids.popleft()

    # check if contains any duplicates by copying into a set
    previous_ids_set = set()
    for index in previous_ids:
        if index in previous_ids_set:
            return True
        else:
            previous_ids_set.add(index)
    return False


def potential_field_planning(
        sx,
        sy,
        gx,
        gy,
        ox,
        oy,
        reso,
        rr,
        area_width,
        kp,
        eta):

    # calc potential field
    pmap, minx, miny = calc_potential_field(
        gx, gy, ox, oy, reso, rr, sx, sy, area_width, kp, eta)

    # search path
    d = np.hypot(sx - gx, sy - gy)
    ix = round((sx - minx) / reso)
    iy = round((sy - miny) / reso)

    rx, ry = [sx], [sy]
    motion = get_motion_model()
    previous_ids = deque()

    while d >= reso:
        minp = float("inf")
        minix, miniy = -1, -1
        for i, _ in enumerate(motion):
            inx = int(ix + motion[i][0])
            iny = int(iy + motion[i][1])
            if inx >= len(pmap) or iny >= len(pmap[0]) or inx < 0 or iny < 0:
                p = float("inf")  # outside area
                print("outside potential!")
            else:
                p = pmap[inx][iny]
            if minp > p:
                minp = p
                minix = inx
                miniy = iny
        ix = minix
        iy = miniy
        xp = ix * reso + minx
        yp = iy * reso + miny
        d = np.hypot(gx - xp, gy - yp)
        rx.append(xp)
        ry.append(yp)

        if (oscillations_detection(previous_ids, ix, iy)):
            print("Oscillation detected at ({},{})!".format(ix, iy))
            break

    return rx, ry


@fp.profile()
def handler(event, context):
    area_width = 50.0
    kp = 5.0  # attractive potential gain
    eta = 100.0  # repulsive potential gain

    sx = 0.0  # start x position [m]
    sy = 5.0  # start y positon [m]
    gx = 45.0  # goal x position [m]
    gy = 45.0  # goal y position [m]

    grid_size = 0.25  # potential grid size [m]
    robot_radius = 2.0  # robot radius [m]

    ox = [15.0, 5.0, 10.0, 20.0, 25.0]  # obstacle x position list [m]
    oy = [25.0, 15.0, 15.0, 26.0, 25.0]  # obstacle y position list [m]

    # path generation
    print("Start potential field")
    rx, ry = potential_field_planning(
        sx, sy, gx, gy, ox, oy, grid_size, robot_radius, area_width, kp, eta)
    print("Stop potential field")

    return {
        "path": list(zip(rx, ry))
    }
