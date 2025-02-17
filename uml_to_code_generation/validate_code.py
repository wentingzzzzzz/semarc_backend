# 验证阶段

# 检查每个类生成的代码是否完整地覆盖了UML类
# 图和类图描述中要求的属性、方法名，以及类之
# 间的继承、实现、组合、聚合、关联和依赖关系。

# 输入 类的描述（类图描述 + 功能点描述），待分析文件路径

# 循环 对每个生成类进行再次与LLM进行交互验证，完善丰富代码内容，补全类之间的关系以及属性、方法相关代码
# 对生成文件进行多次与LLM的交互验证，第一次进行完善、补全，之后进行再次验证完整性

# 输出 更新生成的java代码存储文件


import os

from file_operation import read_file, update_to_file, get_java_files_count, get_and_save_java_code
import tools as tl


def validate_class_structure(diag_desc_path, result_folder_path, llm_kwargs, plugin_kwargs,
                           history, system_prompt):
    """
    验证类的结构以及类之间的关系。
    """
    # TODO: 实现类的结构以及类之间关系的验证逻辑
    # 示例：检查类代码是否正确实现了继承、组合等关系，类中属性、方法是否与需求数一致

    # 读取类图描述的文件 diag_desc_path 并存储信息
    diag_desc_content = read_file(diag_desc_path)

    # 读取需要进行验证 java 代码的文件
    java_files_num, java_file_paths = get_java_files_count(result_folder_path)

    input = "这是类图对应的" + str(java_files_num) + "个类的描述: " + '\n' + diag_desc_content + '\n' + \
            "请你根据这个描述来提取其中每个类之间的关系，包括继承、组合、实现接口、抽象类的实现等关系以及每个类中应该具有的属性。" + '\n' + \
            "我现在将与你进行多次对话，我每次会给你类图所对应的java文件的代码，请你根据我前面给你的类图描述来完善我给你的代码，使得每个文件中的java代码正确实现了继承、组合等关系以及所需要的属性" + '\n' + \
            "请注意，你现在不需要生成代码，不需要介绍属性，不需要你介绍类之间的关系，我会在接下来与你的交互中让你帮我完善代码。"

    print("hello")

    # # 这里是与 GPT 交互获取生成代码的模拟过程
    # # 实际情况下，需要替换这里的代码以与 GPT-4 API进行通信
    # 与 gpt 交互的配置
    tl.set_conf(key="API_KEY", value="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")
    tl.set_conf(key="LLM_MODEL", value="gpt-3.5-turbo-16k")
    chat_kwargs = tl.get_chat_default_kwargs()
    chat_kwargs['inputs'] = input
    # 第一次交互
    result = tl.get_chat_handle()(**chat_kwargs)
    print("完成 gpt 交互")
    # 存储 gpt 的输出
    history.append(input)
    history.append(result)
    chat_kwargs['history'].extend(history)

    # 进行每个类文件的 java 代码的交互来完善代码
    for i in range(java_files_num):
        java_code_path = java_file_paths[i]
        java_code = read_file(java_code_path)
        file_name = os.path.basename(java_code_path)
        input_relation = "这是刚才我给你的描述中对应的：" + file_name + " 的初步代码： " + '\n' + java_code + \
            "请你根据刚才的描述来给我返回你修改过的代码。要求你检验这个类所对应的代码是否完成了与其它类应该有的类之间的继承、组合等关系、类中的属性是否全部都有、类的结构是否正确。" + \
            '\n' + "如果这个类是完整的你只需要将我传给你的代码直接返回给我即可。如果需要进行完善，你将完善过后的代码返回给我。这是返回格式：" + \
            '\n' + "类名：" + '\n' + "xxx.java" + '\n' + \
            "```" + "\n" + "java" + "\n" + "xxx.java的代码" + "\n" + "```"
        # input_relation = "请用20字概括我们刚才的聊天内容"
        chat_kwargs['inputs'] = input_relation
        result = tl.get_chat_handle()(**chat_kwargs)
        get_and_save_java_code(result, java_code_path)
        print("完成 gpt 第 " + str(i + 1) + " 次交互")
        # 存储 gpt 的输出
        chat_kwargs['history'].append(input_relation)
        chat_kwargs['history'].append(result)


if __name__ == "__main__":
    ############################## <测试用> ##################################

    diag_desc_path = ('/Users/moncheri/Downloads/main/大学课程/大四/毕设/gpt_academic/gpt_academic/tests/uml_to_code_test'
                      '/class_diagram_description.txt')
    result_folder_path = ('/Users/moncheri/Downloads/main/大学课程/大四/毕设/gpt_academic/gpt_academic/tests/uml_to_code_test'
                          '/LibraryManagementSystem_Test1')
    validate_class_structure(diag_desc_path, result_folder_path, llm_kwargs={}, plugin_kwargs={},
                           history=[], system_prompt="")
