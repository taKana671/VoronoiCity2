import math
import random

import numpy as np
from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, LColor, Vec3
from panda3d.core import TextureStage, Texture

from shapes import RandomPolygonalPrism
from shapes import Plane
from voronoi_region_generator import BoundedVoronoiGenerator, ConvexPolygonGenerator


class SquareTownBuilder:

    def __init__(self, scale=256):
        self.scale = scale
        self.foundation_tex = base.loader.load_texture('textures/foundation_2.png')
        self.building_tex = base.loader.load_texture('textures/building.png')
        self.roof_tex = base.loader.load_texture('textures/metal_02.png')

    def round_off(self, number, ndigits=0):
        p = 10 ** ndigits
        return (number * p * 2 + 1) // 2 / p

    def sort_counter_clockwise(self, arr):
        center = np.mean(arr, axis=0)
        angles = np.arctan2(arr[:, 1] - center[1], arr[:, 0] - center[0])
        sorted_indices = np.argsort(angles)
        sorted_pts = arr[sorted_indices]
        return sorted_pts

    def build(self):
        for region in BoundedVoronoiGenerator():
            poly_pts = np.array([pt for pt in ConvexPolygonGenerator(region)])

            for i, pts in enumerate(BoundedVoronoiGenerator(pts=poly_pts, bnd=region, shrink=0.003)):
                polygon = np.insert(pts, pts.shape[1], 0, axis=1)
                sorted_pts = self.sort_counter_clockwise(polygon)
                yield self.create_building(sorted_pts, i)

    def create_building(self, sorted_pts, serial):
        nd = NodePath(f'building_{serial}')
        model_creator = RandomPolygonalPrism([pt for pt in sorted_pts])
        edge_length = (model_creator.edge_length * self.scale)
        pos = Point3(*model_creator.center * self.scale)
        ts = TextureStage.get_default()

        # Create building foundation.
        foundation_h = 0.04
        model_creator.height = foundation_h
        foundation = model_creator.create()
        foundation.set_pos_hpr_scale(pos, Vec3(), self.scale)

        su = self.round_off(edge_length / 50)
        foundation.set_tex_scale(ts, (su, 1))
        foundation.set_texture(self.foundation_tex)
        foundation.reparent_to(nd)

        # Create building wall.
        wall_h = random.randint(10, 100) / self.scale
        model_creator.height = wall_h
        wall = model_creator.create()
        wall_pos = Point3(pos.xy, (foundation_h * self.scale))
        wall.set_pos_hpr_scale(wall_pos, Vec3(), self.scale)

        u = edge_length / 50
        su = np.ceil(u * 3) / 3
        v = (wall_h * self.scale) / 50
        sv = np.ceil(v * 4) / 4
        wall.set_tex_scale(ts, (su, sv))
        wall.set_texture(self.building_tex)
        wall.reparent_to(nd)

        # Create building roof.
        model_creator.height = 3 / self.scale
        roof = model_creator.create()
        roof.set_texture(self.roof_tex)
        roof_pos = Point3(pos.xy, (wall_h + foundation_h) * self.scale)
        roof.set_pos_hpr_scale(roof_pos, Vec3(), self.scale)
        roof.reparent_to(nd)

        return nd

    # def calc_perimeter(self, arr):
    #     edges = np.diff(arr, axis=0, append=[arr[0]])
    #     edge_lengths = np.sqrt(np.sum(edges ** 2, axis=1))
    #     return np.sum(edge_lengths)


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

        self.ground = Ground()
        self.ground.reparent_to(self)

        self.buildings_root = NodePath('buildings')
        builder = SquareTownBuilder()

        for building in builder.build():
            building.reparent_to(self.buildings_root)

        self.buildings_root.reparent_to(self)