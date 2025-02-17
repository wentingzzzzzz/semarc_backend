import os
import math
import logging
from collections import Counter
import networkx as nx
from pathlib import Path
from algorithm.repo_info_extractor.depends import parse_depends_db
from networkx.algorithms.community.centrality import girvan_newman
from networkx.algorithms.community.modularity_max import greedy_modularity_communities

from utils.utils import remap_result_dict, view_nx_graph_with_graphviz

logger = logging.getLogger(__name__)

def community_detection(graph, gt_files=None, view_graph = False, weight_keyword = None, return_communities = False, resolution=1):
    result_dict = {}
    if gt_files != None:
        gt_file_set = set(gt_files)
        node_delete = []
        for node in graph.nodes:
            if node not in gt_file_set:
                node_delete.append(node)
        for node in node_delete:
            logger.debug(f"Removing node: {node}")
            graph.remove_node(node)
    if len(graph.nodes) == 0:
        return {}
    # !!!
    elif len(graph.edges) == 0:
        return {n:0 for n in graph.nodes}
    if view_graph:
        view_nx_graph_with_graphviz(graph)
    communities = greedy_modularity_communities(graph, weight=weight_keyword, resolution=resolution)
    if return_communities:
        return communities
    for i, com in enumerate(communities):
        for f in com:
            result_dict[f] = i

    return result_dict    

def delete_unmatched_nodes(nx_graph, node_name_list, copy=True):
    """ Remove nodes in nx_graph which are not in node_name_list. """
    node_name_set = set(node_name_list)
    nodes2delete = [n for n in nx_graph.nodes if n not in node_name_set]
    if copy:
        G = nx_graph.copy()
    else:
        G = nx_graph
    G.remove_nodes_from(nodes2delete)
    return G


def color_node_with_result_dict(G, result_dict, target = 'node'):
    """ 
    给图上的节点染色; 
    @param target: 'node' - 节点的外沿；'name' - 节点的名字
    """
    G = G.copy()
    from utils.plot_result import color_list
    color_list = color_list*100
    if target not in ['node', 'name']:
        raise
    elif target == 'node':
        color_kw = 'color'
    elif target == 'name':
        color_kw = 'fontcolor'
    node_color_update_dict = {}
    for n, r in result_dict.items():
        if n not in G.nodes:
            logging.debug(f'Unknown node: {n}')
            continue
        node_color_update_dict[n] = {color_kw: color_list[r]} 
    nx.set_node_attributes(G, node_color_update_dict)
    return G

def merge_files_in_graph(nx_graph, merged2unmerged_dict, unmerged2merged_dict, remove_self_loop=True, copy=True):
    """ Only files will be merged should appear in unmerged2merged_dict! """
    def merge_info_dicts(info_dicts):
        key_set = set()
        for d in info_dicts:
            for k in d:
                key_set.add(k)
        merged_dict = {}
        for k in sorted(list(key_set)):
            val_list = [d[k] for d in info_dicts if k in d]
            if type(val_list[0]) == str:
                # merged_dict[k] = '|'.join(val_list)
                if len(set(val_list)) == 1:
                    merged_dict[k] = val_list[0]
            else:
                try:
                    merged_dict[k] = sum(val_list)
                except:
                    pass
        return merged_dict
    if copy:
        G = nx_graph.copy()
    else:
        G = nx_graph
    nodes2rm = [n[0] for n in G.nodes(data=True) if n[0] in unmerged2merged_dict]
    nodes2add = []
    for name, names2merge in merged2unmerged_dict.items():
        if all([n not in G.nodes for n in names2merge]):
            continue
        new_attr = merge_info_dicts([G._node[n] for n in names2merge])
        nodes2add.append((name, new_attr))

    edges2rm = [e for e in G.edges(data=True) if e[0] in unmerged2merged_dict or e[1] in unmerged2merged_dict]
    # edges2add = [(ch2group[e[0]], ch2group[e[1]], e[2]) for e in G.edges(data=True) if e[0] in nodes2rm or e[1] in nodes2rm]
    new_edge_dict = {}
    for e in edges2rm:
        start = unmerged2merged_dict[e[0]] if e[0] in unmerged2merged_dict else e[0]
        end = unmerged2merged_dict[e[1]] if e[1] in unmerged2merged_dict else e[1]
        if remove_self_loop and start==end:
            continue
        edge_key = (start, end)
        new_edge_dict[edge_key] = new_edge_dict.get(edge_key, []) + [e[2]]
    edges2add = []
    for k, attrs in new_edge_dict.items():
        start, end = k
        new_attr = merge_info_dicts(attrs)
        edges2add.append((start, end, new_attr))

    G.remove_edges_from(edges2rm)
    G.remove_nodes_from(nodes2rm)
    G.add_nodes_from(nodes2add)
    G.add_edges_from(edges2add)
    return G

def get_impl_link_merge_dict(impl_edges, filelist_unified_sl = None, return_mapping = False):
    # edges_dict = parse_depends_db(db_file_path)
    impl_graph = nx.DiGraph()
    # impl_edges = [(e[0], e[1], {'weight': e[2], 'label': e[2]}) for e in edges_dict['Implement']]
    impl_graph.add_edges_from(impl_edges)
    if filelist_unified_sl != None:
        impl_graph = delete_unmatched_nodes(impl_graph, filelist_unified_sl)
    community_result_dict = community_detection(impl_graph, weight_keyword='weight')

    # import pickle
    # with open('test16', 'rb') as fp:
    #     community_result_dict2 = pickle.load(fp)
    # with open('test16', 'wb') as fp:
    #     pickle.dump(community_result_dict, fp)
    # assert community_result_dict == community_result_dict2

    res_merge_dict = {}
    #!!!
    if len(impl_edges) == 0:
        if return_mapping:
            return {}, {}, {}
        return {}
    for comm_res in range(max(community_result_dict.values())+1):
        sub_nodes = sorted([n for n in community_result_dict if community_result_dict[n] == comm_res])
        sub_impl_graph = impl_graph.subgraph(sub_nodes).copy()
        # for src, des in sub_impl_graph.edges(data=True):
        # remove edge if file implement multiple other files and some of other files has a low weight
        for n in sub_nodes:
            edges_src_is_n = sorted([e for e in sub_impl_graph.edges(data=True) if e[0] == n])
            if len(edges_src_is_n) < 2:
                continue
            max_weight = max([e[2]['weight'] for e in edges_src_is_n])
            weight_thresh = math.sqrt(max_weight)
            edges2rm = [e for e in edges_src_is_n if e[2]['weight'] < weight_thresh]
            sub_impl_graph.remove_edges_from(edges2rm)
        for weight_group_res, subsub_nodes in enumerate(nx.connected_components(sub_impl_graph.to_undirected())):
            if len(subsub_nodes) != 1:
                subsub_graph = sub_impl_graph.subgraph(subsub_nodes)
                h2pack2weight = {}
                pack2c = {}
                for src, des, attr in subsub_graph.edges(data=True):
                    pack = os.path.dirname(src)
                    if pack not in pack2c:
                        pack2c[pack] = []
                    pack2c[pack].append(src)
                    if des not in h2pack2weight:
                        h2pack2weight[des] = {}
                    if pack not in h2pack2weight[des]:
                        h2pack2weight[des][pack] = 0
                    h2pack2weight[des][pack] += attr['weight']
                pack2res = {p:i for i, p in enumerate(pack2c)}
                h2pack = {h:max(pack2weight, key=pack2weight.get) for h, pack2weight in h2pack2weight.items()}
                # h_pack_res = {h:pack2res[pack] for h,pack in h2pack.items()}
                subsub_pack_res = {}
                for h, pack in h2pack.items():
                    subsub_pack_res[h] = pack2res[pack]
                for pack, cs in pack2c.items():
                    for c in cs:
                        subsub_pack_res[c] = pack2res[pack]

                for f, pack_res in subsub_pack_res.items():
                    # res_merge_dict[f] = 10000*comm_res+100*weight_group_res+pack_res+1
                    res_merge_dict[f] = (comm_res, weight_group_res, pack_res)
    res_merge_dict = remap_result_dict(res_merge_dict)
    if return_mapping:
        def get_merge_mapping_from_res_dict(result_merge_dict):            
            ind2filelist = {}
            for k, v in result_merge_dict.items():
                ind2filelist[v] = ind2filelist.get(v, []) + [k]  

            merged2unmerged_dict = {}
            for k,v in ind2filelist.items():
                if len(v) == 0:
                    continue
                # files_not_headers = [f for f in v if not Path(f).suffix.lower().startswith('.h')]
                not_headers_par_list = [str(Path(f).parent) for f in v if not Path(f).suffix.lower().startswith('.h')]
                if len(not_headers_par_list) == 0:
                    not_headers_par_list = [str(Path(f).parent) for f in v]
                merged_par = Counter(not_headers_par_list).most_common(1)[0][0]
                merged_basename = '|'.join(set([Path(p).stem for p in v])) if len(v)>1 else v[0]
                if merged_par == '.':
                    merged_name = merged_basename
                else:
                    merged_name = f'{merged_par}/{merged_basename}'
                merged2unmerged_dict[merged_name] = v 
            # merged2unmerged_dict = {('|'.join(set([Path(p).stem for p in v])) if len(v)>1 else v[0]):v  for k,v in merged2unmerged_dict.items()}
            unmerged2merged_dict = {}
            for k, vs in merged2unmerged_dict.items():
                unmerged2merged_dict.update({v:k for v in vs})
            return merged2unmerged_dict, unmerged2merged_dict
        merged2unmerged_dict, unmerged2merged_dict = get_merge_mapping_from_res_dict(res_merge_dict)
        return res_merge_dict, merged2unmerged_dict, unmerged2merged_dict
    else:
        return res_merge_dict

def get_all_bunch_mqs(nx_graph, result_dict):
    assert len(nx_graph) == len(result_dict)

    # basic
    cluster_sizes = dict(Counter(result_dict.values()))
    K = len(cluster_sizes)

    edges_dict_bunch = {}
    edges_dict_bunch_weighted = {}
    for e in nx_graph.edges(data=True):
        src, des, attr= e
        if 'weight' in attr:
            w = attr['weight']
        else:
            w = 1
        src_res = result_dict[src]
        des_res = result_dict[des]
        try:
            edges_dict_bunch[(src_res, des_res)] += 1
            edges_dict_bunch_weighted[(src_res, des_res)] += w
        except KeyError:
            edges_dict_bunch[(src_res, des_res)] = 1
            edges_dict_bunch_weighted[(src_res, des_res)] = w


    A_values = {}
    for k, v in cluster_sizes.items():
        try:
            A_values[k] = edges_dict_bunch[(k,k)] / v**2
        except KeyError:
            A_values[k] = 0

    

    E_values = {}
    for (src,des), v in edges_dict_bunch.items():
        if src == des:
            continue
        E_values[(src,des)] = v/(2*cluster_sizes[src]*cluster_sizes[des])
        pass

    if len(A_values) == 1:
        basic_mq = list(A_values.values())[0]
    else:
        basic_mq = sum((A_values.values()))/K - sum(E_values.values())*2/(K*(K-1))

    # turbo
    inter_edges_for_clusters = {k:0 for k in A_values}
    for (src,des), v in edges_dict_bunch.items():
        if src == des:
            continue
        inter_edges_for_clusters[src] += v
        inter_edges_for_clusters[des] += v

    inter_edges_for_clusters_weighted = {k:0 for k in A_values}
    for (src,des), v in edges_dict_bunch_weighted.items():
        if src == des:
            continue
        inter_edges_for_clusters_weighted[src] += v
        inter_edges_for_clusters_weighted[des] += v
        
    CFs = {}
    CFs_weighted = {}
    for k in A_values:
        if (k,k) not in edges_dict_bunch:
            CFs[k] = 0
        else:
            ui = edges_dict_bunch[(k,k)]
            CFs[k] = ui/(ui+inter_edges_for_clusters[k]/2)
            ui = edges_dict_bunch_weighted[(k,k)]
            CFs_weighted[k] = ui/(ui+inter_edges_for_clusters_weighted[k]/2)
    turbo_mq = sum(CFs.values())
    turbo_mq_weighted = sum(CFs_weighted.values())

    return basic_mq, turbo_mq, turbo_mq_weighted

    
def get_modx_mq(nx_graph, result_dict):
    assert len(nx_graph) == len(result_dict)

    in_degree_dict = {}
    out_degree_dict = {}
    edge_dict = {}
    for e in nx_graph.edges(data=True):
        src, des, attr = e
        if 'weight' in attr:
            w = attr['weight']
        else:
            w = 1
        try:
            out_degree_dict[src] += w
        except KeyError:
            out_degree_dict[src] = w

        try:
            in_degree_dict[des] += w
        except KeyError:
            in_degree_dict[des] = w
        edge_dict[(src, des)] = w

    W = sum(edge_dict.values())

    Q = 0
    for n1 in nx_graph.nodes():
        for n2 in nx_graph.nodes():
            if n1 == n2:
                continue
            if result_dict[n1] != result_dict[n2]:
                continue
            wij = edge_dict.get((n1,n2),0)
            kiout = out_degree_dict.get(n1, 0)
            kjin = in_degree_dict.get(n2, 0)
            Q += wij-kiout*kjin/W/2

    Q /= (2*W)
    return Q


    A_values = {}
    for k, v in cluster_sizes.items():
        try:
            A_values[k] = edges_dict_bunch[(k,k)] / v**2
        except KeyError:
            A_values[k] = 0

    

    E_values = {}
    for (src,des), v in edges_dict_bunch.items():
        if src == des:
            continue
        E_values[(src,des)] = v/(2*cluster_sizes[src]*cluster_sizes[des])
        pass

    if len(A_values) == 1:
        basic_mq = list(A_values.values())[0]
    else:
        basic_mq = sum((A_values.values()))/K - sum(E_values.values())*2/(K*(K-1))

    # turbo
    inter_edges_for_clusters = {k:0 for k in A_values}
    for (src,des), v in edges_dict_bunch.items():
        if src == des:
            continue
        inter_edges_for_clusters[src] += v
        inter_edges_for_clusters[des] += v

    inter_edges_for_clusters_weighted = {k:0 for k in A_values}
    for (src,des), v in edges_dict_bunch_weighted.items():
        if src == des:
            continue
        inter_edges_for_clusters_weighted[src] += v
        inter_edges_for_clusters_weighted[des] += v
        
    CFs = {}
    CFs_weighted = {}
    for k in A_values:
        if (k,k) not in edges_dict_bunch:
            CFs[k] = 0
        else:
            ui = edges_dict_bunch[(k,k)]
            CFs[k] = ui/(ui+inter_edges_for_clusters[k]/2)
            ui = edges_dict_bunch_weighted[(k,k)]
            CFs_weighted[k] = ui/(ui+inter_edges_for_clusters_weighted[k]/2)
    turbo_mq = sum(CFs.values())
    turbo_mq_weighted = sum(CFs_weighted.values())

    return basic_mq, turbo_mq, turbo_mq_weighted