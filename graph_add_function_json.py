import json
import sys
import os


def convert_component_to_sum(file1, file2):
    # 读取文件1的数据
    with open(file1, 'r') as f:
        file1_data = json.load(f)

    # 初始化文件2的数据结构
    file2_data = {"summary": []}

    # 遍历文件1的数据并转换格式
    for component in file1_data["components"]:
        # 获取组件名称
        component_name = component["name"]

        # 只选择第一条indicator的content
        if component["nested"]:
            first_indicator_content = component["nested"][0]["content"]

            # 将第一条内容添加到文件2的结构中
            file2_data["summary"].append({
                "file": component_name,  # 使用组件名称作为文件名
                "Functionality": first_indicator_content
            })

    # 检查file2是否存在，如果不存在则创建并写入
    if not os.path.exists(file2):
        # 确保目录存在
        os.makedirs(os.path.dirname(file2), exist_ok=True)

    # 将转换后的文件2数据保存为JSON文件
    with open(file2, 'w') as f:
        json.dump(file2_data, f, indent=2)

def merge_functionality_with_clusters(cluster_file, functionality_file, output_file):
    # 读取聚类结果的JSON文件
    with open(cluster_file, 'r', encoding='utf-8') as cluster_f:
        cluster_data = json.load(cluster_f)

    # 读取功能描述的JSON文件
    with open(functionality_file, 'r', encoding='utf-8') as functionality_f:
        functionality_data = json.load(functionality_f)

    # 将功能描述转为字典，文件路径为key，功能为value
    functionality_dict = {item['file']: item['Functionality'] for item in functionality_data['summary']}

    # 遍历聚类数据，并为每个文件项添加Functionality字段
    for group in cluster_data['structure']:
        if group['category'] == 'item' or group['category'] == 'component':
            filename = group['name']
            if filename in functionality_dict:
                group['Functionality'] = functionality_dict[filename]
        # elif group['category'] == 'component':
        #     componentName = group['name']
        #     if componentName in functionality_dict:
        #         group['Functionality'] = functionality_dict[componentName]
        else:
            group['Functionality'] = "none"



    # 将合并后的数据写入新的JSON文件
    with open(output_file, 'w', encoding='utf-8') as output_f:
        json.dump(cluster_data, output_f, indent=4, ensure_ascii=False)

    print(f'Merged data has been written to {output_file}')


# if sys.argv != 4:
#     print("Usage: python merge_functionality_with_clusters.py <cluster_file> <functionality_file> <output_file>")
# cluster_file = sys.argv[1]
# functionality_file = sys.argv[2]
# output_file = sys.argv[3]
# 示例使用方法
# cluster_file = 'D:\组会\\241205\\skia_cluster_result_m131.json'  # 聚类结果文件路径
# functionality_file = 'D:\\lda_demoGPT\\res\\skia-m131\\skia-m131-res.json'  # 功能描述文件路径
# output_file = 'D:\\lda_demoGPT\\res\\skia-m131\\skia-m131-cluster-func.json'  # 输出文件路径

# merge_functionality_with_clusters('D:\\SemArc_backend\\results\\enre\\enre_GraphID.json', 'D:\SemArc_backend\\results\enre\enre_CodeSem.json', 'D:\SemArc_backend\\results\enre\enre_GraphIDFunc.json')
