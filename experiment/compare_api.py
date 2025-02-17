import json

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def find_common_blocks(json_data1, json_data2):
    # 使用集合找到相同的块，比较qualifiedName, file, src_layer, dest_layer
    common_blocks = [
        block1 for block1 in json_data1
        if any(
            block1['qualifiedName'] == block2['qualifiedName'] and
            block1['file'] == block2['file'] and
            block1['src_layer'] == block2['src_layer'] and
            block1['dest_layer'] == block2['dest_layer']
            for block2 in json_data2
        )
    ]
    return common_blocks

def save_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def extract_common_blocks(file1, file2, output_file):
    # 加载两个项目的JSON文件
    json_data1 = load_json(file1)
    json_data2 = load_json(file2)

    # 找到相同的块
    common_blocks = find_common_blocks(json_data1, json_data2)

    # 将相同的块保存到新的JSON文件中
    save_to_json(common_blocks, output_file)

# 使用示例
file1 = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\libuv-1.44\\libuv-1.44_api.json'
file2 = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\libuv-1.48\\libuv-1.48_api.json'
output_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\experiment\\api.json'

extract_common_blocks(file1, file2, output_file)
