import json
from fuzzywuzzy import fuzz

def fuzzy_sort_json_by_order(json_file, order_file, output_file):
    # 读取JSON文件，指定编码为utf-8
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 读取正确顺序的txt文件，指定编码为utf-8
    with open(order_file, 'r', encoding='utf-8') as f:
        order = [line.strip() for line in f]

    # 创建一个新的排序后的数据列表
    sorted_data = []

    # 遍历每行 order.txt 中的文件名
    for target_file in order:
        # 获取目标文件名
        target_filename = target_file.split('/')[-1]

        # 找到所有匹配目标文件名的条目
        matches = [entry for entry in data['summary'] if target_filename in entry['file']]

        if matches:
            # 如果有多个匹配项，则按路径进行进一步匹配
            max_similarity_entry = max(matches, key=lambda x: fuzz.ratio(x['file'], target_file))
            # 将数据加入新的排序后的列表，并统一用order中的文件名
            max_similarity_entry['file'] = target_file
        else:
            # 如果没有匹配项，则直接将目标文件名加入排序后的列表
            max_similarity_entry = {'file': target_file, 'Functionality': target_file}
        
        # 将数据加入新的排序后的列表
        sorted_data.append(max_similarity_entry)

    # 写入排序后的JSON文件，指定编码为utf-8
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, indent=2, ensure_ascii=False)

# 使用示例
fuzzy_sort_json_by_order('.\\res\\hdf\\hdf.json', '.\\res\\hdf\\filenames.txt', '.\\res\\hdf\\hdf-res.json')
