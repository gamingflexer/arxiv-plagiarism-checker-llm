import json
import uuid

def generate_uuid():
    return str(uuid.uuid4().g

def check_id_extis_in_json(file_id):
    with open('file_ids.json', 'r') as f:
        file_ids = json.load(f)
    if file_id in file_ids:
        return True
    else:
        return False

def compare_paper_ids(data, paper_ids):
    existing_dois = {item['doi_no'] for item in data}
    missing_paper_ids = [paper_id for paper_id in paper_ids if paper_id not in existing_dois]
    return missing_paper_ids

def extract_json_from_text(text):
    text = str(text)
    # print("text",text)
    try:
        # Find the JSON part within the text
        start_index = text.find('{')
        end_index = text.rfind('}') + 1
        json_part = text[start_index:end_index]
        json_part = json.loads(json_part.lower())
        print("json",type(json_part))
        print(json_part)
        return json_part.get('data', [])

    except Exception as e:
        print(f"\033[31m Exception occurred while loading JSON: {str(e)} [0m")
        return text