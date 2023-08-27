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

   

It is very important to also include an overall breakdown of your repo's file structure. Let people know what is in each directory and where to look if they need something specific. This will also let users know how your repo needs to structured so that your module can work properly

```
firstname-lastname-repo-name/
    - requirements.txt
    - data/ 
        -- eval_articles.csv
        -- train_articles.csv
        -- Keywords_Springer.csv
    - trained_models/
        -- best.model
    - src/
        -- create_train_data/
            --- query_google.py 
            --- extract_fInclude a brief summary of your module here. For example: this module is responsible for classifying pieces of text using a neural network on top of BERT. 

Note: if this is a second or latter iteration of a module, you may reuse the old iteration's README as a starting point (you should still update it). 

## Setup

List the steps needed to install your module's dependencies: 

1. Include what version of Python (e.g. 3.8.12) and what version of pip (e.g. 21.3.1) you used when running your module. If you do not specify these, other users may run into several problems when trying to install dependencies!

2. Include a requirements.txt containing all of the python dependencies needed at your project's root (see this [link](https://stackoverflow.com/questions/31684375/automatically-create-requirements-txt) for instructions on how to create a requirements.txt). If you used a python virtual environment, use `pip freeze -l > requirements.txt` to generate your requirements.txt file. Make sure to include the below line somewhere in this section to tell users how to use your requirements.txt. 
```
pip install -r requirements.txt 
```

3. Additionally, list any other setup required to run your module such as installing MySQL or downloading data files that you module relies on. 

4. Include instructions on how to run any tests you have written to verify your module is working properly. 

It is very important to also include an overall breakdown of your repo's file structure. Let people know what is in each directory and where to look if they need something specific. This will also let users know how your repo needs to structured so that your module can work properly

```
firstname-lastname-repo-name/
    - requirements.txt
    - data/ 
        -- eval_articles.csv
        -- train_articles.csv
        -- Keywords_Springer.csv
    - trained_models/
        -- best.model
    - src/
        -- create_train_data/
            --- query_google.py 
            --- extract_from_url.py
        -- train.py
        -- classify_articles/
            --- main.py
            --- utils.py
   - tests/
       -- data_preprocess_test.py
       -- eval_pretrained_model_test.py
```

Include text description of all the important files / componenets in your repo. 
* `src/create_train_data/`: fetches and pre-processes articles
* `src/train.py`: trains model from pre-processed data
* `src/classify_articles/`: runs trained model on input data
* `data/eval_artcles.csv`: articles to be classified (each row should include an 'id', and 'title')

## Functional Design (Usage)
Describe all functions / classes that will be available to users of your module. This section should be oriented towards users who want to _apply_ your module! This means that you should **not** include internal functions that won't be useful to the user in this section. You can think of this section as a documentation for the functions of your package. Be sure to also include a short description of what task each function is responsible for if it is not apparent. You only need to provide the outline of what your function will input and output. You do not need to write the pseudo code of the body of the functions. 

* Takes as input a list of strings, each representing a document and outputs confidence scores for each possible class / field in a dictionary
```python
    def classify_docs(docs: list[str]):
        ... 
        return [
            { 'cs': cs_score, 'math': math_score, ..., 'chemistry': chemistry_score },
            ...
        ]
```

* Outputs the weights as a numpy array of shape `(num_classes, num_features)` of the trained neural network 
```python
    def get_nn_weights():
        ...
        return W
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
