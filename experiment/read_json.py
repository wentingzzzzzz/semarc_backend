import ijson

# 读取 JSON 文件
filename = "E:\\XJTU\\架构逆向\\lda_demoGPT\\enre结果\\itk_out.json"

qualified_names = []

with open(filename, 'r') as f:
    # 使用 ijson 解析 JSON 文件
    parser = ijson.parse(f)
    
    # 遍历 JSON 中的每个对象
    for prefix, event, value in parser:
        # 如果当前事件是 "string" 并且前缀是 "variables.item.qualifiedName"
        if event == 'string' and prefix.endswith('.qualifiedName'):
            # 将该值添加到列表中
            qualified_names.append(value)

# 打印列表长度及前十个元素
print("列表长度:", len(qualified_names))
print("前十个元素:")
for name in qualified_names[:10]:
    print(name)

