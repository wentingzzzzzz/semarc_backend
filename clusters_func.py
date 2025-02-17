import json

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
        for item in group['nested']:
            file_name = item['name']
            # 如果该文件在功能描述中存在，添加对应的Functionality字段
            if file_name in functionality_dict:
                item['Functionality'] = functionality_dict[file_name]
            else:
                item['Functionality'] = file_name
    
    # 将合并后的数据写入新的JSON文件
    with open(output_file, 'w',encoding='utf-8') as output_f:
        json.dump(cluster_data, output_f, indent=4, ensure_ascii=False)
    
    print(f'Merged data has been written to {output_file}')

# # 示例使用方法
# cluster_file = "D:\\semantic_analysis\\cluster_result.json" # 聚类结果文件路径
# functionality_file = 'D:\\semantic_analysis\\enre_CodeSem.json'  # 功能描述文件路径
# output_file = '.\\enre-cluster-func.json'  # 输出文件路径

# # 调用函数进行合并
# merge_functionality_with_clusters(cluster_file, functionality_file, output_file)
