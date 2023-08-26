import pandas as pd
import pickle
import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras import Input
from keras.layers import Dense
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm
from .openalex import *

def construct_data(author_name, current_inst, email='email@google.com'):
    
    works, author_id = get_valid_works(author_name, current_inst, email)
    if works == None or author_id == None:
        return None,False
    work_data = []
    mem_table = {}
    print(author_id)
    for work in tqdm(works):
        author_inst_names = []
        co_list = [] 

        # get co-authors list and main-author's institutions
        authorships = work.get("authorships")
        for author_info in authorships:
            author = author_info.get("author")
            id = author.get("id")
            if id != author_id:
                co_list.append(id)
            else:
                author_inst = author_info.get("institutions")

        # get only names of main-author's institutions
        for inst in author_inst:
            author_inst_names.append(inst.get("display_name"))

        # count features regarding co-authors
        co_num = 0
        num_same_inst = 0
        num_diff_inst = 0
        same_inst = []
        diff_inst = []

        year = work.get("publication_year")
        for co in co_list:
            if (co is None) or (co == ""):
                continue

            if co in mem_table:
                mem_data = mem_table[co]
                co_num += mem_data[0]
                num_same_inst += mem_data[1]
                num_diff_inst += mem_data[2]
                continue
                
            co_num_each = 0
            num_same_inst_each = 0
            num_diff_inst_each = 0

            co_work_list = get_work_list(co, email)
            
            for co_work in co_work_list:
                for co_author_info in co_work.get("authorships"):
                    author = co_author_info.get("author")
                    if author.get("id") == author_id:
                        co_num_each += 1
                        author_inst_names_other = []
                        for inst in co_author_info.get("institutions"):
                            author_inst_names_other.append(inst.get("display_name"))
                        if len(set(author_inst_names).intersection(set(author_inst_names_other))) == 0:
                            diff_inst.append(co_author_info.get("institutions"))
                            num_diff_inst_each += 1
                        else:
                            same_inst.append(co_author_info.get("institutions"))
                            num_same_inst_each += 1

            mem_table[co] = (co_num_each, num_same_inst_each,num_diff_inst_each)
            co_num += co_num_each
            num_same_inst += num_same_inst_each
            num_diff_inst += num_diff_inst_each
        
        work_data.append([co_num, num_same_inst, num_diff_inst, year, author_inst[0].get("display_name")])
    df = pd.DataFrame(work_data, columns = ['num_co','num_co_same','num_co_diff','year','inst'])
    df['same_ratio'] = df['num_co_same'] / df['num_co']
    df['diff_ratio'] = df['num_co_diff'] / df['num_co']
    df = df.fillna(0)

    return df,True

def load_saved_model():
    scaler = pickle.load(open('find_timeline/timeline/saved_model/scaler.sav', 'rb'))
    model = load_model('find_timeline/timeline/saved_model/my_model')
    return model, scaler

def build_timeline_map(df_papers, current_inst):
    author_name = 'Luis Gravano'
    tl_map = {}
    inst_dict = {}
    for idx in range(len(df_papers)):
        year = df_papers.iloc[idx]['year']
        inst = df_papers.iloc[idx]['inst']
        pred = df_papers.iloc[idx]['pred']
        if pred == 0:
            continue
        if inst not in inst_dict:
            inst_dict[inst] = [year]
        else:
            if year not in inst_dict[inst]:
                inst_dict[inst].append(year)
    for inst in inst_dict:
        inst_dict[inst] = sorted(inst_dict[inst])
    tl_map[author_name] = inst_dict
    return tl_map

def filter_papers(df_papers, current_inst):
    tl_map = {}
    for idx in range(len(df_papers)):
        year = df_papers.iloc[idx]['year']
        inst = df_papers.iloc[idx]['inst']
        pred = df_papers.iloc[idx]['pred']

        update = False
        if inst == current_inst:
            update = True
        elif pred == 1:
            update = True
        
        if update:
            if inst not in tl_map:
                tl_map[inst] = [year]
            else:
                tl_map[inst].append(year)
    
    for inst in tl_map:
        tl_map[inst] = sorted(list(set(tl_map[inst])))

    return tl_map

def get_filtered_timeline_map(df_papers, author_name, current_inst, model, scaler):
    
    X = df_papers.drop(['year','inst'],axis=1)
    X_scaled = scaler.transform(X)
    
    pred = (model.predict(X_scaled)> 0.5).astype(int)
    
    df_papers['pred'] = pred

    filtered_tl_map = filter_papers(df_papers, current_inst)
    return {author_name: filtered_tl_map}