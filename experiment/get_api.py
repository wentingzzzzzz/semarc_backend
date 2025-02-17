import json

def extract_methods_and_calls(dependencies_data):
    methods = []
    calls = []

    for variable in dependencies_data.get('variables', []):
        # Check if 'category' key exists in the variable
        if 'category' not in variable:
            #print(f"Variable missing 'category' key: {variable}")
            continue
        if variable['category'] == 'Method':
            methods.append(variable)
            print("method:",variable['name'])

    for cell in dependencies_data.get('cells', []):
        if cell['values'].get('Call', 0) > 0:
            src = cell['src']
            dest = cell['dest']
            calls.append((src, dest))

    return methods, calls

def get_layer_of_file(file_name, architecture_data):
    for component in architecture_data.get('structure', []):
        for item in component.get('nested', []):
            if item['name'] == file_name:
                return component['name']
    return None

def find_api_methods(architecture_file, dependencies_file, output_file):
    # Load the architecture and dependencies JSON files
    with open(architecture_file, 'r', encoding='utf-8') as file:
        architecture_data = json.load(file)

    with open(dependencies_file, 'r', encoding='GB2312') as file:
        dependencies_data = json.load(file)

    # Extract methods and calls from the dependencies data
    methods, calls = extract_methods_and_calls(dependencies_data)

    # Identify API methods based on cross-layer calls
    api_methods = []

    for method in methods:
        method_id = method['id']
        method_file = method['File']
        method_layer = get_layer_of_file(method_file, architecture_data)

        for call in calls:
            src_id, dest_id = call

            if src_id == method_id or dest_id == method_id:
                src_file = next((v['File'] for v in dependencies_data['variables'] if v['id'] == src_id), None)
                dest_file = next((v['File'] for v in dependencies_data['variables'] if v['id'] == dest_id), None)

                src_layer = get_layer_of_file(src_file, architecture_data)
                dest_layer = get_layer_of_file(dest_file, architecture_data)

                if src_layer and dest_layer and src_layer != dest_layer:
                    api_methods.append({
                        'qualifiedName': method['qualifiedName'],
                        'name': method['name'],
                        'file': method_file,
                        'src_layer': src_layer,
                        'dest_layer': dest_layer
                    })

    # Save the API methods to a JSON file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(api_methods, file, indent=4)

# Example usage
architecture_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\hadoop\\cluster_result_component.json'
dependencies_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\enre结果\\hadoop-enre-out\\hadoop-out.json'
output_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\hadoop\\hadoop_api.json'

find_api_methods(architecture_file, dependencies_file, output_file)