from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


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