#修改JAVA项目的groundtruth格式使其与抽取结果相匹配
import json
from fuzzywuzzy import process,fuzz

def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def write_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def extract_filename(file_path):
    # 使用'/'拆分路径，然后取路径中的最后一个部分，再使用'.'获取文件名
    parts = file_path.split("/")
    length = len(parts[-1].split("."))
    file_name = parts[-1].split(".")[length-1]
    return file_name

def find_best_match(name, names_list):
    if not names_list:
        return None

    # 提取文件名（不包含路径和扩展名）
    extract_filename_last_part = lambda x: x.split("/")[-1].split(".")[0].split(".")[-1]

    # 使用 fuzzywuzzy 的 process 函数获取可能的匹配项
    matches = process.extract(extract_filename_last_part(name), names_list, scorer=fuzz.token_sort_ratio, limit=1)

    # 从匹配项中获取最佳匹配
    best_match = matches[0]
    return best_match[0]


def rename_files(file_structure, reference_structure):
    renamed_structure = file_structure.copy()

    # 直接使用 reference_structure 中的 variables 作为目标文件名列表
    target_filenames = reference_structure.get("variables", [])

    for group in renamed_structure.get("structure", []):
        for item in group.get("nested", []):
            old_name = item["name"]
            old_name=extract_filename(old_name)
            print("old_name:", old_name)
            
            # 从目标文件名列表中查找最佳匹配项
            new_name = find_best_match(old_name, target_filenames)

            if new_name is not None:
                # 在新的结构中修改匹配项
                item["name"] = new_name

    return renamed_structure

def main():
    # 读取两个 JSON 文件
    file_structure_1 = read_json('E:\\XJTU\\架构逆向\\lda_demoGPT\\gt\\oodt.json')
    file_structure_2 = read_json('E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\\oodt\\oodt-file.json')

    # 重命名文件
    renamed_structure = rename_files(file_structure_1, file_structure_2)

    # 将结果写入输出文件
    write_json(renamed_structure, 'E:\\XJTU\\架构逆向\\lda_demoGPT\\gt\\oodt2.json')

if __name__ == "__main__":
    main()
