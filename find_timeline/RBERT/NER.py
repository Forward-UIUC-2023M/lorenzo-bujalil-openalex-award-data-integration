import os
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import trafilatura
from trafilatura import fetch_url
from trafilatura import extract

base = 'https://www.google.com/search?q='

def load_ner_model():
  tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
  model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
  nlp = pipeline("ner", model=model, tokenizer=tokenizer)
  return nlp

def tag_sentence(sentence, ner_result, author, alternate):
  # find every entity labelled as organization by the NER model
  org_entities = []

  for i, entity in enumerate(ner_result):
    # extract organizations with name of multiple words (n-grams)
    if 'B-ORG' in entity["entity"]: 
      curr_idx = i+1
      while curr_idx < len(ner_result) and  ner_result[curr_idx]['entity'] == 'I-ORG':
        entity['word'] = entity['word'] +' '+ ner_result[curr_idx]['word']
        entity['end'] = ner_result[curr_idx]['end']
        entity['score'] = max(entity['score'], ner_result[curr_idx]['score'])
        curr_idx += 1
      org_entities.append(entity)
  
  # identify author's name within the sentence
  prs_start_char = sentence.index(author)
  prs_end_char = prs_start_char + len(author)

  # quit if no any entity detected as organization
  if len(org_entities) == 0:
    return None

  # choose the organization entity with the highest confidence
  max_org = max(org_entities, key=lambda x:x['score'])

  # tag sentence in approriate order
  if prs_start_char < max_org['start']:
    new_tag_example = sentence[:prs_start_char] + "<e1> " + alternate + " </e1>" + sentence[prs_end_char:max_org['start']] + "<e2> " + max_org['word'] + " </e2>" + sentence[max_org['end']:]
  else:
    new_tag_example = sentence[:max_org['start']] + "<e1> " + max_org["word"] + " </e1>" + sentence[max_org['end']:prs_start_char] + "<e2> " + alternate + " </e2>" + sentence[prs_end_char:]
  
  return new_tag_example

def get_tagged_sentences(author,inst):
  nlp = load_ner_model()

  # consider every possible name
  name_candidates = [author]
  pronouns = ['He', 'She', ' he ', ' she ']
  for candidate in author.split():
    name_candidates.append(candidate)
  for pn in pronouns:
    name_candidates.append(pn)

  # web scraping on google search engine based on the given author and instituion he/she is affiliated with
  document = fetch_url(base + author + " " + inst)
  text = extract(document)
  sentences = text.replace('...','\n').replace('Ph.D.', 'PhD').replace('.', '\n').split('\n')

  # find sentences with relevant information with entities tagged appropriately
  ner_tag_examples =  []
  for sentence in sentences:
    # empty sentence
    if sentence == '':
      continue

    # conduct NER on each non-empty sentence
    ner_result = nlp(sentence)

    # skip if model doesn't detect any entity
    if len(ner_result) == 0:
      continue
    
    # if entities are detected, tag them within a sentence
    new_tag_example = None
    for candidate in name_candidates:
      if candidate in sentence:
        new_tag_example = tag_sentence(sentence, ner_result, candidate, name_candidates[0])
        break
    
    # if the setnece doesn't contain organization/institution entity, disregard it
    if new_tag_example == None:
      continue
    
    ner_tag_examples.append(new_tag_example.strip()+'.')
  return ner_tag_examples

# author's timeline in json format
def find_evidence(author, timeline):
    ner_tag_examples = []
    for inst in timeline:
        ner_tag_examples = ner_tag_examples + get_tagged_sentences(author, inst)
    
    with open('find_timeline/input_ner.txt','w') as f:
        f.writelines("%s\n" % sent for sent in ner_tag_examples)
    f.close()
    os.system("python3 find_timeline/RBERT/predict.py --input_file find_timeline/input_ner.txt --output_file find_timeline/output_ner.txt --model_dir find_timeline/RBERT/model")

    with open('find_timeline/output_ner.txt', 'r') as f:
        result = f.read().split('\n')
    f.close()

    evidence = {}
    for i, example in enumerate(ner_tag_examples):
      org = None
      if result[i] == 'Author-Organization(e1,e2)':
        org = example.split('<e2>')[-1].split('</e2>')[0].strip()
      elif result[i] == 'Author-Organization(e2,e1)':
        org = example.split('<e1>')[-1].split('</e1>')[0].strip()
      
      if org is not None:
        if org in evidence:
          evidence[org].append(example)
        else:
          evidence[org] = [example]

    return evidence