X_ENTITY_DISTANCE = 15
Y_ENTITY_DISTANCE = 25
DEFAULT_ATOMIC_GLYPH_WIDTH = 60
DEFAULT_ATOMIC_GLYPH_HEIGHT = 40


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
        self._compartment_x = 10
        self._compartment_y = 10
        self._current_x = self._compartment_x + X_ENTITY_DISTANCE
        self._current_y = self._compartment_y + Y_ENTITY_DISTANCE

    def calculate_coordinates(self):
        """Calculate and set coordinates for every single entity in equation and get width/height for image."""
        # get coordinates for lef side of equation
        self._calculate_for_one_part(self.left_side)

        # set new compartments and current coordinates
        self._compartment_x = self.x_limit + 324
        self._compartment_y = 10
        self._current_x = self._compartment_x + X_ENTITY_DISTANCE
        self._current_y = self._compartment_y + Y_ENTITY_DISTANCE

        # set process glyph x coordinate
        self.process_glyph_x = self.x_limit + 150

        self._calculate_for_one_part(self.right_side)

        # set process glyph y coordinate
        self.process_glyph_y = self.y_limit / 2

        # set final image width, height
        self.x_limit += 20
        self.y_limit += 30

    def _calculate_for_one_part(self, equation):
        """Calculate coordinates for all entities in one part of equation.
        Also set max_x, max_y what will be necessary for calculation of the main coordinates for image
        and also for process glyph coordinates.

        :param equation: left or right side of equation
        :return:
        """
        for entity in equation.get("children"):  # iterate through the entities separated by `+`
            entity = entity.get("children")[0]
            num_of_children = len(entity.get("children"))  # can have only 2 or 3 children, separated by ::
            if num_of_children == 3:
                # second child will be always complex glyph
                complex_x, complex_y = self._current_x, self._current_y
                self._current_x += X_ENTITY_DISTANCE
                self._current_y += Y_ENTITY_DISTANCE
                max_x, max_y = self._process_unknown_entity(entity.get("children")[0])
                width, height = max_x - complex_x + X_ENTITY_DISTANCE, max_y - complex_y + Y_ENTITY_DISTANCE
                complex_entity = entity.get("children")[1]  # second child will be always complex
                complex_entity["coordinates"] = {
                    "x": complex_x,
                    "y": complex_y,
                    "width": width,
                    "height": height,
                }
                max_x, max_y = complex_x + width, complex_y + height
            else:
                max_x, max_y = self._process_unknown_entity(entity.get("children")[0])

            # set compartment coordinates, last child is always compartment entity
            compartment = entity.get("children")[num_of_children - 1]
            width = max_x - self._compartment_x + X_ENTITY_DISTANCE
            height = max_y - self._compartment_y + Y_ENTITY_DISTANCE
            compartment["coordinates"] = {
                "x": self._compartment_x,
                "y": self._compartment_y,
                "width": width,
                "height": height
            }
            self._check_limits(self._compartment_x, self._compartment_y, width, height)
            # set coordinates for next compartment and current coordinates for next entity
            self._compartment_y = self._compartment_y + height + Y_ENTITY_DISTANCE
            self._current_x = self._compartment_x + X_ENTITY_DISTANCE
            self._current_y = self._compartment_y + Y_ENTITY_DISTANCE

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

                for atomic in structure_entity.get("children"):
                    max_x, max_y = self._set_coordinates_for_atomic_entity(atomic)

                width, height = max_x - structure_x + X_ENTITY_DISTANCE, max_y - structure_y + Y_ENTITY_DISTANCE
                structure_entity["coordinates"] = {
                    "x": structure_x,
                    "y": structure_y,
                    "width": width,
                    "height": height,
                }

                self._check_limits(structure_x, structure_y, width, height)
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
            self._check_limits(complex_agent_x, complex_agent_y, width, height)
            entity_max_x, entity_max_y = complex_agent_x + width, complex_agent_y + height

        return entity_max_x, entity_max_y

    def _set_coordinates_for_atomic_entity(self, atomic_entity):
        """Calculate and set coordinates for atomic entity and for its state if has some.

        :param atomic_entity: atomic entity with state or without
        :return: width, height for parent entity
        """
        width, height = self._calculate_width_height(atomic_entity["token"])
        x, y = self._current_x, self._current_y
        self._check_limits(x, y, width, height)
        atomic_entity["coordinates"] = {"x": x, "y": y, "width": width, "height": height}

        # if has state, set state coordinates
        if len(atomic_entity.get("children")) != 0:
            self._set_state_coordinates(atomic_entity)

        self._current_y = y + height + Y_ENTITY_DISTANCE

        return x + width, y + height

    @staticmethod
    def _set_state_coordinates(structure_entity):
        """Set coordinates for state entity according to parent coordinates.
        Put the state entity at the head of atomic agent.
        """
        state_entity = structure_entity.get("children")[0]
        parent_coor = structure_entity["coordinates"]
        state_entity["coordinates"] = {
            "x": parent_coor["x"] + (parent_coor["width"] - 20) / 2,
            "y": parent_coor["y"] - 7,
            "width": 20,
            "height": 15,
        }

    @staticmethod
    def _calculate_width_height(name_token):
        """Calculate the the width and height for label according to length of entity name."""
        # default parameters
        width, height = DEFAULT_ATOMIC_GLYPH_WIDTH, DEFAULT_ATOMIC_GLYPH_HEIGHT
        name_lenght = len(name_token)
        if name_lenght > 20:
            width, height = name_lenght*3, height

        return width, height

    def _check_limits(self, x, y, width, height):
        """Check and set new max_x, max_y coordinates."""
        if x + width > self.x_limit:
            self.x_limit = x + width
        if y + height > self.y_limit:
            self.y_limit = y + height
