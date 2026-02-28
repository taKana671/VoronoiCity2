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
        n = 30
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
        for region in BoundedVoronoiGenerator():
            bnd = np.array([pt for pt in ConvexPolygonGenerator(region)])

            for pts in BoundedVoronoiGenerator()
        
        
        bnd = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        # n = 100
        # pnts = np.random.rand(n, 2)
        # pnts = np.random.randint(1, 20, (n, 2))

        dummy_pts = np.array([[100, 100], [100, -100], [-100, 0]])
        # dummy_pts = np.array([[1000, 1000], [1000, -1000], [-1000, 0]])
        gn_pnts = np.concatenate([pnts, dummy_pts])

        vor = Voronoi(gn_pnts)
        bnd_poly = Polygon(bnd)
        vor_polys = []

        for i in range(len(gn_pnts) - 3):
            vor_poly = [vor.vertices[v] for v in vor.regions[vor.point_region[i]]]

            ########## cal area ##################
            # area = ConvexHull(vor_poly).volume
            # print(area)
            ######################################

            poly = Polygon(vor_poly)
            shrunk_poly = poly.buffer(-0.02)

            if shrunk_poly.is_empty:
                continue

            # i_cell = bnd_poly.intersection(Polygon(vor_poly))
            i_cell = bnd_poly.intersection(shrunk_poly)
            # vor_polys.append(list(i_cell.exterior.coords[:-1]))

            li = list(i_cell.exterior.coords[:-1])
            self.points_in_convex_polygon(li)
            
            # polygon = [np.array([*p, 0.0]) for p in li]
            # sorted_pts = self.sort_counter_clockwise(polygon)

            # h = random.randint(2, 20) / 100
            # # print(h)

            # model_creator = RandomPolygonalPrism(sorted_pts, height=h)
            # model = model_creator.create()
            # scale = 256
            # model.set_scale(scale)
            # # import pdb; pdb.set_trace()
            # model.set_pos(Point3(*model_creator.center * scale))

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
            # model.reparent_to(self.render)

    def points_in_convex_polygon(self, bnd):
        # bnd = np.array([[0.1, 0.4],[0.3, 0.2],[0.8, 0.3],[1.0, 0.6],[0.7, 0.7],[0.4, 0.7],[0.3, 0.6], [0.2, 0.5]])
        # bnd = np.random.rand(8, 2)

        bnd = np.array(bnd)
        # n = random.randint(3, 6)
        # n = 5
        bndhull = ConvexHull(bnd)

        area = bndhull.volume
        # print(area)
        if area < 0.01:
            print(1, area)
            n = 2
        if area < 0.02:
            print(2, area)
            n = 2
        elif area < 0.03:
            print(3, area)
            n = 3
        elif area < 0.04:
            print(4, area)
            n = 4
        elif area < 0.05:
            print(5, area)
            n = 5
        elif area < 0.06:
            print(6, area)
            n = 6
        elif area < 0.07:
            print(7, area)
            n = 7
        elif area < 0.08:
            print(8, area)
            n = 8
        elif area < 0.09:
            print(9, area)
            n = 9
        else:
            print(10, area)
            n = 10


        bndTmp = bndhull.equations
        bndMat = np.matrix(bndTmp)
        Abnd = np.array(bndMat[:, 0:2])
        bbnd = np.array(bndMat[:, 2])

        xmin = np.min(bnd[:, 0])
        xmax = np.max(bnd[:, 0])
        ymin = np.min(bnd[:, 1])
        ymax = np.max(bnd[:, 1])

        i = 0
        pnts = []

        while i < n:
            pnt = np.random.rand(2)
            pnt[0] = xmin + (xmax - xmin) * pnt[0]
            pnt[1] = ymin + (ymax - ymin) * pnt[1]

            if (np.round(np.dot(Abnd, pnt.transpose()), len(bnd)) <= np.round(-bbnd.transpose(), len(bnd))).all():
            # if (np.round(np.dot(Abnd, pnt.transpose()), 8) <= np.round(-bbnd.transpose(), 8)).all():
                import pdb; pdb.set_trace()
                pnts.append(pnt.tolist())
                i += 1
        
        pnts = np.array(pnts)
        # self.create_buildings2(bnd, pnts)

        
        dummy_pts = np.array([[100, 100], [100, -100], [-100, 0]])
        # dummy_pts = np.array([[1000, 1000], [1000, -1000], [-1000, 0]])
        gn_pnts = np.concatenate([pnts, dummy_pts])

        vor = Voronoi(gn_pnts)
        bnd_poly = Polygon(bnd)
        vor_polys = []

        for i in range(len(gn_pnts) - 3):
            vor_poly = [vor.vertices[v] for v in vor.regions[vor.point_region[i]]]

            ########## cal area ##################
            # area = ConvexHull(vor_poly).volume
            # print(area)
            ######################################

            i_cell = bnd_poly.intersection(Polygon(vor_poly))
            # vor_polys.append(list(i_cell.exterior.coords[:-1]))

            li = list(i_cell.exterior.coords[:-1])
            
            
            polygon = [np.array([*p, 0.0]) for p in li]
            sorted_pts = self.sort_counter_clockwise(polygon)

            h = random.randint(2, 20) / 100
            # print(h)

            model_creator = RandomPolygonalPrism(sorted_pts, height=h)
            model = model_creator.create()
            scale = 256
            model.set_scale(scale)
            # import pdb; pdb.set_trace()
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




        # return np.array(pnts)

    # def change_uv(self, segs):
    #     points = (segs + 1) * (segs + 1)

    #     # bottom
    #     u_end, v_end = 1 / 4, 1 / 2

    #     for i in range(points):
    #         u = u_end - (segs - i % (segs + 1)) * (0.25 / segs)
    #         v = v_end - i // (segs + 1) * (0.5 / segs)
    #         yield (u, v)

    #     # top
    #     u_end, v_end = 1 / 2, 1 / 2

    #     for i in range(points):
    #         u = u_end - (segs - i % (segs + 1)) * (0.25 / segs)
    #         v = v_end - (segs - i // (segs + 1)) * (0.5 / segs)
    #         yield (u, v)

    #     # back
    #     u_end, v_end = 1 / 4, 1

    #     for i in range(points):
    #         u = u_end - (segs - i // (segs + 1)) * (0.25 / segs)
    #         v = v_end - (segs - i % (segs + 1)) * (0.5 / segs)
    #         yield (u, v)

    #     # front
    #     u_end, v_end = 0.5, 1

    #     for i in range(points):
    #         u = u_end - i // (segs + 1) * (0.25 / segs)
    #         v = v_end - (segs - i % (segs + 1)) * (0.5 / segs)
    #         yield (u, v)

    #     # left
    #     u_end, v_end = 0.75, 1

    #     for i in range(points):
    #         u = u_end - i % (segs + 1) * (0.25 / segs)
    #         v = v_end - (segs - i // (segs + 1)) * (0.5 / segs)
    #         yield (u, v)

    #     # right
    #     u_end, v_end = 1.0, 1.0

    #     for i in range(points):
    #         u = u_end - (segs - i % (segs + 1)) * (0.25 / segs)
    #         v = v_end - (segs - i // (segs + 1)) * (0.5 / segs)
    #         yield (u, v)

    # def get_tex_creator(self, file_path, noise_type, grid, size):
    #     if file_path:
    #         tex_creator = TextureAtlasReader(file_path)
    #         return tex_creator

    #     match noise_type:

    #         case NoiseType.VORONOI:
    #             tex_creator = TextureAtlasGenerator.from_voronoi(grid, size)

    #         case NoiseType.EDGES:
    #             tex_creator = TextureAtlasGenerator.from_voronoi_edges(grid, size)

    #         case NoiseType.ROUNDED:
    #             tex_creator = TextureAtlasGenerator.from_voronoi_round_edges(grid, size)

    #         case NoiseType.TRANSPARENT:
    #             edge_color = [0, 0, 255]
    #             tex_creator = TextureAtlasGenerator.from_transparent_round_edges(edge_color, grid, size)

    #         case _:
    #             raise NoiseTypeErrpr(noise_type)

    #     return tex_creator

    # def create_texture(self, file_path, noise_type, grid, size):
    #     tex_creator = self.get_tex_creator(file_path, noise_type, grid, size)
    #     img = tex_creator.generate_texture()
    #     y, x, z = img.shape
    #     fmt = Texture.F_rgb if z == 3 else Texture.F_rgba

    #     tex = Texture('tex_image')
    #     tex.setup_2d_texture(
    #         x_size=x,
    #         y_size=y,
    #         component_type=Texture.T_unsigned_byte,
    #         format=fmt
    #     )

    #     tex.set_ram_image(img)
    #     return tex

    # def create_box(self, file_path, noise_type, tex_grid, tex_size, box_size, box_segs):
    #     # create box model.
    #     box_maker = Box(
    #         width=box_size,
    #         depth=box_size,
    #         height=box_size,
    #         segs_d=box_segs,
    #         segs_w=box_segs,
    #         segs_z=box_segs
    #     )

    #     self.box = box_maker.create()
    #     self.box.set_pos_hpr(Point3(0, 0, 0), Vec3(0, 0, 0))
    #     # self.box.reparent_to(self.render)
    #     self.box.set_transparency(TransparencyAttrib.MAlpha)

    #     # merge the textures for the different sides into an atlas texture.
    #     tex = self.create_texture(file_path, noise_type, tex_grid, tex_size)

    #     # change the UV coordinates of the box so as to point to the respective area in the texture.
    #     geom_node = self.box.node()
    #     geom = geom_node.modify_geom(0)
    #     vdata = geom.modify_vertex_data()
    #     vdata_arr = vdata.modify_array(0)
    #     vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

    #     for i, (u, v) in enumerate(self.change_uv(box_segs)):
    #         idx = i * box_maker.stride
    #         vdata_mem[idx + 10] = u
    #         vdata_mem[idx + 11] = v

    #     # set the atlas texture to the box.
    #     tex.set_wrap_u(Texture.WM_clamp)
    #     tex.set_wrap_v(Texture.WM_clamp)
    #     tex.set_magfilter(Texture.FTNearest)
    #     tex.set_minfilter(Texture.FTNearest)
    #     self.box.set_texture(tex)

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