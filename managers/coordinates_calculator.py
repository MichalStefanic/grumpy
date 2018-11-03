from config import (
    X_ENTITY_DISTANCE,
    Y_ENTITY_DISTANCE,
    DEFAULT_ATOMIC_GLYPH_WIDTH,
    DEFAULT_ATOMIC_GLYPH_HEIGHT,
    DEFAULT_STATE_GLYPH_WIDTH,
    DEFAULT_STATE_GLYPH_HEIGHT,
    MAX_ATOMIC_GLYPH_WIDTH,
)


class CoordinatesCalculator:

    def __init__(self, left_side, right_side):
        # attributes needed for SBGN generation
        self.left_side = left_side
        self.right_side = right_side
        self.process_glyph_x = None
        self.process_glyph_y = None
        # determine process glyph position and width/height of image
        self.x_limit = 0
        self.y_limit = 0

        # helpers attributes for locale purpose
        self._current_x = 0
        self._current_y = 0

        self.compartments = {}

    def calculate_coordinates(self):
        """Calculate and set coordinates for every single entity in equation and get width/height for image."""
        # get coordinates for lef side of equation
        self._calculate_for_one_part(self.left_side)

        # set process glyph x coordinate
        self.process_glyph_x = self.x_limit + 150

        self._calculate_for_one_part(self.right_side, side="right_side")

        self.x_limit, self.y_limit = self._generate_real_coordinates_according_to_compartment()

        # set process glyph y coordinate
        self.process_glyph_y = self.y_limit / 2

        # set final image width, height
        self.x_limit += 10
        self.y_limit += 20

    def _calculate_for_one_part(self, equation, side="left_side"):
        """Calculate coordinates for all entities in one part of equation.
        Also set max_x, max_y what will be necessary for calculation of the main coordinates for image
        and also for process glyph coordinates.

        :param equation: left or right side of equation
        :return:
        """
        max_width = 0
        for entity in equation.get("children"):  # iterate through the entities separated by `+`
            single_entity = entity.get("children")[0]
            num_of_children = len(single_entity.get("children"))  # children separated by ::
            width, height = self._handle_complex_recursion(single_entity, num_of_children - 2)  # penultimate entity
            single_entity["size"] = {"width": width, "height": height}
            if width > max_width:
                max_width = width
            self._current_x, self._current_y = 0, 0

            # add complex into compartments
            compartment_entity = single_entity.get("children")[num_of_children - 1]
            compartment_name = compartment_entity.get("children")[0]["entity"]["token"]
            if self.compartments.get(compartment_name) is None:
                self.compartments[compartment_name] = {"left_side": [], "right_side": []}
                self.compartments[compartment_name][side].append(single_entity)
            else:
                self.compartments[compartment_name][side].append(single_entity)

        if side == "left":
            self.x_limit = max_width + 2*X_ENTITY_DISTANCE
        else:
            self.x_limit += max_width + 2*X_ENTITY_DISTANCE

    def _add_compartment(self, entity, compartment_entity, side):
        compartment_name = compartment_entity.get("children")[0]["entity"]["token"]
        if self.compartments.get(compartment_name) is None:
            self.compartments[compartment_name] = {"left": [], "right": []}
            self.compartments[compartment_name][side].append(entity)
        else:
            self.compartments[compartment_name][side].append(entity)

    def _handle_complex_recursion(self, entity, index):
        if index == 0:
            max_x, max_y = self._process_unknown_entity(entity.get("children")[index])
        else:
            complex_x, complex_y = self._current_x, self._current_y
            self._current_x += X_ENTITY_DISTANCE
            self._current_y += Y_ENTITY_DISTANCE

            # go deeper into recursion
            x, y = self._handle_complex_recursion(entity, index - 1)
            width, height = x - complex_x + X_ENTITY_DISTANCE, y - complex_y + Y_ENTITY_DISTANCE

            entity = entity.get("children")[index]
            entity["coordinates"] = {
                "x": complex_x,
                "y": complex_y,
                "width": width,
                "height": height,
            }

            max_x, max_y = complex_x + width, complex_y + height

        return max_x, max_y

    def _process_unknown_entity(self, entity):
        """Figure out structured of this entity and calculate coordinates for all its parts.

        :param entity: atomic agent, structured agent, even complex
        :return: width, height for parent entity
        """
        is_complex_agent = False
        complex_agent_x, complex_agent_y = None, None
        if len(entity.get("children")) > 1:  # entities separeted by .
            is_complex_agent = True
            complex_agent_x, complex_agent_y = self._current_x, self._current_y
            self._current_x += X_ENTITY_DISTANCE
            self._current_y += Y_ENTITY_DISTANCE

        entity_max_x, entity_max_y = 0, 0
        for structure_entity in entity.get("children"):
            if len(structure_entity.get("children")) == 0:
                atomic = structure_entity.get("entity")
                max_x, max_y = self._set_coordinates_for_atomic_entity(atomic)
            else:
                structure_x, structure_y = self._current_x, self._current_y
                self._current_x += X_ENTITY_DISTANCE
                self._current_y += Y_ENTITY_DISTANCE

                max_x, max_y = 0, 0
                for atomic in structure_entity.get("children"):
                    max_x, max_y = self._set_coordinates_for_atomic_entity(atomic)

                width, height = max_x - structure_x + X_ENTITY_DISTANCE, max_y - structure_y + Y_ENTITY_DISTANCE
                structure_entity["coordinates"] = {
                    "x": structure_x,
                    "y": structure_y,
                    "width": width,
                    "height": height,
                }

                self._current_x, self._current_y = structure_x, structure_y + height + Y_ENTITY_DISTANCE
                max_x, max_y = structure_x + width, structure_y + height

            if max_x > entity_max_x:
                entity_max_x = max_x
            if max_y > entity_max_y:
                entity_max_y = max_y

        if is_complex_agent:
            width = entity_max_x - complex_agent_x + X_ENTITY_DISTANCE
            height = entity_max_y - complex_agent_y + Y_ENTITY_DISTANCE
            entity["coordinates"] = {
                "x": complex_agent_x,
                "y": complex_agent_y,
                "width": width,
                "height": height,
                }
            entity_max_x, entity_max_y = complex_agent_x + width, complex_agent_y + height

        return entity_max_x, entity_max_y

    def _set_coordinates_for_atomic_entity(self, atomic_entity):
        """Calculate and set coordinates for atomic entity and for its state if has some.

        :param atomic_entity: atomic entity with state or without
        :return: width, height for parent entity
        """
        try:
            state_entity = atomic_entity.get("children")[0]
            state_width, state_height = self.calculate_width_height_of_entity(state_entity["token"], state=True)
        except IndexError:
            state_entity, state_width, state_height = None, 0, 0

        width, height = self.calculate_width_height_of_entity(atomic_entity["token"])
        x, y = self._current_x, self._current_y

        # if has state, set state coordinates and recalculate width, height values according to state entity size
        if state_entity:
            if state_width > width:
                width = state_width + 15
            if state_height > height / 2:
                height += state_height
            atomic_entity["coordinates"] = {"x": x, "y": y, "width": width, "height": height}
            self._set_state_coordinates(atomic_entity, state_width, state_height)
        else:
            atomic_entity["coordinates"] = {"x": x, "y": y, "width": width, "height": height}

        # if has state, set state coordinates
        if state_entity:
            self._set_state_coordinates(atomic_entity, state_width, state_height)

        self._current_y = y + height + Y_ENTITY_DISTANCE

        return x + width, y + height

    @staticmethod
    def _set_state_coordinates(atomic_entity, width, height):
        """Set coordinates for state entity according to parent coordinates.
        Put the state entity at the head of atomic agent.
        """
        state_entity = atomic_entity.get("children")[0]
        parent_coor = atomic_entity["coordinates"]
        state_entity["coordinates"] = {
            "x": parent_coor["x"] + (parent_coor["width"] - width) / 2,
            "y": parent_coor["y"] - (height / 2),
            "width": width,
            "height": height,
        }

    @staticmethod
    def calculate_width_height_of_entity(name_token, state=False):
        """Calculate the the width and height for label according to length of entity name."""
        # default parameters
        if state:
            width, height = DEFAULT_STATE_GLYPH_WIDTH, DEFAULT_STATE_GLYPH_HEIGHT
        else:
            width, height = DEFAULT_ATOMIC_GLYPH_WIDTH, DEFAULT_ATOMIC_GLYPH_HEIGHT

        max_word_length = len(name_token)
        """
        num_of_words = len(name_token.split(" "))
        if num_of_words > 1:
            height += num_of_words * 12
            max_word_length = 0
            for word in name_token.split(" "):
                if len(word) > max_word_length:
                    max_word_length = len(word)
            name_token.reaplce(" ", "\n")
        """

        # one letter has width 6
        if max_word_length > width / 7:
            width = max_word_length * 7
            if width > MAX_ATOMIC_GLYPH_WIDTH:
                width = MAX_ATOMIC_GLYPH_WIDTH
        return width, height

    def _generate_real_coordinates_according_to_compartment(self):
        self.compartments = self._get_sorted_compartments()
        final_compartments = {}
        left_current_x, left_current_y = X_ENTITY_DISTANCE, Y_ENTITY_DISTANCE
        right_current_x, right_current_y = self.process_glyph_x + 174, Y_ENTITY_DISTANCE

        for compartments in self.compartments.get("both_side_comps"):
            for compartment, entities in compartments.items():
                comp_x, comp_y = left_current_x, left_current_y
                comp_width, comp_height = 0, 0
                left_current_x += X_ENTITY_DISTANCE
                left_current_y += Y_ENTITY_DISTANCE
                right_current_y += Y_ENTITY_DISTANCE
                for left_entity in entities.get("left_side"):
                    self._recalculate_coordinates(left_entity, left_current_x, left_current_y)
                    left_current_y += left_entity["size"]["height"] + Y_ENTITY_DISTANCE
                    if left_current_y - comp_y > comp_height:
                        comp_height = left_current_y - comp_y
                for right_entity in entities.get("right_side"):
                    self._recalculate_coordinates(right_entity, right_current_x, right_current_y)
                    right_current_y += right_entity["size"]["height"] + Y_ENTITY_DISTANCE
                    if right_current_y - comp_y > comp_height:
                        comp_height = right_current_y - comp_y
                    if right_current_x + right_entity["size"]["width"] + X_ENTITY_DISTANCE - comp_x > comp_width:
                        comp_width = right_current_x + right_entity["size"]["width"] + X_ENTITY_DISTANCE - comp_x

                final_compartments[compartment] = {
                    "coordinates": {
                        "x": comp_x,
                        "y": comp_y,
                        "width": comp_width,
                        "height": comp_height
                    }
                }

                if left_current_y > right_current_y:
                    left_current_y, right_current_y = left_current_y, left_current_y
                else:
                    left_current_y, right_current_y = right_current_y, right_current_y

                left_current_x = X_ENTITY_DISTANCE
                right_current_x = self.process_glyph_x + 174
                left_current_y += Y_ENTITY_DISTANCE
                right_current_y += Y_ENTITY_DISTANCE

        for compartments in self.compartments.get("left_side_comps"):
            for compartment, entities in compartments.items():
                comp_x, comp_y = left_current_x, left_current_y
                comp_width, comp_height = 0, 0
                left_current_x += X_ENTITY_DISTANCE
                left_current_y += Y_ENTITY_DISTANCE
                for left_entity in entities.get("left_side"):
                    self._recalculate_coordinates(left_entity, left_current_x, left_current_y)
                    left_current_y += left_entity["size"]["height"] + Y_ENTITY_DISTANCE
                    if left_current_y - comp_y > comp_height:
                        comp_height = left_current_y - comp_y
                    if left_current_x + left_entity["size"]["width"] + X_ENTITY_DISTANCE - comp_x > comp_width:
                        comp_width = left_current_x + left_entity["size"]["width"] + X_ENTITY_DISTANCE - comp_x

                final_compartments[compartment] = {
                    "coordinates": {
                        "x": comp_x,
                        "y": comp_y,
                        "width": comp_width,
                        "height": comp_height
                    }
                }

                left_current_x = X_ENTITY_DISTANCE
                left_current_y += Y_ENTITY_DISTANCE

        for compartments in self.compartments.get("right_side_comps"):
            for compartment, entities in compartments.items():
                comp_x, comp_y = right_current_x, right_current_y
                comp_width, comp_height = 0, 0
                right_current_x += X_ENTITY_DISTANCE
                right_current_y += Y_ENTITY_DISTANCE
                for right_entity in entities.get("right_side"):
                    self._recalculate_coordinates(right_entity, right_current_x, right_current_y)
                    right_current_y += right_entity["size"]["height"] + Y_ENTITY_DISTANCE
                    if right_current_y - comp_y > comp_height:
                        comp_height = right_current_y - comp_y
                    if right_current_x + right_entity["size"]["width"] + X_ENTITY_DISTANCE - comp_x > comp_width:
                        comp_width = right_current_x + right_entity["size"]["width"] + X_ENTITY_DISTANCE - comp_x

                final_compartments[compartment] = {
                    "coordinates": {
                        "x": comp_x,
                        "y": comp_y,
                        "width": comp_width,
                        "height": comp_height
                    }
                }

                right_current_x = self.process_glyph_x + 174
                right_current_y += Y_ENTITY_DISTANCE

        self.compartments = final_compartments
        max_y = left_current_y if left_current_y > right_current_y else right_current_y
        return right_current_x, max_y

    def _get_sorted_compartments(self):
        """Sort compartments into three categories: whether they are on left, right or both sides of rule.

        :return: sorted compartments
        """
        sorted_compartments = {"left_side_comps": [], "right_side_comps": [], "both_side_comps": []}
        for key, value in self.compartments.items():
            if value.get("left_side") and value.get("right_side"):
                sorted_compartments["both_side_comps"].append({key: value})
            elif value.get("left_side"):
                sorted_compartments["left_side_comps"].append({key: value})
            else:
                sorted_compartments["right_side_comps"].append({key: value})

        return sorted_compartments

    def _recalculate_coordinates(self, entity, x, y):
        for complex_entity in entity.get("children")[:-1]:
            try:
                self._raise_coordinates(complex_entity["coordinates"], x, y)
            except KeyError:
                pass
            for nested_complex_entity in complex_entity.get("children"):
                try:
                    self._raise_coordinates(nested_complex_entity["coordinates"], x, y)
                except KeyError:
                    pass
                entity_node = nested_complex_entity["entity"]
                try:
                    self._raise_coordinates(entity_node["coordinates"], x, y)
                except KeyError:
                    pass
                for state_entity in entity_node.get("children"):
                    self._raise_coordinates(state_entity["coordinates"], x, y)
                for structured_entity in nested_complex_entity.get("children"):
                    self._raise_coordinates(structured_entity["coordinates"], x, y)
                    for state_entity in structured_entity.get("children"):
                        self._raise_coordinates(state_entity["coordinates"], x, y)

    @staticmethod
    def _raise_coordinates(coordinates, x, y):
        orig_x, orig_y = coordinates["x"], coordinates["y"]
        coordinates["x"], coordinates["y"] = orig_x + x, orig_y + y
