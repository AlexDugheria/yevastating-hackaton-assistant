from difflib import SequenceMatcher
from conf.settings import HIERARCHY



def find_most_similar(hierarchy_dict, val):
    most_similar = ''
    most_sim_val = 0

    for key in hierarchy_dict.keys():
        sim = SequenceMatcher(None, key, val).ratio()

        if sim > most_sim_val:
            most_sim_val = sim
            most_similar = key

    return most_similar

def find_deepest_granularity_hierarchy(tags):
    deepest_val = 0
    deepest_gran = 'MEDIAPLAN'

    for tag in tags:
        level = find_most_similar(HIERARCHY,tag.upper())

        if HIERARCHY[level] > deepest_val:
            deepest_val = HIERARCHY[level]
            deepest_gran = level

    return deepest_gran

def find_shallow_granularity_hierarchy(tags):
    shallow_val = 3
    shallow_gran = 'MEDIAROW'

    for tag in tags:
        level = find_most_similar(HIERARCHY,tag.upper())

        if HIERARCHY[level] < shallow_val:
            shallow_val = HIERARCHY[level]
            shallow_gran = level

    return shallow_gran

