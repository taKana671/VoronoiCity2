import random

import numpy as np
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletTriangleMeshShape, BulletTriangleMesh
from panda3d.bullet import BulletConvexHullShape, BulletCylinderShape, ZUp
from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, BitMask32, LColor
from panda3d.core import TextureStage, TransformState
from panda3d.core import AmbientLight, DirectionalLight

from shapes import RandomPolygonalPrism
from shapes import Plane, Cylinder
from voronoi_generator.voronoi_2d import BoundedVoronoiGenerator, ConvexPolygonGenerator
from voronoi_generator.polygon_mixin import PolygonMixin


class Building(NodePath):

    def __init__(self, serial):
        super().__init__(BulletRigidBodyNode(f'building_{serial}'))
        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_mass(0)

    def assemble(self, model, pos):
        shape = BulletConvexHullShape()
        shape.add_geom(model.node().get_geom(0))
        self.node().add_shape(shape, TransformState.make_pos(pos))
        model.set_pos(pos)
        model.reparent_to(self)


class Garden(NodePath):

    def __init__(self, serial):
        super().__init__(BulletRigidBodyNode(f'garden_{serial}'))
        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_mass(0)

    def assemble(self, model, pos, is_convex=True):
        if is_convex:
            shape = BulletConvexHullShape()
            shape.add_geom(model.node().get_geom(0))
        else:
            mesh = BulletTriangleMesh()
            mesh.add_geom(model.node().get_geom(0))
            shape = BulletTriangleMeshShape(mesh, dynamic=False)

        self.node().add_shape(shape, TransformState.make_pos(pos))
        model.set_pos(pos)
        model.reparent_to(self)

    def plant_tree(self, model, pos):
        tree = model.copy_to(self)
        tree.set_transform(TransformState.make_pos(Vec3(0, 0, -4)))

        end, tip = tree.get_tight_bounds()
        height = (tip - end).z
        shape = BulletCylinderShape(0.5, height, ZUp)
        self.node().add_shape(shape, TransformState.make_pos(pos))
        tree.set_pos_hpr_scale(pos, Vec3(), 1.6)
        tree.reparent_to(self)


class SquareTownBuilder(PolygonMixin):

    def __init__(self, scale=256):
        self.scale = scale
        self.foundation_tex = base.loader.load_texture('textures/foundation_2.png')
        self.building_tex = base.loader.load_texture('textures/building.png')
        self.roof_tex = base.loader.load_texture('textures/metal_02.png')
        self.spot_tex = base.loader.load_texture('textures/concrete_01.jpg')
        self.grass_tex = base.loader.load_texture('textures/grass_04.jpg')
        self.tree_model = base.loader.load_model('models/pinetree/tree2.bam')

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

        garden_np = Garden(serial)
        # Create the edge of the circular garden.
        spot = Cylinder(spot_rad, inner_radius=inner_radius, height=height).create()
        spot.set_texture(self.spot_tex)
        garden_np.assemble(spot, Point3(0, 0, 0), is_convex=False)

        # Create the lawn area of the circular garden
        green = Cylinder(inner_radius, height=height - 0.1).create()
        green.set_texture(self.grass_tex)
        garden_np.assemble(green, Point3(0, 0, 0))

        # Plant trees.
        pos_candidates = random.sample(range(-n, n), 2 * n - 2)

        for i in range(0, len(pos_candidates) - 1, 2):
            x, y = pos_candidates[i: i + 2]
            dist = (x ** 2 + y ** 2) ** 0.5
            if dist < inner_radius:
                garden_np.plant_tree(self.tree_model, Point3(x, y, 0))

        pos = Point3(*center, 0) * self.scale - Vec3(self.scale / 2, self.scale / 2, 0)
        garden_np.set_pos(pos)
        return garden_np

    def create_building(self, sorted_pts, serial):
        building_np = Building(serial)
        scaled_pts = sorted_pts * self.scale
        model_creator = RandomPolygonalPrism([pt for pt in scaled_pts])
        ts = TextureStage.get_default()

        # Create building foundation.
        foundation_h = 0.04 * self.scale
        model_creator.height = foundation_h
        foundation = model_creator.create()

        su = self.round_off(model_creator.edge_length / 50)
        foundation.set_tex_scale(ts, (su, 1))
        foundation.set_texture(self.foundation_tex)
        building_np.assemble(foundation, Point3(0, 0, 0))

        # Create building wall.
        wall_h = random.choice([10, 20, 30, 40, 50, 60, 70, 80])
        model_creator.height = wall_h
        model_creator.segs_a = int(wall_h / 2)
        wall = model_creator.create()

        u = model_creator.edge_length / 50
        su = np.ceil(u * 3) / 3
        v = wall_h / 50
        sv = np.ceil(v * 4) / 4
        wall.set_tex_scale(ts, (su, sv))
        wall.set_texture(self.building_tex)
        building_np.assemble(wall, Point3(0, 0, foundation_h))

        # Create building roof.
        model_creator.height = 3
        model_creator.segs_a = 3
        roof = model_creator.create()
        roof.set_texture(self.roof_tex)
        roof.set_z(wall_h + foundation_h)
        building_np.assemble(roof, Point3(0, 0, wall_h + foundation_h))

        pos = Point3(*model_creator.center) - Vec3(self.scale / 2, self.scale / 2, 0)
        building_np.set_pos(pos)
        return building_np


class Ground(NodePath):

    def __init__(self, w=280, d=280, segs_w=16, segs_d=16):
        super().__init__(BulletRigidBodyNode('ground'))
        plane = Plane(w, d, segs_w, segs_d)
        self.model = plane.create()
        self.model.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        self.model.reparent_to(self)

        mesh = BulletTriangleMesh()
        mesh.add_geom(self.model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)

        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))


class Scene(NodePath):

    def __init__(self):
        super().__init__(PandaNode('scene'))
        self.reparent_to(base.render)

        self.ground = Ground()
        self.ground.set_pos(Point3(0, 0, 0))
        self.ground.reparent_to(self)
        base.world.attach(self.ground.node())
        self.build_town()
        self.setup_light()

    def build_town(self):
        self.buildings_root = NodePath('buildings')
        builder = SquareTownBuilder()

        for building in builder.build():
            building.reparent_to(self.buildings_root)
            base.world.attach(building.node())

        self.buildings_root.reparent_to(self.ground)

    def setup_light(self):
        ambient_light = NodePath(AmbientLight('ambient_light'))
        ambient_light.reparent_to(base.render)
        ambient_light.node().set_color(LColor(0.6, 0.6, 0.6, 1.0))
        base.render.set_light(ambient_light)

        directional_light = NodePath(DirectionalLight('directional_light'))
        directional_light.node().get_lens().set_film_size(200, 200)
        directional_light.node().get_lens().set_near_far(1, 100)
        directional_light.node().set_color(LColor(1, 1, 1, 1))
        directional_light.set_pos_hpr(Point3(0, 0, 50), Vec3(-30, -45, 0))
        # directional_light.node().show_frustom()
        base.render.set_light(directional_light)
        directional_light.node().set_shadow_caster(True)
        base.render.set_shader_auto()