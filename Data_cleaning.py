import pandas as pd
import os, re
import string
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk import word_tokenize

with open('junk_words.txt') as f:
    junk = f.read().lower().split('\n')
print(junk)

def text_clean(text):
    if not (pd.isnull(text)):
        if not type(text)=='str':
            text = str(text)
        text = re.sub(r'(https?:\/\/.*[\n]*)|(\\\\.*[\n]*)', ' ', text)
        for j in junk:
            text = text.lower().replace(j,'')
# =============================================================================
#         words = word_tokenize(text)
#         text = ' '.join([word for word in words if not word.startswith('\\')])
#         text = ' '.join([word for word in words if not word.startswith('//')])
# =============================================================================
        bad_chars = list(string.punctuation)+['\\n','Ã','¶']
        for char in bad_chars:
            text = text.replace(char, " ")
      #  text = re.sub('\d+', "", text)
        text = re.sub("[^A-Za-z ]"," ",str(text).lower())
        text = re.sub("  "," ",str(text).lower())
        return text
    else:
        print('## Blank Text ##')
        return " "

def stop_and_stem(text, stem=False, stemmer=PorterStemmer()):
    if not (pd.isnull(text)):
        stoplist = [stop for stop in stopwords.words('english') if not stop in ['not','no']]
        if stem:
            text_stemmed = [stemmer.stem(word) for word in word_tokenize(text) if word not in stoplist and len(word)>=2 and len(word)<=18]
        else:
            text_stemmed = [word for word in word_tokenize(text) if word not in stoplist and len(word)>=2 and len(word)<=18]
        text = ' '.join(text_stemmed)
        return text
    else:
        return " "

# =============================================================================
# text = """a) Description: Comments are not displayed for every scenario when maintenance activity fails.
# 
# - Expected behavior: Comments should be displayed when a maintenance activity fails.
# - Observed behavior: Comments are not displayed when a maintenance activity fails.
# 
# - Steps to reproduce: 
# 1. Perform an IM or pooler maintenance activity when instrument is not in standby.
# 2. Perform archive maintenance when archive settings are not available.
# 3. Perform Sample pipettor tightness check and Maintenance teach when teach tool is not present.
# 
# Problem report path: \\tromsgfp221\4_VerificationValidation_Share2\9_Issues\01_Large_Attachments_On_Share_2\844745
# 
# b) Related requirement, id and text: [IGTRQ66120] The Instrument Gateway shall provide a printable execution history in the maintenance activity 
# detail view which shows the following information for a selected maintenance activity for the last 90 days- - Execution date and time, - Outcome"""   
# print(stop_and_stem(text_clean(text)))
# =============================================================================
