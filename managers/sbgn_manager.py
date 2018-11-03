"""SBGN manager."""
import os
from libsbgnpy import libsbgn, render
from libsbgnpy.libsbgnTypes import Language, GlyphClass, ArcClass, Orientation

from config import PROCESS_GLYPH_SIZE, STOICHIOMETRY_GLYPH_SIZE


class SbgnManager:
    def __init__(self, width, height, pg_x, pg_y):
        """
        :param width: total width of final image
        :param height: total height of final image
        :param pg_x: x coordinate of process glyph
        :param pg_y: x coordinate of process glyph
        """
        self.sbgn = libsbgn.sbgn()
        self.map = libsbgn.map(language=Language.PD)
        self.sbgn.set_map(self.map)
        self.box = libsbgn.bbox(x=0, y=0, w=width, h=height)
        self.map.set_bbox(self.box)

        # process glyph size
        self.pg_size = PROCESS_GLYPH_SIZE

        self.port_in = None
        self.port_out = None
        self._set_process_glyph(pg_x, pg_y)

    def __hash__(self):
        """Return hash of SBGN object."""
        return hash(self.sbgn)

    def _set_process_glyph(self, pg_x, pg_y):
        """Set process glyph coordinates.

        :param pg_x: x coordinate of process glyph
        :param pg_y: y coordinate of process glyph
        :return:
        """
        glyph = libsbgn.glyph(class_=GlyphClass.PROCESS, id='pg', orientation=Orientation.HORIZONTAL)
        glyph.set_bbox(libsbgn.bbox(x=pg_x, y=pg_y, w=self.pg_size, h=self.pg_size))

        # set port in and port out for process glyph where production/consumption arcs will be heading into)
        self.port_in = {"x": pg_x - (self.pg_size / 2), "y": pg_y + (self.pg_size / 2), "id": "pg_in"}
        self.port_out = {"x": pg_x + self.pg_size + (self.pg_size / 2), "y": pg_y + (self.pg_size / 2), "id": "pg_out"}

        glyph.add_port(libsbgn.port(x=self.port_in["x"], y=self.port_in["y"], id=self.port_in["id"]))
        glyph.add_port(libsbgn.port(x=self.port_out["x"], y=self.port_out["y"], id=self.port_out["id"]))

        self.map.add_glyph(glyph)

    def add_glyph(self, glyph_class, gid, x, y, width, height, label=None, compartment=None, label_coords=None):
        """Method for adding specific glyph object to SBGN with all necessary parameters.

        :param glyph_class: type of glyph (MACROMOLECULE, COMPLEX, COMPARTMENT...)
        :param gid: Glyph ID
        :param x: glyph x coordinate
        :param y: glyph y coordinate
        :param width: glyph width
        :param height: glyph height
        :param label: name of glyph
        :param compartment: current compartment into which glyph belong
        :param label_coords: coordinates for label (for COMPLEX glyph)
        :return:
        """
        cid = None if compartment is None else compartment.id
        glyph = libsbgn.glyph(class_=glyph_class, id=gid, compartmentRef=cid)

        bbox = None
        if label_coords:
            bbox = libsbgn.bbox(
                x=label_coords["x"],
                y=label_coords["y"],
                w=label_coords["width"],
                h=label_coords["height"]
            )
        # complex doesn't have label
        if label:
            glyph.set_label(libsbgn.label(text=label, bbox=bbox))
        glyph.set_bbox(libsbgn.bbox(x=x, y=y, w=width, h=height))
        self.map.add_glyph(glyph)

        return glyph

    def add_arc_glyph(self, glyph, side="left", stoichiometry=None):
        """Method for adding specific arc with all needed parameters and right direction.
        It can be CONSUMPTION, PRODUCTION or MODULATION arc.

        :param glyph: Glyph from arc should start or end.
        :param side: determine direction and type of arc
        :return:
        """
        if side == "left":
            x_start, y_start = glyph.bbox.get_x() + glyph.bbox.get_w(), glyph.bbox.get_y() + (glyph.bbox.get_h() / 2)
            x_end, y_end = self.port_in["x"], self.port_in["y"]
            arc = libsbgn.arc(
                class_=ArcClass.CONSUMPTION,
                source=glyph.get_id()[0],
                target=self.port_in["id"],
                id=glyph.get_id()[0] + "_in"
            )
            arc.set_start(libsbgn.startType(x=x_start, y=y_start))
            arc.set_end(libsbgn.endType(x=x_end, y=y_end))
        elif side == "right":
            x_start, y_start = self.port_out["x"], self.port_out["y"]
            x_end, y_end = glyph.bbox.get_x(), glyph.bbox.get_y() + (glyph.bbox.get_h() / 2)
            arc = libsbgn.arc(
                class_=ArcClass.PRODUCTION,
                source=self.port_out["id"],
                target=glyph.get_id()[0],
                id=glyph.get_id()[0] + "_out"
            )
            arc.set_start(libsbgn.startType(x=x_start, y=y_start))
            arc.set_end(libsbgn.endType(x=x_end, y=y_end))
        else:
            if glyph.bbox.get_y() > self.port_in["y"]:
                x_start, y_start = glyph.bbox.get_x() + glyph.bbox.get_w() / 2, glyph.bbox.get_y()
                x_end, y_end = self.port_in["x"] + self.pg_size, self.port_in["y"] + (self.pg_size / 2)
            else:
                x_start, y_start = glyph.bbox.get_x() + glyph.bbox.get_w() / 2, glyph.bbox.get_y() + glyph.bbox.get_h()
                x_end, y_end = self.port_in["x"] + self.pg_size, self.port_in["y"] - (self.pg_size / 2)
            arc = libsbgn.arc(
                class_=ArcClass.MODULATION,
                source=glyph.get_id()[0],
                target=self.port_in["id"],
                id=glyph.get_id()[0] + "_modifier"
            )
            arc.set_start(libsbgn.startType(x=x_start, y=y_start))
            arc.set_end(libsbgn.endType(x=x_end, y=y_end))

        if stoichiometry and stoichiometry != 0:
            stoichiometry_glyph = libsbgn.glyph(class_=GlyphClass.STOICHIOMETRY, id=str(hash(glyph)))
            stoichiometry_glyph.set_label(libsbgn.label(text=stoichiometry))
            x, y = self._get_middle_of_edge(x_start, y_start, x_end, y_end)
            stoichiometry_glyph.set_bbox(libsbgn.bbox(x=x, y=y, w=STOICHIOMETRY_GLYPH_SIZE, h=STOICHIOMETRY_GLYPH_SIZE))
            self.map.add_glyph(stoichiometry_glyph)
            arc.add_glyph(stoichiometry_glyph)

        self.map.add_arc(arc)

    @staticmethod
    def _get_middle_of_edge(x1, y1, x2, y2):
        """Calculate middle of the edge, according to coordinates of its vertices.

        :param x1: x coordinates of the vertex
        :param y1: y coordinates of the vertex
        :param x2: x coordinates of the vertex
        :param y2: y coordinates of the vertex
        :return: x and y of the middle
        """
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        if y1 > y2:
            x -= 15
        return x, y

    def render_sbgn(self):
        """Render an image from SBGN object and return.

        :return: PNG image of SGBN object
        """
        file_name = "{}/tmp_images/{}".format(os.getcwd(), str(self.__hash__()) + ".png")
        render.render_sbgn(self.sbgn, image_file=file_name, file_format="png")

        return file_name
