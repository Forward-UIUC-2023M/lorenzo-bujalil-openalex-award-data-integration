# jae-doo-timelinegenerator-wiki

## Overview
This module incldues a timeline generator solely based on the Openalex database and the advanced version integrated with RBERT and NER model on top of the base Openalex timeline generator. For more information regarding Openalex, check out this [Openalex documentation](https://docs.openalex.org/). 

## Setup

List the steps needed to install your module's dependencies: 

1. Python 3.8.15 and pip 22.3.1

2. Install dependencies with the requirements.txt file. Notice that only MacOS users should install tensorflow-macos.
```
pip install -r requirements.txt 
```

3. Run the following line to verify if the module is working properly
```
python example.py
```

It is very important to also include an overall breakdown of your repo's file structure. Let people know what is in each directory and where to look if they need something specific. This will also let users know how your repo needs to structured so that your module can work properly

```
jae-doo-timelinegenerator-wiki/
    - requirements.txt
    - example.py
    - input_ner.txt
    - output_ner.txt
    - RBERT/ 
        -- data/
            --- label.txt
            --- train.tsv
            --- test.tsb
        -- model/
            --- pytorch_model.bin
            --- training_args.bin
        -- predict.py
        -- NER.py
    - timeline/
        -- data/
            --- test.csv
        -- saved_model/
            --- my_model/
                ---- keras_metadata.pb
                ---- saved_model.pb
        -- openalex.py
        -- timeline.py
```

Include text description of all the important files / componenets in your repo. 
* `RBERT/NER.py`: integrates NER model wit the RBERT model
* `RBERT.predict.py`: makes the prediction with given input sentences
* `RBERT/train.csv`: tagged senteces to train the RBERT model (a tagged sentence and corresponding label for each row)
* `timeline/timeline.py`: generates base Openalex timeline


## Functional Design (Usage)
* Takes the name of the author, the current institution with which the author is affiliated, and the email address of user for Openalex API call as inputs and outputs the timeline of the author in json format
```python
    def generate_timeline(name: str, current_inst: str, email: str):
        # cosntructing dataframe based on Openalex works data
        df = construct_data(name, current_inst, email)
        ...

        # load pre-trained model for papers classification
        model, scaler = load_saved_model()
        ...
        
        # filter out some papers predicted as incorrect
        timeline_map = get_filtered_timeline_map(df, name, current_inst, model, scaler)

        # map optimization for better prediction of timeline
        optimized_timeline_map = map_optimization(timeline_map)
        ...
        
        # return the timeline in json format
        return json.dumps(optimized_timeline_map, cls=NpEncoder)
```

* Takes the name of the author and the timeline of the author as inputs and outputs the found evidence of affiliations as a dictionary.
```python
    def find_evidence(author, timeline):
        # 
        ner_tag_examples = []
        for inst in timeline:
          ner_tag_examples = ner_tag_examples + get_tagged_sentences(author, inst) 
        ...
        
        # Write ner_tag_examples in input_file

        os.system("python RBERT/predict.py --input_file input_ner.txt --output_file output_ner.txt --model_dir RBERT/model")

        # Read results(relationships) from output_file
        ...

        evidence = {}
        # put the ner_tag_examples with Author-Organiztion relationships in evidence with (institution, sentences) as key-value pair.
        ...

        return evidence
```

## Demo video

#### generate_timeline Demo


https://user-images.githubusercontent.com/42979408/210810448-7177773e-fc25-487d-8298-3228abc4a0ba.mp4


#### find_evidence Demo


https://user-images.githubusercontent.com/42979408/210810464-e72a2956-66eb-4a8f-92b9-b2ee7be4a823.mp4


## Algorithmic Design 

#### Base Openalex timeline
Due to possible incorrect information in Openalex database, the generator goes through two procedures before making a prediction:
1. Filters out the papers with wrong data by pre-built Neural Network model
2. Timeline optimization by scoring method

In order to classify the wrong papers, we utilizes the knowledge of co-authorship of each paper to measure the confidence. Then, we construct the dataset based on this informaiton and feed it into the classification model for filtering process.

The optimization is performed to generate a clean and consistent timeline for each author. We measure the confidence of each institution for each year based on the observations from surrounding years, and select the instituion with the highest score(confidence). From several trials, we could observe that scoring method plays significant role on ruling out the wrong data, which has low confidence in this case, collected from Openalex as well.


#### Web Scraping 
In order to compensate the lack of information of Openalex, we suggests the evidence of several affiliations found by web scraping on google search engine. We takes advantage of the **Trafilatura** module as a web scraping tool as it automatically outputs only relevant sentences(information) from raw html response.


#### RBERT & NER
Given the sentences scraped by Trafilatura, we select the sentences including the instiutions with which the author is possibly affiliated. Then, we tag the sentences as follows: 
1. Detect the Person and Organization entities by BERT-base-NER model.
2. Wrap around the entity that comes first in the sentence with &lt;e1&gt; and &lt;/e1&gt;
3. Similarly, tag the second entity with &lt;e2&gt; and &lt;/e2&gt;

The reason we are making use of NER model is that it enables us to discover the new institutions that weren't inlcuded in the original Openalex timeline, allowing to extract the knowledge beyond the scope of Openalex.

Now, the sentences are tagged appropriately to be passed to the RBERT model. The RBERT model makes the predictions on the relationships between two entities. Since we are interested in the author's affiliations, we only consider Author-Organization relationship. We save the evidence in a form of dictionary with institution and tagged sentences as key-value pair. Finally, we output the author's timeline along with relevant evidence. 


#### Evaluation
The Timeline generator is evaluated on 10 randomly selected authors. Each page of the report corresponds to each author, and it's formatted as ground truth on the tope of the page with model prediction and personal evaluation below it. 


## Issues and Future Work

* Openalex API calls sometimes fail
* Expensive Openalex timeline generation runtime (Over 3 mins for author with 100 works)
* Add more training examples for RBERT (added 100 customized examples so far)


## Change log

Fall 2022 (Jae Doo)
* Week of 12/31/2022: created the module
* Week of 2/25/2023: added Evaluation report


## References 

* RBERT paper: [Enriching Pre-trained Language Model with Entity Information for Relation Classification (Wu et al. 2019)](https://arxiv.org/pdf/1905.08284.pdf)
* RBERT code: https://github.com/monologg/R-BERT
* BERT-base-NER: https://huggingface.co/dslim/bert-base-NER
* OpenAlex GUI: https://explore.openalex.org/
