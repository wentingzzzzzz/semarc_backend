def parse_rsf_file(filename):
    clusters = {}
    clustersnames = {}
    cluster_number = 1  # 初始簇号
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith("contain"):
                parts = line.split()
                cluster_name = parts[1]
                filename = parts[2]
                if cluster_name not in clustersnames:
                    clustersnames[cluster_name] = cluster_number
                    cluster_number += 1  # 自增簇号
                clusters[filename] = clustersnames[cluster_name]
    return clusters

# 用法示例
filename = "E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\oodt\\OODT-acdc.rsf"  # 请将文件名替换为你的RSF文件名
clusters = parse_rsf_file(filename)
print(clusters)
