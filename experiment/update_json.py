#对于同一个软件的不同版本，如果文件没有发生变更则json文件中的对应描述不变

import json

# 加载JSON文件1和JSON文件2
with open('E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\libuv-1.44\\libuv-1.44-res.json', 'r', encoding='utf-8') as f:
    json_data_1 = json.load(f)

with open('E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\libuv-1.48\\libuv-1.48-res.json', 'r', encoding='utf-8') as f:
    json_data_2 = json.load(f)

# 加载TXT文件中的文件名
with open('E:\XJTU\架构逆向\lda_demoGPT\libuv变更分析\libuv变更文件列表.txt', 'r', encoding='utf-8') as f:
    txt_files = set(line.strip() for line in f)

# 构建一个file到Functionality的映射，方便后续查找
functionality_map = {entry['file']: entry['Functionality'] for entry in json_data_1['summary']}

# 修改json文件2的内容
for entry in json_data_2['summary']:
    file_name = entry['file']
    # 如果file不在txt文件列表中，替换Functionality
    if file_name not in txt_files and file_name in functionality_map:
        entry['Functionality'] = functionality_map[file_name]

# 将修改后的结果保存为新的JSON文件3
with open('E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\libuv-1.48\\libuv-1.48-res-new.json', 'w', encoding='utf-8') as f:
    json.dump(json_data_2, f, ensure_ascii=False, indent=4)

print("JSON文件3已生成。")
