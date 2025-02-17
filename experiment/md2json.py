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
    # 将JSON数据写入JSON文件
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_blocks, json_file, ensure_ascii=False, indent=4)

# 用法示例
json_file_path = "D:\\lda_demoGPT\\res\\hdf\\hdf.json"
md_file_path = "D:\\lda_demoGPT\\res\\hdf\\GPT-Academic-2024-12-23-18-57-49.md"
json_blocks = extract_json_blocks_from_markdown_file(md_file_path)
save_json_blocks_to_file(json_blocks, json_file_path)
print(f"JSON数据已保存到文件: {json_file_path}")

if json_blocks:
    print(json_blocks)
else:
    print("无法提取或解析JSON数据。")
