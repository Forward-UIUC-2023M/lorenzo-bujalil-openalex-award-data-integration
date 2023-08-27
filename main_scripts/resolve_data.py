"""
Module: resolve_data.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Main algorithm used to match authors.
1. Preprocess Name and build database index
2. Create author's timeline
3. Use authors name, and authors institution
timeline in order to reduce number of query results
which will be used in the similarity matching.
4. Use a combination of similarity matching algorithms
in order to come up with the name that is the most similar.
Dependencies:
- pandas
- json
- csv
- sys
- requests
- difflib
"""

import sys
sys.path.append('helper_scripts')
sys.path.append('find_timeline')
sys.path.append('find_timeline/timeline/saved_model')
from example import openalex_timeline
from connect_to_postgres import setPostgresConnection,close_conn
import pandas as pd
import requests 
import json
import csv
from difflib import SequenceMatcher

def initialize_names(name):
    """
    Function is used to create a 
    set of new names from one name.
    This is then used for further result reduction.
    e.g. Lorenzo Bujalil -> [Lorenzo B, L Bujalil]

    Parameters:
    name : string
        Name of the author
    
    Returns:
    List
        List of the new names
    """
    names = name.split()
    initialized_names = []

    for i in range(len(names)):
        new_name = names.copy()
        new_name[i] = new_name[i][0]
        initialized_names.append(new_name)

    return initialized_names



def shorten_middle_name(full_name):
    """
    Shortens the middle name of the author

    Parameters:
    full_name : string
        Name of the author
    
    Returns:
    string
        New name of the author with shorter middle name
    """
    name_parts = full_name.split()
    if len(name_parts) > 2:  # We assume a middle name exists
        name_parts[1] = name_parts[1][0]  # Shorten the middle name to the first character
    return ' '.join(name_parts)

def query_index(name_list,award_recipient):
    """
    Main function that applies the matching algorithm.

    Parameters:
    """
    conn = setPostgresConnection()
    cur = conn.cursor()
    # print(name_list[0])
    # print(name_list[-1])
    print(" ".join(name_list))
    
    # shortened_name = shorten_middle_name(" ".join(name_list))
    name  = " ".join(name_list)

    initialized_names = initialize_names(name)
    initialized_names_list = [name]+[' '.join(name) for name in initialized_names]
    # print(initialized_names_list)
    
    inst_list = []
    for i in initialized_names_list:
        author_timeline = openalex_timeline(i,award_recipient,'lbujalil@gmail.com')
        if author_timeline:
            for author in author_timeline:
                for inst in author_timeline[author]:
                    # print(inst)
                    # print('\t'+inst,end='')
                    # high = author_timeline[author][inst][0]
                    # low = author_timeline[author][inst][-1]
                    # print(': '+str(low)+'~'+str(high))
                    inst_list.append(inst)
            break


    print(inst_list)

    inst_or = ' OR '.join([f"i.last_known_institution_name ILIKE '%{ins}%'" for ins in inst_list])

    print(inst_or)


    sql_and_list = []
    for n in initialized_names:
        sql_and_list.append(' AND '.join([f"display_name ILIKE '%{name}%'" for name in n]))

    sql_and_list.append(' AND '.join([f"display_name ILIKE '%{name}%'" for name in name_list]))
    
    sql_and = '(' + ') OR ('.join(sql_and_list) + ')'

    # print(sql_and)

    cur.execute(f'''
                    WITH preprocessed AS (
                        SELECT 
                        display_name,
                        REGEXP_REPLACE(display_name, '[^\w\s]', '', 'g') as cleaned_name, 
                        LOWER(display_name) as lower_name,
                        CASE
                            WHEN POSITION(' ' IN display_name) > 0 THEN LOWER(SPLIT_PART(display_name, ' ', 1))
                            ELSE NULL
                        END as first_name,
                        CASE
                            WHEN POSITION(' ' IN display_name) > 1 THEN LOWER(SPLIT_PART(display_name, ' ', 2))
                            ELSE NULL
                        END as middle_initial,
                        CASE
                            WHEN POSITION(' ' IN display_name) > 0 THEN LOWER(SPLIT_PART(display_name, ' ', 3))
                            ELSE NULL
                        END as last_name,
                        last_known_institution
                        FROM openalex.authors_partition ap JOIN openalex.institution_dimension_2 i ON (i.id=ap.id)
                        WHERE LENGTH(display_name) <= 255
                        AND ap.last_known_institution IS NOT NULL
                        AND ({sql_and})
                        AND ({inst_or})
                    ), scored AS (
                        SELECT 
                        display_name,
                        last_known_institution,
                        -- cleaned_name, 
                        GREATEST(
                            SIMILARITY(lower_name,'{name}'),
                            SIMILARITY(CONCAT(first_name, ' ', middle_initial, ' ', last_name), '{name}')
                        ) as best_similarity
                        -- SIMILARITY(last_known_institution,'{award_recipient}') as institution_sim
                        -- CASE WHEN SOUNDEX(lower_name) = SOUNDEX('{name}') THEN 1 ELSE 0 END as soundex_score,
                        -- CASE WHEN METAPHONE(lower_name,10) = METAPHONE('{name}',10) THEN 1 ELSE 0 END as metaphone_score,
                        -- CASE WHEN DMETAPHONE(lower_name) = DMETAPHONE('{name}') THEN 1 ELSE 0 END as dmetaphone_score,
                        -- LEAST(1.0, LEVENSHTEIN(lower_name,'{name}') / 100.0) AS normalized_levenshtein_score
                        FROM preprocessed
                    )
                        SELECT 
                        display_name,
                        last_known_institution,
                        -- cleaned_name,
                        -- best_similarity,
                        -- soundex_score,
                        -- metaphone_score,
                        -- dmetaphone_score,
                        -- normalized_levenshtein_score,
                        -- (0.9 * best_similarity) + (0.1 * soundex_score) + (0.1 * metaphone_score) + (0.1 * dmetaphone_score) - (0.01 * normalized_levenshtein_score) as total_score
                        best_similarity as total_score
                        FROM scored
                        ORDER BY total_score DESC
                        LIMIT 10;
                ''')


    rows = cur.fetchall()
    conn.commit()


    for row in rows:
        print(row)


    
    close_conn(cur,conn)

    return rows,len(rows)





if __name__ == "__main__":
    df = pd.read_csv("data/conformed/awards/clean_authors_partition.csv")
    authors_mapping = {}
    total_authors = 0
    mapped_authors = 0
    for index, row in df.iterrows():
        
        name = row['names']
        award_recipient = row['insitutions']

        if (name,award_recipient) in authors_mapping:
            continue
        total_authors +=1

        authors_mapping[(name,award_recipient)] = []
        # shortened_name = shorten_middle_name(name)
        name_list = name.split(' ')
        
        res,res_length = query_index(name_list,award_recipient)
        if res_length > 0:
            mapped_authors+=1
        for row in res:
            orcid = row[1]
            matched = row[0]
            institution = row[1]
            base_url = 'https://api.openalex.org/institutions/'
            api_url = base_url + institution.replace("https://openalex.org/","")
            response = requests.get(api_url)


            institution_name = (response.json()).get("display_name")
            if SequenceMatcher(None,award_recipient.lower().strip(),institution_name.lower().strip()).ratio() > 0.85:
                authors_mapping[(name,award_recipient)].append([matched,institution_name])
            
        # print(total_authors)

    # with open('data/mapping/timeline.txt','w') as f:
    #     for author in authors_mapping:
    #         timelines = []
    #         for match in authors_mapping[author]:



    #             base_url = 'https://api.openalex.org/institutions/'
    #             api_url = base_url + match[1].replace("https://openalex.org/","")
    #             response = requests.get(api_url)


    #             name = (response.json()).get("display_name")
    #             print(name,type(name))
    #             print(match[0],type(match[0]))
    #             timeline = openalex_timeline(match[0],name,"lbujalil@gmail.com")
    #             if timeline != None:
    #                 f.write(f'{author} --------> {json.dumps(timeline)}')
    #                 break


    with open('data/mapping/mapped_authors.txt','w') as f:
        for author in authors_mapping:
            f.write(f'{author} ---------> {authors_mapping[author]}\n')

    # find the maximum number of matches for any name
    max_matches = max(len(matches) for matches in authors_mapping.values())

    # create the header row
    header = ['name'] +['recipient']+ [f'match {i+1}' for i in range(max_matches)]

    # write the csv file
    with open('data/mapping/mapping.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for name, matches in authors_mapping.items():
            # if there are fewer matches than max_matches, pad the row with empty strings
            # also, flatten the list of matches
            row = [name] + [str(match) for match in matches] + [''] * (max_matches - len(matches))
            writer.writerow(row)



    print(f"Percent Mapped:{mapped_authors/total_authors * 100}%")
