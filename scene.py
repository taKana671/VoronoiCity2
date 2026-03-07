import math
import random

import numpy as np
from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, LColor, Vec3
from panda3d.core import TextureStage, Texture, TransformState
from shapely.geometry import Polygon

from shapes import RandomPolygonalPrism
from shapes import Plane, Cylinder

from voronoi_region_generator import BoundedVoronoiGenerator, ConvexPolygonGenerator
from polygon_mixin import PolygonMixin


class PineTree(NodePath):

    def __init__(self, model, name, scale=2):
        super().__init__(PandaNode(name))
        tree = model.copy_to(self)
        tree.set_transform(TransformState.make_pos(Vec3(0, 0, -4)))
        tree.reparent_to(self)
        self.set_scale(scale)


class SquareTownBuilder(PolygonMixin):

    def __init__(self, scale=256):
        self.scale = scale
        self.foundation_tex = base.loader.load_texture('textures/foundation_2.png')
        self.building_tex = base.loader.load_texture('textures/building.png')
        self.roof_tex = base.loader.load_texture('textures/metal_02.png')
        self.spot_tex = base.loader.load_texture('textures/concrete_01.jpg')
        self.grass_tex = base.loader.load_texture('textures/grass_04.jpg')
        self.tree_model = base.loader.load_model('models/pinetree/tree2.bam')

    def round_off(self, number, ndigits=0):
        p = 10 ** ndigits
        return (number * p * 2 + 1) // 2 / p

    def build(self):
        for i, region in enumerate(BoundedVoronoiGenerator()):
            poly_pts = np.array([pt for pt in ConvexPolygonGenerator(region)])

            for j, pts in enumerate(BoundedVoronoiGenerator(pts=poly_pts, bnd=region, shrink=0.003)):
                polygon = np.insert(pts, pts.shape[1], 0, axis=1)
                serial = f'{i}_{j}'

                if j == 0:
                    if nd := self.create_green(polygon, serial):
                        yield nd
                        continue

                sorted_pts = self.sort_counter_clockwise(polygon)
                yield self.create_building(sorted_pts, serial)

    def create_green(self, sorted_pts, serial):
        center, radius = self.get_max_inscribed_circle(sorted_pts)
        spot_rad = radius * self.scale
        inner_radius = spot_rad - 0.5
        height = 0.001 * self.scale

        # If the radius of a circular garden is too small, do not create the garden.
        if (n := int(inner_radius) - 2) <= 0:
            return None

        nd = NodePath(f'garden_{serial}')
        # Create the edge of the circular garden.
        spot = Cylinder(spot_rad, inner_radius=inner_radius, height=height).create()
        pos = Point3(*center, 0) * self.scale
        spot.set_texture(self.spot_tex)
        spot.set_pos(pos)
        spot.reparent_to(nd)

        # Create the lawn area of the circular garden
        green = Cylinder(inner_radius, height=height - 0.1).create()
        green.set_pos(pos)
        green.set_texture(self.grass_tex)
        green.reparent_to(nd)

        # Plant trees.
        pos_candidates = random.sample(range(-n, n), 2 * n - 2)

        for i in range(0, len(pos_candidates) - 1, 2):
            x, y = pos_candidates[i: i + 2]
            dist = (x ** 2 + y ** 2) ** 0.5
            if dist < inner_radius:
                tree = PineTree(self.tree_model, f'tree_{i}')
                tree_pos = pos + Vec3(x, y, 8.5)
                tree.set_pos(tree_pos)
                tree.reparent_to(nd)

        return nd

    def create_building(self, sorted_pts, serial):
        nd = NodePath(f'building_{serial}')
        scaled_pts = sorted_pts * self.scale
        model_creator = RandomPolygonalPrism([pt for pt in scaled_pts])

        # edge_length = model_creator.edge_length
        pos = Point3(*model_creator.center)
        ts = TextureStage.get_default()

        # Create building foundation.
        foundation_h = 0.04
        model_creator.height = foundation_h
        foundation = model_creator.create()
        foundation.set_pos(pos)

        su = self.round_off(model_creator.edge_length / 50)
        foundation.set_tex_scale(ts, (su, 1))
        foundation.set_texture(self.foundation_tex)
        foundation.reparent_to(nd)

        # Create building wall.
        wall_h = random.choice([10, 20, 30, 40, 50, 60, 70, 80])
        model_creator.height = wall_h
        wall = model_creator.create()
        wall_pos = Point3(pos.xy, foundation_h)
        wall.set_pos(wall_pos)

        u = model_creator.edge_length / 50
        su = np.ceil(u * 3) / 3
        v = wall_h / 50
        sv = np.ceil(v * 4) / 4
        wall.set_tex_scale(ts, (su, sv))
        wall.set_texture(self.building_tex)
        wall.reparent_to(nd)

        # Create building roof.
        model_creator.height = 3
        roof = model_creator.create()
        roof.set_texture(self.roof_tex)
        roof_pos = Point3(pos.xy, wall_h + foundation_h)
        roof.set_pos(roof_pos)
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