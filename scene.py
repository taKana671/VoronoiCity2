import math
import random

import numpy as np
from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, LColor, Vec3

from shapes import RandomPolygonalPrism
from shapes import Plane
from voronoi_region_generator import BoundedVoronoiGenerator, ConvexPolygonGenerator


class Buildings(NodePath):

    def __init__(self):
        super().__init__(PandaNode('buildings'))

    def create_model(self, pts):
        # h = random.randint(2, 20) / 100
        h = random.randint(5, 50) / 256
        model_creator = RandomPolygonalPrism(pts, height=h)
        model = model_creator.create()

        scale = 256
        pos = Point3(*model_creator.center * scale)
        model.set_pos_hpr_scale(pos, Vec3(), scale)

        # colors = [
        #     LColor(1, 0, 0, 1),
        #     LColor(0, 0, 1, 1),
        #     LColor(1, 1, 0, 1),
        #     LColor(0, 0.5, 0, 1),
        #     LColor(1, 0.549, 0, 1),
        #     LColor(1, 0, 1, 1),
        #     LColor(0.501, 0, 0.501, 1),
        #     LColor(0, 1, 0, 1),
        #     LColor(0.54, 0.16, 0.88, 1),
        #     LColor(0, 0.74, 1, 1)
        # ]
        # color = random.choice(colors)

        # model.set_color(color)
        model.set_texture(base.loader.load_texture('textures/building.png'))
        model.reparent_to(self)

        model_creator.height = 3 / 256
        roof_model = model_creator.create()
        roof_model.set_scale(scale)
        roof_model.set_texture(base.loader.load_texture('textures/metal2.png'))
        # import pdb; pdb.set_trace()
        pos = Point3(pos.x, pos.y, h * scale)
        roof_model.set_pos(pos)
        roof_model.reparent_to(self)

    def sort_counter_clockwise(self, points):
        center = sum(points) / len(points)
        sorted_pts = sorted(points, key=lambda p: math.atan2(p[1] - center[1], p[0] - center[0]))
        return sorted_pts

    def build(self):
        # pnts = np.array([
        #     [0.13263839, 0.24470754],
        #     [0.0463067, 0.62523463],
        #     [0.29250558, 0.52613095],
        #     [0.6029066, 0.46856697],
        #     [0.90166906, 0.01566895],
        #     [0.67575255, 0.21000379],
        #     [0.66646577, 0.75574618],
        #     [0.05895997, 0.81893289],
        #     [0.17170195, 0.43868171],
        #     [0.0187921, 0.64751741]
        # ])
        for region in BoundedVoronoiGenerator():
            poly_pts = np.array([pt for pt in ConvexPolygonGenerator(region)])

            for pts in BoundedVoronoiGenerator(pts=poly_pts, bnd=region, shrink=0.003):
                polygon = np.insert(pts, pts.shape[1], 0, axis=1)
                sorted_pts = self.sort_counter_clockwise(polygon)
                self.create_model(sorted_pts)


class Ground(NodePath):

    def __init__(self, w=280, d=280, segs_w=16, segs_d=16):
        super().__init__(PandaNode('ground'))
        plane = Plane(w, d, segs_w, segs_d)
        self.model = plane.create()
        self.model.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        self.model.set_pos(Point3(128, 128, 0))
        self.model.reparent_to(self)


class Scene(NodePath):

    def __init__(self):
        super().__init__(PandaNode('scene'))
        self.reparent_to(base.render)

        self.buildings = Buildings()
        self.buildings.reparent_to(self)
        self.buildings.build()

        self.ground = Ground()
        self.ground.reparent_to(self)

