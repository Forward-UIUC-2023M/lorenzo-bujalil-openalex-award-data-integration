import requests
import math
from fuzzywuzzy import fuzz
page_number = '&page='
paging = '&per-page=200'

def get_work_list(author_id, email):
    polite_pool = '&mailto=' + email
    base_url = 'https://api.openalex.org/works?filter=author.id:'
    api_url = base_url + author_id + \
        page_number + str(1) + paging + polite_pool
    response = requests.get(api_url)
    if response.status_code != 200:
        return []
    count = (response.json()).get("meta").get("count")
    num_pages = math.ceil(int(count) / 200)

    work_list = []

    for i in range(1, num_pages + 1):
        api_url = base_url + author_id + page_number + str(i) + paging + polite_pool
        response = requests.get(api_url)
        
        if (response.json()).get("results") is None:
            continue
        work_list = work_list + (response.json()).get("results")

    return work_list

def find_author(work, author_id):
    authorships = work.get("authorships")
    for author_info in authorships:
        author = author_info.get("author")
        if author.get("id") == author_id:
            inst = author_info.get("institutions")
            return inst, author_info.get("raw_affiliation_string")

def get_most_works_author(author_list):
    author_id = None
    highest_cnt = 0
    for author in author_list:
        works_cnt = author.get("works_count")
        if works_cnt > highest_cnt:
            highest_cnt = works_cnt
            author_id = author.get("id")
    return(author_id)


def get_author_id(author_name, current_inst, email):
    polite_pool = '&mailto=' + email
    base_url = 'https://api.openalex.org/authors?filter=display_name.search:'
    api_url = base_url + author_name +\
        page_number + str(1) + paging + polite_pool
    response = requests.get(api_url)
    count = (response.json()).get("meta").get("count")
    num_pages = math.ceil(int(count) / 200)
    
    
    author_list = []
    for i in range(1, num_pages + 1):
        api_url = base_url + author_name + page_number + str(i) + paging + polite_pool
        response = requests.get(api_url)
        author_list = author_list + (response.json()).get("results")
    # print(author_list)
    if len(author_list) == 0:
        return -1

    author_match = []
    for author in author_list:
        last_inst = author.get('last_known_institution')
        
        if last_inst is not None and fuzz.ratio(last_inst.get("display_name").lower(), current_inst.lower())>50:
            # print(fuzz.ratio(last_inst.get("display_name").lower(), current_inst.lower()))
            author_match.append(author)
    # print(author_match)
    author_valid = []
    for author in author_match:
        if author.get("ids").get("mag") is not None:
            author_valid.append(author)
    if len(author_valid) == 0:
        if len(author_match) == 0:
            # print(get_most_works_author(author_list))
            # return get_most_works_author(author_list)
            return -1
        else:
            return get_most_works_author(author_match)
    elif len(author_valid) == 1:
        return author_valid[0].get("id")
    else:
        return get_most_works_author(author_valid)
    

def get_valid_works(author_name, current_inst, email):
    author_id = get_author_id(author_name, current_inst, email)
    if author_id == -1:
        print(f"The author named {author_name} doesn't exists in Openalex")
        return None,None
    
    work_list = get_work_list(author_id, email)
    valid_works = []
    for work in work_list:
        inst, raw = find_author(work, author_id)
        for v in inst:
            if v.get("id") != None:
                valid_works.append(work)
    return valid_works, author_id