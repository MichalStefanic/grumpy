"""API handlers."""
import requests

from flask import send_file
from typing import Dict

import config

from helpers import (
    clean_image_folder,
    concatenate_images,
    get_reaction_items_from_ecyano_api,
    is_reaction_reversible,
    make_conversion,
    sort_reactions_items_by_type,
)
from parser.rule_parser import parse_rule
from managers.coordinates_calculator import CoordinatesCalculator
from managers.rule_manager import RuleManager
from managers.reaction_manager import ReactionManager


def pong() -> Dict:
    """Pong the received ping."""

    return {"pong": True}


def get_rule(data):
    """Handler for reaction API endpoint.

    :param data: data dictionary, check swagger schema
    :return: PNG or SVG image of rule in SBGN
    """
    rule = data.get("rule")
    as_svg = data.get("as_svg")

    clean_image_folder()  # clean image folder to not waste disc space

    rule_dict = parse_rule(rule)
    equation = rule_dict.get("children")[0]

    reaction_type = config.REACTION_TYPE[equation.get("token")]

    # left side of rule
    left_side = equation.get("children")[0]
    # right side of rule
    right_side = equation.get("children")[1]

    # calculate coordinates for all components and process glyph
    processed_equation = CoordinatesCalculator(left_side, right_side)
    processed_equation.calculate_coordinates()

    sbgn = RuleManager().create_sbgn_from_rule(processed_equation)  # create SBGN representation of rule
    file_name = sbgn.render_sbgn()  # render SBGN diagram

    if reaction_type == "reversible":
        #  in case of reversible rule, exchange left and right side of equation and create second image
        processed_equation = CoordinatesCalculator(right_side, left_side)
        processed_equation.calculate_coordinates()

        sbgn = RuleManager().create_sbgn_from_rule(processed_equation)
        file_name2 = sbgn.render_sbgn()

        # join final images into one
        file_name = concatenate_images(file_name, file_name2)

    return send_response(file_name, as_svg)


def get_reaction(data):
    """Handler for reaction API endpoint.

    :param data: data dictionary, check swagger schema
    :return: PNG or SVG image of reaction in SBGN
    """
    model_id = data.get("model_id")
    reaction_id = data.get("reaction_id")
    as_svg = data.get("as_svg")

    clean_image_folder()  # clean image folder to not waste disc space

    # get reaction items from e-cyano API
    api_response = get_reaction_items_from_ecyano_api(model_id, reaction_id)
    reaction_items = api_response["data"]

    # sort reaction items by type (reactant, product, modifier)
    sorted_reaction_items = sort_reactions_items_by_type(reaction_items)

    reaction_manager = ReactionManager(sorted_reaction_items)
    sbgn = reaction_manager.create_sbgn_from_reaction()

    file_name = sbgn.render_sbgn()

    try:
        # check whether reaction is reversible or not with e-cyano API
        is_reversible = is_reaction_reversible(model_id, reaction_id)
    except requests.RequestException:
        raise("Cannot contact e-cyano API or missing data for model {} - reaction {}".format(model_id, reaction_id))

    if is_reversible:
        # in case of reversible reaction, exchange products and reactions and generate second image
        new_reaction_items = {
            "reactants": sorted_reaction_items["products"],
            "products": sorted_reaction_items["reactants"],
            "modifiers": sorted_reaction_items["modifiers"]
        }

        sbgn = ReactionManager(new_reaction_items).create_sbgn_from_reaction()
        file_name2 = sbgn.render_sbgn()

        # join final images into one
        file_name = concatenate_images(file_name, file_name2)

    return send_response(file_name, as_svg)


def send_response(file, is_svg=False):
    """If SVG was requested, make conversion from PNG to SVG and send image to response.

    :param file: str: name of image
    :param is_svg: bool: return as svg
    :return:
    """
    # return type of image
    mimetype = "image/png"

    # if svg format was requested, make conversion from png and change return type
    if is_svg:
        file = make_conversion(file)
        mimetype = "image/svg+xml"

    return send_file(file, mimetype=mimetype)
