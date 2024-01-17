def compare_paper_ids(data, paper_ids):
    existing_dois = {item['doi_no'] for item in data}
    missing_paper_ids = [paper_id for paper_id in paper_ids if paper_id not in existing_dois]
    return missing_paper_ids