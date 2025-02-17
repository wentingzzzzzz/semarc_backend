import json

def sort_json_by_all_letters(json_file, output_file):
    # 读取JSON文件，指定编码为utf-8
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按文件名的所有字母顺序进行排序，不区分大小写
    sorted_data = sorted(data['summary'], key=lambda x: x['file'].lower())

    # 写入排序后的JSON文件，指定编码为utf-8
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, indent=2, ensure_ascii=False)

# 使用示例
sort_json_by_all_letters('.\\res\\hdf\\hdf.json', '.\\res\\hdf\\hdf-res-sorted.json')
