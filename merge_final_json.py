import json


def merge_json_files(file1_path, file2_path, output_path):
    # 读取第一个和第二个 JSON 文件
    with open(file1_path, 'r', encoding='utf-8') as file1:
        file1_data = json.load(file1)

    with open(file2_path, 'r', encoding='utf-8') as file2:
        file2_data = json.load(file2)

    # 获取第一个文件的 'structure'
    file1_structure = file1_data.get('structure', [])

    # 获取第二个文件的 'structure'
    file2_structure = file2_data.get('structure', [])

    # 直接将第二个文件中的 group 加到第一个文件的 structure 中
    merged_structure = file1_structure + file2_structure

    # 合并后的数据
    merged_data = {
        "@schemaVersion": file1_data.get("@schemaVersion", ""),
        "name": file1_data.get("name", ""),
        "structure": merged_structure
    }

    # 将合并后的数据保存到输出文件
    with open(output_path, 'w', encoding='utf-8') as output_file:
        json.dump(merged_data, output_file, ensure_ascii=False, indent=4)

    print(f"Merged JSON file saved to: {output_path}")


# 使用示
