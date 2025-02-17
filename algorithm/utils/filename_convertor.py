""" 
Filenames have 3 formats in this project:
1) raw path: the path that you may access the file directly;
2) unified path: the relative path to the root path of the project, in unix format;
3) ground truth name: the filename in ground truth files:
    - c/c++: equivalent to unified path
    - java: use package name instead
"""
import os
import re
import logging
from pathlib import Path

from utils.utils import json2cluster_dict

logger = logging.getLogger(__name__)

def raw_paths_to_unified_paths(raw_paths, par):
    def single(path, par):
        return Path(path).relative_to(par).as_posix()
    if type(raw_paths) == str:
        return single(raw_paths, par)
    else:
        ret_list = []
        for p in raw_paths:
            ret_list.append(single(p, par))
        return ret_list

def raw_paths_to_ground_truth_format_paths(raw_paths, par, lang = None):    
    """ 
    Convert raw paths to ground truth format paths.
    MAY NOT MATCH WITH THE GROUND TRUTH!
    """
    def single(path, par, lang):
        f_ext = os.path.splitext(path)[-1].lower()
        # determine the file type        
        if lang == None:
            lang_type = None
            if f_ext in ['.c', '.h', '.cpp', '.hpp']:
                lang_type = 'c'
            elif f_ext in ['.java']:
                lang_type = 'java'
            else:
                logger.warning(f'Cannot determine language of {path}')
                lang_type = 'c'
        else:
            if lang.lower() in ['c', 'cpp', 'c++']:
                lang_type = 'c'
            elif lang.lower() in ['java']:
                lang_type = 'java'
            else:
                logger.warning(f"Unsupported lang: {lang}")
                lang_type = 'c'
        logger.debug(f'File type of {path} is determined as {lang_type}')

        # parse the file name for different langs
        if lang_type == 'c':
            fn = Path(path).relative_to(par).as_posix()
        elif lang_type == 'java':                
            with open (path, 'r', encoding='utf-8', errors='ignore') as fp:
                pkg_name = None
                for line in fp:
                    line = line.strip()
                    if line.startswith('package'):
                        res = re.search(r'package\s(\S+)\s{0,};', line)
                        if res != None:
                            pkg_name = res.group(1)
                            break
                if pkg_name == None:
                    if f_ext == '.java':
                        logger.warning(f'Fail to find package info for {path}')
                    fn = Path(path).relative_to(par).as_posix()
                else:
                    fn = f'{pkg_name}.{Path(path).stem}'
        else:
            logger.error('Unknown lang_type: {lang_type} (file: {file})')
            fn = Path(path).relative_to(par).as_posix()

        return fn

    if type(raw_paths) == str:
        return single(raw_paths, par, lang)
    else:
        ret_list = []
        for p in raw_paths:
            ret_list.append(single(p, par, lang))
        return ret_list

def match_filelist_with_ground_truth(filelist, ground_truth, remove_none = False):
    """ 
    Match a list of filenames (in ground truth format) to the filenames in ground truth json. 
    Unmatched files will be replaced with None.
    @param ground_truth: path to the ground truth json or the file name list of the ground truth.
    """
    # resolve ground truth
    if type(ground_truth) == str:
        gt_files = set(json2cluster_dict(ground_truth).keys())
    else:
        gt_files = set(ground_truth)
    
    # match files
    processed_filelist = []
    for f in filelist:
        matched_fn = None
        for f_gt in gt_files:
            # !!!
            if f == f_gt or (f_gt.endswith(f'.{f}') or f.endswith(f'.{f_gt}')):
                matched_fn = f_gt
                gt_files.remove(f_gt)
                break
        processed_filelist.append(matched_fn)
    
    if remove_none:
        processed_filelist = [f for f in processed_filelist if f != None]
        
    return processed_filelist
    