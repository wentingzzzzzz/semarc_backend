"""
    类生成阶段
    GPT-4生成每个类的代码。由于回复长度的限制，GPT-4可
    能需要分多次回复来完成所有类的代码生成。这一阶段需要
    与GPT-4进行多次交互，确保所有类的代码都被生成。

    输入 类图加上类图描述、功能点描述，生成文件路径

    循环 多次交互直到生成的类的数目与需求类的数目以及需求一致

    输出 每个类的java代码并创建对应文件存储进去
"""

from file_operation import read_file, create_and_write_file, update_to_file, get_project_information, create_folder
import tools as tl


def uml_to_code(diag_path, diag_desc_path, func_desc_path, first_stage_result_path, llm_kwargs, plugin_kwargs,
                history, system_prompt):
    """
    从UML图生成代码的整个流程。
    :param diag_path: UML类图路径。
    :param diag_desc_path: 类的描述信息描述。
    :param func_desc_path: 类的方法信息描述
    """

    # 读取类图的描述、类的功能的文件并存储信息
    diag_desc_content = read_file(diag_desc_path)
    func_desc_content = read_file(func_desc_path)

    input = "我现在需要你根据我给你的类图的描述以及类的功能的描述来生成各个java类的代码" + '\n' + \
            "UML类图的描述：" + '\n' + diag_desc_content + '\n' + "各个类的功能点的描述:" + '\n' + \
            func_desc_content + '\n' + "请按照以下格式给我回复：" + '\n' + "project名：" '\n' + "类的个数：" + '\n' + "xxx.java" + '\n' + \
            "```" + "\n" + "java" + "\n" + "xxx.java的代码片段" + "\n" + "```"

    # # 这里是与 GPT 交互获取生成代码的模拟过程
    # # 实际情况下，需要替换这里的代码以与 GPT-4 API进行通信
    # 与 gpt 交互的配置
    tl.set_conf(key="API_KEY", value="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")
    tl.set_conf(key="LLM_MODEL", value="gpt-3.5-turbo")
    chat_kwargs = tl.get_chat_default_kwargs()
    chat_kwargs['inputs'] = input
    # 交互
    result = tl.get_chat_handle()(**chat_kwargs)
    print("完成 gpt 交互")
    # 存储 gpt 的输出
    update_to_file(first_stage_result_path, result)
    print("完成 存储 gpt 的输出")
    # 处理输出得到项目名、类的个数、java文件名及对应的代码
    project_name, class_count, extracted_date = get_project_information(first_stage_result_path)
    project_path = create_folder(first_stage_result_path, project_name)
    print("完成创建项目")
    for i in range(class_count):
        create_and_write_file(extracted_date[i]["filename"], extracted_date[i]["code"], project_path)
    print("完成类代码的生成和存储")
    # print('\n*************\n' + result + '\n*************\n')
    print("hello~")

    # 还需要编写生成的类的数目是否与需求一致的代码，确保所有类的代码都被生成
    # 如果生成的类的代码与需求的不一致，就还需要多次与 gpt 进行交互完善代码


if __name__ == "__main__":
    ############################## <测试用> ##################################

    diag_path = 'path/to/your/test/uml_image.png'
    diag_desc_path = '/Users/moncheri/Downloads/main/大学课程/毕设/gpt_academic/gpt_academic/tests/uml_to_code_test/class_diagram_description.txt'
    func_desc_path = '/Users/moncheri/Downloads/main/大学课程/毕设/gpt_academic/gpt_academic/tests/uml_to_code_test/class_functions_description.txt'

    first_stage_result_path = '/Users/moncheri/Downloads/main/大学课程/毕设/gpt_academic/gpt_academic/tests/uml_to_code_test/first_stage_result.txt'

    # 指定输出目录
    # output_path = 'path/to/your/output/directory'

    # 调用函数
    uml_to_code(diag_path, diag_desc_path, func_desc_path, first_stage_result_path, llm_kwargs={}, plugin_kwargs={},
                history=[], system_prompt="")
