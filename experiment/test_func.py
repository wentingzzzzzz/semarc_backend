def parse_depends_db(db_file_path, node_file_list=None, edge_types = None):
    def find_parent_file(id, node_dict, known_parent = None):
        #enre中直接有parentID
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