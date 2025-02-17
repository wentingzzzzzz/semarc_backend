import json
from collections import defaultdict
from tqdm import tqdm

def extract_methods_and_calls(dependencies_data):
    methods = []
    calls = []
    files = []

    for variable in dependencies_data.get('variables', []):
        if 'category' not in variable:
            continue
        if variable['category'] == 'Function':
            methods.append(variable)
            print("method:", variable['qualifiedName'])
        elif variable['category'] == 'File':
            files.append(variable)
            print("file:", variable['qualifiedName'])

    for cell in dependencies_data.get('relations', []):
        if cell['category'] == 'Calls':
            src = cell['from']
            dest = cell['to']
            calls.append((src, dest))

    return methods, calls, files

def get_module_of_file(file_name, architecture_data):
    for group in architecture_data.get('structure', []):
        for item in group.get('nested', []):
            if item['name'] == file_name['qualifiedName']:
                return group['name']
    return None

def find_api_methods(architecture_file, dependencies_file, output_file):
    # Load the architecture and dependencies JSON files
    with open(architecture_file, 'r', encoding='utf-8') as file:
        architecture_data = json.load(file)

    with open(dependencies_file, 'r', encoding='GB2312') as file:
        dependencies_data = json.load(file)

    # Extract methods and calls from the dependencies data
    methods, calls, files = extract_methods_and_calls(dependencies_data)

    # Dictionary to track occurrences of (method, src_module, dest_module) combination
    method_dependencies_count = defaultdict(int)
    # Dictionary to track methods between modules
    module_apis = defaultdict(list)

    api_methods = []
    
    for method in methods:
        method_id = method['id']
        method_file = next((file for file in files if file['id'] == method['entityFile']), None)

        if not method_file:
            continue  # If no file found for the method, skip it
        
        for call in calls:
            src_id, dest_id = call

            if src_id == method_id or dest_id == method_id:
                # Get the source and destination file for the call
                src_file_id = next((v['entityFile'] for v in dependencies_data['variables'] if v['id'] == src_id and 'entityFile' in v), None)
                dest_file_id = next((v['entityFile'] for v in dependencies_data['variables'] if v['id'] == dest_id and 'entityFile' in v), None)
                src_file = next((file for file in files if file['id'] == src_file_id), None)
                dest_file = next((file for file in files if file['id'] == dest_file_id), None)

                if src_file and dest_file:
                    # Get the module of the source and destination file
                    src_module = get_module_of_file(src_file, architecture_data)
                    dest_module = get_module_of_file(dest_file, architecture_data)

                    if src_module and dest_module and src_module != dest_module:
                        # Create a key for the current combination of method, file, and modules
                        method_key = (method['qualifiedName'], method_file['qualifiedName'], src_module, dest_module)

                        # Increment the count for this combination
                        method_dependencies_count[method_key] += 1

                        # Add the method to the module_apis dictionary for this module pair
                        module_apis[(src_module, dest_module)].append({
                            'qualifiedName': method['qualifiedName'],
                            'weight': method_dependencies_count[method_key]
                        })

    
    for method_key, count in method_dependencies_count.items():
        method_name, method_file_name, src_module, dest_module = method_key
        api_methods.append({
            'qualifiedName': method_name,
            'file': method_file_name,
            'src_module': src_module,
            'dest_module': dest_module,
            'weight': count  
        })

    
    module_apis_result = []
    for (src_module, dest_module), methods_list in module_apis.items():
        # Sort methods by weight in descending order and get the top 5
        sorted_methods = sorted(methods_list, key=lambda x: x['weight'], reverse=True)[:5]
        module_apis_result.append({
            'src_module': src_module,
            'dest_module': dest_module,
            'top_methods': sorted_methods  # Top 5 methods by weight
        })

    # Save the API methods and module APIs to a JSON file with a progress bar
    total_items = len(api_methods) + len(module_apis_result)
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump({
            'api_methods': api_methods,
            'module_apis': module_apis_result
        }, file, indent=4)

    # Using tqdm to show progress
    print("Writing to output file with progress...")
    for _ in tqdm(range(total_items), desc="Writing JSON"):
        pass  # Here, we're just simulating progress for demo purposes

# Example usage
# architecture_file = 'E:\\XJTU\\胡杨林基金\\双周例会\\1121\\skia\\skia_cluster_result_0310.json'
# dependencies_file = 'E:\\XJTU\\enre_result\\skia_out.json'
# output_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\skia\\skia0310_api.json'

architecture_file = 'D:\\组会\\241205\\skia_cluster_result_0310.json'
dependencies_file = 'D:\\enre\\skia0310_out.json'
output_file = 'D:\\lda_demoGPT\\res\\skia-0.31.0\\skia0310_api_m.json'

find_api_methods(architecture_file, dependencies_file, output_file)