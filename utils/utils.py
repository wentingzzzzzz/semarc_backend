import csv
import os
import re
import json
import logging
from collections import Counter
from pathlib import Path
from typing import List
import subprocess
from settings import SUPPORTED_FILE_TYPES

logger = logging.getLogger(__name__)


def get_intersect_lists_from_two_dict(result_dict1, result_dict2):
    filelist = [fn for fn in result_dict1 if fn in result_dict2]
    result1 = list(map(lambda x: result_dict1[x], filelist))
    result2 = list(map(lambda x: result_dict2[x], filelist))
    return filelist, result1, result2


def json2cluster_dict(json_fn, get_titles=False):
    with open(json_fn) as fp:
        cluster_js = json.load(fp)
        cluster_dict = {}
        title_list = []
        for i, cluster in enumerate(cluster_js['structure']):
            if get_titles:
                title_list.append(cluster['name'])
            for f in cluster['nested']:
                cluster_dict[f['name']] = i
    if get_titles:
        return cluster_dict, title_list
    else:
        return cluster_dict


def cluster2json(filenames, result, cluster_names=None, num_clusters=None):
    """Save to clustering json file."""
    if num_clusters is None:
        num_clusters = max(result) + 1
    dict1 = {"@schemaVersion": "1.0", "name": "clustering", "structure": []}
    for i in range(num_clusters):
        if cluster_names is None:
            dict1["structure"].append({"@type": "group", "name": str(i), "nested": []})
        else:
            dict1["structure"].append({"@type": "group", "name": cluster_names[i], "nested": []})
    for i in range(len(result)):
        dict1["structure"][result[i]]["nested"].append({"@type": "item", "name": filenames[i]})
    return dict1


def cluster2json_rec_words(filenames, result, cluster_words=None, num_clusters=None):
    """Save to clustering json file with recommended words."""
    if num_clusters is None:
        num_clusters = max(result) + 1
    cluster_names = []
    for i in range(num_clusters):
        cluster_names.append(", ".join(cluster_words[i]))
    return cluster2json(filenames, result, cluster_names, num_clusters)


def is_csv_file(data_path: str) -> bool:
    """ Return if a file is a csv file. """
    if os.path.exists(data_path) and data_path.endswith('.csv'):
        return True
    else:
        return False


def get_pack_dict_from_filelist(filelist, get_path_names=False):
    path_names = []
    pack_dict = {}
    for f in filelist:
        p, fn = os.path.split(f)
        if p not in path_names:
            path_names.append(p)
        pack_dict[f] = path_names.index(p)
    if get_path_names:
        return pack_dict, path_names
    else:
        return pack_dict


def post_process(result_pkg):
    for item in result_pkg["structure"]:
        p, f = os.path.split(item["name"])
        if p != "":
            for d in result_pkg["structure"][:result_pkg["structure"].index(item)]:
                if p == d["name"]:
                    item["parent"] = result_pkg["structure"].index(d)
    return result_pkg


def post_process_python(result_dict, result_pack_dict, data_path):
    for key in result_dict:
        # if (not os.path.getsize(os.path.join(data_path, key))) and key.endswith("__init__.py"):
        if key.endswith("__init__.py") and key != "__init__.py":
            t = result_pack_dict[key]
            grp_list = [key for key, value in result_pack_dict.items() if value == t]
            grp_pairs = {key: result_dict[key] for key in grp_list if key in result_dict}
            if len(grp_pairs) > 3:
                grp_pairs.pop(key)
            grp_pairs_counts = Counter(grp_pairs.values())
            most_common_value = grp_pairs_counts.most_common(1)[0][0]
            result_dict[key] = most_common_value
    num_clusters = max(result_dict.values())+1
    i = 0
    while i < num_clusters:
        while i not in result_dict.values():
            for key, value in result_dict.items():
                if value > i:
                    result_dict[key] = value - 1
            num_clusters -= 1
        i += 1
    return result_dict


def post_process_python2(result_dict, lang, data_path, num_clusters):
    if lang == 'python':
        f = open('init2.csv', 'a', newline='')
        writer = csv.writer(f)
        for i in range(num_clusters):
            tmp_list = []
            t = False
            for item in result_dict["structure"][i]["nested"]:
                if os.path.getsize(os.path.join(data_path, item['name'])):
                    t = True
                    if item['name'].endswith("__init__.py"):
                        tmp_list.append(item['name'])
            if tmp_list:
                writer.writerow(tmp_list)
            if not t:
                result_dict["structure"][i]['isEmpty'] = True
        f.close()
    return result_dict


def post_process_python3(result_dict, lang, result_pack_dict, num_clusters):
    if lang == 'python':
        num2 = len(result_pack_dict["structure"])
        for i in range(num2):
            if len(result_pack_dict["structure"][i]["nested"]) == 1:
                loc1 = loc2 = loc3 = -1
                for j in range(num_clusters):
                    for item in result_dict["structure"][j]["nested"]:
                        if item['name'] == result_pack_dict["structure"][i]["nested"][0]['name']:
                            loc1 = loc2 = j
                            loc3 = result_dict["structure"][j]["nested"].index(item)
                            break
                maxfre = 1
                for j in range(num2):
                    if result_pack_dict["structure"][j].get('parent', -1) == i:
                        for k in range(num_clusters):
                            tmp = 0
                            for item in result_dict["structure"][k]["nested"]:
                                if item['name'].startswith(result_pack_dict["structure"][i]['name']):
                                    tmp = tmp+1
                            if tmp > maxfre:
                                loc2 = k
                        break
                if loc1 != loc2:
                    item = result_dict["structure"][loc1]["nested"].pop(loc3)
                    result_dict["structure"][loc2]["nested"].append(item)
    return result_dict


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def get_prj_lang(src_path):
    file_num = {
        'c': 0,
        'cpp': 0,
        'java': 0,
        'python': 0,
    }
    for root, dirs, files in os.walk(src_path):
        for f in files:
            f = f.lower()
            if f.endswith(".c") or f.endswith(".h"):
                file_num['c'] += 1
            elif f.endswith(".cpp") or f.endswith(".hpp") or f.endswith(".cxx") or f.endswith(".hxx"):
                file_num['cpp'] += 1
            elif f.endswith(".java"):
                file_num['java'] += 1
            elif f.endswith(".py"):
                file_num['python'] += 1
    if sum(file_num.values()) == 0:
        raise Exception(f"No supported files founded! Current language includes: {list(file_num.keys())}")
    return sorted(file_num.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[0][0]


def subprocess_realtime_log(cmd, log_level=logging.DEBUG):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    while True:
        output = p.stdout.readline().decode()
        if (output == '') and (p.poll() != None):
            break
        if output:
            logger.log(log_level, output.strip())

    err = p.stderr.readlines()
    if err:
        for line in err:
            logger.error(line.strip().decode())

    return p.poll()


def unmerge_result_dict(merged_result_dict, merged2unmerged_dict):
    unmerged = {}
    for k, v in merged_result_dict.items():
        if k in merged2unmerged_dict:
            unmerged.update({n: v for n in merged2unmerged_dict[k]})
        else:
            unmerged[k] = v
    return unmerged


import networkx as nx
import tempfile
import graphviz
from networkx.drawing.nx_pydot import to_pydot


def view_nx_graph_with_graphviz(nx_graph, use_base_name=False):
    if use_base_name:
        name_mapping = {f: os.path.basename(f) for f in nx_graph.nodes}
        nx_graph = nx.relabel_nodes(nx_graph, name_mapping, copy=True)
    new_file, filename = tempfile.mkstemp()
    graphviz_dot = graphviz.Source(to_pydot(nx_graph).to_string())
    graphviz_dot.render(filename=filename, view=True, format='pdf')


def remap_result_dict(result_dict):
    result_ret = {}
    val_set = set(result_dict.values())
    val_set = sorted(list(val_set))
    val_map = {v: i for i, v in enumerate(val_set)}
    for f in result_dict:
        result_ret[f] = val_map[result_dict[f]]
    return result_ret


def get_c_h_group_dict(filenames):
    file_base_names = []
    file_exts = []
    pairs = []
    for f in filenames:
        file_base_names.append(Path(f).stem)
        file_exts.append(os.path.splitext(f)[-1])
    for i, ext in enumerate(file_exts):
        if ext == '.c':
            fn = file_base_names[i]
            same_name_inds = [j for j, x in enumerate(file_base_names) if x == fn and file_exts[j] in ['.c', '.h']]
            if len(same_name_inds) > 2:
                continue
            elif len(same_name_inds) == 2:
                for ind in same_name_inds:
                    if ind == i:
                        continue
                    if file_exts[ind] != '.h':
                        continue
                    pairs.append((i, ind))
    c2h_dict = {}
    for p in pairs:
        c2h_dict[filenames[p[0]]] = filenames[p[1]]

    return c2h_dict


def get_ch2group_dict(filenames):
    file_base_names = []
    file_exts = []
    pairs = []
    for f in filenames:
        file_base_names.append(Path(f).stem)
        file_exts.append(os.path.splitext(f)[-1])
    for i, ext in enumerate(file_exts):
        if ext == '.c':
            fn = file_base_names[i]
            same_name_inds = [j for j, x in enumerate(file_base_names) if x == fn and file_exts[j] in ['.c', '.h']]
            if len(same_name_inds) > 2:
                continue
            elif len(same_name_inds) == 2:
                for ind in same_name_inds:
                    if ind == i:
                        continue
                    if file_exts[ind] != '.h':
                        continue
                    # !!! for libxml
                    if file_base_names[i] == 'libxml':
                        continue
                    pairs.append((i, ind))
    ch2group = {f: f for f in filenames}
    for p in pairs:
        group_name = filenames[p[0]] + 'h'
        ch2group[filenames[p[0]]] = group_name
        ch2group[filenames[p[1]]] = group_name

    return ch2group


def get_pack_dict_java(filelist, get_path_names=False):
    path_names = []
    pack_dict = {}
    for f in filelist:
        # p,fn = os.path.split(f)
        p = f.split('/')[0]
        if p not in path_names:
            path_names.append(p)
        pack_dict[f] = path_names.index(p)
    if get_path_names:
        return pack_dict, path_names
    else:
        return pack_dict


def get_pack_dict_level(filelist_unified, level=2):
    if [] in [f.split('/')[:-1] for f in filelist_unified]:
        level += 1

    pack_dict = {f: [] for f in filelist_unified}
    next_filelists = [filelist_unified.copy()]
    for l in range(level):
        curr_filelists = next_filelists
        next_filelists = []
        for curr_filelist in curr_filelists:
            splitted_files = [f.split('/')[:-1] + [None] for f in curr_filelist]
            # rm common path
            first_pn_set = set([lp[0] for lp in splitted_files])
            pack_dict_level = {f: [] for f in curr_filelist}
            while len(first_pn_set) == 1 and None not in first_pn_set:
                pack_name2rm = splitted_files[0][0]
                splitted_files = [lp[1:] for lp in splitted_files]
                for f in curr_filelist:
                    pack_dict_level[f].append(pack_name2rm)
                first_pn_set = set([lp[0] for lp in splitted_files])
            for f in pack_dict_level:
                pack_dict[f] = pack_dict_level[f]
            # get next level path
            for p in first_pn_set:
                if p is not None:
                    next_filelists.append([curr_filelist[i] for i, lp in enumerate(splitted_files) if lp[0] == p])
    return {f: '/'.join(lp) for f, lp in pack_dict.items()}
