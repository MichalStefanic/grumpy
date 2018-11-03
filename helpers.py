"""Helper function of application."""
import os
import requests
import numpy as np

from subprocess import call
from PIL import Image

from config import ECYANO_API_URL


class Coordinates:
    """Class representation of coordinates."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def increase_coordinates(self, x, y):
        """Increase value of one or both coordinates about provided value."""
        if x:
            self.x += x
        if y:
            self.y += y


def sort_reactions_items_by_type(reaction_items):
    """Sort items into dictionary by type of reaction item (product, reactant or modifier).

    :param reaction_items: dict with all reaction items
    :return: dict of sorted items by type
    """
    items = {"reactants": [], "products": [], "modifiers": []}

    for item in reaction_items:
        if item["type"] == "reactant":
            items["reactants"].append(item)
        elif item["type"] == "product":
            items["products"].append(item)
        elif item["type"] == "modifier":
            items["modifiers"].append(item)

    # if there are no reactants add source instead
    if not items["reactants"]:
        items["reactants"].append({"type": "source/sink", "stoichiometry": 0})

    # if there are no products add source instead
    if not items["products"]:
        items["products"].append({"type": "source/sink", "stoichiometry": 0})

    return items


def make_conversion(file_name):
    """Convert PNG image to SVG.
    Firstly, PNG need to be convert to PPM, then PPM is converted into SVG.

    :param file_name: name of image file
    :return: name of svg image
    """
    im = Image.open(file_name)

    ppm_temp_file = file_name.split(".")[0] + ".ppm"
    im.save(ppm_temp_file)
    svg_file = ppm_temp_file.split(".")[0] + ".svg"
    call(["potrace", "-s", ppm_temp_file, "-o", svg_file])

    return svg_file


def concatenate_images(filename1, filename2):
    """Concatenate two images into one.

    :param filename1: name of first image
    :param filename2: name of second image
    :return: name final image
    """
    images = [Image.open(i) for i in [filename1, filename2]]

    # resize larger image to size of the smaller one
    min_shape = sorted([(np.sum(i.size), i.size) for i in images])[0][1]
    imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in images))

    new_filename = filename1.split(".")[0] + filename2.split("/")[-1]

    # save that beautiful picture
    imgs_comb = Image.fromarray(imgs_comb)
    imgs_comb.save(new_filename)

    return new_filename


def clean_image_folder():
    """Delete images from image folder if exist, otherwise create empty folder."""
    image_folder = "{}/tmp_images".format(os.getcwd())
    try:
        for the_file in os.listdir(image_folder):
            file_path = os.path.join(image_folder, the_file)
            os.unlink(file_path)
    except FileNotFoundError:
        os.mkdir(image_folder)


def get_reaction_items_from_ecyano_api(model_id, reaction_id):
    """Call e-cyano API and get reaction items for reaction with provided IDs.

    :param model_id: model ID
    :param reaction_id: reaction ID
    :return: reaction items of reaction in current model
    """
    session = requests.Session()
    url = ECYANO_API_URL + "/models/{}/reactions/{}/reactionItems".format(model_id, reaction_id)
    try:
        response = session.get(url)
        return response.json()
    except Exception:
        raise requests.RequestException("Failed to contact e-cyano API.")


def is_reaction_reversible(model_id, reaction_id):
    """Call e-cyano API with provided IDs and check if reaction is reversible.

    :param model_id: model ID
    :param reaction_id: reaction ID
    :return: reaction items of reaction in current model
    """
    session = requests.Session()
    url = ECYANO_API_URL + "/models/{}/reactions/{}".format(model_id, reaction_id)
    try:
        response = session.get(url).json()
        is_reversible = response["data"][0]["isReversible"] == 1

        return is_reversible
    except Exception:
        raise requests.RequestException("Failed to contact e-cyano API.")


def get_entity_api_response(label):
    """Call e-cyano entity API and check entity type.

    :param label: name of entity
    :return: dict with entity data or error
    """
    session = requests.Session()
    url = ECYANO_API_URL + "/entities/{}".format(label)
    try:
        response = session.get(url)
        return response.json()
    except Exception:
        raise requests.RequestException("Failed to contact e-cyano API.")
