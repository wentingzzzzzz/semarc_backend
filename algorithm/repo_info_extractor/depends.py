import os
import logging
import subprocess
import tempfile
import shutil
import json
import pickle
import networkx as nx

from settings import DEPENDS_PATH, CACHE_PATH, DEPENDS_PUB_PATH, DEPENDS_TIMEOUT_SEC
from algorithm.cache_manager import hash_file, cache_depends_info, get_cached_depends_info
# from utils import subprocess_realtime_log
from utils.filename_convertor import raw_paths_to_unified_paths

logger = logging.getLogger(__name__)

def parse_depends_db(db_file_path, node_file_list=None, edge_types = None):
    def find_parent_file(id, node_dict, known_parent = None):
        str_id = str(id)
        if node_dict[str_id]['type'] == "File":
            par = node_dict[str_id]['name']
        elif node_dict[str_id]['parentId'] == -1:
            return -1
        elif known_parent != None and str_id in known_parent:
            return known_parent[str_id]
        else:
            par = find_parent_file(node_dict[str(id)]['parentId'], node_dict)   
        if known_parent != None:         
            known_parent[str(id)] = par
        return par
    known_parent = {}
    if node_file_list != None:
        node_file_set = set(node_file_list)
    with open(db_file_path) as fp:
        db_json = json.load(fp)
    node_dict = {}
    for i, n in enumerate(db_json['nodes']):
        node_dict[str(n['id'])] = db_json['nodes'][i]
    ret_dict = {}
    # for t in edge_types:
    #     ret_dict[t] = 0
    for e in db_json['edges']:
        if edge_types == None or e['type'] in edge_types:
            if e['type'] not in ret_dict:
                ret_dict[e['type']] = {}
            start_file = find_parent_file(e['from'], node_dict, known_parent)
            end_file = find_parent_file(e['to'], node_dict, known_parent)
            for f in [start_file, end_file]:
                assert f != -1
                if node_file_list != None and (start_file not in node_file_set or end_file not in node_file_set):
                    continue
            edge_key = (start_file, end_file)
            if edge_key not in ret_dict[e['type']]:
                ret_dict[e['type']][edge_key] = [start_file, end_file, 0]
            ret_dict[e['type']][edge_key][2] += 1
    for k in ret_dict:
        ret_dict[k] = list(ret_dict[k].values())
    return ret_dict


def parse_depends_db_func_pub(db_file_path):
    if isinstance(db_file_path, str):
        with open(db_file_path, 'rb') as f:
            data = pickle.load(f)
    else:
        data = db_file_path
    obj2id = {(fn,fn, 'file'):i for i, fn in enumerate(data['variables'])}
    # id2info = {i:{'file':fn, 'func_id':None, 'object':None, 'line':None, 'type':'file'} for i, fn in enumerate(data['variables'])}
    id2info = {i:{'file':fn, 'func_id':None, 'type':'file', 'object':None} for i, fn in enumerate(data['variables'])}
    # id2fn = {i:fn for i, fn in enumerate(data['variables'])}

    print("obj2id:",obj2id)
    edge_dict = {}
    for file_dep in data['cells']:
        src_fid, dst_fid = file_dep['src'], file_dep['dest']
        # if src_fid == dst_fid:
        #     for e in file_dep['details']:
        #         if e['type'] == 'Contain':
        #             a = 1
        #         pass
        for e in file_dep['details']:
            src_key = (e['src']['file'], e['src']['object'], e['src']['type'])
            dst_key = (e['dest']['file'], e['dest']['object'], e['dest']['type'])
            for key in [src_key, dst_key]:
                obj2id.setdefault(key, len(obj2id))
            src_id, dst_id = obj2id[src_key], obj2id[dst_key]
            edge_dict.setdefault(e['type'], {}).setdefault((src_id, dst_id), 0)
            edge_dict[e['type']][(src_id, dst_id)] += 1
            # id2info.setdefault(src_id, 
            #     {'file':e['src']['file'], 'func_id':None, 'object':e['src']['object'], 'line':e['src']['lineNumber'], 'type':e['src']['type']})
            # id2info.setdefault(dst_id,
            #     {'file':e['dest']['file'], 'func_id':None, 'object':e['dest']['object'], 'line':e['dest']['lineNumber'], 'type':e['dest']['type']})
            id2info.setdefault(src_id, 
                {'file':e['src']['file'], 'func_id':None, 'type':e['src']['type'], 'object':e['src']['object']})
            id2info.setdefault(dst_id,
                {'file':e['dest']['file'], 'func_id':None, 'type':e['dest']['type'], 'object':e['dest']['object']})
            # func
            # TODO: propagate func info
            if e['src']['type'] in ['function', 'functionimpl']:
                id2info[src_id]['func_id'] = src_id
            if e['dest']['type'] in ['function', 'functionimpl']:
                id2info[dst_id]['func_id'] = dst_id
            if e['type'] == 'Implement' and e['src']['type'] ==  'functionimpl':
                id2info[dst_id]['func_id'] = src_id
                # assert src_id == id2info[src_id]['func_id']
            if src_fid == dst_fid and e['type'] == 'Use' and e['src']['type'] in ['function', 'functionimpl'] and e['dest']['type'] == 'var':
                id2info[dst_id]['func_id'] = src_id
                
    return edge_dict, id2info

def parse_depends_pub_to_file_dep_graph(db_file_path):
    with open(db_file_path, 'rb') as f:
        data = pickle.load(f)
    id2fn = {i:fn for i, fn in enumerate(data['variables'])}
    nodes = data['variables']
    edges = []
    for file_dep in data['cells']:
        src_fid, dst_fid = file_dep['src'], file_dep['dest']
        edges.append((id2fn[src_fid], id2fn[dst_fid]))
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    
    return G

def mdg2graph(mdg_file):
    di_graph = nx.DiGraph()
    with open(mdg_file) as fp:
        for line in fp:
            splitted_line = line.split()
            if len(splitted_line) == 3 and splitted_line[0] == 'depends':
                src = splitted_line[1]
                des = splitted_line[2]
                # nodes will be automatically added
                di_graph.add_edge(src, des)
            elif len(splitted_line) != 0:
                logger.warning(f"Unknown line in {mdg_file}: {line.rstrip()}")
    return di_graph


def generate_and_parse_dependency_pub(src_path, prj_name, prj_id, result_folder, prj_lang, cache_dir) -> dict:
    
    if prj_lang.lower() in ['c', 'cpp', 'c++']:
        analysis_type = 'cpp'
    elif prj_lang.lower() in ['java']:
        analysis_type = 'java'
    elif prj_lang.lower() in ['python']:
        analysis_type = 'python'
    else:
        raise Exception(f"Depends does not support {prj_lang}! Supported language are: C/C++, Java, python")
    try:
        src_path = raw_paths_to_unified_paths(src_path, '.')
    except:
        # src_path = raw_paths_to_unified_paths(src_path, '/')
        pass
    result_folder = raw_paths_to_unified_paths(result_folder, '.')
    # result_folder='D:\\enre\\jabref'
    depends_jar_sha = hash_file(DEPENDS_PUB_PATH)
    depends_inputs = (
        src_path,
        result_folder,
        prj_name,
        prj_lang,
        prj_id,
        depends_jar_sha
    )

    dep_file_dict = {}

    cached_record = get_cached_depends_info(depends_inputs, cache_dir)
    if cached_record != None:
        logger.info(f"Found cached Depends result for {prj_name}...")
        dep_file_dict['dep_result'] = cached_record['dep_result']['path']
        dep_file_dict['edges_dict_func'] = cached_record['edges_dict_func']['path']
        dep_file_dict['id2node_info'] = cached_record['id2node_info']['path']
        return dep_file_dict

    logger.info(f"Running Depends for {prj_name}...")
    
    # run depends
    tmp_folder = tempfile.mkdtemp()
    # cmd = f'java -Xmx51200m -jar {DEPENDS_PUB_PATH} --auto-include --detail --output-self-deps -f=json -s -p / -d {tmp_folder} {analysis_type} {src_path} {prj_name}'
    cmd = f'java -Xmx51200m -jar {DEPENDS_PUB_PATH} --auto-include --detail -f=json -s -p / -d {tmp_folder} {analysis_type} {src_path} {prj_name}'
    logger.debug(cmd)

    with open(os.path.join(result_folder, 'depends_stdout.log'), 'w') as fp:
        # return_code = subprocess_realtime_log(cmd, log_level=logging.DEBUG)
        # subprocess.run(cmd, shell=True, timeout=DEPENDS_TIMEOUT_SEC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(cmd, shell=True, timeout=DEPENDS_TIMEOUT_SEC, stdout=fp, stderr=fp)
    logger.info(f"Depends Finished.") 
    try:
        shutil.move('depends.log', os.path.join(result_folder, 'depends.log'))
    except:
        pass

    # copy files
    # shutil.copyfile(
    #     os.path.join(tmp_folder, result_fn),
    #     os.path.join(result_folder, result_fn)
    #     )
    src_abs_path = os.path.abspath(src_path)
    if src_abs_path[-1] != os.sep:
        src_abs_path = src_abs_path + os.sep
    # result_fn = f'{prj_name}-file.json'
    # with open(os.path.join(tmp_folder, result_fn), 'r') as f:
    #     with open(os.path.join(result_folder, result_fn), 'w') as fo:
    #         for line in f:
    #             fo.write(line.replace(src_abs_path, '').strip())
    
    # logger.info(f"Copied Depends result to {result_folder}.") 
    
    ## parse and cache results
    result_dep_fn = f'{prj_name}-file.json'
    result_fn = f'{prj_name}-file.pkl'
    with open(os.path.join(tmp_folder, result_dep_fn), 'r') as fp:
        depends_result_dict = json.load(fp)
    #替换为enre
    # result_dep_fn = f'D:\\enre\\jabref\\jabref_out_depends.json'
    # result_fn = f'{prj_name}-file.pkl'
    # with open(result_dep_fn, 'r') as fp:
    #     depends_result_dict = json.load(fp)

    # # change fns
    # for i, fn in enumerate(depends_result_dict['variables']):
    #     depends_result_dict['variables'][i] = fn.replace(src_abs_path, '')
    # for file_dep in depends_result_dict['cells']:
    #     for dep in file_dep['details']:
    #         for k in ['src', 'dest']:
    #             dep[k]['object'] = dep[k]['object'].replace(src_abs_path, '')
    #             dep[k]['file'] = dep[k]['file'].replace(src_abs_path, '')

    with open(os.path.join(result_folder, result_fn), 'wb') as fp:
        pickle.dump(depends_result_dict, fp)
    dep_file_dict = {'dep_result': os.path.join(result_folder, result_fn)}

    edges_dict_func, id2node_info = parse_depends_db_func_pub(depends_result_dict)
    logger.debug(f"Parsed Depends result.") 
    ed_fn = 'edges_dict_func.pkl'
    node_fn = 'id2node_info.pkl'
    with open(os.path.join(result_folder, ed_fn), 'wb') as fp:
        pickle.dump(edges_dict_func, fp)
    with open(os.path.join(result_folder, node_fn), 'wb') as fp:
        pickle.dump(id2node_info, fp)

    # cache results
    dep_file_dict['edges_dict_func'] = os.path.join(result_folder, ed_fn)
    dep_file_dict['id2node_info'] = os.path.join(result_folder, node_fn)
    cache_depends_info(depends_inputs, dep_file_dict, cache_dir)
        
    return dep_file_dict


if __name__ == "__main__":
    pass