"""Reaction manager."""
from libsbgnpy.libsbgn import GlyphClass

from config import (
    DEFAULT_ATOMIC_GLYPH_WIDTH as WIDTH,
    DEFAULT_ATOMIC_GLYPH_HEIGHT as HEIGHT,
    PROCESS_GLYPH_SIZE,
    REACTANTS_PRODUCTS_DISTANCE,
    X_DISTANCE,
    Y_DISTANCE,
)
from helpers import Coordinates
from managers.sbgn_manager import SbgnManager


class ReactionManager:
    def __init__(self, reaction_items):
        self.sbgn = None
        self.reaction_items = reaction_items
        self.entity_num = 1
        self.max_coordinates = Coordinates(0, 0)

        # helpers parameters
        self.current_coordinates = Coordinates(10, 10)
        # right_x parameter indicate where product should be located
        self.right_x = X_DISTANCE + WIDTH + REACTANTS_PRODUCTS_DISTANCE

    def create_sbgn_from_reaction(self):
        """Calculate coordinates, create and render SBGN."""
        if self.reaction_items["modifiers"]:
            # in case reactions contain modifiers, calculate coordinates with modifiers
            self.calculate_with_modifiers()
        else:
            self.calculate_reactants_and_products_coordinates()

        self.sbgn = SbgnManager(
            width=self.max_coordinates.x,
            height=self.max_coordinates.y,
            pg_x=(self.max_coordinates.x / 2) - PROCESS_GLYPH_SIZE / 2,
            pg_y=(self.max_coordinates.y / 2) - PROCESS_GLYPH_SIZE / 2,
        )

        for item in self.reaction_items["reactants"]:
            if item["type"] == "source/sink":
                glyph = self.add_source_sink(item)
            else:
                glyph = self.add_macromolecule(item)
            self.sbgn.add_arc_glyph(glyph=glyph, side="left", stoichiometry=item["stoichiometry"])

        for item in self.reaction_items["products"]:
            if item["type"] == "source/sink":
                glyph = self.add_source_sink(item)
            else:
                glyph = self.add_macromolecule(item)
            self.sbgn.add_arc_glyph(glyph=glyph, side="right", stoichiometry=item["stoichiometry"])

        for item in self.reaction_items["modifiers"]:
            glyph = self.add_macromolecule(item)
            self.sbgn.add_arc_glyph(glyph=glyph, side="modifier")

        return self.sbgn

    def add_macromolecule(self, item):
        """Add marcomolecule glyph, which represent reactant, product or modifier, to SBGN.

        :param item: dictionary with name and coordinates
        :return: new macromolecule glyph
        """
        gid = item["name"] + str(self.entity_num),
        glyph = self.sbgn.add_glyph(
            glyph_class=GlyphClass.MACROMOLECULE,
            gid=gid,
            x=item["coordinates"].x,
            y=item["coordinates"].y,
            width=WIDTH,
            height=HEIGHT,
            label=item["name"],
        )
        self.entity_num += 1
        return glyph

    def add_source_sink(self, item):
        """Add source/sink glyph to SBGN.

        :param item: dictionary with coordinates
        :return: new source/sink glyph
        """
        gid = "sink/source" + str(self.entity_num),
        glyph = self.sbgn.add_glyph(
            glyph_class=GlyphClass.SOURCE_AND_SINK,
            gid=gid,
            x=item["coordinates"].x,
            y=item["coordinates"].y,
            width=50,
            height=50,
        )
        self.entity_num += 1
        return glyph

    def calculate_with_modifiers(self):
        """Calculate coordinates with modifiers."""
        modifiers = self.reaction_items["modifiers"]

        middle = self.get_middle_index(len(modifiers))
        # split modifiers into two arrays, first modifiers will be up, second will be at the bottom of diagram
        upper_modifiers = modifiers[:middle]
        lower_modifiers = modifiers[middle:]

        self.current_coordinates.increase_coordinates(WIDTH + X_DISTANCE, None)
        self.calculate_modifiers_coordinates(upper_modifiers)
        # y coordinate where first product should be located
        new_y = self.current_coordinates.y + HEIGHT + Y_DISTANCE

        if self.current_coordinates.x > self.right_x:
            self.right_x = self.current_coordinates.x
        self.current_coordinates = Coordinates(10, new_y)

        # y coordinate where rest of the modifiers should be located at the bottom
        new_y = self.calculate_reactants_and_products_coordinates()
        self.current_coordinates = Coordinates(10 + WIDTH + X_DISTANCE, new_y)

        self.calculate_modifiers_coordinates(lower_modifiers)
        self.max_coordinates = Coordinates(self.right_x + WIDTH + X_DISTANCE,
                                           self.current_coordinates.y + HEIGHT + Y_DISTANCE)

    def calculate_modifiers_coordinates(self, modifiers):
        """Calculate modifiers coordinates.

        :param modifiers: list of modifiers
        """
        for modifier in modifiers:
            modifier["coordinates"] = Coordinates(self.current_coordinates.x, self.current_coordinates.y)
            self.current_coordinates.increase_coordinates(WIDTH + X_DISTANCE, None)

    def calculate_reactants_and_products_coordinates(self):
        """Calculate coordinates for product and reactants."""
        reactants = self.reaction_items["reactants"]
        products = self.reaction_items["products"]

        # this will be needed to put product at same level as reactant
        right_y = self.current_coordinates.y
        for reactant in reactants:
            reactant["coordinates"] = Coordinates(self.current_coordinates.x, self.current_coordinates.y)
            self.current_coordinates.increase_coordinates(None, HEIGHT + Y_DISTANCE)

        max_y1 = self.current_coordinates.y  # y coordinates where last reactant end
        self.current_coordinates = Coordinates(self.right_x, right_y)

        for product in products:
            product["coordinates"] = Coordinates(self.current_coordinates.x, self.current_coordinates.y)
            self.current_coordinates.increase_coordinates(None, HEIGHT + Y_DISTANCE)

        max_y2 = self.current_coordinates.y  # y coordinates where last product end
        self.max_coordinates = Coordinates(self.current_coordinates.x + WIDTH + X_DISTANCE, max(max_y1, max_y2))

        # return max y coordinate
        return max(max_y1, max_y2)

    @staticmethod
    def get_middle_index(length):
        """Get middle of array.

        :param length: length of array
        :return: middle index of array
        """
        return (length // 2) + (length % 2)
