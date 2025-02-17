# 进行文件的读取或者写入
import os
import re
import time


# 目前仅支持 java 文件

# 读取 .java 文件
def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
        # 在这里，file_content 变量包含了文件的内容
    except FileNotFoundError:
        return "文件未找到"
    except Exception as e:
        print(f"读取文件时发生错误：{e}")


# 更新文件
def update_to_file(file_path, code):
    with open(file_path, 'w') as file:
        file.write(code)



# 创建新的文件并存储代码
def create_and_write_file(class_name, code, file_path=None):
    if file_path:
        full_path = os.path.join(file_path, f"{class_name}")
    else:
        full_path = f"{class_name}"

    with open(full_path, 'w') as file:
        file.write(code)


# 从指定路径中提取信息
def get_project_information(first_stage_path):
    """
    从指定文件中提取项目信息。

    此函数读取由 'first_stage_path' 指定的文件内容，并提取项目名称、类的数量以及包含类名及其对应代码的列表。

    参数:
    first_stage_path (str): GPT初始生成文本的文件路径。

    返回:
    tuple: 包含以下内容的元组：
        - project_name (str): 项目名称。若未找到则为 None。
        - class_count (int): 类的数量。若未找到则为 None。
        - extracted_data (list): 字典列表，每个字典包含 'filename' 和 'code' 键，分别代表类的文件名和代码。
    """
    # 原始字符串
    result = read_file(first_stage_path)

    # 提取 project 名
    project_name_match = re.search(r'project名：(.*?)\n', result)
    project_name = project_name_match.group(1) if project_name_match else None

    # 提取类的个数
    class_count_match = re.search(r'类的个数：(\d+)', result)
    class_count = int(class_count_match.group(1)) if class_count_match else None

    # 使用正则表达式匹配Java文件名和代码
    pattern = r"(\w+\.java)\s*```java\s*([\s\S]+?)\s*```"
    matches = re.findall(pattern, result)

    # 提取文件名和代码
    extracted_data = [{"filename": match[0], "code": match[1]} for match in matches]
    a = len(extracted_data)
    b = extracted_data[0]["filename"]
    c = extracted_data[0]["code"]
    return project_name, class_count, extracted_data


# get_project_information("/Users/moncheri/Downloads/main/大学课程/毕设/gpt_academic/gpt_academic/tests/uml_to_code_test/first_stage_result.txt")

# 根据指定 file_path 和 folder_name 在该文件路径同级目录下创建文件夹，文件夹名为 folder_name
def create_folder(file_path, folder_name):
    """
    根据给定的文件路径和文件夹名称创建新文件夹。

    参数:
    - file_path (str): 给定文件路径，新文件夹将在该文件所在的文件夹中创建。
    - folder_name (str): 新文件夹的基本名称。

    返回:
    str: 新文件夹的完整路径。

    注意:
    如果文件夹不存在，直接创建新文件夹。如果文件夹已存在，则在基本名称后添加当前时间戳，并创建带时间戳的新文件夹。
    """

    # 获取文件所在的文件夹路径
    folder_path = os.path.dirname(file_path)

    # 新文件夹的完整路径
    new_folder_path = os.path.join(folder_path, folder_name)

    # 检查文件夹是否存在，如果不存在则创建
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)
        return new_folder_path
    else:
        # 文件夹已存在，添加时间戳
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        new_folder_name_with_timestamp = f'{folder_name}_{timestamp}'
        new_folder_path_with_timestamp = os.path.join(folder_path, new_folder_name_with_timestamp)

        # 创建带时间戳的新文件夹
        os.makedirs(new_folder_path_with_timestamp, exist_ok=True)
        return new_folder_path_with_timestamp

# 根据指定 folder_path 得到该文件夹路径下的 java 文件数目及
def get_java_files_count(folder_path):
    """
    获取指定文件夹路径下的Java文件数量
    """
    java_files = [file for file in os.listdir(folder_path) if file.endswith(".java")]
    java_file_paths = [os.path.join(folder_path, java_file) for java_file in java_files]
    java_files_num = len(java_files)
    return java_files_num, java_file_paths


# 根据传入的字符串 raw_string 和文件路径 java_code_path 来进行提取 java 代码并存储到文件中
def get_and_save_java_code(raw_string, java_code_path):
    """
    得到并存储 java 代码
    """
    java_code_pattern = re.compile(r'```java(.*?)```', re.DOTALL)
    match = java_code_pattern.search(raw_string)
    java_code = match.group(1).strip()
    update_to_file(java_code_path, java_code)




#
# # # 使用示例
# folder_path = ('/Users/moncheri/Downloads/main/大学课程/大四/毕设/gpt_academic/gpt_academic/tests/uml_to_code_test'
#                '/LibraryManagementSystem_Test1')
#
# print(get_java_files_count(folder_path))


# # 使用示例
# java_code = 'public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}'
#
# 使用示例
# new_code = 'public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}'
# update_to_java_file('example.java', new_code)
# # 在当前目录创建文件
# create_and_write_java_file('HelloWorld', java_code)
#
# # 在指定路径创建文件
# create_and_write_java_file('HelloWorld', java_code, '/path/to/directory')
