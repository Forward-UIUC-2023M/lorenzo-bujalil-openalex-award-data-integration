from timeline import generate_timeline
from RBERT import find_evidence
import json

def openalex_timeline(name, current_inst, email):
    timeline = generate_timeline(name, current_inst, email)
    if timeline == None:
        return None
    author_timeline = json.loads(timeline)
    return author_timeline

def read_timeline(file_name):
    with open(file_name, 'r') as f:
        timeline = json.load(f)
    f.close()
    return timeline


def main():
    names = ["martin d burke"]
    current_inst = "UNIVERSITY OF ILLINOIS AT URBANA-CHAMPAIGN"
    email = "lbujalil@gmail.com"
    for name in names:
            
        timeline = generate_timeline(name, current_inst, email)
        if timeline == None:
            continue
        author_timeline = json.loads(timeline)
        
        with open('find_timeline/timeline.json', 'w') as f:
            f.write(json.dumps(author_timeline))
        f.close()
        author_timeline = read_timeline("find_timeline/timeline.json")
        evidence = find_evidence(name, author_timeline)
        new_inst = set(evidence.keys())

        for author in author_timeline:
            print(author)
            for inst in author_timeline[author]:
                print('\t'+inst,end='')
                high = author_timeline[author][inst][0]
                low = author_timeline[author][inst][-1]
                print(': '+str(low)+'~'+str(high))
                
                if inst in evidence:
                    new_inst.remove(inst)
                    print('\t\tfound evidence:')
                    for sentence in evidence[inst]:
                        print('\t\t\t'+sentence)
        
        print('\tNew Institutions found by Web scraping:')
        for inst in list(new_inst):
            print('\t\t'+inst)
            for sentence in evidence[inst]:
                print('\t\t\t'+sentence)

if __name__ == "__main__":
    main()
    