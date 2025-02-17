import json

def extract_calls(dependencies_data):
    calls = []
    # 只提取"type"为"Call"的依赖关系
    for cell in dependencies_data.get('cells', []):
        for detail in cell.get('details', []):
            if detail['type'] == 'Call':
                calls.append((detail['src'], detail['dest']))
    return calls

def get_layer_of_file(file_name, architecture_data):
    for component in architecture_data.get('structure', []):
        for item in component.get('nested', []):
            if item['name'] == file_name:
                return component['name']
    return None

def find_api_methods(architecture_file, dependencies_file, output_file):
    # 加载architecture和dependencies的JSON文件
    with open(architecture_file, 'r', encoding='utf-8') as file:
        architecture_data = json.load(file)

    with open(dependencies_file, 'r', encoding='GB2312') as file:
        dependencies_data = json.load(file)

    # 提取"type"为"Call"的依赖关系
    calls = extract_calls(dependencies_data)

    # 存储API方法
    api_methods = []
    i = 0

    for src_method, dest_method in calls:
        src_file = src_method['file']
        dest_file = dest_method['file']

        # 查找src和dest文件所在的层
        src_layer = get_layer_of_file(src_file, architecture_data)
        dest_layer = get_layer_of_file(dest_file, architecture_data)

        # 如果src_layer和dest_layer不相等，则记录为API方法
        if src_layer and dest_layer and src_layer != dest_layer:
            api_methods.append({
                'qualifiedName': dest_method['object'],
                'file': dest_file,
                'src_layer': src_layer,
                'dest_layer': dest_layer
            })
            print(i)
            i += 1

    # 将API方法保存到JSON文件
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(api_methods, file, indent=4)

# 使用示例
architecture_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\libuv-1.44\\cluster_result_component.json'
dependencies_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\ext_tools\\libuv144-file.json'
output_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\libuv-1.44\\libuv-1.44_api.json'

find_api_methods(architecture_file, dependencies_file, output_file)
