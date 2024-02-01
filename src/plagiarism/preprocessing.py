from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import time
from operator import itemgetter
import fitz
import re

def fonts(doc, granularity=False):
    """Extracts fonts and their usage in PDF documents.

    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool

    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = "{0}_{1}_{2}_{3}".format(s['size'], s['flags'], s['font'], s['color'])
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                        else:
                            identifier = "{0}".format(s['size'])
                            styles[identifier] = {'size': s['size'], 'font': s['font']}

                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage

    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")

    return font_counts, styles


def font_tags(font_counts, styles):
    """Returns dictionary with font sizes as keys and tags as value.

    :param font_counts: (font_size, count) for all fonts occuring in document
    :type font_counts: list
    :param styles: all styles found in the document
    :type styles: dict

    :rtype: dict
    :return: all element tags based on font-sizes
    """
    p_style = styles[font_counts[0][0]]  # get style for most used font by count (paragraph)
    p_size = p_style['size']  # get the paragraph's size

    # sorting the font sizes high to low, so that we can append the right integer to each tag
    font_sizes = []
    for (font_size, count) in font_counts:
        font_sizes.append(float(font_size))
    font_sizes.sort(reverse=True)

    # aggregating the tags for each font size
    idx = 0
    size_tag = {}
    for size in font_sizes:
        idx += 1
        if size == p_size:
            idx = 0
            size_tag[size] = '<p>'
        if size > p_size:
            size_tag[size] = '<h{0}>'.format(idx)
        elif size < p_size:
            size_tag[size] = '<s{0}>'.format(idx)

    return size_tag


def headers_para(doc, size_tag):
    """Scrapes headers & paragraphs from PDF and return texts with element tags.

    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param size_tag: textual element tags for each size
    :type size_tag: dict

    :rtype: list
    :return: texts with pre-prended element tags
    """
    paragraphs = []  # list with paragraphs
    first = True  # boolean operator for first header
    previous_s = {}  # previous span

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # this block contains text

                # REMEMBER: multiple fonts and sizes are possible IN one block

                block_string = ""  # text found in block
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if s['text'].strip():  # removing whitespaces:
                            if first:
                                previous_s = s
                                first = False
                                block_string = s['text'] if size_tag[s['size']] == '<p>' else ''
                            else:
                                if s['size'] == previous_s['size']:
                                    if block_string:  # in the same block, so concatenate strings
                                        block_string += " " + s['text']
                                else:
                                    if block_string:  # new block has started, so append the paragraph
                                        paragraphs.append(block_string)
                                    block_string = s['text'] if size_tag[s['size']] == '<p>' else ''

                                previous_s = s

                if block_string:  # append the last paragraph in the block
                    if len(block_string) > 80:
                        # print(len(block_string), block_string,'\n')
                        paragraphs.append(block_string)

    return paragraphs

def get_pdf_info(document_path):
    docs = fitz.open(document_path)
    only_text = ""
    for page in docs:
        only_text += page.get_text() + " "
    font_counts, styles = fonts(docs, granularity=False)
    size_tag = font_tags(font_counts, styles)
    elements = headers_para(docs, size_tag)
    paragraphs = []
    for element in elements:
        if len(element) > 100: 
            paragraphs.append(element.lower())
    pattern = r'\d+(\.\d+)?\n'
    cleaned_text = re.sub(pattern, '', only_text)
    return cleaned_text.lower(),paragraphs


def remove_numbers(words_list: list) -> list:
    """Remove all numbers from a list of strings."""
    return [word for word in words_list if not word.isdigit()]

def remove_stop_words(words_list: list) -> list:
    """Remove stop words from a list of strings."""
    stop_words = set(stopwords.words('english'))
    return [word for word in words_list if word.lower() not in stop_words]

def lemmatize(words_list: list) -> list:
    """Lemmatize a list of strings."""
    lemmatizer = WordNetLemmatizer()
    return [lemmatizer.lemmatize(word) for word in words_list]