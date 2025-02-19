from crazy_utils import input_clipping
from crazy_utils_no_ui import request_gpt_model_multi_threads_with_no_ui_and_high_efficiency, \
    request_gpt_model_in_new_thread_with_no_ui, generate_manifest_and_project_folder
from uml_to_code_generation.toolbox_no_ui import promote_file_to_downloadzone
from uml_to_code_generation import tools as tl
from toolbox import write_history_to_file
import os, glob,copy,sys
from md2json import md2json_sum,md2json
from arch_pattern_analysis import execute_parsing_and_analysis

# 修改后的code_semantic_analysis函数
def code_semantic_analysis(language, project_folder, llm_kwargs, plugin_kwargs, history, system_prompt):
    summary_batch_isolation = True
    inputs_array = []
    inputs_show_user_array = []
    history_array = []
    sys_prompt_array = []
    report_part_1 = []

    if language == "python" or language == "Python":
        file_manifest=[f for f in glob.glob(f'{project_folder}/**/*.py', recursive=True)]
    elif language == "cpp" or language == "c":
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.h', recursive=True)]  + \
                    [f for f in glob.glob(f'{project_folder}/**/*.cpp', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.hpp', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.c', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.cc', recursive=True)]
    elif language == "java":
            file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.java', recursive=True)] 
        
    assert len(file_manifest) <= 100000, "源文件太多（超过512个）, 请缩减输入文件的数量。或者，您也可以选择删除此行警告，并修改代码拆分file_manifest列表，从而实现分批次处理。"

    ############################## <第一步，逐个文件分析，多线程> ##################################
    for index, fp in enumerate(file_manifest):
        # 读取文件
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
        prefix = "接下来请你逐文件分析下面的工程" if index==0 else ""
        i_say = prefix + f'请对下面的程序文件做一个概述文件名是{os.path.relpath(fp, project_folder)}，文件代码是 ```{file_content}```'
        i_say_show_user = prefix + f'[{index}/{len(file_manifest)}] 请对下面的程序文件做一个概述: {fp}'

        # 装载请求内容
        inputs_array.append(i_say)
        inputs_show_user_array.append(i_say_show_user)
        history_array.append([])
        sys_prompt_array.append("你是一个程序架构分析师，正在分析一个源代码项目。你的回答必须简单明了。")
    
    # 文件读取完成，对每一个源代码文件，生成一个请求线程，发送到chatgpt进行分析
    print("开始调用多线程分析源代码文件")  # 调试信息
    gpt_response_collection = request_gpt_model_multi_threads_with_no_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        history_array=history_array,
        sys_prompt_array=sys_prompt_array,
        llm_kwargs=llm_kwargs
    )

    # 全部文件解析完成，结果写入文件，准备对工程源代码进行汇总分析
    report_part_1 = copy.deepcopy(gpt_response_collection)
    history_to_return = report_part_1
    res = write_history_to_file(report_part_1)
    promote_file_to_downloadzone(res)

    ############################## <第二步，综合，单线程，分组+迭代处理> ##################################
    batchsize = 16  # 10个文件为一组
    report_part_2 = []
    previous_iteration_files = []
    last_iteration_result = ""
    while True:
        if len(file_manifest) == 0: 
            break
        this_iteration_file_manifest = file_manifest[:batchsize]
        this_iteration_gpt_response_collection = gpt_response_collection[:batchsize * 2]
        file_rel_path = [os.path.relpath(fp, project_folder) for index, fp in enumerate(this_iteration_file_manifest)]
        # 把“请对下面的程序文件做一个概述” 替换成 精简的 "文件名：{all_file[index]}"
        for index, content in enumerate(this_iteration_gpt_response_collection):
            if index % 2 == 0: 
                this_iteration_gpt_response_collection[index] = f"{file_rel_path[index // 2]}"  # 只保留文件名节省token
        this_iteration_files = [os.path.relpath(fp, project_folder) for index, fp in enumerate(this_iteration_file_manifest)]
        previous_iteration_files.extend(this_iteration_files)
        previous_iteration_files_string = ', '.join(previous_iteration_files)
        current_iteration_focus = ', '.join(this_iteration_files)
        if summary_batch_isolation:
            focus = current_iteration_focus
        else:
            focus = previous_iteration_files_string
        i_say = f'用一个md文件的json块从架构师的角度详细描述以下文件的功能，格式是\'\'\'json{{"summary": [{{"file": 文件名1,"Functionality": 功能描述1}}, {{"file": 文件名2,"Functionality": 功能描述2}},....,描述时用英文：{focus}]}}：'

        if last_iteration_result != "":
            sys_prompt_additional = "已知某些代码的局部作用是:" + last_iteration_result + "\n请继续分析其他源代码，从而更全面地理解项目的整体功能。"
        else:
            sys_prompt_additional = ""

        inputs_show_user = f'根据以上分析，对程序的整体功能和构架重新做出概括，由于输入长度限制，可能需要分组处理，本组文件为 {current_iteration_focus} + 已经汇总的文件组。'

        this_iteration_history = copy.deepcopy(this_iteration_gpt_response_collection)
        this_iteration_history.append(last_iteration_result)

        # 裁剪input
        inputs, this_iteration_history_feed = input_clipping(inputs=i_say, history=this_iteration_history,
                                                             max_token_limit=2560)

        print(f"调用GPT进行综合分析: {i_say}")  # 调试信息
        result = request_gpt_model_in_new_thread_with_no_ui(
            inputs=inputs, inputs_show_user=inputs_show_user, llm_kwargs=llm_kwargs,
            history=this_iteration_history_feed,  # 迭代之前的分析
            sys_prompt="你是一个程序架构分析师，正在分析一个项目的源代码。" + sys_prompt_additional)

        print(f"获取分析结果: {result}")  # 调试信息
        summary = "请用一句话概括这些文件的整体功能"
        summary_result = request_gpt_model_in_new_thread_with_no_ui(
            inputs=summary,
            inputs_show_user=summary,
            llm_kwargs=llm_kwargs,
            history=[i_say, result],  # 迭代之前的分析
            sys_prompt="你是一个程序架构分析师，正在分析一个项目的源代码。" + sys_prompt_additional)

        report_part_2.extend([i_say, result])
        last_iteration_result = summary_result
        file_manifest = file_manifest[batchsize:]
        gpt_response_collection = gpt_response_collection[batchsize * 2:]

    ############################## <END> ##################################
    history_to_return.extend(report_part_2)
    res = write_history_to_file(history_to_return)
    promote_file_to_downloadzone(res)
    return res

def get_semantic(folder_path):
    # folder_path=sys.argv[1]
    result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    project_name = os.path.basename(folder_path)

    llm_kwargs = tl.get_default_kwargs()
    language = "c"

    # 调用 get_semantic 函数
    code_sem_res = code_semantic_analysis(language, folder_path, llm_kwargs, plugin_kwargs={}, history=[],
                                          system_prompt="")

    # 保存语义信息到results目录
    code_sem_path = os.path.join(result_dir, project_name, f'{project_name}_CodeSem.json')
    os.makedirs(os.path.dirname(code_sem_path), exist_ok=True)
    md2json_sum(code_sem_res, code_sem_path)
    print(f"Code semantic information saved to: {code_sem_path}")

    arch_sem_res = execute_parsing_and_analysis(txt_json=code_sem_path, llm_kwargs=llm_kwargs, plugin_kwargs={},
                                                history=[], system_prompt="")
    arch_sem_path = os.path.join(result_dir, project_name, f'{project_name}_ArchSem.json')
    os.makedirs(os.path.dirname(arch_sem_path), exist_ok=True)
    md2json(arch_sem_res, arch_sem_path)
    print(f"Architecture semantic information saved to: {arch_sem_path}")


# if __name__ == "__main__":
#     ############################## <测试用> ##################################
#     get_semantic('.\\enre')
