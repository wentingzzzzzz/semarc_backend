import os
from utils.filename_convertor import raw_paths_to_unified_paths, raw_paths_to_ground_truth_format_paths, match_filelist_with_ground_truth

def get_raw_paths_from_prj_folder(src_path, supported_exts = None):
    """ Get unprocessed file paths """
    raw_filelist = []
    for root, dirs, files in os.walk(src_path):
        for file in files:
            ext = os.path.splitext(file)[-1]
            raw_fn = os.path.join(root, file)
            if supported_exts == None or ext in supported_exts: 
                raw_filelist.append(raw_fn)
    return raw_filelist

def get_unified_paths(src_path, supported_exts = None):
    """ Get unified file paths """
    raw_filelist = get_raw_paths_from_prj_folder(src_path, supported_exts)
    return raw_paths_to_unified_paths(raw_filelist, src_path)

def get_raw_and_unified_and_gt_filenames_from_prj_folder(src_path, ground_truth = None, supported_exts = None, prj_lang = None):
    """ Get ground truth file list. Files not in gt will be removed. """
    # Get raw file list, then convert to unified/gt format.
    raw_filelist = get_raw_paths_from_prj_folder(src_path, supported_exts)
    unified_filelist = raw_paths_to_unified_paths(raw_filelist, src_path)
    gt_format_filelist = raw_paths_to_ground_truth_format_paths(raw_filelist, src_path, prj_lang)

    # Remove unmatched files if ground truth is provided
    if ground_truth != None:
        gt_filelist = match_filelist_with_ground_truth(gt_format_filelist, ground_truth, remove_none=False)        
        raw_list_ret = []
        unified_list_ret = []
        gt_file_list_ret = []
        for i, gt in enumerate(gt_filelist):
            if gt == None:
                continue
            gt_file_list_ret.append(gt)
            raw_list_ret.append(raw_filelist[i])
            unified_list_ret.append(unified_filelist[i])
    else:
        raw_list_ret = raw_filelist
        unified_list_ret = unified_filelist
        gt_file_list_ret = gt_format_filelist

    # assert
    assert len(raw_list_ret) == len(unified_list_ret)
    assert len(raw_list_ret) == len(gt_file_list_ret)

    return raw_list_ret, unified_list_ret, gt_file_list_ret
    