"""Rule manager."""
import requests
from libsbgnpy.libsbgnTypes import GlyphClass

from helpers import get_entity_api_response
from managers.sbgn_manager import SbgnManager


class RuleManager:

    def __init__(self):
        self.sbgn = None
        self.entity_num = 1
        self.compartments = {}
        self.current_compartment = None
        self.stoichiometry = None

    def create_sbgn_from_rule(self, processed_equation):
        """Create SBGN representation of processed rule.

        :param processed_equation: processed rule with all coordinates
        :return: final SBGN with all entities
        """

        self.sbgn = SbgnManager(
            width=processed_equation.x_limit,
            height=processed_equation.y_limit,
            pg_x=processed_equation.process_glyph_x,
            pg_y=processed_equation.process_glyph_y,
        )

        # build all compartments
        for compartment, coordinates in processed_equation.compartments.items():
            x, y, w, h = self.get_coordinates(coordinates["coordinates"])
            self.compartments[compartment] = self.build_compartment_glyph(compartment, x, y, w, h)

        # generate left side of equation
        self.generate_one_side(processed_equation.left_side)
        # generate right side of equation
        self.generate_one_side(processed_equation.right_side, side="right")

        return self.sbgn

    def generate_one_side(self, entity, side="left"):
        """Process one side of equation.

        :param entity: one side of equation which should be process
        :param side: determine side of equation
        :return: sbgn
        """
        for entity in entity.get("children"):
            self.stoichiometry = entity.get("token")
            entity = entity.get("children")[0]

            num_of_children = len(entity.get("children"))

            # last child is always compartment
            compartment = entity.get("children")[num_of_children - 1]
            self.current_compartment = self.compartments[self.get_label_name(compartment)]

            # glyph where arc start or end
            primary_glyph = self.handle_nested_complexes(entity, num_of_children - 2)

            self.sbgn.add_arc_glyph(glyph=primary_glyph, side=side, stoichiometry=self.stoichiometry)

        return self.sbgn

    def handle_nested_complexes(self, entity, index):
        """Method that is solving nested  complexes.

        :param entity: reactant or product
        :param index: index in array of children from parser
        :return:
        """
        if index == 0:
            return self.check_and_build_entities(entity.get("children")[0])
        else:
            complex = entity.get("children")[index]
            complex_glyph = self.build_complex_glyph(complex, label=True)
            nested_glyph = self.handle_nested_complexes(entity, index - 1)
            complex_glyph.add_glyph(nested_glyph)

            return complex_glyph

    def check_and_build_entities(self, entity):
        """Process and handle creation of nested entities.
        Can contain complex, structured, atomic and state entities.

        :param entity: nested entities
        :return:
        """
        complex_agent = None
        if len(entity.get("children")) != 1:
            complex_agent = self.build_complex_glyph(entity)

        glyph = None
        for structure in entity.get("children"):
            glyph = self.build_structured_agent(structure)
            if complex_agent:
                complex_agent.add_glyph(glyph)

        return complex_agent if complex_agent else glyph

    def build_structured_agent(self, structure):
        """Process and build a structured agent.
        It can be just atomic agent or structured agent with some atomic agent inside.

        :param structure: structure dict from processed rule
        :return:
        """
        if len(structure.get("children")) == 0:
            structure_entity = structure["entity"]
            entity_type = self.check_entity_type(structure_entity)
            if entity_type == "atomic":
                glyph = self.build_atomic_agent(structure_entity)
            else:
                glyph = self.build_atomic_agent(structure_entity, entity_type=GlyphClass.COMPLEX)
        else:
            x, y, w, h = self.get_coordinates(structure["coordinates"])
            label = structure["entity"]["token"]
            structured_glyph = self.sbgn.add_glyph(
                glyph_class=GlyphClass.COMPLEX,
                gid=label + "_structured{}".format(str(self.entity_num)),
                x=x,
                y=y,
                width=w,
                height=h,
                label=label,
                compartment=self.current_compartment,
                label_coords={"x": x + 4, "y": y + 4, "width": 40, "height": 15}
            )
            self.entity_num += 1
            for atomic in structure.get("children"):
                atomic_glyph = self.build_atomic_agent(atomic)
                structured_glyph.add_glyph(atomic_glyph)

            glyph = structured_glyph

        return glyph

    def build_atomic_agent(self, atomic, entity_type=GlyphClass.MACROMOLECULE):
        """Create and add atomic glyph to SBGN and return.

        :param atomic: atomic dict of processed rule
        :param entity_type: glyph type, MACROMOLECULE by default
        :return:
        """
        x, y, w, h = self.get_coordinates(atomic["coordinates"])
        label = atomic["token"]
        glyph = self.sbgn.add_glyph(
            glyph_class=entity_type,
            gid=label + "_atomic{}".format(str(self.entity_num)),
            label=label,
            x=x,
            y=y,
            width=w,
            height=h,
            compartment=self.current_compartment,
        )
        if len(atomic.get("children")) != 0:
            state_glyph = self.add_state_glyph(atomic)
            glyph.add_glyph(state_glyph)
        self.entity_num += 1
        return glyph

    def add_state_glyph(self, parent):
        """Add state glyph to parent glyph.

        :param parent: parent glyph to which state belong
        :return:
        """
        state = parent.get("children")[0]
        x, y, w, h = self.get_coordinates(state["coordinates"])
        label = state["token"]
        state_glyph = self.sbgn.add_glyph(
            glyph_class=GlyphClass.STATE_VARIABLE,
            gid=label + "_atomic{}".format(str(self.entity_num)),
            x=x,
            y=y,
            width=w,
            height=h,
            label=label,
        )
        self.entity_num += 1
        return state_glyph

    def build_complex_glyph(self, complex, label=None):
        """Create and add complex glyph to SBGN and return.

        :param complex: complex dict from processed rule
        :param label: indicate if complex has name
        :return:
        """
        x, y, w, h = self.get_coordinates(complex["coordinates"])
        if label:
            label = self.get_label_name(complex)
            gid = label + "_complex{}".format(str(self.entity_num)),
            label_coords = {"x": x + 4, "y": y + 4, "width": 40, "height": 15}
        else:
            gid = "nameless_complex{}".format(str(self.entity_num)),
            label_coords = None
        complex_glyph = self.sbgn.add_glyph(
            glyph_class=GlyphClass.COMPLEX,
            gid=gid,
            x=x,
            y=y,
            width=w,
            height=h,
            compartment=self.current_compartment,
            label=label,
            label_coords=label_coords
        )
        self.entity_num += 1
        return complex_glyph

    def build_compartment_glyph(self, label, x, y, w, h):
        """Create and add compartment glyph to SBGN and return.

        :param label: compartment dict from processed rule
        :return: compartment glyph
        """
        compartment_glyph = self.sbgn.add_glyph(
            glyph_class=GlyphClass.COMPARTMENT,
            gid=label + "_compartment{}".format(str(self.entity_num)),
            label=label,
            x=x,
            y=y,
            width=w,
            height=h,
            label_coords={"x": x + 4, "y": y + 4, "width": 40, "height": 15}
        )
        self.entity_num += 1
        return compartment_glyph

    @staticmethod
    def get_coordinates(coordinates):
        """Unpack coordinates of provided entity from dict and return.

        :param coordinates: dict with coordinates attributes
        :return: x coordinate, y coordinate, width and height of entity
        """
        x, y = coordinates["x"], coordinates["y"]
        width, height = coordinates["width"], coordinates["height"]
        return x, y, width, height

    @staticmethod
    def get_label_name(entity):
        """Return entity name from nested dict.

        :param entity:
        :return: entity name
        """
        name = entity.get("children")[0]["entity"]["token"]

        return name

    @staticmethod
    def check_entity_type(entity):
        """Check entity type trough e-cyano entity API. In case of unsuccessful call - return default atomic type.

        :param entity: entity which type should be checked
        :return: entity type
        """
        label = entity["token"]
        try:
            entity_data = get_entity_api_response(label)
            try:
                entity_type = entity_data.get("data")["type"]
                return entity_type
            except Exception:
                return "atomic"

        except requests.RequestException:
            return "atomic"
