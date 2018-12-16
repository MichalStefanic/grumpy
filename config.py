"""Config with application parameters."""

HOST = "localhost"
PORT = 5000

ECYANO_API_URL = "https://api.e-cyanobacterium.org"

REACTION_TYPE = {
    "<=>": "reversible",
    "=>": "ireversible"
}

PROCESS_GLYPH_SIZE = 24
STOICHIOMETRY_GLYPH_SIZE = 15

# for reactions
X_DISTANCE = 10
Y_DISTANCE = 10
REACTANTS_PRODUCTS_DISTANCE = 180

# for rules
X_ENTITY_DISTANCE = 20
Y_ENTITY_DISTANCE = 30

DEFAULT_ATOMIC_GLYPH_WIDTH = 70
DEFAULT_ATOMIC_GLYPH_HEIGHT = 50

DEFAULT_STATE_GLYPH_WIDTH = 25
DEFAULT_STATE_GLYPH_HEIGHT = 20

MAX_ATOMIC_GLYPH_WIDTH = 120

TEST_RULE = "3 pbc{n}::pbs::X::cyt + 2 phe{-}::ps1::ext + 5 ps2(chl{n}|p680{+}).phe(chl{n})::tlm => " \
            "3 pbc{n}::pbs::cell + 2 phe{n}::ps1::cyt + 5 ps2(chl{n}|p680{n})::tlm + 5 phe(chl{-})::tlm"
