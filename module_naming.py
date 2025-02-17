from toolbox import update_ui
from toolbox import CatchException, report_exception
from toolbox import write_history_to_file, promote_file_to_downloadzone
from crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
import glob,os,sys
from clusters_func import merge_functionality_with_clusters
from uml_to_code_generation import tools as tl
import json
from pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
from request_llms.bridge_all import model_info
from crazy_utils_no_ui import request_gpt_model_multi_threads_with_no_ui_and_high_efficiency, \
    request_gpt_model_in_new_thread_with_no_ui, generate_manifest_and_project_folder
from md2json import md2json_name

def analysis_json(json_file, llm_kwargs, plugin_kwargs, history, system_prompt):

    max_token = model_info[llm_kwargs['llm_model']]['max_token']
    TOKEN_LIMIT_PER_FRAGMENT = max_token * 3 // 4
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
    except Exception as e:
        raise RuntimeError(f'无法读取JSON文件: {json_file}，错误信息: {str(e)}')

    # 处理JSON文件中的每个模块（group）
    modules = json_content.get('structure', [])
    overall_summary = []
    for module in modules:
        module_name = module.get('name', 'Unknown Module')
        nested_items = module.get('nested', [])
        module_type = module.get('@type', '')

        # 收集模块中所有文件的功能描述
        functionalities = []

        def extract_functionalities(items, functionalities_list):
            for item in items:
                if item.get('@type') == 'item':
                    functionality = item.get('Functionality', '')
                    if functionality:
                        functionalities_list.append(functionality)
                elif item.get('@type') == 'group':
                    # 递归处理嵌套的group
                    extract_functionalities(item.get('nested', []), functionalities_list)

        extract_functionalities(nested_items, functionalities)

        # 分段处理功能描述，避免超过token限制
        functionality_fragments = breakdown_text_to_satisfy_token_limit(
            txt='\n'.join(functionalities),
            limit=TOKEN_LIMIT_PER_FRAGMENT,
            llm_model=llm_kwargs['llm_model']
        )

        module_summaries = []
        for i, fragment in enumerate(functionality_fragments):
            i_say = f'以下是一些文件的功能描述，请根据这些描述总结该模块的主要功能：```{fragment}```'
            i_say_show_user = f'正在总结模块 {module_name} 的第 {i+1}/{len(functionality_fragments)} 个片段。'

            gpt_say = request_gpt_model_in_new_thread_with_no_ui(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs,
                history=[],
                sys_prompt="请总结模块的主要功能，并根据功能为模块取一个合适的名称。"
            )

            history.extend([i_say_show_user, gpt_say])
            module_summaries.append(gpt_say)

        # 如果有多个片段，对模块进行综合总结并命名
        if len(functionality_fragments) > 1:
            combined_summaries = '\n'.join(module_summaries)
            i_say = f'根据以上的总结，进一步总结模块 {module_name} 的主要功能，并为其取一个合适的名称，模块名用英文，回答时只回答 模块编号:模块名，切勿回答其他任何信息。'
            i_say_show_user = f'正在综合总结模块 {module_name}。'

            gpt_say =request_gpt_model_in_new_thread_with_no_ui(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs,
                history=history,
                sys_prompt="请总结模块的主要功能，并为其取一个合适的名称。"
            )

            history.extend([i_say_show_user, gpt_say])
            module_summary = gpt_say
        else:
            module_summary = module_summaries[0]

        i_say = f'根据以上的总结，将所有模块名统一成md文件中的json块格式输出，格式是\'\'\'json{{"modules": [{{"no": 模块编号1,"name": 模块名1}}, {{"no": 模块编号2,"name": 模块名2}},....}}'
        i_say_show_user = f'正在综合模块名...'

        gpt_say =request_gpt_model_in_new_thread_with_no_ui(
            inputs=i_say,
            inputs_show_user=i_say_show_user,
            llm_kwargs=llm_kwargs,
            history=history,
            sys_prompt="请总结所有模块的名称，将他们和编号对应。"
        )
        history.extend([i_say_show_user, gpt_say])
        module_summary = gpt_say

        # 保存模块的总结和名称
        overall_summary.append({
            'module_name': module_name,
            'module_summary': module_summary
        })

    # 处理完所有模块后，将总结写入文件
    summary_output = '模块功能总结：\n'
    for module_info in overall_summary:
        summary_output += f"模块 {module_info['module_name']}:\n{module_info['module_summary']}\n\n"

    # 将总结结果写入历史记录并提供下载
    res = write_history_to_file(history)
    return res

def mapping_module(cluster_file,module_names,output_file):
    with open(cluster_file, 'r', encoding='utf-8') as cf:
        clusters = json.load(cf)

    # 读取第二个 JSON 文件
    with open(module_names, 'r', encoding='utf-8') as mn:
        names = json.load(mn)

    # 创建一个字典，将模块编号映射到模块名称
    module_mapping = {module['no']: module['name'] for module in names['modules']}

    # 遍历第一个文件的结构，替换 group 的 name 字段为模块名称
    for group in clusters['structure']:
        group_no = int(group['name'])  # 获取组的编号
        if module_mapping.get(group_no):
            group['name'] = module_mapping.get(group_no)
        else:
            group['name'] = group_no

    # 将修改后的数据保存到新的 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f_out:
        json.dump(clusters, f_out, ensure_ascii=False, indent=4)


def replace_no_with_name(cluster_result_path, cc_map, output_path):
    # 读取 cluster_result_named.json 文件
    with open(cluster_result_path, 'r', encoding='utf-8') as f:
        cluster_data = json.load(f)

    # 创建一个映射字典
    no_to_name = {module['no']: module['name'] for module in cluster_data['modules']}

    # 读取 enre_cluster_component_mapping.json 文件
    with open(cc_map, 'r', encoding='utf-8') as f:
        map_data = json.load(f)

    # 检查 enre_data 是否包含 'structure' 键
    if 'structure' not in map_data:
        print("错误: 'structure' 键不存在于 enre_cluster_component_mapping.json 文件中")
        print("文件内容:", map_data)
    else:
        # 遍历 'structure' 中的每个 'component'
        for component in map_data['structure']:
            # 遍历 'nested' 数组中的每个 'cluster'
            for cluster in component['nested']:
                no = cluster['No.']
                if no in no_to_name:
                    cluster['No.'] = no_to_name[no]

        # 将修改后的数据写入一个新文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, ensure_ascii=False, indent=4)

        print(f"替换完成，结果已写入 {output_path}")

def check_file_exists_and_not_empty(file_path):
    return os.path.exists(file_path) and os.path.getsize(file_path) > 0

def module_naming(result_dir,project_name,cluster_path,functionality_path):
    llm_kwargs = tl.get_default_kwargs()
    # cluster_path=sys.argv[2]
    # functionality_path=sys.argv[3]
    # folder_path=sys.argv[1

    merged_path='.\\cache\\merged.json'
    named_cluster_path= os.path.join(result_dir,project_name, f"{project_name}_NamedClusters.json")
    module_name_path = os.path.join(result_dir, project_name, 'cluster_result_named.json')
    cc_map = os.path.join(result_dir, project_name, f"{project_name}_cluster_component_mapping.json")
    cluster_component_path = os.path.join(result_dir, project_name, f"{project_name}_ClusterComponent.json")

    if check_file_exists_and_not_empty(merged_path) and check_file_exists_and_not_empty(named_cluster_path) and check_file_exists_and_not_empty(module_name_path):
        print("Find cache.")
        return  # 如果文件都存在且不为空，直接结束函数

    merge_functionality_with_clusters(cluster_path, functionality_path, merged_path)
    module_name_res=analysis_json(json_file=merged_path,llm_kwargs=llm_kwargs, plugin_kwargs={}, history=[], system_prompt="")
    md2json_name(module_name_res,module_name_path)
    mapping_module(cluster_path,module_name_path,named_cluster_path)
    replace_no_with_name(module_name_path,cc_map,cluster_component_path)


# if __name__ == "__main__":
#     ############################## <测试用> ##################################
#     module_naming('.\\enre','.\\cluster_result.json','.\\enre_CodeSem.json')