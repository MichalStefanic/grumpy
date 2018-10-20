import config
from parser.rule_parser import parse_rule

from main.coordinates_calculator import CoordinatesCalculator
from main.sbgn_rule_maker import SBGNRuleMaker


def get_rule(rule):
    rule_dict = parse_rule(rule)
    equation = rule_dict.get("children")[0]

    reaction_type = config.reaction_type[equation.get("token")]

    # left side of reaction
    left_side = equation.get("children")[0]
    # right side of reaction
    right_side = equation.get("children")[1]

    # set coordinates to individual entity and set process glyph coordinates and image width, height
    processed_equation = CoordinatesCalculator(left_side, right_side)
    processed_equation.calculate_coordinates()

    # create SBGN representation of parsed rule
    sbgn = SBGNRuleMaker().create_sbgn_from_rule(processed_equation)

    """
    if reaction_type == "rev":
        reversed_sbgn = reverse_sbgn(sbgn)
    """

    return sbgn


def get_reaction():
    pass
