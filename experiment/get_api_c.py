import json

def extract_methods_and_calls(dependencies_data):
    methods = []
    calls = []
    files = []

    for variable in dependencies_data.get('variables', []):
        # Check if 'category' key exists in the variable
        if 'category' not in variable:
            #print(f"Variable missing 'category' key: {variable}")
            continue
        if variable['category'] == 'Function':
            methods.append(variable)
            print("method:",variable['qualifiedName'])
        elif variable['category'] == 'File':
            files.append(variable)
            print("file:",variable['qualifiedName'])

    for cell in dependencies_data.get('relations', []):
        if cell['category'] == 'Calls':
            src = cell['from']
            dest = cell['to']
            calls.append((src, dest))

    return methods, calls,files

def get_layer_of_file(file_name, architecture_data):
    for component in architecture_data.get('structure', []):
        for item in component.get('nested', []):
            if item['name'] == file_name['qualifiedName']:
                return component['name']
    return None

def find_api_methods(architecture_file, dependencies_file, output_file):
    # Load the architecture and dependencies JSON files
    with open(architecture_file, 'r', encoding='utf-8') as file:
        architecture_data = json.load(file)

    with open(dependencies_file, 'r', encoding='GB2312') as file:
        dependencies_data = json.load(file)

    # Extract methods and calls from the dependencies data
    methods, calls,files = extract_methods_and_calls(dependencies_data)

    # Identify API methods based on cross-layer calls
    api_methods = []

    for method in methods:
        method_id = method['id']
        method_file = next((file for file in files if file['id'] == method['entityFile']), None)
        method_layer = get_layer_of_file(method_file, architecture_data)

        for call in calls:
            src_id, dest_id = call

            if src_id == method_id or dest_id == method_id:
                src_file_id = next((v['entityFile'] for v in dependencies_data['variables'] if v['id'] == src_id and 'entityFile' in v), None)
                dest_file_id = next((v['entityFile'] for v in dependencies_data['variables'] if v['id'] == dest_id and 'entityFile' in v), None)
                src_file=next((file for file in files if file['id'] == src_file_id), None)
                dest_file=next((file for file in files if file['id'] == dest_file_id), None)

                src_layer = get_layer_of_file(src_file, architecture_data)
                dest_layer = get_layer_of_file(dest_file, architecture_data)

                if src_layer and dest_layer and src_layer != dest_layer:
                    api_methods.append({
                        'qualifiedName': method['qualifiedName'],
                        'file': method_file,
                        'src_layer': src_layer,
                        'dest_layer': dest_layer
                    })

    # Save the API methods to a JSON file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(api_methods, file, indent=4)

# Example usage
architecture_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\bash-5.1\\cluster_result_component.json'
dependencies_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\enre结果\\bash-5.1_out.json'
output_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\bash-5.1\\bash-5.1_api.json'

find_api_methods(architecture_file, dependencies_file, output_file)