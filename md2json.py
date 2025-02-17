import re
import json

def extract_json_blocks_from_markdown(md_content):
    # 定义匹配JSON数据的正则表达式
    pattern = r'```json(.*?)```'
    
    # 使用re.DOTALL标志以匹配多行内容
    matches = re.finditer(pattern, md_content, re.DOTALL)
    
    json_blocks = []
    
    for match in matches:
        # 获取匹配到的JSON字符串
        json_str = match.group(1)
        
        try:
            # 解析JSON字符串
            json_data = json.loads(json_str)
            json_blocks.append(json_data)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")

    if not json_blocks:
        print("未找到匹配的JSON数据块")
    
    return json_blocks

def extract_json_blocks_from_markdown_file(md_file_path):
    # 读取Markdown文件内容
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 调用提取JSON数据的函数
    return extract_json_blocks_from_markdown(md_content)

def save_json_blocks_to_file(json_blocks, json_file_path):
    # 将所有JSON数据合并到一个summary中
    combined_summary = []
    for block in json_blocks:
        if isinstance(block, dict) and "summary" in block:
            combined_summary.extend(block["summary"])
    
    # 创建最终的JSON结构
    final_json = {
        "summary": combined_summary
    }

    # 将JSON数据写入JSON文件
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_json, json_file, ensure_ascii=False, indent=4)

def save_json_blocks_module_names(json_blocks, json_file_path):
    combined_summary = []
    for block in json_blocks:
        if isinstance(block, dict) and "modules" in block:
            combined_summary.extend(block["modules"])
    
    # 创建最终的JSON结构
    final_json = {
        "modules": combined_summary
    }

    # 将JSON数据写入JSON文件
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_json, json_file, ensure_ascii=False, indent=4)

def save_json_blocks_no_summary(json_blocks, json_file_path): 
    """
    For JSON files without 'summary' field, extract 'architecture pattern' and 'components'
    and save them into a simplified structure without merging 'indicators'.
    """
    # Create a simplified structure without 'summary'
    simplified_json = []

    for block in json_blocks:
        if isinstance(block, dict):
            architecture_pattern = block.get("architecture pattern", "Unknown")
            components = block.get("components", [])
            components_summary = []
            
            for component in components:
                component_name = component.get("name", "Unnamed")
                nested_indicators = component.get("nested", [])
                components_summary.append({
                    "name": component_name,
                    "nested": nested_indicators  # Keep 'nested' structure intact
                })

            simplified_json.append({
                "architecture_pattern": architecture_pattern,
                "components": components_summary
            })

    # Save the simplified JSON structure to file
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        # Write without the outer list
        json.dump(simplified_json[0], json_file, ensure_ascii=False, indent=4)

def md2json_sum(md_file_path, json_file_path):
    json_blocks = extract_json_blocks_from_markdown_file(md_file_path)

    save_json_blocks_to_file(json_blocks, json_file_path)
    print(f"JSON数据（代码语义信息）已保存到文件: {json_file_path}")

    if json_blocks:
        print(json_blocks)
    else:
        print("无法提取或解析JSON数据。")

def md2json(md_file_path, json_file_path):
    json_blocks = extract_json_blocks_from_markdown_file(md_file_path)
    save_json_blocks_no_summary(json_blocks, json_file_path)
    print(f"JSON数据（架构语言信息）已保存到文件: {json_file_path}")

    if json_blocks:
        print(json_blocks)
    else:
        print("无法提取或解析JSON数据。")

def md2json_name(md_file_path, json_file_path):
    json_blocks = extract_json_blocks_from_markdown_file(md_file_path)
    save_json_blocks_module_names(json_blocks, json_file_path)
    print(f"JSON数据（架构语言信息）已保存到文件: {json_file_path}")

    if json_blocks:
        print(json_blocks)
    else:
        print("无法提取或解析JSON数据。")

# 用法示例
# json_file_path = "enre-res.json"
# md_file_path = "D:\\解析项目源代码\\gpt_log\\default_user\\shared\\GPT-Academic-2025-01-15-22-58-24.md"
# md2json(md_file_path, json_file_path)