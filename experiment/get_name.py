import json

def extract_group_names(gt_file_path, output_file_path):
    # 加载GT文件
    with open(gt_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 提取所有group的name
    group_names = []
    for item in data['structure']:
        if item['@type'] == 'group':
            group_names.append(item['name'])
    
    # 将group名称以逗号分隔写入文本文件
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(','.join(group_names))

# GT文件路径
gt_file_path = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\gt\\django_gt.json'
# 输出文件路径
output_file_path = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\django\\module_names.txt'

extract_group_names(gt_file_path, output_file_path)
