import json
import os
import time
import argparse
import sys
from typing import List
import numpy as np
from shutil import copyfile
from sklearn.manifold import TSNE
import traceback

from algorithm.clustering_methods import *
from utils.plot_result import plot_two_result_list
from algorithm.comparing_clusters import compare_two_cluster_results
from algorithm.cache_manager import get_prj_id
from algorithm.project_file_loader import get_raw_and_unified_and_gt_filenames_from_prj_folder
from utils.utils import get_intersect_lists_from_two_dict, json2cluster_dict, cluster2json, is_csv_file, \
    get_pack_dict_from_filelist, str2bool, get_prj_lang, post_process_python, post_process_python2, post_process, \
    post_process_python3
from settings import CACHE_PATH, SUPPORTED_FILE_TYPES,DEFAULT_STOP_WORD_LIST

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(filename)s line: %(lineno)d] %(levelname)s - %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]")
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.WARNING)
logging.getLogger('gensim').setLevel(logging.WARNING)
logging.getLogger('utils.utils').setLevel(logging.INFO)
logging.getLogger('project_file_manager.filename_convertor').setLevel(logging.INFO)



#LDA
DEFAULT_NUM_TOPICS = 100
DEFAULT_NUM_CLUSTER = 'auto'
DEFAULT_NUM_LDA_PASS = 50
DEFAULT_LDA_ITER = 50
DEFAULT_VAR_WORD_WEIGHTS = 3

def cluster_project(
    data_paths:List[str], 
    gt_json_paths:List[str]=None, 
    result_folder_name:str=None, 
    cache_dir = CACHE_PATH,
    # get word from project
    csv_save_fns:List[str]=None, 
    save_to_csvfile:bool=True,
    var_weight:float=DEFAULT_VAR_WORD_WEIGHTS,
    stopword_files=DEFAULT_STOP_WORD_LIST,
    # LDA parameters
    num_cluster:int=None,
    num_topics:int=DEFAULT_NUM_TOPICS,
    lda_passes:int = DEFAULT_NUM_LDA_PASS,
    lda_iterations:int = DEFAULT_LDA_ITER,
    alpha:float=None,
    eta:float=None,
    gamma_threshold:float = 0.001,
    random_state:int = 101,
    lda_dtype:np.dtype = np.float64,
    # clustering
    min_cluster_size:int = 2,
    cluster_method:str = 'hierarchy',
    resolution:float = 1.7,
    # figure 
    generate_figures:bool = True,
    fig_add_texts=[True],
    # llm parameters
    llm_file:List[str]=None,
    pattern_file:List[str]=None
    ):

    if len(data_paths) == 1 and data_paths[0].endswith('.txt'):
        with open(data_paths[0], 'r') as f:
            for l in f:
                l = l.strip()
                if l:
                    data_paths.append(l)
        data_paths = data_paths[1:]
    start_time_str = time.strftime("%Y%m%d_%H-%M-%S",time.localtime(int(time.time())))
    # get project names
    prj_names = []
    for p in data_paths:
        if is_csv_file(p):
            raise Exception("Please input the root path of the target project!")
        prj_names.append(os.path.basename(p))
    
    #---------- processing inputs ---------- 
    num_prj = len(data_paths)
    if alpha == None:
        alpha = [50 / num_topics] * num_topics

    if result_folder_name == None: 
        if len(prj_names) < 10:
            result_foldername_suffix = '_'.join(prj_names)
        else:
            result_foldername_suffix = str(len(prj_names))
        result_folder_name = "results/" + result_foldername_suffix

    if gt_json_paths == None:
        gt_json_paths = [None] * num_prj
    elif len(gt_json_paths) != num_prj:
        raise Exception("Number of gt_json_paths does not match the number of projects!")

    if csv_save_fns == None:
        csv_save_fns = [f"extracted_info/{p}/{p}.csv" for p in prj_names]
    elif len(csv_save_fns) != num_prj:
            raise Exception("Number of csv names does not match the number of projects!")

    if len(fig_add_texts) == 1:
        fig_add_texts = fig_add_texts * num_prj
    elif len(fig_add_texts) != num_prj:
        raise Exception("Number of fig_add_texts does not match the number of projects!")
        
    #---------- processing the projects ---------- 
    metrics_all = {}
    success = False
    for prj_ind in range(num_prj):
        try:
            prj_start_time = time.time()
            data_path = data_paths[prj_ind]
            csv_save_fn = csv_save_fns[prj_ind]
            gt_json_path = gt_json_paths[prj_ind]
            fig_add_text = fig_add_texts[prj_ind]
            prj_name = prj_names[prj_ind]
            logging.info(f"Processing project: {prj_name} ({data_path})")

            #---------- get basic info ----------
            prj_id = get_prj_id(data_path, SUPPORTED_FILE_TYPES)
            prj_lang = get_prj_lang(data_path)
            logger.info(f"{prj_name} lang: {prj_lang}")
            prj_result_folder = os.path.join(result_folder_name)
            # get all of the file names in the prject folder
            # filelist_raw_full, filelist_unified_full, filelist_gt_format_full = get_raw_and_unified_and_gt_filenames_from_prj_folder(data_path, None, supported_exts=SUPPORTED_FILE_TYPES, prj_lang=prj_lang)
            
            ## filenames shortlisted by ground truth
            # filelist_raw_sl, filelist_unified_sl, filelist_gt_sl = get_raw_and_unified_and_gt_filenames_from_prj_folder(data_path, gt_json_path, supported_exts=SUPPORTED_FILE_TYPES, prj_lang=prj_lang)
            filelist_raw_sl, filelist_unified_sl, filelist_gt_sl = get_raw_and_unified_and_gt_filenames_from_prj_folder(data_path, gt_json_path, supported_exts=SUPPORTED_FILE_TYPES, prj_lang='c')
            
            
            #---------- get clustering result ----------
            
            cluster_result,file_to_component,additional_info = clustering_method_dep_lda_func_weight(
                data_path, prj_id=prj_id, prj_name=prj_name, prj_lang=prj_lang, cache_dir=cache_dir, prj_result_folder=prj_result_folder,
                filelist_raw_sl=filelist_raw_sl, filelist_unified_sl=filelist_unified_sl, filelist_gt_sl=filelist_gt_sl,
                stopword_files=stopword_files, save_to_csvfile=save_to_csvfile, csv_save_fn=csv_save_fn, 
                var_weight=var_weight, num_topics=num_topics, alpha=alpha, eta=eta,gamma_threshold=gamma_threshold, random_state=random_state, lda_dtype=lda_dtype, lda_passes=lda_passes, lda_iterations=lda_iterations,
                gt_json=gt_json_path, resolution=resolution,llm_file=llm_file,pattern_file=pattern_file
            )

            if type(cluster_result) == tuple:
                result_dict = cluster_result[0]
                additional_info = cluster_result[1]
            else:
                result_dict = cluster_result
                additional_info = {}

            # !!!
            # additional_info = {}
            # result_dict = {f:0 for f in filelist_unified_sl}
            # assert sorted(list(result_dict.keys())) == sorted(filelist_unified_sl)

            
            
            #---------- get result data ----------
            result_pack_dict, path_names = get_pack_dict_from_filelist(filelist_unified_sl, get_path_names=True)

            # post process python demo
            if prj_lang == 'python':
                result_dict = post_process_python(result_dict=result_dict, result_pack_dict=result_pack_dict,
                                                  data_path=data_path)

            if gt_json_path != None:
                # parse gt json file
                result_gt_dict, cluster_gt_titles = json2cluster_dict(gt_json_path, get_titles=True)
                # change the name style
                gt2unified = dict(zip(filelist_gt_sl, filelist_unified_sl))
                result_gt_dict = {gt2unified[gt]:res for gt, res in result_gt_dict.items() if gt in gt2unified}

                # get metric results
                metrics_result_dict = compare_two_cluster_results(result_dict, result_gt_dict)
                #print("result_dict:",result_dict)
                #print("result_gt_dict:",result_gt_dict)
                for k, v in additional_info.items():
                    metrics_result_dict[k] = v
                metrics_all[prj_name] = metrics_result_dict
                # plot
                filelist_intersect, result_intersect, result_gt_intersect =  get_intersect_lists_from_two_dict(result_dict, result_gt_dict)
            elif additional_info:
                metrics_all[prj_name] = additional_info

            # Step 1: Initialize cluster_component_count to track file counts for each component per cluster
            cluster_component_count = defaultdict(lambda: defaultdict(int))

            # Step 2: Fill cluster_component_count with file-to-component mapping
            file_to_component = {file.replace("\\", "/"): component for file, component in file_to_component.items()}
            cluster_result = {file.replace("\\", "/"): cluster for file, cluster in cluster_result.items()}
            for file, cluster in cluster_result.items():
                if file in file_to_component:
                    component = file_to_component[file]
                    cluster_component_count[cluster][component] += 1

            # Step 3: Map each cluster to the component with the most files
            cluster_to_component = defaultdict(list)

            for cluster, component_count in cluster_component_count.items():
                if component_count:  # Only process if there are components mapped to this cluster
                    main_component = max(component_count.items(), key=lambda x: x[1])[0]
                    cluster_to_component[main_component].append(cluster)

            print("————————————————————————————————————————————\n", cluster_to_component)

            # 将 cluster 和组件的映射关系转换为所需的JSON格式
            output_data = {
                "@schemaVersion": "1.0",
                "name": "clustering",
                "structure": []
            }

            for component, clusters in cluster_to_component.items():
                component_entry = {
                    "@type": "component",
                    "name": component,
                    "nested": []
                }
                for cluster in clusters:
                    component_entry["nested"].append({
                        "@type": "cluster",
                        "No.": cluster
                    })
                output_data["structure"].append(component_entry)

            # ---------- save results ----------
            # make result dir
            os.makedirs(result_folder_name, exist_ok=True)
            os.makedirs(prj_result_folder, exist_ok=True)
            # 输出到JSON文件
            with open(os.path.join(prj_result_folder, f"{prj_name}_cluster_component_mapping.json"), 'w') as json_file:
                json.dump(output_data, json_file, indent=2)

            print("JSON file 'cluster_component_mapping.json' has been created.")

            if gt_json_path != None:
                with open(os.path.join(prj_result_folder, "metrics_our_to_GT.json"), 'w', newline="") as fp:
                    json.dump(metrics_result_dict, fp, indent=4)
                # save to both prj folder and root result folder
                if generate_figures:
                    logger.info('Plotting figures...')

                    plot_two_result_list(result_intersect, result_gt_intersect, cluster_gt_titles, os.path.join(prj_result_folder, 'comparing_with_gt.png'), show_fig=False, add_text=fig_add_text, fig_title=prj_name, add_boarder = True)
                    
                    copyfile(src=os.path.join(prj_result_folder, 'comparing_with_gt.png'), dst=os.path.join(result_folder_name, f'comparing_with_gt_{prj_name}.png'))
                
                # # 读取 GT 文件
                # file_to_module_path = gt_json_path  # 替换为实际的文件路径
                # component_to_module_path = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\pattern_gt\\bash-4.2-pattern-GT.json'  #待修改

                # with open(file_to_module_path, 'r', encoding='utf-8') as f:
                #     file_to_module_gt = json.load(f)

                # with open(component_to_module_path, 'r', encoding='utf-8') as f:
                #     component_to_module_gt = json.load(f)

                # # 创建模块到文件的映射
                # module_to_files = defaultdict(list)
                # for module in file_to_module_gt['structure']:
                #     module_name = module['name']
                #     for item in module['nested']:
                #         if item['@type'] == 'item':
                #             module_to_files[module_name].append(item['name'])

                # # 创建组件到模块的映射
                # component_to_modules = {}
                # for component in component_to_module_gt['structure']:
                #     component_name = component['name']
                #     modules = [item['name'] for item in component['nested'] if item['@type'] == 'module']
                #     component_to_modules[component_name] = modules

                # # 创建文件到组件的GT映射
                # file_to_component_gt = {}
                # for component, modules in component_to_modules.items():
                #     for module in modules:
                #         for file in module_to_files.get(module, []):
                #             file_to_component_gt[file] = component

                # # 计算准确率
                # component_file_counts = defaultdict(int)
                # correct_counts = defaultdict(int)

                # for file, predicted_component in file_to_component.items():
                #     component_file_counts[predicted_component] += 1
                #     if file_to_component_gt.get(file) == predicted_component:
                #         correct_counts[predicted_component] += 1

                # accuracy = {}
                # for component, total in component_file_counts.items():
                #     correct = correct_counts[component]
                #     accuracy[component] = round((correct / total) * 100, 2)

                # # 打印结果
                # for component, acc in accuracy.items():
                #     print(f'{component}: {acc}%')
                
            elif additional_info != {}:
                with open(os.path.join(prj_result_folder, "metrics.json"), 'w', newline="") as fp:
                    json.dump(additional_info, fp, indent=4)
                
                    
            dict4json = cluster2json(list(result_dict.keys()), list(result_dict.values()))
            with open(os.path.join(prj_result_folder, "cluster_result.json"), 'w') as fp:
                json.dump(dict4json, fp, indent=4)

            dict4json_pkg = cluster2json(list(result_pack_dict.keys()), list(result_pack_dict.values()), path_names)
            with open(os.path.join(prj_result_folder, "cluster_result_pkg.json"), 'w') as fp:
                json.dump(dict4json_pkg, fp, indent=4)

            # #---------- plot TSNE result ----------
            logger.info(f'{prj_name} finished in {(time.time() - prj_start_time):.2f} seconds.')
            success = True
        except Exception as e:
            logger.error(f'{prj_name} failed: {e}')
            traceback.print_exc()
            try:
                import shutil
                shutil.rmtree(prj_result_folder)
            except:
                pass

    # save all the metric results
    if success:
        metric_avg = {}
        for prj, metrics_prj in metrics_all.items():
            for metric, val in metrics_prj.items():
                if metric not in metric_avg:
                    metric_avg[metric] = 0
                metric_avg[metric] += val / num_prj
        metrics_all['average'] = metric_avg
        with open(os.path.join(result_folder_name, "metrics_our_to_GT.json"), 'w', newline="") as fp:
            json.dump(metrics_all, fp, indent=4)

        logging.info(f"Results saved to: {os.path.abspath(result_folder_name)}")
    else:
        logging.info(f"All projects failed...")
