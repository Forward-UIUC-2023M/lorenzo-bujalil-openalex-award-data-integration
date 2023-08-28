# OpenAlex Award Data Integration

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

**Description for all files/functions within file/function definition**
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


Important Files
* `main_scripts/conform_awards.py`: Conform awards is main script that handles the cleaning of the award data specifically to the principal_investigators in this data.
* `main_scripts/conform_authors.py`: Main script used to clean up institution data currently found in
the postgres database. This is done to create a new database
that has the full name written out in the database.
* `main_scripts/load_raw_awards.py`: Main script to call helper scripts to create the database, 
load data, and insert the data into the new database.
* `main_scripts/resolve_data.py`: Main algorithm used to match authors.
```
1. Preprocess Name and build database index
2. Create author's timeline
3. Use authors name, and authors institution
timeline in order to reduce number of query results
which will be used in the similarity matching.
4. Use a combination of similarity matching algorithms
in order to come up with the name that is the most similar.
```
* `find_timeline`: [Detailed Documentation](https://github.com/Forward-UIUC-2022F/jae-doo-timelinegenerator-wiki)

## Functional Design (Usage)

* `main_scripts/resolve_data.py`: Takes as input the name of the author and institution found in the award data. Some name preprocessing is done, and then the timeline of the author is generated. This timeline will be a list of the institutions where the author has published works. Once this list is generated, we can use it to get authors where their last known institution is one of the institutions in the timeline. This greatly reduces the number of authors that we need to search through in order to find the right one. Once we have these authors, we can apply a few more strategies to reduce the number of records. In this function, I implemented a strategy that essentially checks if different variations of the authors name exist in a given record. For example, it will check if the name contains the last name then it will not filter the record. Once a majority of records have been filtered out, we can use a variety of different similarity algorithms and use them in combination to determine the most similar name. Then we can order by this combined score and return the 10 most similar names. From this information we can filter out any unwanted authors, but we now have the most probable match. This function can be used for every single author and then we can determine the best record to match and then can integrate the award dataset.
```python
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
* `main_scripts/conform_awards.py`: Conform awards is main script that handles the cleaning of the award data specifically to the principal_investigators in this data. There are many different patterns that appear in the award data, which requires for complicated and intricate pattern matching to standardize the dataset. When linking records together based on the author's name, it is very important how the name appears in both datasets. The closer we are able to get those names to match, the easier it becomes to match that record. This script is enforcing strict standardization rules on the variety of patterns, in order to have each name in this form: FIRST MI LAST. These rules are clearly defined in helper_scripts/normalize.py and are later called in main_scripts/conform_awards.py. This script is using SQL queries to verify the accurate count of records remaining after cleaning the majority of the authors and normalize.py defines cases where specific strings appear in a pattern then cleans those.
  
```python
# helper_scripts/normalize.py

def clean_author_data(author,clean_authors):
    """
    Main purpose of this function is to clean the author name data by dealing with the variety of cases.

    Parameters:
    author : string
            Raw name in the awards data.
    clean_authors : List
            List of clean authors where the newly cleaned author will be appended to.

    Returns:
    None

    """
    if 'Contact PI / Project Leader: ' in author:
        if 'Other PI or Project Leader(s):' in author:
            divide = author.split('\n')
            primary_author = divide[0]
            primary_author = primary_author.replace("Contact PI / Project Leader: ", "")
            secondary_author = divide[1]
            secondary_author = secondary_author.replace("Other PI or Project Leader(s): ","")
            author_list = (primary_author+' ; '+secondary_author).split(";")
            author_list = [author.strip() for author in author_list]
            author_list = [author.split(",")[1][1:].lower() + " " + author.split(",")[0].lower() for author in author_list]
            
            clean_authors.append(' ; '.join(author_list))
        else:
            updated_author = author.replace("Contact PI / Project Leader: ", "")
            
            updated_author_list = updated_author.split(",")

            if len(updated_author.split(", ")) == 1:
                updated_author = updated_author_list[0].lower()
            else:
                updated_author = updated_author_list[1][1:].lower() + " " + updated_author_list[0].lower()
            updated_author = updated_author.replace(".","")
            updated_author = updated_author.replace(",","")
            updated_author = updated_author.replace('''"''',"")

            clean_authors.append(updated_author.strip())
    ...
```
```python
# main_scripts/conform_awards.py

...

if __name__ == "__main__":
query = '''SELECT principal_investigators FROM awards''' # Pull all of the authors from the sqlite database
conn = establish_conn() # Create a connection with the sqlite database
conn.create_function("REGEXP", 2, regexp) # Create a regex function for complex queries
res = get_data(conn,query,'') # Retrieve data from the sqlite database using the above query
raw_data = res.fetchall() # Retrieve all the data from the result
raw_data_list = [] # Create a list to store the raw data
for data in raw_data: # Load the list with the raw data
    raw_data_list.append(data[0])

print(f'Size of raw data:{len(raw_data)}') # Total amount of raw data 

# Prints the number of authors remaining to clean
print("Remaining authors: ", read_data(conn,'''SELECT count(principal_investigators) 
                                            FROM awards 
                                            WHERE principal_investigators NOT LIKE '%Contact PI / Project Leader: %' 
                                            AND principal_investigators NOT LIKE 'Name:%' 
                                            AND principal_investigators NOT LIKE 'None' 
                                            AND principal_investigators NOT LIKE 'Phone:%' 
                                            AND principal_investigators NOT LIKE '%(Principal Investigator)%'
                                            AND principal_investigators NOT LIKE '%(Former Principal Investigator)%'
                                            AND principal_investigators NOT REGEXP ?''', (r'\b[A-Za-z]+\s+(?<!\n)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\r?\n?',))) 
clean_authors = [] # Create an empty list of authors to store the clean authors
clean_authors_idx = [] # Stores the index of the clean authors
null_values = 0 # Counts the number of null values that appear in the award data
none_authors = 0 # Counts the number of records that have no principal investigators in the award data
phone_numbers = 0 # Counts the number of records that have only a phone number as the principal investigator in the award data

for idx,author in enumerate(raw_data): # Iterate through the raw data and run the cleaning function found in the normalization helper script
    if author[0] != None and author[0].startswith('Phone:'):
        phone_numbers+=1
        continue
    if author[0] == 'None':
        none_authors+=1
        continue
    if author[0] != None:
        clean_authors_count = len(clean_authors)
        clean_author_data(author[0],clean_authors)
        if clean_authors_count == len(clean_authors)-1:
            clean_authors_idx.append(idx)
    else:
        null_values+=1
...
```



## Demo video

Include a link to your demo video, which you upload to our shared Google Drive folder (see the instructions for code submission).

## Algorithmic Design 

Data is initally loaded from the awards.xml file using a lxml parser and a sqlite database, awards.db, is created for this data in order to ensure rapid data access. Now that this data is located in quick access storage, the data needs to be conformed in preparation for the matching process. There are a variety of different patterns that appear within the names of the primary investigators of the raw award data. Enforcing strict rules, FIRST MI LAST, for standardization of names within the award data will ensure for quicker and easier record linkage, specifically due to data filtering and then name matching. Once the names are standardized, they can be moved into the conformed data source. 

Before the data matching process can begin, however, some preprocessing on the institution name needs to be done in order to properly filter out names in the algorithm. In conform authors, a connection to the openalex database is created to be able to retrieve data on the institutions. Currently in our openalex database, the authors last known institution is made up of a url. In order to use the institutions name, we can pull the data and use the openalex api to retrieve the name for each of these institutions. Then we can make a new table that contains the name for all of these institutions. This can further benefit future projects by allowing tables to join and retrieve new information. Conform authors builds this table to then be used when records are being filtered out based on the instutions generated in the timeline. 

Then the resolve data file picks up the conformed data to begin the data matching process. In this process, resolve data iterates through each of the conformed names conducts the following steps: generates author timeline, filters out records using timeline data and display name information, and finally uses a combination of trigram similarity, soundex, double metaphone, metaphone, and levenshtein distance to find the most similar author. Once the most similar author is found then it is placed in a mapping data source which will then be used to generate another dimension table to join the awards table to the authors table. 


![design architecture](https://github.com/Forward-UIUC-2023M/lorenzo-bujalil-openalex-award-data-integration/blob/main/data/research.drawio.png)





## Issues and Future Work

* Author Timeline Generation run time varies between 5-7 minutes, which limits the data matching process
* Investigate hashing names in order to reduce search time
* OpenAlex API low rate limit prevents from rapid, consecutive data retrieval when building institution dimension
* OpenAlex deleted authors remain in our database, which will cause for potentially many matches for one award
* Investigate data deduplication to remove authors / OpenAlex will release new updated database


## Change log

Summer 2023 First Iteration:
* Week of 08/20/2023:
    * Built README to document work completed over the Summer
    * Developed a clear video to explain how algorithm works
    * Wrote report to explain methodologies and research


## References 
include links related to datasets and papers describing any of the methodologies models you used. E.g. 

* https://github.com/Forward-UIUC-2022F/jae-doo-timelinegenerator-wiki
* https://www.freecodecamp.org/news/fuzzy-string-matching-with-postgresql/
* https://towardsdatascience.com/python-tutorial-fuzzy-name-matching-algorithms-7a6f43322cc5
* https://towardsdatascience.com/fuzzy-matching-at-scale-84f2bfd0c536
* https://medium.com/bcggamma/an-ensemble-approach-to-large-scale-fuzzy-name-matching-b3e3fa124e3c
* https://towardsdatascience.com/fuzzy-matching-people-names-6e738d6b8fe
* https://medium.com/compass-true-north/fuzzy-name-matching-dd7593754f19
* https://www.crunchydata.com/blog/fuzzy-name-matching-in-postgresql
