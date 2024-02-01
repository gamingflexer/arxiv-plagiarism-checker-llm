reference_extraction = {
    "inputs": ["refs"],
    "template": """You are a master PDF reader and when given a set of references you
always extract the most important information of the papers. For example, when
you were given the following references:

Lei Jimmy Ba, Jamie Ryan Kiros, and Geoffrey E.
Hinton. 2016. Layer normalization. CoRR ,
abs/1607.06450.
Eyal Ben-David, Nadav Oved, and Roi Reichart.
2021. PADA: A prompt-based autoregressive ap-
proach for adaptation to unseen domains. CoRR ,
abs/2102.12206.
Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie
Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind
Neelakantan, Pranav Shyam, Girish Sastry, Amanda
Askell, Sandhini Agarwal, Ariel Herbert-V oss,
Gretchen Krueger, Tom Henighan, Rewon Child,
Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu,
Clemens Winter, Christopher Hesse, Mark Chen,
Eric Sigler, Mateusz Litwin, Scott Gray, Benjamin
Chess, Jack Clark, Christopher Berner, Sam Mc-
Candlish, Alec Radford, Ilya Sutskever, and Dario
Amodei. 2020. Language models are few-shot learn-
ers. In Advances in Neural Information Processing
Systems 33: Annual Conference on Neural Informa-
tion Processing Systems 2020, NeurIPS 2020, De-
cember 6-12, 2020, virtual .

You extract the following:

Layer normalization | Lei Jimmy Ba, Jamie Ryan Kiros, Geoffrey E. Hinton | 2016
PADA: A prompt-based autoregressive approach for adaptation to unseen domains | Eyal Ben-David, Nadav Oved, Roi Reichart | 2021
Language models are few-shot learners | Tom B. Brown, et al. | 2020

In the References below there are many papers. Extract their titles, authors, and years.

References: {refs}

Title: """
}

prompt_unquiness_para = """
    You are Plagarism researcher, and we have a dataset of all arxiv papers in vector format.
    Given title as {title} and summary as {summary}.
    paragrphs are - {text}
    
    1. Understand the paper
    2. As a Plagarism researcher your job is to find the paragrphs which are unique and are may not present in any other paper.
    3. So we can use those paragrphs to find the unique papers.
    
    So help and return it in a format 'data':['para','para','para']. Only provide the response in a JSON FORMAT. no extra explanation is needed.
    """
    
google_search_titles =  """
    You are Plagarism researcher and you want to find the most relevant papers for your research.
    GIven title as {title} and summary as {summary}.
    
    1. Understand the topics mentioned inside the paper
    2. As a researcher your job is to find the most relevant papers from google search regarding the topics
    3. After understanding the topics amd summary you can to think about the titles which can be searched on google to get the papers which have implmeneted or are the most similar things.
    
    So help me generate the titles to search on google and return it in a format 'data':['title1','title2','title3']. Only provide the response in a JSON FORMAT. no extra explanation is needed.
    """