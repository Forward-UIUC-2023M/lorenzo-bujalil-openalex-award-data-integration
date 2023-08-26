"""
Module: normalize.py
Author: Lorenzo Bujalil Silva
Date: 2023-08-26

Description:
Helper script with the main function to deal with various cases of unnormalized author names in the award database.

Dependencies:
- re
"""

import re

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

    elif author.startswith('Name:'):

        author_name_line = author.split("\n")[0]
        
        updated_author = author_name_line.split(":")[1]

        if updated_author.startswith(' '):
            updated_author = updated_author[1:]

        updated_author = updated_author.replace("Dr.","")
        updated_author = updated_author.replace("Dr ","")

        updated_author = updated_author.replace("Jr.","")
        if updated_author.endswith("Jr"):
            updated_author = updated_author.replace("Jr","")


        updated_author = updated_author.replace("Ph.d.","")
        updated_author = updated_author.replace("Phd","")
        updated_author = updated_author.replace("Ph.d","")
        updated_author = updated_author.replace("Mr.","")
        updated_author = updated_author.replace("Mr ","")
        updated_author = updated_author.replace("D.sc","")
        updated_author = updated_author.replace("Ph D","")
        updated_author = updated_author.replace("Pe","")
        updated_author = updated_author.replace("M.d.","")
        updated_author = updated_author.replace("Dds","")
        updated_author = updated_author.replace("Ph","")
        updated_author = updated_author.replace("P.E.","")
        updated_author = updated_author.replace("Ph.D.","")
        updated_author = updated_author.replace("Dsc","")
        updated_author = updated_author.replace(", P","")
        updated_author = updated_author.replace(".D.","")
        updated_author = updated_author.replace("MR. ","")
        updated_author = updated_author.replace("DR. ","")
        updated_author = updated_author.replace('''"''',"")
        
        updated_author_temp_list = updated_author.split(', ')
        updated_author_temp_list.reverse()
        updated_author = ' '.join(updated_author_temp_list)
        # updated_author = updated_author.replace(".","")
        # updated_author = updated_author.replace(",","")
        # updated_author = updated_author.lower()
        # print(updated_author.strip().lower())
        with open('data/testing/normal.txt','a') as f:
            f.write(updated_author.strip() + '\n')

        updated_author = updated_author.lower()
        clean_authors.append(updated_author.strip())

    elif '(Principal Investigator)' in author:
        divide = author.split('\n')
        
        res = ''
        pattern_plus = r'[\w\.-]+\+?@[\w\.-]+'
        match_plus = re.search(pattern_plus,divide[0])
        if match_plus:
            res+=divide[0].replace(match_plus.group(),"").replace("(Principal Investigator)","")
            res+='; '
        if len(divide) > 2:
            for i in range(1,len(divide)):
                # print(divide[i],end=' -> ')
                if divide[0]==divide[i]:
                    continue
                co_clean_author = divide[i].replace("(Co-Principal Investigator)","")
                co_clean_author = co_clean_author.replace("(Former Principal Investigator)","")
                co_clean_author = co_clean_author.replace("(Former Co-Principal Investigator)","")
                res += co_clean_author
                res+=' ; '
        elif len(divide) > 1:
            
            clean_author = divide[1].replace("(Co-Principal Investigator)","")
            clean_author_list = clean_author.split(",")
            
            for au in clean_author_list:
                res+= au
                res+=' ; '
        # print(res)
        clean_authors.append(res)
    elif '(Former Principal Investigator)' in author:
        # print(author)
        res=''
        temp_authors =author.replace("(Former Principal Investigator)","").replace("(Former Co-Principal Investigator)","").replace("(Co-Principal Investigator)","")
        temp_authors = temp_authors.split("\n")
        for auth in temp_authors:
            res+=auth
            res+=' ; '
        # print(res)
        clean_authors.append(res)

    elif re.findall(r'\b[A-Za-z]+\s+(?<!\n)[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\r?\n?', author):
        temp = author
        match = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\r?\n?', author)
        temp = temp.replace(match[0],"")
        
        clean_authors.append(temp)
        # print(author)
        
