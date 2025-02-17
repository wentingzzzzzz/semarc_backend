import os
import re
import csv
import json
from typing import List, Tuple
import subprocess
from pathlib import Path

from comment_parser import comment_parser
import nltk
from nltk.stem import WordNetLemmatizer

from settings import CTAG_PATH, USE_NLTK, DEFAULT_STOP_WORD_LIST

import logging


# word processing
def clip_list(src_list,count):
    clip_back=[]
    if len(src_list) > count:
        for i in range(int(len(src_list) / count)):
            clip_a = src_list[count * i:count * (i + 1)]
            clip_back.append(clip_a)
            
        last = src_list[int(len(src_list) / count) * count:]
        if last:
            clip_back.append(last)
    else:  
        clip_back.append(src_list)
    return clip_back

def _words_from_files_batch_splittype(filenames, filepath:str='.', batchsize = 50):
    filenames = [os.path.join(filepath, f) for f in filenames]

    var_words = []
    comment_words = []
    for f in filenames:
        var_words.append([])
        comment_words.append([])
    fns_lists = clip_list(filenames, batchsize)
 
    filename2index = dict(zip(filenames, range(len(filenames))))

    # var_words
    for fns in fns_lists: 
        # print(fns)
        fns = '" "'.join(fns)
        fns = '"' + fns + '"'
        # ctag https://docs.ctags.io/en/latest/man/ctags.1.html?highlight=kinds#kinds
        cmd = f'"{CTAG_PATH}" --kinds-c=+xp --output-format=json --extras=-{{anonymous}} {fns}'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=".")
        try:
            out, err = p.communicate()
            return_code = p.returncode
        except Exception as e:
            print("error: " + e + " ")    
            continue
        if err:
            print(bytes.decode(err))

        out_str = bytes.decode(out)
        for l in out_str.split(os.linesep):
            try:
                j = json.loads(l)
                var_words[filename2index[j["path"]]].append(j["name"])
            except:
                if l != '':
                    print("Wrong record: " + l)

    # comments
    for i, fn in enumerate(filenames): 
        # print(fn)
        if fn.endswith(".c") or fn.endswith(".h"):
            comment_str = 'text/x-c'
        elif fn.endswith(".cpp") or fn.endswith(".hpp"):
            comment_str = 'text/x-c++'
        elif fn.endswith(".java"):
            comment_str = 'text/x-java'
        elif fn.endswith(".py"):
            comment_str = 'text/x-python'
        elif fn.endswith(".rb"):
            comment_str = 'text/x-ruby'
        elif fn.endswith(".go"):
            comment_str = 'text/x-go'
        elif fn.endswith(".js"):
            comment_str = 'text/x-javascript'
        else:
            continue
        try:
            comments = comment_parser.extract_comments(fn, comment_str)
        except Exception as e:
            comments = []
        comment_word = []
        for c in comments:
            t = c.text()
            t = re.sub('([^0-9a-zA-Z])', r' ', t)
            if t.lower().find("copyright") != -1:
                continue
            t = t.split()
            comment_word.extend(t)
        comment_words[i].extend(comment_word)


    return var_words, comment_words

def split_var_words(str):
    str = re.sub('([^0-9a-zA-Z])', r' ', str)
    str = re.sub('([a-z])([A-Z])', r'\1 \2', str)
    str = re.sub(r'([A-Z]{2})([A-Z][a-z])', r'\1 \2', str)
    str = str.lower()
    return str.split()

def _preprocess_words(file_words, stopword_list = None):
    if stopword_list == None:
        try:
            stopword_list = []
            with open(DEFAULT_STOP_WORD_LIST) as fp:
                for line in fp:
                    stopword_list.append(line.strip())
            
        except Exception as e:
            logging.error(e)
            stopword_list = []
    data_words = []
    for i, f in enumerate(file_words):
        tmp = []
        for w in f:
            tmp.extend(split_var_words(w))
        data_words.append(tmp)

    for i in range(len(data_words)):
        data_words[i] = [x for x in data_words[i] 
                         if len(x) > 1 and x not in stopword_list and not x[0].isdigit()]

    if USE_NLTK:
        nltk_keys = []
        for f in data_words:
            nltk_keys.extend(f)
        nltk_keys = list(set(nltk_keys))
        nltk_keys.sort()
        nltk_results = list(lemmatize_all(nltk_keys))
        nltk_map = dict(zip(nltk_keys, nltk_results))

        for i, f in enumerate(data_words):
            for i, w in enumerate(f):
                f[i] = nltk_map[w]

        for i in range(len(data_words)):
            data_words[i] = [x for x in data_words[i] 
                            if len(x) > 1 and x not in stopword_list and not x[0].isdigit()]
    for i in range(len(data_words)):
        data_words[i].sort()
    return data_words

def lemmatize_all(word_list):
    wnl = WordNetLemmatizer()
    try:
        for word, tag in nltk.pos_tag(word_list):
            if tag.startswith('NN'):
                yield wnl.lemmatize(word, pos='n')
            elif tag.startswith('VB'):
                yield wnl.lemmatize(word, pos='v')
            elif tag.startswith('JJ'):
                yield wnl.lemmatize(word, pos='a')
            elif tag.startswith('R'):
                yield wnl.lemmatize(word, pos='r')
            else:
                yield word
    except Exception:
        logging.warning("Missing NLTK resources! Trying to download...")
        nltk.download('averaged_perceptron_tagger')
        nltk.download('wordnet')
        for w in lemmatize_all(word_list):
            yield w


def merge_var_comments(var_words:List[str], comment_words:List[str], var_weight:int=3):
    data_words = comment_words.copy()
    for i in range(len(data_words)):
        for j in range(var_weight):
            data_words[i].extend(var_words[i])
    return data_words

def get_words_from_csv(csv_fn) -> Tuple[List[List[str]], List[List[str]], List[List[str]]]:
    """Get words from a single csv file."""
    filelist = []
    var_words = []
    comment_words = []
    curr_ind = -1
    with open(csv_fn, 'r') as f:
        r_csv = csv.reader(f)
        for line in r_csv:
            fn = line[0]
            if fn not in filelist:
                filelist.append(fn)
                var_words.append([])
                comment_words.append([])
            curr_ind = filelist.index(fn)
            if line[1] == "var":
                var_words[curr_ind].extend(line[2:])
            elif line[1] == "comment":
                comment_words[curr_ind].extend(line[2:]) 
    return filelist, var_words, comment_words

def get_words_from_csv_folder(csv_path, group_by = 'file'):
    """Get words from a folder that contains multiple csv files."""

    csv_fns = os.listdir(csv_path)
    csv_fns = [fn for fn in csv_fns if os.path.getsize(os.path.join(csv_path, fn))]
    prj_names = [Path(f).stem for f in csv_fns]
    
    var_words = []
    comment_words = []

    if group_by == 'file':
        filenames = []
        for csv_fn in csv_fns:
            with open(os.path.join(csv_path, csv_fn), 'r') as f:
                r_csv = csv.reader(f)
                for line in r_csv:
                    fn = Path(csv_fn).stem + '/' + line[0]
                    if fn not in filenames:
                        filenames.append(fn) 
                        var_words.append([])
                        comment_words.append([])
                    if line[1] == "var":
                        var_words[-1].extend(line[2:])
                    else:
                        comment_words[-1].extend(line[2:])
    else:
        filenames = prj_names
        for csv_fn in csv_fns:
            var_words.append([])
            comment_words.append([])
            with open(os.path.join(csv_path, csv_fn), 'r') as f:
                r_csv = csv.reader(f)
                for line in r_csv:
                    if line[1] == "var":
                        var_words[-1].extend(line[2:])
                    else:
                        comment_words[-1].extend(line[2:])

    return filenames, var_words, comment_words

def get_processed_words_from_files(filelist, stopword_files):
    var_words, comment_words = _words_from_files_batch_splittype(filelist)

    stopwords = None
    if stopword_files != None:
        if type(stopword_files) == str:
            stopword_files = [stopword_files]
        stopwords = set()
        for f in stopword_files:
            with open(f, encoding='utf-8', errors='ignore') as fp:
                for line in fp:
                    stopwords.add(line.strip())
            
    var_words = _preprocess_words(var_words, stopwords)
    comment_words = _preprocess_words(comment_words, stopwords)
    
    return var_words, comment_words

def get_processed_words_from_prj_folder(data_path, ext_list:List[str], stopword_files):    
    filelist = []
    for root, dirs, files in os.walk(data_path):
        for file in files:
            ext = os.path.splitext(file)[-1]
            if ext in ext_list: 
                filelist.append(os.path.join(root, file))
    var_words, comment_words = get_processed_words_from_files(filelist, stopword_files)
    return filelist, var_words, comment_words

def save_words_to_csv(filelist:List[str], var_words:List[str], comment_words:List[str], csv_fn:str, makedir = True):
    if makedir:
        csv_path = os.path.dirname(csv_fn)
        if csv_path != '' and not os.path.isdir(csv_path):
            os.makedirs(csv_path)
    with open(csv_fn, 'w', newline="") as f:
        w_csv = csv.writer(f)
        for i in range(len(filelist)):
            w_csv.writerow([filelist[i], 'var'] + var_words[i])
            w_csv.writerow([filelist[i], 'comment'] + comment_words[i])
