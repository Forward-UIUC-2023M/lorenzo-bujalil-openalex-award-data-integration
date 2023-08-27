# Award Data Integration

## Overview

This module is responsible for integrating award data into the openalex schema. We are using the information found in the award data to be able to create relationships to other tables in order to finally build an awards table. The problem to solve in this case is of data consolidation, which is to join disparate datasets and ensure data standardization. We aim to use this module to standardize award data and ensure appropriate record linkage. In order to ensure, the appropriate integration of this data, I implemented a name matching algorithm to link records. In the rest of this documentation, I will explain how the algorithm works, and how to use it.

## Setup

### Prerequisites / Recommendations
Prerequisites: Python 3.9.6 | pip 21.2.4 | git-lfs | Cisco AnyConnect VPN

Recommendations: Use Python Virtual Environment | pgAdmin

#### Installations

Homebrew Installation: Git-LFS
```
brew install git-lfs
```
[Cisco AnyConnect VPN](https://answers.uillinois.edu/illinois/98773)

[pgAdmin](https://www.pgadmin.org/download/)

### Setup/Validation Steps

1. Ensure your system is setup and using the above prerequisites in order to install dependencies
2. Clone repository to load scripts and large files (Ensure that you have the model files for the timeline project)
3. Go to this [Google Drive](https://drive.google.com/drive/folders/1csESJHr97hR1JKJx2fGhnH_6oFrB6lcl?usp=drive_link) and install the xml file and place it within the source directory. This is the raw data file and can be used to load data.
4. Now that you have all the files, run the following two commands inorder to install of the dependencies for this project.
```
pip3 install -r requirements.txt
```
```
pip3 install -r find_timeline/requirements.txt
```
5. Connect to the VPN using your UIUC credentials.
6. Test the setup by running the following scripts. If no errors occur, the setup was a success. (Feel free to cancel resolve_data.py after the first author)

**Make sure to run all scripts within the root of the project**
```
python3 find_timeline/example.py
```
```
python3 main_scripts/resolve_data.py
```
7. You are now setup and can use the module.

## Repository Structure   

It is very important to also include an overall breakdown of your repo's file structure. Let people know what is in each directory and where to look if they need something specific. This will also let users know how your repo needs to structured so that your module can work properly

```
lorenzo-bujalil-openalex-award-data-integration/
    - requirements.txt
    - source/
        -- awards-20230530.xml
        -- awards-20230530.xsd
    - main_scripts/
        -- conform_authors.py
        -- conform_awards.py
        -- load_raw_awards.py
        -- resolve_data.py
    - helper_scripts/
        -- connect_to_postgres.py
        -- normalize.py
        -- query_sqlite_db.py
        -- xml_to_sqlite.py
    - find_timeline/
        -- RBERT/
        -- timeline/
        -- example.py
        -- input_ner.txt
        -- output_ner.txt
        -- requirements.txt
        -- timeline.json
    - data/ 
        -- conformed/
            -- authors/
               -- insert_names.csv
               -- visited_cleaned_names.csv
            -- awards/
               -- institutions/
                   -- raw_data.txt
               -- clean_authors_parition.csv
               -- clean_authors.csv
               -- clean_authors.txt
               -- mapped.csv
               -- raw_data.csv
               -- raw_data.txt
               -- remaining_authors.txt
        -- mapping/
            -- demo.txt
            -- mapped_authors.txt
            -- mapping_null.csv
            -- mapping.csv
            -- timeline.txt
        -- sqlite/
            -- awards.db
        -- testing/
            -- normal.txt
```
**Description for all files/functions within file/function definition**

Important Files
* `main_scripts/conform_awards.py`: Main script to call helper scripts to create the database, 
load data, and insert the data into the new database.
* `main_scripts/conform_authors.py`: Main script used to clean up institution data currently found in
the postgres database. This is done to create a new database
that has the full name written out in the database.
* `main_scripts/load_raw_awards.py`: Main script to call helper scripts to create the database, 
load data, and insert the data into the new database.
* `main_scripts/resolve_data.py`: Main algorithm used to match authors.
1. Preprocess Name and build database index
2. Create author's timeline
3. Use authors name, and authors institution
timeline in order to reduce number of query results
which will be used in the similarity matching.
4. Use a combination of similarity matching algorithms
in order to come up with the name that is the most similar.


## Functional Design (Usage)

* Takes as input the name of the author and institution found in the award data. Some name preprocessing is done, and then the timeline of the author is generated. This timeline will be a list of the institutions where the author has published works. Once this list is generated, we can use it to get authors where their last known institution is one of the institutions in the timeline. This greatly reduces the number of authors that we need to search through in order to find the right one. Once we have these authors, we can apply a few more strategies to reduce the number of records. In this function, I implemented a strategy that essentially checks if different variations of the authors name exist in a given record. For example, it will check if the name contains the last name then it will not filter the record. Once a majority of records have been filtered out, we can use a variety of different similarity algorithms and use them in combination to determine the most similar name. Then we can order by this combined score and return the 10 most similar names. From this information we can filter out any unwanted authors, but we now have the most probable match. This function can be used for every single author and then we can determine the best record to match and then can integrate the award dataset.
```python Fo
    def query_index(name_list,award_recipient):
        ...
        inst_list = []
        for i in initialized_names_list:
            author_timeline = openalex_timeline(i,award_recipient,'lbujalil@gmail.com')
            if author_timeline:
                for author in author_timeline:
                    for inst in author_timeline[author]:
                        inst_list.append(inst)
                break
        ...
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
                            cleaned_name, 
                            GREATEST(
                                SIMILARITY(lower_name,'{name}'),
                                SIMILARITY(CONCAT(first_name, ' ', middle_initial, ' ', last_name), '{name}')
                            ) as best_similarity
                            SIMILARITY(last_known_institution,'{award_recipient}') as institution_sim
                            CASE WHEN SOUNDEX(lower_name) = SOUNDEX('{name}') THEN 1 ELSE 0 END as soundex_score,
                            CASE WHEN METAPHONE(lower_name,10) = METAPHONE('{name}',10) THEN 1 ELSE 0 END as metaphone_score,
                            CASE WHEN DMETAPHONE(lower_name) = DMETAPHONE('{name}') THEN 1 ELSE 0 END as dmetaphone_score,
                            LEAST(1.0, LEVENSHTEIN(lower_name,'{name}') / 100.0) AS normalized_levenshtein_score
                            FROM preprocessed
                        )
                            SELECT 
                            display_name,
                            last_known_institution,
                            cleaned_name,
                            best_similarity,
                            soundex_score,
                            metaphone_score,
                            dmetaphone_score,
                            normalized_levenshtein_score,
                            (0.9 * best_similarity) + (0.1 * soundex_score) + (0.1 * metaphone_score) + (0.1 * dmetaphone_score) - (0.01 * normalized_levenshtein_score) as total_score
                            best_similarity as total_score
                            FROM scored
                            ORDER BY total_score DESC
                            LIMIT 10;
                    ''')
        ...
        return rows,len(rows)
```

## Demo video

Include a link to your demo video, which you upload to our shared Google Drive folder (see the instructions for code submission).

## Algorithmic Design 
This section should contain a detailed description of all different components and models that you will be using to achieve your task as well as a diagram. Here is a very basic example of what you should include:

We generate vector representations for each document using BERT, we then train a simple, single-layer fully connected neural network using the documents and labels from the training set.

First, we select a set of labeled text documents `d_1, d_2, …, d_N` from the arxiv dataset available on Kaggle. The documents are randomly partitioned into two sets for training and testing. We use the BERT language model's output as the input to the neural network. Only the weights of the neural network are modified during training. 

After training, we run the trained model to classify the test documents into one of the classes in C. Below is a picture of the architecture of the module. The diagram below was constructed using draw.io 


![design architecture](https://github.com/Forward-UIUC-2021F/guidelines/blob/main/template_diagrams/sample-design.png)





## Issues and Future Work

In this section, please list all know issues, limitations, and possible areas for future improvement. For example:

* High false negative rate for document classier. 
* Over 10 min run time for one page text.
* Replace linear text search with a more efficient text indexing library (such as whoosh)
* Include an extra label of "no class" if all confidence scores low. 


## Change log

Use this section to list the _major_ changes made to the module if this is not the first iteration of the module. Include an entry for each semester and name of person working on the module. For example 

Fall 2021 (Student 1)
* Week of 04/11/2022: added two new functions responsible for ...
* Week of 03/14/2022: fixed bug and added support for ...

Spring 2021 (Student 2)
...

Fall 2020 (Student 3)
...


## References 
include links related to datasets and papers describing any of the methodologies models you used. E.g. 

* Dataset: https://www.kaggle.com/Cornell-University/arxiv 
* BERT paper: Jacob Devlin, Ming-Wei Chang, Kenton Lee, & Kristina Toutanova. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.
