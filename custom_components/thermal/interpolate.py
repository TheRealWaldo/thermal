"""Interpolation methods"""

import numpy as np

# Based on https://stackoverflow.com/questions/52700878/bicubic-interpolation-python
def bicubic(xi, yi, values, xo, yo):
    z = np.zeros((xo.size, yo.size))

    deltax = xi[1] - xi[0]
    deltay = yi[1] - yi[0]

    for n, x in enumerate(xo):
        for m, y in enumerate(yo):

            if xi.min() <= x <= xi.max() and yi.min() <= y <= yi.max():

                i = np.searchsorted(xi, x) - 1
                j = np.searchsorted(yi, y) - 1

                x1 = xi[i]
                x2 = xi[i + 1]

                y1 = yi[j]
                y2 = yi[j + 1]

                px = (x - x1) / (x2 - x1)
                py = (y - y1) / (y2 - y1)

                f00 = values[i - 1, j - 1]  # row0 col0 >> x0,y0
                f01 = values[i - 1, j]  # row0 col1 >> x1,y0
                f02 = values[i - 1, j + 1]  # row0 col2 >> x2,y0

                f10 = values[i, j - 1]  # row1 col0 >> x0,y1
                f11 = p00 = values[i, j]  # row1 col1 >> x1,y1
                f12 = p01 = values[i, j + 1]  # row1 col2 >> x2,y1

                f20 = values[i + 1, j - 1]  # row2 col0 >> x0,y2
                f21 = p10 = values[i + 1, j]  # row2 col1 >> x1,y2
                f22 = p11 = values[i + 1, j + 1]  # row2 col2 >> x2,y2

                if 0 < i < xi.size - 2 and 0 < j < yi.size - 2:

                    f03 = values[i - 1, j + 2]  # row0 col3 >> x3,y0

                    f13 = values[i, j + 2]  # row1 col3 >> x3,y1

                    f23 = values[i + 1, j + 2]  # row2 col3 >> x3,y2

                    f30 = values[i + 2, j - 1]  # row3 col0 >> x0,y3
                    f31 = values[i + 2, j]  # row3 col1 >> x1,y3
                    f32 = values[i + 2, j + 1]  # row3 col2 >> x2,y3
                    f33 = values[i + 2, j + 2]  # row3 col3 >> x3,y3

                elif i <= 0:
                    f03 = f02  # row0 col3 >> x3,y0

                    f13 = f12  # row1 col3 >> x3,y1

                    f23 = f22  # row2 col3 >> x3,y2

                    f30 = values[i + 2, j - 1]  # row3 col0 >> x0,y3
                    f31 = values[i + 2, j]  # row3 col1 >> x1,y3
                    f32 = values[i + 2, j + 1]  # row3 col2 >> x2,y3
                    f33 = f32  # row3 col3 >> x3,y3

                elif j <= 0:

                    f03 = values[i - 1, j + 2]  # row0 col3 >> x3,y0

                    f13 = values[i, j + 2]  # row1 col3 >> x3,y1

                    f23 = values[i + 1, j + 2]  # row2 col3 >> x3,y2

                    f30 = f20  # row3 col0 >> x0,y3
                    f31 = f21  # row3 col1 >> x1,y3
                    f32 = f22  # row3 col2 >> x2,y3
                    f33 = f23  # row3 col3 >> x3,y3

                elif i == xi.size - 2 or j == yi.size - 2:

                    f03 = f02  # row0 col3 >> x3,y0

                    f13 = f12  # row1 col3 >> x3,y1

                    f23 = f22  # row2 col3 >> x3,y2

                    f30 = f20  # row3 col0 >> x0,y3
                    f31 = f21  # row3 col1 >> x1,y3
                    f32 = f22  # row3 col2 >> x2,y3
                    f33 = f23  # row3 col3 >> x3,y3

                Z = (
                    np.array(
                        [
                            f00,
                            f01,
                            f02,
                            f03,
                            f10,
                            f11,
                            f12,
                            f13,
                            f20,
                            f21,
                            f22,
                            f23,
                            f30,
                            f31,
                            f32,
                            f33,
                        ]
                    )
                    .reshape(4, 4)
                    .transpose()
                )

                X = np.tile(np.array([-1, 0, 1, 2]), (4, 1))
                X[0, :] = X[0, :] ** 3
                X[1, :] = X[1, :] ** 2
                X[-1, :] = 1

                Cr = Z @ np.linalg.inv(X)
                R = Cr @ np.array([px ** 3, px ** 2, px, 1])

                Y = np.tile(np.array([-1, 0, 1, 2]), (4, 1)).transpose()
                Y[:, 0] = Y[:, 0] ** 3
                Y[:, 1] = Y[:, 1] ** 2
                Y[:, -1] = 1

                Cc = np.linalg.inv(Y) @ R

                z[n, m] = Cc @ np.array([py ** 3, py ** 2, py, 1])

    return z


def linear(xi, yi, values, xo, yo):
    return np.zeros((xo.size, yo.size))


def interpolate(xi, yi, values, xo, yo, method="bicubic"):
    if method == "bicubic":
        return bicubic(xi, yi, values, xo, yo)
    elif method == "linear":
        return linear(xi, yi, values, xo, yo)
