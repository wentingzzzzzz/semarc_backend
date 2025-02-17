import json

def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def convert_gt_to_component_file_relationship(component_module_gt, module_file_gt):
    """Convert ground truth data to a component-file relationship."""
    component_file_mapping = {}

    # 建立module到file的映射
    module_to_file = {}
    for group in module_file_gt['structure']:
        module_name = group['name']
        file_names = [nested_item['name'] for nested_item in group['nested']]
        module_to_file[module_name] = file_names

    print("Module to File Mapping:")
    for module, files in module_to_file.items():
        print(f"{module}: {files}")

    # 建立component到file的映射
    for component in component_module_gt['structure']:
        component_name = component['name']
        if component_name not in component_file_mapping:
            component_file_mapping[component_name] = set()
        
        for item in component['nested']:
            module_name = item['name']
            if module_name in module_to_file:
                component_file_mapping[component_name].update(module_to_file[module_name])

    return component_file_mapping

def compute_accuracy(recovered, gt_component_file):
    """Compute the accuracy for each component and the average accuracy."""
    component_accuracies = {}

    for component in gt_component_file:
        gt_files = gt_component_file[component]
        recovered_files = set(item['name'] for comp in recovered['structure'] if comp['name'] == component for item in comp['nested'])

        component_total_files = len(gt_files)
        component_correct_assignments = len(gt_files.intersection(recovered_files))

        component_accuracy = component_correct_assignments / component_total_files if component_total_files else 0
        component_accuracies[component] = component_accuracy

        print(f"Component: {component}")
        print(f"GT Files: {gt_files}")
        print(f"Recovered Files: {recovered_files}")
        print(f"Correct Assignments: {component_correct_assignments}")
        print(f"Component Accuracy: {component_accuracy:.2%}\n")

    average_accuracy = sum(component_accuracies.values()) / len(component_accuracies) if component_accuracies else 0
    return average_accuracy, component_accuracies

if __name__ == "__main__":
    recovered_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\bash\\cluster_result_component.json'  # 恢复得到的文件路径
    module_file_gt_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\gt\\bash-4.2-GT.json'  # module和文件的包含关系文件路径
    component_module_gt_file = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\pattern_gt\\bash-4.2-pattern-GT.json'  # component和module的包含关系文件路径

    recovered_data = load_json(recovered_file)
    component_module_gt_data = load_json(component_module_gt_file)
    module_file_gt_data = load_json(module_file_gt_file)

    gt_component_file = convert_gt_to_component_file_relationship(component_module_gt_data, module_file_gt_data)
    overall_accuracy, component_accuracies = compute_accuracy(recovered_data, gt_component_file)

    print(f'Overall Component Recovery Accuracy: {overall_accuracy:.2%}')
    for component, accuracy in component_accuracies.items():
        print(f'{component} Accuracy: {accuracy:.2%}')
