import numpy as np
import pandas as pd
import json
from copy import deepcopy
from .load_data import load_saved_model
from .load_data import get_filtered_timeline_map
from .load_data import construct_data


def get_full_years(author_map):
    years = []
    for inst in author_map:
        for year in author_map[inst]:
            if year not in years:
                years.append(year)
    return sorted(years, reverse=True)

def get_inst_by_year(author_map, year):
    inst_list = []
    for inst in author_map:
        if year in author_map[inst]:
            inst_list.append(inst)
    return(inst_list)

def score_per_year(y_map, unique_list):
    score_map = {}
    copy_y_map = deepcopy(y_map)
    for year in copy_y_map:
        inst_score = []
        for inst in unique_list:
            score = 0
            if (year+1) in copy_y_map and inst in copy_y_map[year+1]:
                score += 1
            if (year-1) in copy_y_map and inst in copy_y_map[year-1]:
                score += 1
            if inst in copy_y_map[year]:
                score += 1
            inst_score.append(score)
        score_map[year] = inst_score
    return score_map

def score_addition(s_per_year):
    new_s_per_year = {}
    for year in s_per_year:
        sum_year = np.array(s_per_year[year])
        if year+1 in s_per_year:
            sum_year += np.array(s_per_year[year+1])
        if year-1 in s_per_year:
            sum_year += np.array(s_per_year[year-1])
        new_s_per_year[year] = list(np.sqrt(sum_year))
    return new_s_per_year


def find_best_match(s_per_year, unique_list):
    y_map = {}
    prev_idx = None
    prev_year = None
    for year in s_per_year:
        best_idx = np.argmax(s_per_year[year])
        if prev_idx is None:
            y_map[year] = [unique_list[best_idx]]
        else:
            if best_idx != prev_idx and (prev_year == (year+1)):
                y_map[year] = [unique_list[best_idx], unique_list[prev_idx]]
            else:
                y_map[year] = [unique_list[best_idx]]
        prev_idx = best_idx
        prev_year = year
    return y_map

def get_unique_inst(years_map):
    ret = []
    for year in years_map:
        for inst in years_map[year]:
            if inst not in ret:
                ret.append(inst)
    return ret

def fill_missing(y_map):
    extra_years = []
    years = list(y_map.keys())[::-1]
    for i, year in enumerate(years):
        if i < (len(y_map)-1) and (year+1) not in y_map:
            current_inst = y_map[year]
            next_inst = y_map[years[i+1]]

            common_inst = list(set(current_inst).intersection(next_inst))
            if len(common_inst) > 0:
                for j in range(year+1, years[i+1]):
                    extra_years.append((j, common_inst))

    for y, i in extra_years:
        y_map[y] = i

def build_new_author_map(y_map):
    copy_y_map = deepcopy(y_map)
    unique_inst = get_unique_inst(copy_y_map)
    new_author_map = {}
    for year in copy_y_map:
        for inst in copy_y_map[year]:
            if inst not in new_author_map:
                new_author_map[inst] = [year]
            else:
                new_author_map[inst].append(year)
    return new_author_map

def map_optimization(openalex_map):
    op_copy = deepcopy(openalex_map)
    new_op_map = {}
    for author in op_copy:
        full_years = get_full_years(op_copy[author])
        years_map = {}
        for year in full_years:
            years_map[year] = get_inst_by_year(op_copy[author], year)
        unique_list = get_unique_inst(years_map)

        s_per_year = score_per_year(years_map, unique_list)
        new_s_per_year = score_addition(score_addition(s_per_year))

        y_map = find_best_match(new_s_per_year, unique_list)

        fill_missing(y_map)
        new_op_map[author] = build_new_author_map(y_map)
    return new_op_map

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def generate_timeline(name, current_inst, email):
    # create dataframe of author
    print("Start Constructing Author's data ... ", end='')
    df,val = construct_data(name, current_inst, email)
    
    print('Done')
    if val == False:
        return None
    # load a pre-trained model
    model, scaler = load_saved_model()

    # filter out some papers predicted as incorrect
    print('Filtering Papers ... ', end='')
    tl_map = get_filtered_timeline_map(df, name, current_inst, model, scaler)
    print('Done')

    # map optimization for better prediction of timeline
    print('Generating a timeline of Author ... ', end='')
    opt_tl_map = map_optimization(tl_map)
    print('Done')

    return json.dumps(opt_tl_map, cls=NpEncoder)