import numpy as np
from shapely.constructive import maximum_inscribed_circle
from shapely.geometry import Polygon


class PolygonMixin:

    def get_max_inscribed_circle(self, pts):
        """Get the radius and center of the inscribed circle.
            Args:
                pts (numpy.ndarray): Iregular polygon vertices
        """
        poly = Polygon(pts)
        mic = maximum_inscribed_circle(poly)
        center = mic.coords[0]
        radius = mic.length

        return center, radius

    def sort_counter_clockwise(self, arr):
        center = np.mean(arr, axis=0)
        angles = np.arctan2(arr[:, 1] - center[1], arr[:, 0] - center[0])
        sorted_indices = np.argsort(angles)
        sorted_pts = arr[sorted_indices]
        return sorted_pts