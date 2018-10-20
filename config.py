entity_url = "https://api.e-cyanobacterium.org/entities"
reaction_url = "https://api.e-cyanobacterium.org/reactions"

reaction_type = {
    "<=>": "rev",
    "=>": "irev"
}

test_rule = "pbc{n}::pbs::cyt + 5 ps2(chl{*}|p680{n}).phe(chl{n})::tlm => NADHP{n}::pbs::cell + phe::cyt + ps2(chl{p}|p680{*})::tlm"
