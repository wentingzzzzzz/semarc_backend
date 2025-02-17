import os
import json
import hashlib
import logging

from settings import DISABLE_CACHE


logger = logging.getLogger(__name__)

WORD_DATA_DIR = 'word_data'
WORD_DATA_INFO_JSON = 'csv_info.json'
LDA_MODEL_DIR = 'lda_model'
DEPENDS_DIR = 'depends'

USE_FILE_STATE_INSTEAD = True

def hash_file(f, block_size = 256):
    if USE_FILE_STATE_INSTEAD:
        return hash_file_state(f)
    else:
        sha = hashlib.md5()
        with open(f, 'rb') as fp:
            buf = fp.read(block_size)
            while buf:
                sha.update(buf)
                buf = fp.read(block_size)
                
        return sha.hexdigest()

def hash_file_state(f):
    stat = os.stat(f)
    return hashlib.sha256(str((stat.st_mtime_ns,stat.st_size)).encode('utf-8')).hexdigest()

def _get_hash_from_inputs(inputs, input_files):
    file_shas = []
    for f in input_files:
        file_shas.append(hash_file(f))
    sha_inputs = (
        inputs,
        file_shas
    )
    hash_result = hashlib.sha256(str(sha_inputs).encode("utf-8")).hexdigest()
    return hash_result

def get_prj_id(prj_path, exts = None):
    """ Determine the project id by CRC file modified time """
    def scan(dir, exts):
        crc = 0
        for fs_obj in os.scandir(dir):
            if fs_obj.is_dir():
                crc ^= scan(fs_obj, exts)
            elif fs_obj.is_file():
                if exts != None and os.path.splitext(fs_obj.name)[-1].lower() not in exts:
                    continue
                # prevent all files are modified at the same time
                crc ^= (fs_obj.stat().st_mtime_ns + fs_obj.stat().st_size)
        return crc

    exts_lower = set()
    for ext in exts:
        exts_lower.add(ext.lower())
    
    time_crc = scan(prj_path, exts_lower)
    if time_crc == 0:
        raise Exception(f"Empty project {prj_path}, no files with exts {exts} found!")
    prj_id = hashlib.sha256(str(time_crc).encode()).hexdigest()
    return prj_id


def get_cached_csv_file(inputs, input_files, cache_dir):
    if DISABLE_CACHE:
        return None
    """ Try to find cached processed word data. """
    word_id = _get_hash_from_inputs(inputs, input_files)
    json_fn = os.path.join(cache_dir, WORD_DATA_DIR, word_id, WORD_DATA_INFO_JSON)
    if os.path.exists(json_fn):
        with open(json_fn, encoding='utf-8') as fp:
            csv_info = json.load(fp)
        csv_path = csv_info['csv_fn']
        if os.path.exists(csv_path):
            hash_now = hash_file(csv_path)
            if hash_now == csv_info['hash']:
                return csv_path
    return None    
    
def cache_csv_info(inputs, input_files, csv_fn, cache_dir):
    if DISABLE_CACHE:
        return None
    word_id = _get_hash_from_inputs(inputs, input_files)
    csv_hash = hash_file(csv_fn)
    json_data = {
        'csv_fn': csv_fn,
        'hash': csv_hash
    }
    os.makedirs(os.path.join(cache_dir, WORD_DATA_DIR, word_id), exist_ok=True)
    with open(os.path.join(cache_dir, WORD_DATA_DIR, word_id, WORD_DATA_INFO_JSON), 'w', encoding='utf-8') as fp:
        json.dump(json_data, fp)
    logger.info(f'Cached word csv info to {os.path.join(cache_dir, WORD_DATA_DIR, word_id, WORD_DATA_INFO_JSON)}')
    
def get_cached_lda_model_path(lda_inputs, cache_dir):
    if DISABLE_CACHE:
        return None
    hash_id = _get_hash_from_inputs(lda_inputs, [])
    lda_dir = os.path.join(cache_dir, LDA_MODEL_DIR, hash_id)
    if os.path.exists(lda_dir):
        return os.path.join(lda_dir, 'lda_model')
    else:
        return None

def cache_lda_model(lda_inputs, lda_model, cache_dir):
    if DISABLE_CACHE:
        return None
    hash_id = _get_hash_from_inputs(lda_inputs, [])
    lda_dir = os.path.join(cache_dir, LDA_MODEL_DIR, hash_id)
    os.makedirs(lda_dir, exist_ok=True)
    lda_model.save(os.path.join(lda_dir, 'lda_model'))
    logger.info(f'Cached lda model to {lda_dir}')

def get_cached_depends_info(inputs, cache_dir):
    if DISABLE_CACHE:
        return None
    """ Try to find cached depends data. """
    hash_id = _get_hash_from_inputs(inputs, [])
    json_fn = os.path.join(cache_dir, DEPENDS_DIR, hash_id, 'cached_info.json')
    if not os.path.exists(json_fn):
        return None

    with open(json_fn, encoding='utf-8') as fp:
        cached_info = json.load(fp)
    for record_name, record_info in cached_info.items():
        path = record_info['path']
        if not os.path.exists(path):
                return None
        hash_now = hash_file(path)
        file_hash = record_info['hash']
        if hash_now != file_hash:
            return None
    return cached_info


def cache_depends_info(inputs, record_name2path, cache_dir):
    hash_id = _get_hash_from_inputs(inputs, [])
    json_data = {}
    for record_name, path in record_name2path.items():
        file_hash = hash_file(path)
        json_data[record_name] = {
            'path': path,
            'hash': file_hash
        }
    os.makedirs(os.path.join(cache_dir, DEPENDS_DIR, hash_id), exist_ok=True)
    with open(os.path.join(cache_dir, DEPENDS_DIR, hash_id, 'cached_info.json'), 'w', encoding='utf-8') as fp:
        json.dump(json_data, fp)
    if not DISABLE_CACHE:
        logger.info(f'Cached depends info to {os.path.join(cache_dir, DEPENDS_DIR, hash_id, "cached_info.json")}')




def cache_result_info(inputs, input_files, record_name2path, sub_dir, cache_dir):
    if input_files == None:
        input_files = []
    hash_id = _get_hash_from_inputs(inputs, input_files)
    json_data = {}
    for record_name, path in record_name2path.items():
        file_hash = hash_file(path)
        json_data[record_name] = {
            'path': path,
            'hash': file_hash
        }
    os.makedirs(os.path.join(cache_dir, sub_dir), exist_ok=True)
    with open(os.path.join(cache_dir, sub_dir, f'{hash_id}.json'), 'w', encoding='utf-8') as fp:
        json.dump(json_data, fp)
    pass

def get_cached_info(inputs, input_files, sub_dir, cache_dir, check_hash = True):
    """ Try to find cached data. """
    if input_files == None:
        input_files = []
    hash_id = _get_hash_from_inputs(inputs, input_files)
    json_fn = os.path.join(cache_dir, sub_dir, f'{hash_id}.json')

    if not os.path.exists(json_fn):
        return None

    with open(json_fn, encoding='utf-8') as fp:
        cached_info = json.load(fp)
    if not check_hash:
        return cached_info
    else:
        for record_name, record_info in cached_info.items():
            path = record_info['path']
            if not os.path.exists(path):
                    return None
            hash_now = hash_file(path)
            file_hash = record_info['hash']
            if hash_now != file_hash:
                return None
        return cached_info


if __name__ == "__main__":
    pass