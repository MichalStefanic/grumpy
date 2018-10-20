from libsbgnpy import libsbgn, render
from libsbgnpy.libsbgnTypes import Language, GlyphClass, ArcClass, Orientation


class SbgnGenerator:
    """Class for creation and manipulation with SBGN object."""

    def __init__(self, width, height, pg_x, pg_y):
        self.sbgn = libsbgn.sbgn()
        self.map = libsbgn.map(language=Language.PD)
        self.sbgn.set_map(self.map)
        self.box = libsbgn.bbox(x=0, y=0, w=width, h=height)
        self.map.set_bbox(self.box)

        # process glyph size
        self.pg_size = 24

        self.port_in = None
        self.port_out = None
        self._set_process_glyph(pg_x, pg_y)

    def _set_process_glyph(self, pg_x, pg_y):
        """Set process glyph coordinates.

        :param pg_x: x coordinate for process glyph
        :param pg_y: y coordinate for process glyph
        :return:
        """
        glyph = libsbgn.glyph(class_=GlyphClass.PROCESS, id='pg', orientation=Orientation.HORIZONTAL)
        glyph.set_bbox(libsbgn.bbox(x=pg_x, y=pg_y, w=24, h=24))

        # set port in and out where production/consumption arcs will be heading into)
        self.port_in = {"x": pg_x - (self.pg_size / 2), "y": pg_y + (self.pg_size / 2), "id": "pg_in"}
        self.port_out = {"x": pg_x + self.pg_size + (self.pg_size / 2), "y": pg_y + (self.pg_size / 2), "id": "pg_out"}

        glyph.add_port(libsbgn.port(x=self.port_in["x"], y=self.port_in["y"], id=self.port_in["id"]))
        glyph.add_port(libsbgn.port(x=self.port_out["x"], y=self.port_out["y"], id=self.port_out["id"]))

        self.map.add_glyph(glyph)

    def add_glyph(self, glyph_class, gid, x, y, width=60, height=60, label=None, compartment=None, l_coords=None):
        """Method for adding specific glyph object with all needed parameters into SBGN.

        :param glyph_class: type of glyph (MACROMOLECULE, COMPLEX, COMPARTMENT...)
        :param gid: Glyph ID
        :param x: glyph x coordinate
        :param y: glyph y coordinate
        :param width: glyph width
        :param height: glyph height
        :param label: name of glyph
        :param compartment: current compartment into which glyph belong
        :param l_coords: coordinates for label (for COMPLEX glyph)
        :return:
        """
        glyph = libsbgn.glyph(class_=glyph_class, id=gid, compartmentRef=compartment)
        glyph.get_id()

        bbox = None
        if l_coords:
            bbox = libsbgn.bbox(x=l_coords["x"], y=l_coords["y"], w=l_coords["width"], h=l_coords["height"])
        if label:
            glyph.set_label(libsbgn.label(text=label, bbox=bbox))
        glyph.set_bbox(libsbgn.bbox(x=x, y=y, w=width, h=height))
        self.map.add_glyph(glyph)

        return glyph

    def add_arc_glyph(self, glyph, side="left"):
        """Method for adding specific arc with all needed paramaters and right direction.

        :param glyph: Glyph from arc should start or end.
        :param side: determine direction and type of arc
        :return:
        """
        if side == "left":
            arc = libsbgn.arc(
                class_=ArcClass.CONSUMPTION,
                source=glyph.get_id()[0],
                target=self.port_in["id"],
                id=glyph.get_id()[0] + "_in"
            )
            arc.set_start(libsbgn.startType(
                x=glyph.bbox.get_x() + glyph.bbox.get_w(),
                y=glyph.bbox.get_y() + (glyph.bbox.get_h() / 2))
            )
            arc.set_end(libsbgn.endType(x=self.port_in["x"], y=self.port_in["y"]))
        else:
            arc = libsbgn.arc(
                class_=ArcClass.PRODUCTION,
                source=self.port_out["id"],
                target=glyph.get_id()[0],
                id=glyph.get_id()[0] + "_out"
            )
            arc.set_start(libsbgn.startType(x=self.port_out["x"], y=self.port_out["y"]))
            arc.set_end(libsbgn.endType(x=glyph.bbox.get_x(), y=glyph.bbox.get_y() + (glyph.bbox.get_h() / 2)))

        self.map.add_arc(arc)

    def render_sbgn(self):
        """Render an image from SBGN object and return.

        :return: PNG image of SGBN object
        """
        render.render_sbgn(self.sbgn, image_file="test.png", file_format="png")


def test_sbgn():
    """Just test method for SBGN creation (testing purpose). Should be deleted later."""
    sbgn = libsbgn.sbgn()

    # create map, set language and set in sbgn
    map = libsbgn.map()
    map.set_language(Language.PD)
    sbgn.set_map(map)

    # create a bounding box for the map
    box = libsbgn.bbox(x=0, y=0, w=363, h=253)
    map.set_bbox(box)

    # compartment
    gc = libsbgn.glyph(class_=GlyphClass.COMPARTMENT, id='c0')
    bbox = libsbgn.bbox(x=10, y=85, w=20, h=20)
    gc.set_label(libsbgn.label(text="tlm", bbox=bbox))
    gc.set_bbox(libsbgn.bbox(x=10, y=80, w=130, h=190))
    map.add_glyph(gc)

    # glyphs with labels
    g = libsbgn.glyph(class_=GlyphClass.MACROMOLECULE, id='glyph_adh1')
    g.set_label(libsbgn.label(text='ADH1'))
    g.set_bbox(libsbgn.bbox(x=106, y=20, w=108, h=60))
    map.add_glyph(g)

    # complex
    g = libsbgn.glyph(class_=GlyphClass.COMPLEX, id='glyph_complex', compartmentRef=gc)
    g.set_bbox(libsbgn.bbox(x=20, y=100, w=100, h=160))
    map.add_glyph(g)

    g1 = libsbgn.glyph(class_=GlyphClass.MACROMOLECULE, id='glyph1', compartmentRef=gc)
    g1.set_label(libsbgn.label(text='Ethanol'))
    g1.set_bbox(libsbgn.bbox(x=40, y=120, w=60, h=60))
    map.add_glyph(g1)

    g2 = libsbgn.glyph(class_=GlyphClass.SIMPLE_CHEMICAL, id='glyph_nad', compartmentRef=gc)
    g2.set_label(libsbgn.label(text='NAD+'))
    g2.set_bbox(libsbgn.bbox(x=40, y=190, w=60, h=60))
    map.add_glyph(g2)

    g.add_glyph(g1)
    g.add_glyph(g2)

    g = libsbgn.glyph(class_=GlyphClass.SIMPLE_CHEMICAL, id='glyph_nadh')
    g.set_label(libsbgn.label(text='NADH'))
    g.set_bbox(libsbgn.bbox(x=300, y=150, w=60, h=60))
    map.add_glyph(g)

    # glyph with ports (process)
    g = libsbgn.glyph(class_=GlyphClass.PROCESS, id='pn1',
                      orientation=Orientation.HORIZONTAL)
    g.set_bbox(libsbgn.bbox(x=148, y=168, w=24, h=24))
    g.add_port(libsbgn.port(x=136, y=180, id="pn1.1"))
    g.add_port(libsbgn.port(x=184, y=180, id="pn1.2"))
    map.add_glyph(g)

    # arcs
    # create arcs and set the start and end points
    a = libsbgn.arc(class_=ArcClass.CONSUMPTION, source="glyph1", target="pn1.1", id="a01")
    a.set_start(libsbgn.startType(x=98, y=160))
    a.set_end(libsbgn.endType(x=136, y=180))
    map.add_arc(a)

    a = libsbgn.arc(class_=ArcClass.PRODUCTION, source="pn1.2", target="glyph_nadh", id="a02")
    a.set_start(libsbgn.startType(x=184, y=180))
    a.set_end(libsbgn.endType(x=300, y=180))
    map.add_arc(a)

    a = libsbgn.arc(class_=ArcClass.CATALYSIS, source="glyph_adh1", target="pn1", id="a03")
    a.set_start(libsbgn.startType(x=160, y=80))
    a.set_end(libsbgn.endType(x=160, y=168))
    map.add_arc(a)

    a = libsbgn.arc(class_=ArcClass.CONSUMPTION, source="glyph_nad", target="pn1.1", id="a06")
    a.set_start(libsbgn.startType(x=95, y=202))
    a.set_end(libsbgn.endType(x=136, y=180))
    map.add_arc(a)

    render.render_sbgn(sbgn, image_file="test.png", file_format="png")
