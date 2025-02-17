import os
import logging
import pickle
import math
import numpy as np
import networkx as nx
import numpy as np
import json
from collections import defaultdict,Counter

from utils.graph_utils import color_node_with_result_dict, community_detection, delete_unmatched_nodes, get_impl_link_merge_dict, merge_files_in_graph
from algorithm.repo_info_extractor.depends import  mdg2graph, parse_depends_db, parse_depends_db_func_pub, generate_and_parse_dependency_pub, parse_depends_pub_to_file_dep_graph
from algorithm.repo_info_extractor.func_len import get_func_info
from algorithm.comparing_clusters import compare_two_cluster_results
from algorithm.word_processing import get_processed_words_from_prj_folder, get_words_from_csv, merge_var_comments, save_words_to_csv
from algorithm.cache_manager import cache_csv_info, get_cached_csv_file

from utils.lda_utils import cluster_with_topic_mat, get_cluster_number, train_lda_model
from utils.filename_convertor import raw_paths_to_unified_paths
from utils.utils import get_c_h_group_dict, get_pack_dict_level, json2cluster_dict, remap_result_dict, unmerge_result_dict, view_nx_graph_with_graphviz
from utils.fcag_utils import FCAG,read_and_embed,print_clustering_results,save_clustering_results_to_json,assign_files_to_components
from settings import INTERMIDIATE_INFO_PATH, SUPPORTED_FILE_TYPES

from experiment.sentence2matrix import generate_matrix_from_json,get_sentence_vector_sentence_transformer,get_sentence_vector


logger = logging.getLogger(__name__)

def clustering_method_dep_lda_func_weight(
    # basic info
    src_path, prj_id, prj_name, prj_lang, cache_dir, prj_result_folder,
    # shortlisted filelists
    filelist_raw_sl, filelist_unified_sl, filelist_gt_sl,
    # word info
    stopword_files, save_to_csvfile, csv_save_fn, 
    # lda
    var_weight, num_topics, alpha, eta, gamma_threshold, random_state, lda_dtype, lda_passes, lda_iterations,
    # gt
    gt_json,
    # weight
    edge_weight_dict = None,
    resolution=1.7,
    # llm
    llm_file=None,
    pattern_file=None
    ):

    USE_LDA = True
    USE_PACK = True
    USE_FUNC = True
    USE_EDGE_TYPE_WEIGHT = True


    USE_PAGERANK = True
    USE_REVERSE_PAGERANK = True
    
    USE_WEIGHT = True

    USE_ONE_SIDE_PR = True
    LDF_ONLY = False
    USE_NEW_PACK = True
    MERGE_FILE = True if prj_lang != 'java' else False
    USE_ADDITIONAL_INFO = False

    if not USE_WEIGHT:
        USE_LDA = False
        USE_FUNC = False
        USE_PACK = False
        MERGE_FILE = False
    
    KEEP_GRAPHS = False
    DEFAULT_CALL_GRAPH_WEIGHT = 0.5

    file_to_component = {}

    # region - get words 获取单词数据
    logging.info("Getting word data...")
    # try to get cached csv data 尝试获取缓存的 CSV 数据
    word_process_inputs = (prj_id)
    word_process_input_files = stopword_files
    cached_csv_fn = get_cached_csv_file(word_process_inputs, word_process_input_files, cache_dir)
    if cached_csv_fn == None:
        # no cache found 没有找到缓存
        fn_raw_all, var_words, comment_words = get_processed_words_from_prj_folder(src_path, SUPPORTED_FILE_TYPES, stopword_files)
        filenames = raw_paths_to_unified_paths(fn_raw_all, src_path)
        # save word data to csv 保存单词数据到 CSV 文件    
        if save_to_csvfile:
            save_words_to_csv(filenames, var_words, comment_words, csv_save_fn)
            #缓存 CSV 信息
            cache_csv_info(word_process_inputs, word_process_input_files, csv_save_fn, cache_dir)
    else:
        # found cached csv找到了缓存的 CSV 数据
        logging.info(f"Found cached word data for {prj_name}: {cached_csv_fn}")
        filenames, var_words, comment_words = get_words_from_csv(cached_csv_fn)
        # 如果需要保存到不同的 CSV 文件，则再次保存
        if save_to_csvfile and cached_csv_fn != csv_save_fn:
            save_words_to_csv(filenames, var_words, comment_words, csv_save_fn)
    

    # shortlist files
    ind2del = set([i for i,f in enumerate(filenames) if f not in filelist_unified_sl])
    filenames = [f for i,f in enumerate(filenames) if i not in ind2del]
    var_words = [w for i,w in enumerate(var_words) if i not in ind2del]
    comment_words = [w for i,w in enumerate(comment_words) if i not in ind2del]

    data_words = merge_var_comments(var_words, comment_words, var_weight=var_weight)
    # endregion

    # region - LDA模型训练
    if llm_file==None:
        #train model LDA 训练模型
        lda_model, id2word, corpus = train_lda_model(
            data_words=data_words,
            num_topics=num_topics,
            alpha=alpha,
            eta=eta,
            gamma_threshold=gamma_threshold,
            random_state=random_state,
            dtype=lda_dtype,
            lda_passes=lda_passes,
            lda_iter=lda_iterations,
            cache_dir=cache_dir
        )

        #get file topic vectors 获取文件主题向量
        file_topics_mat = lda_model.inference(corpus)[0]
        file_topics_mat_norm = file_topics_mat.copy()
        for i in range(len(file_topics_mat_norm)):
            file_topics_mat_norm[i] = file_topics_mat_norm[i] / np.mean(file_topics_mat_norm[i]) / num_topics * 100
            if len(set(file_topics_mat_norm[i])) == 1:
                file_topics_mat_norm[i][0] += 1e-8
        
        # #将filenames写入txt文件为json文件提供顺序，保证向量化后的矩阵和文件一一对应
        # with open('.\\res\\oodt\\filenames.txt', "w") as file:
        #     for filename in filenames:
        #         file.write(filename + "\n")

        # # 查看指定文件的主题词
        # # 假设指定文件的索引
        # doc_ids = [172, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170,171]
        #
        # # 创建一个字典来存储所有文件的前五个关键词及其概率分布
        # all_docs_top_keywords = {}
        #
        # for doc_id in doc_ids:
        #     # 获取指定文件的主题向量
        #     doc_topic_vector = file_topics_mat_norm[doc_id]
        #
        #     # 创建一个列表来存储当前文件的所有主题关键词及其概率
        #     all_keywords = []
        #     for topic_id, topic_prob in enumerate(doc_topic_vector):
        #         keywords = lda_model.show_topic(topic_id, topn=len(id2word))  # 获取所有关键词
        #         weighted_keywords = [(word, prob * topic_prob) for word, prob in keywords]
        #         all_keywords.extend(weighted_keywords)
        #
        #     # 根据概率排序所有关键词并选择前五个关键词
        #     top_keywords = sorted(all_keywords, key=lambda x: x[1], reverse=True)[:5]
        #
        #     # 将当前文件的前五个关键词及其概率分布添加到总字典中
        #     all_docs_top_keywords[doc_id] = top_keywords
        #
        # # 变量 all_docs_top_keywords 现在包含了11个文件的前五个关键词及其概率分布
        #
        # print(file_topics_mat_norm.shape)
        # filename2topic_vector = {filenames[i]:file_topics_mat_norm[i] for i in range(len(filenames))}
    else:
        # 替换为大模型生成的矩阵       
        file_topics_mat=generate_matrix_from_json(llm_file[0])
        file_topics_mat_norm = file_topics_mat.copy()
        for i in range(len(file_topics_mat_norm)):
            #file_topics_mat_norm[i] = file_topics_mat_norm[i] / np.mean(file_topics_mat_norm[i]) / num_topics * 100
            if len(set(file_topics_mat_norm[i])) == 1:
                file_topics_mat_norm[i][0] += 1e-8
    
    # region - get edge weight & gt & pack info - pack lv 10!!!
    #获取边权重，若未提供则使用默认
    if edge_weight_dict == None:
        #enre
        edge_weight_dict = {
            'Call': 0.17798518558606657, 
            'Cast': 0.7016392265114024, 
            'Contain': 4.477916968184886, 
            'Create': 1.6656515647579562, 
            'Set': 1.6656515647579562,
            'Extend': 2.1587537686435225,
            'Inherit': 2.1587537686435225,
            'ImplLink': 9.333357461737855, 
            'Implement': 7.575446074325573, 
            'Import': 8.300005412973677, #depends
            'Alias': 8.300005412973677, 
            'Parameter': 5.146578440414076, 
            'Pkg': 0.0017590006908943627, 
            'Return': 5.701817203541004, 
            'Throw': 9.053840401957205, 
            'Use': 0.5099939721025104,  #depends
            'Annotate': 1.0,
            'Modify': 1.0,
            'Typed': 1.0,
            'Override': 1.0,
            'Reflect': 1.0,
            'Except': 1.0,
            'Friends': 1.0,
            'Alias': 8.300005412973677,  # 原来存在
            'Call': 0.17798518558606657,  # Call 在两者中都存在
            'Define': 1.0,  # 没有找到对应的权重，设为 1.0
            'Except': 9.053840401957205,  # 对应原来的 'Throw'
            'Extend': 2.1587537686435225,  # Extend 在两者中都存在
            'Friend': 1.0,  # 没有找到对应的权重，设为 1.0
            'Include': 8.300005412973677,  # 对应原来的 'Includes' 或 'Import'
            'Modify': 1.0,  # 原来存在且权重为 1.0
            'Override': 1.0,  # 原来存在且权重为 1.0
            'Parameter': 5.146578440414076,  # 对应原来的 'Parameter'
            'Set': 1.6656515647579562,  # Set 在两者中都存在
            'Using': 0.5099939721025104,  # Using 在两者中都存在
            'Cast': 0.7016392265114024,  # Cast 在两者中都存在
            'Declares': 1.0,  # 没有找到对应的权重，设为 1.0
            'Addr_Parameter_Use': 1.0,  # 没有找到对应的权重，设为 1.0
            'Embed': 1.0,  # 没有找到对应的权重，设为 1.0
            'Flow_to': 1.0,  # 没有找到对应的权重，设为 1.0
            'Parameter_Use_Field_Reference': 1.0,  # 没有找到对应的权重，设为 1.0
            'Parameter_Use': 1.0,  # 没有找到对应的权重，设为 1.0
            'Macro_Use': 1.0,  # 没有找到对应的权重，设为 1.0
            'Extern_Declare': 1.0  # 没有找到对应的权重，设为 1.0
        }

        edge_weight_dict['Link'] = edge_weight_dict['ImplLink']
        for k in list(edge_weight_dict.keys()):
            edge_weight_dict[f'{k}(possible)'] = edge_weight_dict[k]*0.5
        if not USE_EDGE_TYPE_WEIGHT:
            edge_weight_dict = {k:1 for k in edge_weight_dict.keys()}
    #获取gt，如果提供了gt则将json数据转化为聚类结果格式
    if gt_json != None:
        result_gt_dict, gt_titles = json2cluster_dict(gt_json, get_titles=True)

        gt_dict = {}
        for k, v in result_gt_dict.items():
            if k in filelist_gt_sl:
                gt_dict[gt_titles[v]] = gt_dict.get(gt_titles[v], []) + [k]
        # #!!!
        # files_in_gt = []
        # for k,v in gt_dict.items():
        #     files_in_gt += v
    #获取包信息
    pack_dict = get_pack_dict_level(filelist_unified_sl, level=10)
    result_pack_dict_ori_match = remap_result_dict(pack_dict)
    # endregion

    # region - load dep graph & pack dict all - pack lv 10!!!
    #加载依赖图和目录信息
    prj_info_path = raw_paths_to_unified_paths(os.path.join(INTERMIDIATE_INFO_PATH, prj_name), '.')
    dep_file_dict = generate_and_parse_dependency_pub(src_path=src_path, prj_name=prj_name, prj_id=prj_id, result_folder=prj_info_path, prj_lang=prj_lang, cache_dir=cache_dir)
    with open(dep_file_dict['edges_dict_func'], 'rb') as f:
        edges_dict_func = pickle.load(f)
    with open(dep_file_dict['id2node_info'], 'rb') as f:
        id2node_info = pickle.load(f)
    # edges_dict_func, id2node_info = parse_depends_db_func_pub(dep_file_dict['dep_result'])

    if False:
        mdg_file_path = dep_file_dict['mdg']
        db_file_path = dep_file_dict['db']
        dep_graph_ori = mdg2graph(mdg_file_path)

    # edges_dict = parse_depends_db(db_file_path)
    #构建原始依赖图
    dep_graph_ori = parse_depends_pub_to_file_dep_graph(dep_file_dict['dep_result'])
    result_pack_dict_dep = get_pack_dict_level(list(dep_graph_ori.nodes), level=10)
    result_pack_dict_dep = remap_result_dict(result_pack_dict_dep)
    # cache?
    

    # dep_graph_ori = dep_graph.copy()
    # dep_graph_ori_match = delete_unmatched_nodes(dep_graph_ori, filelist_unified_sl)
    unfound_nodes = [f for f in filelist_unified_sl if f not in dep_graph_ori]
    logger.debug(f"unfound nodes: {len(unfound_nodes)}")
    # dep_graph_ori_match.add_nodes_from(unfound_nodes)
    dep_graph_ori.add_nodes_from(unfound_nodes)
    if USE_FUNC and not USE_PAGERANK:
        func_info = get_func_info(src_path=src_path, prj_name=prj_name, prj_id=prj_id, result_folder=prj_info_path, cache_dir=cache_dir)
    # endregion

    # region - weight dependency
    # 计算依赖权重
    dep_edge_weight_dict = {(e[0], e[1]): 0  for e in dep_graph_ori.edges}
    #计算函数调用边的权重
    if USE_FUNC:
        if USE_PAGERANK:
            FUNC_EDGE_WEIGHT_DICT = {
                'Call': 1,
                'Use': 1,
                'Return': 1,
                'Link': 1,
            }
            for k in list(FUNC_EDGE_WEIGHT_DICT.keys()):
                FUNC_EDGE_WEIGHT_DICT[f'{k}(possible)'] = FUNC_EDGE_WEIGHT_DICT[k]/2
            
            func_node_id_set = set(n for n in id2node_info if id2node_info[n]['type'] == 'function' or id2node_info[n]['type'] == 'functionimpl')
            # func_node_id_set = set(n for n in id2node_info if id2node_info[n]['type'] == 'Function' or id2node_info[n]['type'] == 'Call') #enre
            # func_node_id_set = set(n for n in id2node_info if id2node_info[n]['type'] == 'Method' or id2node_info[n]['type'] == 'Call') #enrejava
            type_node_id_set = set(n for n in id2node_info if id2node_info[n]['type'] == 'type')
            call_graph = nx.DiGraph()
            call_graph.add_nodes_from(func_node_id_set)

            call_graph_node_set = set(call_graph.nodes)
            for e_type, ed in edges_dict_func.items():
                for e,w in ed.items():
                    if e[0] in call_graph_node_set and e[1] in call_graph_node_set:
                        call_graph.add_edge(e[0], e[1], weight=FUNC_EDGE_WEIGHT_DICT.get(e_type, DEFAULT_CALL_GRAPH_WEIGHT)*w)
            func2weight = nx.pagerank(call_graph, weight='weight')
            min_val = min(func2weight.values())
            for k in func2weight:
                func2weight[k] = func2weight[k] / min_val
            reversed_call_graph = call_graph.reverse(copy=True)
            func2weight_reversed = nx.pagerank(reversed_call_graph, weight='weight')
            min_val = min(func2weight_reversed.values())
            for k in func2weight_reversed:
                func2weight_reversed[k] = func2weight_reversed[k] / min_val

            if USE_REVERSE_PAGERANK:
                func2weight = func2weight_reversed
            

            func_weight_sorted = sorted(func2weight.values(), reverse=True)
            avg_page_rank = sum(func2weight.values())/len(func2weight)
            min_page_rank = min(func2weight.values())
            # mean_func_weight = avg_page_rank
            default_func_weight = min_page_rank
            # important_pr_threshold = avg_page_rank
            important_pr_threshold = func_weight_sorted[int(len(func_weight_sorted)*0.1)]
        else: 
            sum_func_weight = 0
            len_func_weight = 0
            for f, infos in func_info.items():
                for d in infos.values():
                    for v in d.values():
                        sum_func_weight += v
                        len_func_weight += 1
            default_func_weight = sum_func_weight/len_func_weight
    else:
        logger.warning("NO FUNC WEIGHT!!!!!!!")

    # assign weight
    #分配权重给依赖边，如果两个函数属于一个文件则权重为0
    # for edge_type, ed in edges_dict_func.items():
    #     for e, w in ed.items():
    #         n1_info = id2node_info[e[0]]
    #         n2_info = id2node_info[e[1]]

    #         f1 = n1_info['file']
    #         f2 = n2_info['file']
    #         if f1 == f2:
    #             continue
    #         edge_key = (f1, f2)
    #         if edge_key not in dep_edge_weight_dict:
    #         # if False:
    #             logger.error(f'Not found in dep: {edge_type} - {edge_key}')
    #             raise
    # 报错但继续执行
    for edge_type, ed in edges_dict_func.items():
        for e, w in ed.items():
            n1_info = id2node_info[e[0]]
            n2_info = id2node_info[e[1]]

            f1 = n1_info['file']
            f2 = n2_info['file']
            if f1 == f2:
                continue  # 如果两个函数在同一个文件，跳过
            edge_key = (f1, f2)
            if edge_key not in dep_edge_weight_dict:
                logger.error(f'Not found in dep: {edge_type} - {edge_key}')
                continue  # 跳过未找到依赖边的情况
            else:
                
                if not USE_FUNC:
                    func_weight = 1
                else:
                    if USE_PAGERANK:
                        func_id_src = n1_info['func_id']
                        func_id_dst = n2_info['func_id']
                        func_weight_src = func2weight[func_id_src] if func_id_src is not None else None
                        func_weight_dst = func2weight[func_id_dst] if func_id_dst is not None else None
                        if func_weight_src == None:
                            func_weight_src = func2weight.get(e[0], default_func_weight)
                        if func_weight_dst == None:
                            func_weight_dst = func2weight.get(e[1], default_func_weight)
                        if USE_ONE_SIDE_PR:
                            if func_weight_dst > important_pr_threshold:
                                func_weight_dst = default_func_weight

                        func_weight = (func_weight_src + func_weight_dst)/2
                    else:
                        func_weights_tmp = [None, None]
                        for i, info in enumerate([n1_info, n2_info]):
                            try:
                                for k, v in func_info[info['file']][info['func']].items():
                                    if abs(int(k) - info['line']) <= 1:
                                        func_weights_tmp[i] = v
                                        break
                            except KeyError:
                                pass
                                
                        if func_weights_tmp[0] == None and func_weights_tmp[1] == None:
                            func_weight = default_func_weight
                        elif func_weights_tmp[0] == None and func_weights_tmp[1] != None:
                            func_weight = func_weights_tmp[1]
                        elif func_weights_tmp[1] == None and func_weights_tmp[0] != None:
                            func_weight = func_weights_tmp[0]
                        else:
                            func_weight = (func_weights_tmp[0]+func_weights_tmp[1])/2
                            
                try:
                    dep_edge_weight_dict[edge_key] += edge_weight_dict[edge_type] * w * func_weight
                except:
                    dep_edge_weight_dict[edge_key] += w * func_weight

    for e, w in dep_edge_weight_dict.items():
        if w == 0:
            logger.debug(e)
    # endregion
    
    # region - apply weights 创建带权重的依赖图
    logger.debug("Apply weights")
    dep_graph_weighted_dep = nx.DiGraph()
    dep_graph_weighted_dep.add_nodes_from(dep_graph_ori.nodes)
    dep_graph_weighted_dep.add_edges_from((e[0], e[1], {'weight': w}) for e, w in dep_edge_weight_dict.items())
    # endregion
    
    # region - merge files合并同一文件中的function
    if MERGE_FILE and USE_EDGE_TYPE_WEIGHT:
        # logger.info("merge files")
        if 'Implement' in edges_dict_func:
            impl_edges = [(id2node_info[e[0]]['file'], id2node_info[e[1]]['file'], {'weight': w, 'label': w}) for e, w in edges_dict_func['Implement'].items()]
        else:
            impl_edges = []
        res_merge_dict, merged2unmerged_dict, unmerged2merged_dict = get_impl_link_merge_dict(impl_edges, filelist_unified_sl, return_mapping=True)
    else:
        merged2unmerged_dict = unmerged2merged_dict = {}
        logger.warning("NO MERGE!!!!!!!")
    # endregion

    ###查看指定边权重
    # 指定的文件列表
    # valid_files = [
    #     'alias.c', 'shell.c', 'command.h', 'lib/malloc/malloc.c',
    #     'lib/malloc/imalloc.h', 'lib/malloc/watch.c',
    #     'lib/sh/strerror.c', 'lib/sh/stringlist.c'
    # ]
    # # # 新的字典，保存两端都在valid_files范围内的边
    # filtered_edges = {}
    # # # 遍历edges字典
    # for node1 in valid_files:
    #     for node2 in valid_files:
    #         # 确保 node1 和 node2 是 dep_graph_weighted_dep 的有效索引
    #         if node1 in dep_graph_weighted_dep and node2 in dep_graph_weighted_dep[node1]:
    #             # 确保 node1 和 node2 不相等，并且边的权重不为 0
    #             if node2 != node1 and dep_graph_weighted_dep[node1][node2]['weight'] != 0:
    #                 filtered_edges[(node1, node2)] = dep_graph_weighted_dep[node1][node2]['weight']
    #         else:
    #             # 如果 node1 或 node2 不是索引，则跳过
    #             continue
    ###

    # # region - community detection 社区检测

    dep_graph_ori_match = delete_unmatched_nodes(dep_graph_ori, filelist_unified_sl, copy=True)
    dep_graph_ori_match.add_nodes_from(unfound_nodes)
    dep_graph_ori_match_merged = merge_files_in_graph(dep_graph_ori_match, merged2unmerged_dict, unmerged2merged_dict)
    merged_dict = community_detection(dep_graph_ori_match_merged, None, weight_keyword='weight',resolution=resolution)
    result_dep_dict = unmerge_result_dict(merged_dict, merged2unmerged_dict)

    # # endregion
    
    # region - discrepency 比较聚类结果
    if USE_LDA:
        num_cluster = max(result_dep_dict.values())+1
        result = cluster_with_topic_mat(file_topics_mat_norm, num_cluster, cluster_method = 'hierarchy')
        result_lda_dict = dict(zip(filenames, result)) 
    else:
        result_lda_dict = result_dep_dict
        
    metrics_similarity_dep_lda = compare_two_cluster_results(result_dep_dict, result_lda_dict)
    metrics_similarity_dep_pkg = compare_two_cluster_results(result_dep_dict, result_pack_dict_ori_match)
    metrics_similarity_pkg_lda = compare_two_cluster_results(result_lda_dict, result_pack_dict_ori_match)
    # endregion
    
    # -------------------------------------------
    select_metric = 'a2a_adj' #选择相似性度量方法
    max_metric = max(metrics_similarity_dep_lda[select_metric], metrics_similarity_dep_pkg[select_metric], metrics_similarity_pkg_lda[select_metric])
    
    if USE_FUNC:
        LDA_WEIGHT = (metrics_similarity_dep_lda[select_metric]/max_metric)**2
        edge_weight_dict['Pkg'] = (1- min(metrics_similarity_dep_pkg[select_metric]/max_metric, 1)) **2
    else:    
        LDA_WEIGHT = metrics_similarity_dep_lda[select_metric]
        edge_weight_dict['Pkg'] = 1 - metrics_similarity_dep_pkg[select_metric]
    
    resolution_clustering = resolution


    # region - weight lda
    if LDF_ONLY:
        dep_edge_weight_dict = {}
        dep_weight_mean = 1
    else:
        dep_weight_mean = sum(dep_edge_weight_dict.values())/len(dep_edge_weight_dict) if dep_edge_weight_dict else 1
    if USE_LDA:
        print("len(filenames):",len(filenames))
        topic_corr_mat = np.corrcoef(file_topics_mat_norm)
        for i in range(len(filenames)-5):
            for j in range(i+1, len(filenames)-5):
                f1 = filenames[i]
                f2 = filenames[j]
                corr = topic_corr_mat[i][j]
                for e in [(f1, f2), (f2, f1)]:
                    if e in dep_edge_weight_dict:
                        lda_coef = 1 + math.sqrt(abs(corr*2))*np.sign(corr)* LDA_WEIGHT
                        dep_edge_weight_dict[e] *= max(lda_coef, 0) 
                    elif corr >= 0.5:
                        dep_edge_weight_dict[e] = corr*dep_weight_mean*LDA_WEIGHT
    else:
        logger.warning("NO LDA!!!!!!")
    # endregion

    # region - weight pack (might apply weight)
    if USE_PACK:
        # get pack result
        if USE_NEW_PACK:
            
            def get_pack_result_by_max_modularity(dep_graph, existing_partition=[], curr_files=None, curr_folder = ''):
                if curr_files == None:
                    curr_files = list(dep_graph.nodes())
                if len(curr_folder) != 0 and curr_folder[-1] != '/':
                    curr_folder = curr_folder + '/'
                # a = get_pack_dict_level(curr_files, level=1, return_type=1)
                curr_pack_names = [f[len(curr_folder):].split('/')[0] if '/' in f[len(curr_folder):] else '' for f in curr_files]
                curr_pack_dict = {}
                for i, p in enumerate(curr_pack_names):
                    curr_pack_dict[p] = curr_pack_dict.get(p,[]) + [curr_files[i]]
                
                if len(curr_pack_dict) == 1 and '' in curr_pack_dict:
                    return [curr_files]
                if len(curr_pack_dict) <= 1:
                    mod_full = mod_split = -1
                else:
                    try:
                        mod_split = nx.algorithms.community.quality.modularity(
                            dep_graph, 
                            existing_partition + list(curr_pack_dict.values()), 
                            weight='weight', resolution=1)
                        mod_full = nx.algorithms.community.quality.modularity(
                            dep_graph, 
                            existing_partition + [curr_files], 
                            weight='weight', resolution=1)
                    except:
                        logger.warning(f"modularity error: {curr_files}")
                        mod_full = mod_split = -1
                # split_mod = nx.algorithms.community.quality.modularity(
                #     dep_graph.subgraph(curr_files), 
                #     curr_pack_dict.values(), 
                #     weight='weight', resolution=1)

                if mod_full > mod_split:
                    return [curr_files]
                else:
                    ret = []
                    for pack4split in curr_pack_dict:
                        if pack4split == '':
                            ret += [curr_pack_dict[pack4split]]
                            continue
                        next_files = curr_pack_dict[pack4split]
                        next_existing_partition = existing_partition + [v for k,v in curr_pack_dict.items() if k!=pack4split]
                        next_folder = f'{curr_folder}{pack4split}/' if curr_folder != '' else f'{pack4split}/'
                        ret += get_pack_result_by_max_modularity(dep_graph, next_existing_partition, next_files, next_folder)
                    return ret
                    
            pack_lists = get_pack_result_by_max_modularity(dep_graph_weighted_dep)
            result_pack_dict = {}
            for i, fl in enumerate(pack_lists):
                for f in fl:
                    if f in filelist_unified_sl:
                        result_pack_dict[f] = i
            for f in filelist_unified_sl:
                if f not in result_pack_dict:
                    result_pack_dict[f] = -1
        else:
            result_pack_dict = result_pack_dict_ori_match
            pack_lists = {}
            for f, v in result_pack_dict_dep.items():
                pack_lists[v] = pack_lists.get(v, []) + [f]
            pack_lists = list(pack_lists.values())
            logger.info("use old pack")
        
        pack_modularity = nx.algorithms.community.quality.modularity(dep_graph_weighted_dep, pack_lists, weight='weight', resolution=1)
        dep_modularity = nx.algorithms.community.quality.modularity(
            dep_graph_weighted_dep, 
            community_detection(dep_graph_weighted_dep, resolution=1, weight_keyword='weight', return_communities=True), 
            weight='weight', resolution=1
        )

        pack_modularity = int(pack_modularity*10**12)/10**12
        dep_modularity = int(dep_modularity*10**12)/10**12


        dep_modularity = max(min(dep_modularity, 1), 0)
        pack_modularity = max(min(pack_modularity, 1), 0)   #改成1试一下
        pack_weight = 1-(pack_modularity*(1-dep_modularity))**0.5
        pack_weight *= edge_weight_dict['Pkg']

        for k in dep_edge_weight_dict:
            if k[0] in result_pack_dict and k[1] in result_pack_dict and result_pack_dict[k[0]] != result_pack_dict[k[1]]:
                dep_edge_weight_dict[k] *= pack_weight
    else:
        logger.warning("NO PACK!!!!!!")
        pack_weight = None
    # endregion
    
    # region - apply weights
    if USE_WEIGHT:    
        dep_graph_weighted_dep_pack_lda = nx.DiGraph()
        dep_graph_weighted_dep_pack_lda.add_nodes_from(dep_graph_ori.nodes)
        dep_graph_weighted_dep_pack_lda.add_edges_from((*e, {'weight':dep_edge_weight_dict[e]}) for e in dep_edge_weight_dict)
    else:
        dep_graph_weighted_dep_pack_lda = dep_graph_ori.copy()
        dep_graph_weighted_dep_pack_lda.remove_edges_from(e for i, e in enumerate(dep_graph_ori.edges) if i % 4 == 0)

    # endregion

    # # region - cluster
    if KEEP_GRAPHS:
        dep_graph_final = dep_graph_weighted_dep_pack_lda.copy()
    else:
        dep_graph_final = dep_graph_weighted_dep_pack_lda

    dep_graph_final = delete_unmatched_nodes(dep_graph_final, filelist_unified_sl, copy=False)
    dep_graph_final.add_nodes_from(f for f in filelist_unified_sl if f not in dep_graph_final)

    if pattern_file == None:
        # 不进行锚点聚类在全局图上进行合并
        dep_graph_final_merged = merge_files_in_graph(dep_graph_final, merged2unmerged_dict, unmerged2merged_dict, copy=False)
        merged_dict = community_detection(dep_graph_final_merged, None, weight_keyword='weight', resolution=resolution_clustering)
        result_dict = unmerge_result_dict(merged_dict, merged2unmerged_dict)
    else:
        #————————————————————————————————锚点聚类————————————————————————————————————#
        dep_graph_final_merged = dep_graph_final
        # 从JSON文件中读取数据
        json_file_components = pattern_file[0]
        # json_file_components = '.\\architecture_pattern\\layered.json'
        json_file_files = llm_file[0]

        # 读取数据并生成锚点和文件向量
        file_vectors, labels, component_names, file_names, component_vectors = read_and_embed(json_file_components, json_file_files)

        # 执行FCAG聚类
        print("开始执行FCAG聚类...")
        # 调整 FCAG 调用，传递 `file_names`，并接收 `anchor_indices`
        y, label, U, iter_num, obj, anchor_vectors, anchor_indices = FCAG(
            component_vectors, 
            file_vectors, 
            component_count=len(component_names), 
            file_names=file_names,          # 传递 file_names
            labels=labels,                  # 传递 labels
            anchors_per_component=3, 
            max_iter=10, 
            tol=1e-3, 
            alpha=0.1
        )

        # 根据锚点和组件的相似度进行归类
        print("开始将锚点和文件归类到组件...")
        clusters = assign_files_to_components(
            component_names, 
            file_names, 
            anchor_vectors, 
            component_vectors, 
            label, 
            y
        )
        # 打印聚类结果
        for component, files in clusters.items():
            for file in files:
                file_to_component[file] = component
        # 保存聚类结果到JSON文件
        # save_clustering_results_to_json(clusters, '.\\res\\oodt')

        ###查看指定节点权重
        # for node1 in valid_files:
        #     for node2 in valid_files:
        #         if node2!=node1 and dep_graph_final[node1][node2]['weight']!=0:
        #             filtered_edges[(node1, node2)] = dep_graph_final[node1][node2]['weight']
        # # #——————————————————————————方法1：根据FCAG结果调整权重后聚类——————————————————————————
        # 遍历每个组件名称，调整同一组件之间文件的边权重
        for component_name, cluster_files in clusters.items():
            for i in range(len(cluster_files)):
                for j in range(i + 1, len(cluster_files)):
                    if dep_graph_final.has_edge(cluster_files[i], cluster_files[j]):
                        dep_graph_final[cluster_files[i]][cluster_files[j]]['weight'] *= 3
            
        # 在全局图上进行合并
        ###查看指定节点权重
        # for node1 in valid_files:
        #     for node2 in valid_files:
        #         if node2!=node1 and dep_graph_final[node1][node2]['weight']!=0:
        #             filtered_edges[(node1, node2)] = dep_graph_final[node1][node2]['weight']

        dep_graph_final_merged = merge_files_in_graph(dep_graph_final, merged2unmerged_dict, unmerged2merged_dict, copy=False)
        
        # 在合并后的图上进行社区检测
        merged_dict = community_detection(dep_graph_final_merged, None, weight_keyword='weight', resolution=resolution_clustering)
        
        # 在全局图上进行解合并
        result_dict = unmerge_result_dict(merged_dict, merged2unmerged_dict)

        # # #——————————————————————————方法2：根据FCAG结果划分子图后聚类——————————————————————————
        # # # 初始化结果字典和全局聚类编号计数器
        # # result_dict = {}
        # # global_cluster_id = 0

        # # #遍历每个组件名称并进行聚类
        # # for component_name in set(y):
        # #     cluster_files = [file_names[i] for i in range(len(y)) if y[i] == component_name]
        # #     subgraph = dep_graph_final_merged.subgraph(cluster_files).copy()
        # #     # 仅合并包含在子图中的节点
        # #     # 构造 filtered_unmerged2merged_dict
        # #     filtered_unmerged2merged_dict = {}
        # #     for k, v in unmerged2merged_dict.items():
        # #         if v in subgraph:
        # #             filtered_unmerged2merged_dict[k] = v
        # #         elif any(node in subgraph for node in merged2unmerged_dict[v]):
        # #             filtered_unmerged2merged_dict[k] = v
        # #     # 构造 filtered_merged2unmerged_dict
        # #     filtered_merged2unmerged_dict = {}
        # #     for k, v in filtered_unmerged2merged_dict.items():
        # #         if v not in filtered_merged2unmerged_dict:
        # #             filtered_merged2unmerged_dict[v] = []
        # #         if k in subgraph:
        # #             filtered_merged2unmerged_dict[v].append(k)
            
        # #     subgraph_merged = merge_files_in_graph(subgraph, filtered_merged2unmerged_dict, filtered_unmerged2merged_dict, copy=False)
            
        # #     # 在子图上进行社区检测
        # #     merged_dict = community_detection(subgraph_merged, None, weight_keyword='weight', resolution=resolution_clustering)
            
        # #     # 在全局图上进行解合并
        # #     unmerged_result = unmerge_result_dict(merged_dict, filtered_merged2unmerged_dict)
            
        # #     # 重新编号子图的聚类结果
        # #     local_to_global_mapping = {}
        # #     for local_cluster_id in set(unmerged_result.values()):
        # #         local_to_global_mapping[local_cluster_id] = global_cluster_id
        # #         global_cluster_id += 1

        # #     # 更新聚类结果字典，使用全局编号
        # #     for file_name, local_cluster_id in unmerged_result.items():
        # #         result_dict[file_name] = local_to_global_mapping[local_cluster_id]
        # #     # endregion

        #组件-cluster包含关系
        # def assign_clusters_to_components(clusters, result_dict, component_names):
        #     cluster_to_component = {}

        #     # 遍历每个簇
        #     for cluster_num, cluster_files in clusters.items():
        #         # 统计该簇中文件所属的组件
        #         component_count = Counter()

        #         for file in cluster_files:
        #             # 使用 result_dict 找到该文件的簇号，并确定该簇所属的组件
        #             cluster_id = result_dict.get(file)
        #             if cluster_id is not None:
        #                 # 根据 result_dict 查找到文件对应的簇，并更新对应簇所属的组件
        #                 for component_name in component_names:
        #                     if file in clusters.get(component_name, []):
        #                         component_count[component_name] += 1
        #                         break

        #         # 找到出现最多的组件
        #         if component_count:
        #             most_common_component = component_count.most_common(1)[0][0]
        #             cluster_to_component[cluster_num] = most_common_component

        #     return cluster_to_component

        # # 保存结果到指定格式的JSON文件
        # def save_clustering_to_json(cluster_to_component, clusters, output_file):
        #     structure = []
            
        #     # 遍历每个组件，整理嵌套模块
        #     for component, cluster_ids in cluster_to_component.items():
        #         nested_modules = [{"@type": "module", "number": cluster_id} for cluster_id in cluster_ids]
        #         structure.append({
        #             "@type": "component",
        #             "name": component,
        #             "nested": nested_modules
        #         })
            
        #     # 构建最终JSON结构
        #     result = {
        #         "@schemaVersion": "1.0",
        #         "name": "pattern",
        #         "structure": structure
        #     }
            
        #     # 写入JSON文件
        #     with open(output_file, 'w') as f:
        #         json.dump(result, f, indent=4)

        # # 执行新的聚类结果分配逻辑
        # print("根据聚类结果，将簇归类到组件...")
        # cluster_to_component = assign_clusters_to_components(clusters, result_dict,component_names)

        # # 保存最终聚类结果到JSON文件
        # output_file = 'D:\\lda_demoGPT\\res\\oodt\\cluster_component_result.json'
        # save_clustering_to_json(cluster_to_component, clusters, output_file)

        # print(f"聚类结果已保存到 {output_file}")
    #end
    
    #生成cluster依赖关系
    def generate_cluster_graph_with_files(result_dict, dep_graph_final):
        # 创建一个字典来存储cluster之间的依赖关系及详细文件信息
        cluster_edges = defaultdict(lambda: defaultdict(lambda: {"weight": 0, "details": []}))

        # 遍历原始图中的每一条边
        for source, target, data in dep_graph_final.edges(data=True):
            # 在result_dict中找到source和target对应的簇编号
            cluster_source = result_dict.get(source)
            cluster_target = result_dict.get(target)

            # 确保source和target有对应的簇编号，并且不是同一个簇
            if cluster_source is not None and cluster_target is not None and cluster_source != cluster_target:
                # 增加簇之间的边权重
                cluster_edges[cluster_source][cluster_target]["weight"] += 1
                # 记录详细的文件依赖信息
                cluster_edges[cluster_source][cluster_target]["details"].append({
                    "from_file": source,
                    "to_file": target
                })

        # 构建JSON结构
        cluster_graph = {
            "nodes": [{"id": cluster} for cluster in set(result_dict.values())],
            "edges": []
        }

        # 将聚类间的边信息填入JSON结构中
        for source_cluster, targets in cluster_edges.items():
            for target_cluster, edge_info in targets.items():
                cluster_graph["edges"].append({
                    "source": source_cluster,
                    "target": target_cluster,
                    "weight": edge_info["weight"],
                    "details": edge_info["details"]
                })

        return cluster_graph

    # 假设 result_dict 是原始文件与聚类后的cluster的映射关系
    # dep_graph_final 是原始图的结构，包含文件之间的依赖关系
    cluster_graph = generate_cluster_graph_with_files(result_dict, dep_graph_final)

    # 将结果保存为JSON文件
    # output_json_file = '.\\res\\skia-m131\\cluster_dep2.json'
    # with open(output_json_file, 'w') as f:
    #     json.dump(cluster_graph, f, indent=4)

    # print(f"Cluster graph with file details saved to {output_json_file}")
    # endregion

    # begin: 聚类结果和组件的对应关系
    # def assign_clusters_to_components(clusters, result_dict):
    # # 初始化每个簇的组件计数
    #     cluster_component_count = defaultdict(lambda: defaultdict(int))

    #     # 统计每个簇中每个组件的文件数量
    #     for file_name, cluster_id in result_dict.items():
    #         for component_name, component_files in clusters.items():
    #             if file_name in component_files:
    #                 cluster_component_count[cluster_id][component_name] += 1

    #     # 确定每个簇的主要组件
    #     cluster_to_component = {}
    #     for cluster_id, component_count in cluster_component_count.items():
    #         # 找到文件数量最多的组件
    #         main_component = max(component_count.items(), key=lambda x: x[1])[0]
    #         cluster_to_component[cluster_id] = main_component

    #     # 构建组件和簇的最终结构
    #     component_structure = defaultdict(list)
    #     for cluster_id, component_name in cluster_to_component.items():
    #         component_structure[component_name].append(cluster_id)

    #     # 转换为JSON格式
    #     json_structure = []
    #     for component_name, cluster_ids in component_structure.items():
    #         component_entry = {
    #             "@type": "component",
    #             "name": component_name,
    #             "nested": [{"@type": "cluster", "No.": str(cid)} for cid in cluster_ids]
    #         }
    #         json_structure.append(component_entry)

    #     return {
    #         "@schemaVersion": "1.0",
    #         "name": "clustering",
    #         "structure": json_structure
    #     }

    # # 调用示例
    # final_structure = assign_clusters_to_components(clusters, result_dict)

    # # 打印并保存结果
    # import json
    # with open('cluster_component_result.json', 'w') as f:
    #     json.dump(final_structure, f, indent=4)

    # print(json.dumps(final_structure, indent=4))
    # end

    # region - eval
    if USE_ADDITIONAL_INFO:
        try:
            from utils.graph_utils import get_all_bunch_mqs, get_modx_mq
            basic_mq_final, turbo_mq_final, turbo_mq_weighted_final = get_all_bunch_mqs(
                dep_graph_final,
                result_dict
            )
            modx_mq = get_modx_mq(
                dep_graph_final,
                result_dict
            )
            basic_mq_ori, turbo_mq_ori, turbo_mq_weighted_ori = get_all_bunch_mqs(
                dep_graph_ori_match,
                result_dict
            )
            assert turbo_mq_ori == turbo_mq_weighted_ori

            graph_communities = {}
            for k,v in merged_dict.items():
                graph_communities[str(v)] = graph_communities.get(str(v), []) + (merged2unmerged_dict[k] if k in merged2unmerged_dict else [k])
            graph_modularity = nx.algorithms.community.quality.modularity(dep_graph_ori_match, graph_communities.values(), weight='weight', resolution=1)
            graph_modularity_final = nx.algorithms.community.quality.modularity(dep_graph_final, graph_communities.values(), weight='weight', resolution=1)
            
            pack_communities = {}
            for k,v in result_pack_dict.items():
                pack_communities[str(v)] = pack_communities.get(str(v), []) + [k]
            
            pack_graph_modularity = nx.algorithms.community.quality.modularity(dep_graph_ori_match, pack_communities.values(), weight='weight', resolution=1)

            additional_info = {
                # 'gt_modularity': gt_modularity,
                'graph_modularity': graph_modularity,
                'graph_modularity_final': graph_modularity_final,
                # 'merged_graph_modularity': merged_graph_modularity,
                'pack_modularity': pack_graph_modularity,
                'discrepency_dep_lda': metrics_similarity_dep_lda['ARI'],
                'discrepency_dep_pkg': metrics_similarity_dep_pkg['ARI'],
                'discrepency_pkg_lda': metrics_similarity_pkg_lda['ARI'],


                'basic_mq_final': basic_mq_final,
                'turbo_mq_final': turbo_mq_final,
                'turbo_mq_weighted_final': turbo_mq_weighted_final,
                'basic_mq_ori': basic_mq_ori,
                'turbo_mq_ori': turbo_mq_ori,
                'modx_mq': modx_mq,
                
            }
            
        except Exception as e:
            additional_info = {}
            err_info = str(e)[:100]+'......' if len(str(e)) > 100 else str(e)
            logger.error(err_info)
            pass
    else:
        additional_info = {}
    
    # endregion
    
    # 打印最终结果中形成的簇的数量
    num_clusters_final = len(set(result_dict.values()))
    print(f"最终结果中形成的簇的数量：{num_clusters_final}")

    return result_dict,file_to_component,additional_info
