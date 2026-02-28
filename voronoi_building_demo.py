import sys
from enum import StrEnum, Enum, auto
from scipy.spatial import ConvexHull, Voronoi
from shapely.geometry import Polygon

import math
import numpy as np
import random

from shapes import RandomPolygonalPrism
from voronoi_region_generator import BoundedVoronoiGenerator, ConvexPolygonGenerator

from direct.gui.DirectWaitBar import DirectWaitBar
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.stdpy import threading
from panda3d.core import Point3, NodePath, Vec3, Vec2, LColor
from panda3d.core import AntialiasAttrib, TransparencyAttrib, Texture
from panda3d.core import AmbientLight, DirectionalLight



class Status(Enum):

    SETUP = auto()
    WAIT = auto()
    FINISH = auto()
    DISPLAY = auto()
    START = auto()


class Progress(DirectWaitBar):

    def __init__(self, parent=None):
        self.range_max = 50
        self.bar_color = (1, 1, 1, 1)

        super().__init__(
            parent=parent,
            text='generating...',
            text_fg=self.bar_color,
            text_scale=0.05,
            text_pos=(0, 0.05, 0),
            range=self.range_max,
            value=0,
            barColor=self.bar_color,
            frameSize=(-0.3, 0.3, 0, 0.025),
            pos=(0.0, 0.5, 0.0)
        )
        self.initialiseoptions(type(self))
        self.updateBarStyle()

    def update_progress(self):
        if self['value'] > self.range_max:
            self['value'] -= self.range_max
        else:
            self['value'] += 1

    def finish(self):
        if self['value'] > self.range_max:
            return True
        self['value'] += 1


class VoronoiCube(ShowBase):
    """A class to apply different textures to each side of the cube.
        Args:
            file_path (str):
                Path to the image file used as a texture.
                The image must be created using create_texture_atlas.py.
                When specifying the file_path, set noise_type to None.
            noise_type (str):
                Specifying a noise type from voronoi, edges, rounded, or transparent
                dynamically generates textures from the noise.
                The size and grid must be specified.
            tex_grid (int): the number of vertical and horizontal grids.
            tex_size (int): image size.
            box_size (float): box size.
            box_segs (int): the number of subdivisions in width, depth, and height.
    """

    def __init__(self, file_path=None, noise_type="voronoi", tex_grid=4, tex_size=256,
                 box_size=30, box_segs=5):
        super().__init__()
        self.disable_mouse()
        self.render.set_antialias(AntialiasAttrib.MAuto)

        self.camera_root = NodePath('camera_root')
        self.camera_root.reparent_to(self.render)

        # self.camera.set_pos(0, -100, 50)
        self.camera.set_pos(-100, -100, 300)
        # self.camera.set_pos(0, 0, 50)
        self.camera.look_at(Point3(100, 100, 0))
        self.camera.reparent_to(self.camera_root)

        self.dragging = False
        self.before_mouse_pos = None
        self.show_wireframe = False

        # self.start(file_path, noise_type, tex_grid, tex_size, box_size, box_segs)
        self.status = Status.START


        bnd = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        n = 10
        pnts = np.random.rand(n, 2)
        self.create_buildings2(bnd, pnts)
        # self.points_in_convex_polygon()
        self.setup_light()

        self.accept('d', self.toggle_wireframe)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)
        self.accept('escape', sys.exit)
        self.task_mgr.add(self.update, 'update')

    # def start(self, file_path, noise_type, tex_grid, tex_size, box_size, box_segs):
    #     self.bar = Progress(self.aspect2d)
    #     self.voronoi_thread = threading.Thread(
    #         target=self.create_box,
    #         args=(file_path, noise_type, tex_grid, tex_size, box_size, box_segs)
    #     )
        # self.voronoi_thread.start()
        # self.status = Status.SETUP

    def toggle_wireframe(self):
        if self.show_wireframe:
            self.box.set_render_mode_filled()
        else:
            self.box.set_render_mode_wireframe()

        # self.toggle_wireframe()
        self.show_wireframe = not self.show_wireframe

    def setup_light(self):
        ambient_light = NodePath(AmbientLight('ambient_light'))
        ambient_light.reparent_to(self.render)
        ambient_light.node().set_color(LColor(0.6, 0.6, 0.6, 1.0))
        self.render.set_light(ambient_light)

        directional_light = NodePath(DirectionalLight('directional_light'))
        directional_light.node().get_lens().set_film_size(200, 200)
        directional_light.node().get_lens().set_near_far(1, 100)
        directional_light.node().set_color(LColor(1, 1, 1, 1))
        directional_light.set_pos_hpr(Point3(0, 0, 50), Vec3(-30, -45, 0))
        # directional_light.node().show_frustom()
        self.render.set_light(directional_light)
        directional_light.node().set_shadow_caster(True)
        self.render.set_shader_auto()

    def sort_counter_clockwise(self, points):
        center = sum(points) / len(points)
        sorted_pts = sorted(points, key=lambda p: math.atan2(p[1] - center[1], p[0] - center[0]))
        return sorted_pts

    def create_buildings(self):
        # import pdb; pdb.set_trace()
        points = np.random.rand(30, 2)
        vor = Voronoi(points)
        for i, region_idx in enumerate(vor.point_region):
            region = vor.regions[region_idx]

            if -1 not in region and len(region) > 0:
                polygon = [vor.vertices[i] for i in region]

                polygon = [np.array([*p, 0.0]) for p in polygon]
                sorted_pts = self.sort_counter_clockwise(polygon)

                h = random.randint(2, 20) / 10
                model_creator = RandomPolygonalPrism(sorted_pts, height=h)
                model = model_creator.create()
                model.set_scale(10)
                # import pdb; pdb.set_trace()
                model.set_pos(Point3(*model_creator.center * 10))

                colors = [
                    LColor(1, 0, 0, 1),
                    LColor(0, 0, 1, 1),
                    LColor(1, 1, 0, 1),
                    LColor(0, 0.5, 0, 1),
                    LColor(1, 0.549, 0, 1),
                    LColor(1, 0, 1, 1),
                    LColor(0.501, 0, 0.501, 1),
                    LColor(0, 1, 0, 1),
                    LColor(0.54, 0.16, 0.88, 1),
                    LColor(0, 0.74, 1, 1)
                ]
                color = random.choice(colors)

                model.set_color(color)
                model.reparent_to(self.render)

    def create_buildings2(self, bnd, pnts):
        pnts = np.array([
            [0.13263839, 0.24470754],
            [0.0463067, 0.62523463],
            [0.29250558, 0.52613095],
            [0.6029066, 0.46856697],
            [0.90166906, 0.01566895],
            [0.67575255, 0.21000379],
            [0.66646577, 0.75574618],
            [0.05895997, 0.81893289],
            [0.17170195, 0.43868171],
            [0.0187921, 0.64751741]
        ])
        for region in BoundedVoronoiGenerator(pnts):
            poly_pts = np.array([pt for pt in ConvexPolygonGenerator(region)])

            for pts in BoundedVoronoiGenerator(pts=poly_pts, bnd=region, shrink=None):
                polygon = np.insert(pts, pts.shape[1], 0, axis=1)
                sorted_pts = self.sort_counter_clockwise(polygon)

                h = random.randint(2, 20) / 100

                model_creator = RandomPolygonalPrism(sorted_pts, height=h)
                model = model_creator.create()
                scale = 256
                model.set_scale(scale)

                model.set_pos(Point3(*model_creator.center * scale))

                colors = [
                    LColor(1, 0, 0, 1),
                    LColor(0, 0, 1, 1),
                    LColor(1, 1, 0, 1),
                    LColor(0, 0.5, 0, 1),
                    LColor(1, 0.549, 0, 1),
                    LColor(1, 0, 1, 1),
                    LColor(0.501, 0, 0.501, 1),
                    LColor(0, 1, 0, 1),
                    LColor(0.54, 0.16, 0.88, 1),
                    LColor(0, 0.74, 1, 1)
                ]
                color = random.choice(colors)

                model.set_color(color)
                model.reparent_to(self.render)

    def mouse_click(self):
        self.dragging = True
        self.dragging_start_time = globalClock.get_frame_time()

    def mouse_release(self):
        self.dragging = False
        self.before_mouse_pos = None

    def rotate_camera(self, mouse_pos, dt):
        if self.before_mouse_pos:
            angle = Vec3()

            if (delta := mouse_pos.x - self.before_mouse_pos.x) < 0:
                angle.x += 180
            elif delta > 0:
                angle.x -= 180

            if (delta := mouse_pos.y - self.before_mouse_pos.y) < 0:
                angle.z -= 180
            elif delta > 0:
                angle.z += 180

            angle *= dt
            self.camera_root.set_hpr(self.camera_root.get_hpr() + angle)

        self.before_mouse_pos = Vec2(mouse_pos.xy)

    def update(self, task):
        dt = globalClock.get_dt()

        if self.mouseWatcherNode.has_mouse():
            mouse_pos = self.mouseWatcherNode.get_mouse()

            if self.dragging:
                if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                    self.rotate_camera(mouse_pos, dt)


        # match self.status:

        #     case Status.SETUP:
        #         if not self.voronoi_thread.is_alive():
        #             self.status = Status.WAIT
        #             self.voronoi_thread = None
        #             # del self.voronoi_thread
        #         else:
        #             self.bar.update_progress()

        #     case Status.WAIT:
        #         if self.bar.finish():
        #             self.bar.destroy()
        #             self.status = Status.FINISH

        #     case Status.FINISH:
        #         self.box.reparent_to(self.render)
        #         self.status = Status.DISPLAY

        #     case Status.DISPLAY:
        #         if self.mouseWatcherNode.has_mouse():
        #             mouse_pos = self.mouseWatcherNode.get_mouse()

        #             if self.dragging:
        #                 if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
        #                     self.rotate_camera(mouse_pos, dt)

        #     case Status.START:
        #         self.voronoi_thread.start()
        #         self.status = Status.SETUP

        return task.cont


if __name__ == '__main__':
    app = VoronoiCube()
    app.run()