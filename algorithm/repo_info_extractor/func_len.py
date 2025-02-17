import os
import logging
import subprocess
import json

from algorithm.cache_manager import cache_result_info, get_cached_info
from utils.filename_convertor import raw_paths_to_unified_paths
from settings import CTAG_PATH, SUPPORTED_FILE_TYPES

logger = logging.getLogger(__name__)
CACHE_SUB_DIR_NAME = 'func_info'

def get_func_info_ctags(src_path, prj_name, prj_id, result_folder, cache_dir):
    src_path = raw_paths_to_unified_paths(src_path, '.')
    result_folder = raw_paths_to_unified_paths(result_folder, '.')

    ctag_inputs = (
        src_path,
        result_folder,
        prj_name,
        prj_id
    )
    ctag_input_files = [CTAG_PATH]


    cached_record = get_cached_info(ctag_inputs, ctag_input_files, CACHE_SUB_DIR_NAME, cache_dir)
    if cached_record != None:
        with open(cached_record['info']['path']) as fp:
            result_dict = json.load(fp)
        return result_dict

    logger.info(f"Getting function info for {prj_name}...")
    
    # run ctags
    # todo java
    cmd = f'"{CTAG_PATH}" --output-format=json --kinds-c=f --fields=NFne --if0=yes -R {src_path}'
    # cmd = f'{CTAG_PATH} --output-format=json --kinds-java=mc --fields=NFne -R {src_path}'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=".")
    try:
        out, err = p.communicate()
        return_code = p.returncode
    except Exception as e:
        raise Exception("error: " + e + " ")
    if err:
        print(bytes.decode(err))
    
    out = bytes.decode(out)    
    result_dict = {}
    for line in out.splitlines():
        d = json.loads(line)
        fn = d['path']
        ext = os.path.splitext(fn)[1]
        if ext.lower() not in SUPPORTED_FILE_TYPES:
            continue
        if fn not in result_dict:
            result_dict[fn] = {}
        if 'end' in d:
            result_dict[fn][d['name']] = {
                'start': d['line'],
                'end': d['end'],
                'len': d['end'] - d['line']
            }
    result_dict = {raw_paths_to_unified_paths(k,src_path):v for k,v in result_dict.items()}

    # save result
    func_file_fullpath = os.path.join(result_folder, f'{prj_name}_func_info.json')
    with open(func_file_fullpath, 'w') as fp:
        json.dump(result_dict, fp)
    logger.info(f"Dumped func info to {result_folder}.") 
    
    # cache results
    func_file_dict = {
        'info': func_file_fullpath
    }
    cache_result_info(ctag_inputs, ctag_input_files, func_file_dict, 'func_info', cache_dir)
        
    return result_dict

def get_func_info(src_path, prj_name, prj_id, result_folder, cache_dir):
    try:
        src_path = raw_paths_to_unified_paths(src_path, '.')
    except:
        pass
    result_folder = raw_paths_to_unified_paths(result_folder, '.')

    ctag_inputs = (
        src_path,
        result_folder,
        prj_name,
        prj_id
    )
    ctag_input_files = [CTAG_PATH]


    cached_record = get_cached_info(ctag_inputs, ctag_input_files, CACHE_SUB_DIR_NAME, cache_dir)
    if cached_record != None:
        with open(cached_record['info']['path']) as fp:
            result_dict = json.load(fp)
        return result_dict

    logger.info(f"Getting function info for {prj_name}...")
    
    # run ctags
    # todo java
    cmd = f'"{CTAG_PATH}" --output-format=json --kinds-c=f --kinds-java=m --fields=NFne --if0=yes -R {src_path}'
    # cmd = f'{CTAG_PATH} --output-format=json --kinds-java=mc --fields=NFne -R {src_path}'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=".")
    try:
        out, err = p.communicate()
        return_code = p.returncode
    except Exception as e:
        raise Exception("error: " + e + " ")
    if err:
        print(bytes.decode(err))
    
    out = bytes.decode(out)    
    result_dict = {}
    for line in out.splitlines():
        d = json.loads(line)
        fn = d['path']
        ext = os.path.splitext(fn)[1]
        if ext.lower() not in SUPPORTED_FILE_TYPES:
            continue
        if fn not in result_dict:
            result_dict[fn] = {}
        if 'end' in d:
            # result_dict[fn][d['name']] = {
            #     'start': d['line'],
            #     'end': d['end'],
            #     'len': d['end'] - d['line']
            # }
            if d['name'] not in result_dict[fn]:
                result_dict[fn][d['name']] = {}
            result_dict[fn][d['name']][d['line']] = d['end'] - d['line']

    result_dict = {raw_paths_to_unified_paths(k,src_path):v for k,v in result_dict.items()}

    # save result
    func_file_fullpath = os.path.join(result_folder, f'{prj_name}_func_info.json')
    with open(func_file_fullpath, 'w') as fp:
        json.dump(result_dict, fp)
    logger.info(f"Dumped func info to {result_folder}.") 
    
    # cache results
    func_file_dict = {
        'info': func_file_fullpath
    }
    cache_result_info(ctag_inputs, ctag_input_files, func_file_dict, 'func_info', cache_dir)
        
    return result_dict
