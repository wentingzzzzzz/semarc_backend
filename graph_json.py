import json
import sys

def convert_structure(data):
    """
    Convert the nested structure into a flat list with ids, parentId, and qualifiedName.
    """
    result = []
    current_id = 0  # 编号从0开始

    # 用于保存每个组件和簇的信息
    component_info = {}  # 用于记录组件名和id的信息
    cluster_info = {}  # 用于记录簇名和id的信息
    cluster_father = {} #用于记录父组件名和簇名的关系
    # 遍历结构体进行处理
    for item in data.get("structure", []):
        if item["@type"] == "component":
            # 处理component类型节点
            component_id = current_id
            result.append({
                "id": component_id,
                "name": item["name"],
                "category": "component",
                "parentId": -1,  # 组件的父节点是-1
                "qualifiedName": item["name"]
            })
            component_info[item["name"]] = component_id
            current_id += 1

            # 处理component下的cluster
            if "nested" in item:
                for cluster in item["nested"]:
                    if cluster["@type"] == "cluster":
                        cluster_id = current_id
                        qualified_name = f"{item['name']}.{cluster['name']}"
                        result.append({
                            "id": cluster_id,
                            "name": cluster["name"],
                            "category": "cluster",
                            "parentId": component_id,  # cluster的parentId是component的id
                            "qualifiedName": qualified_name
                        })
                        cluster_info[cluster["name"]] = cluster_id
                        cluster_father[cluster["name"]] = item["name"]
                        current_id += 1
                        print(result)
        elif item["@type"] == "group":
            if item["name"] not in cluster_info:
                cluster_id = current_id
                parent_component = cluster_father[item["name"]]
                qualified_name = f"{cluster_father[item['name']]}.{item['name']}"
                result.append({
                            "id": cluster_id,
                            "name": item["name"],
                            "category": "cluster",
                            "parentId": component_info[parent_component],  # cluster的parentId是component的id
                            "qualifiedName": qualified_name
                        })
                # print(result)
            if "nested" in item:
                for file in item["nested"]:
                    if file["@type"] == "item":
                        file_id = current_id
                        qualified_name = f"{cluster_info[item['name']]}.{item['name']}.{file['name']}"
                        result.append({
                            "id": file_id,
                            "name": file["name"],
                            "category": "item",
                            "parentId": cluster_info[item['name']],  # item的parentId是cluster的id
                            "qualifiedName": qualified_name
                        })
                        current_id += 1
    return result

def graph_json(input_file_path,output_file_path):
    # if len(sys.argv) != 3:
    #     print("Usage: python convert_json.py <input_json_file> <output_json_file>")
    #     sys.exit(1)
    #
    # input_file_path = sys.argv[1]
    # output_file_path = sys.argv[2]

    try:
        # 读取输入的 JSON 文件
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            data = json.load(input_file)

        # 转换数据结构
        converted_data = convert_structure(data)

        # 将转换后的数据保存为新的 JSON 文件
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump({"structure": converted_data}, output_file, ensure_ascii=False, indent=2)

        print("Conversion completed successfully.")
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

# if __name__ == "__main__":
#     graph_json()
# graph_json('D:\\SemArc_backend\\results\\enre\\enre_Final.json','D:\\SemArc_backend\\results\\enre\\enre_GraphID.json')
