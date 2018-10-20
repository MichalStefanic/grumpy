from __future__ import absolute_import

import json
import os
import sys

sys.path.append("{}/BCSLruleParser/bin/lib/python".format(os.getcwd()))
try:
    import RuleParserPy
except Exception:
    raise ImportError("Invalid import path.")


def parse_rule(rule):
    """
    Parse SBGB rule via SBGNruleParser.

    :param rule: SBGN rule in string representation
    :return: dict: Parsed rule in tree structured
    """
    # parser return error if `|` occur in rule, because he expected `,`
    rule = rule.replace("|", ",")
    try:
        raw_response = RuleParserPy.parseEquations(rule)
        parsed_rule = json.loads(raw_response)  # convert from string to dictionary

        if parsed_rule.get("error"):
            raise IOError("Not a valid rule tree.")

        return parsed_rule
    except Exception:
        raise Exception("Rule parsing failed.")
