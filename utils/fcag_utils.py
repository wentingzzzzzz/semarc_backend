import numpy as np
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from utils.sentence2matrix import get_sentence_vector_sentence_transformer, get_sentence_vector
import os

# 打印进度的embedding函数
def get_sentence_vectors(sentence, index=None, total=None):
    if index is not None and total is not None:
        print(f"Embedding {index + 1}/{total} ...")  # 显示当前进度
    # sentence_embedding = get_sentence_vector_sentence_transformer(sentence)
    sentence_embedding = get_sentence_vector(sentence)
    return sentence_embedding

def balanced_kmeans(file_vectors, file_indices, num_clusters=2, max_adjustments=5):
    if len(file_vectors) < num_clusters:
        print(f"Not enough files to form {num_clusters} clusters. Returning single cluster.")
        return [file_indices], [file_vectors.mean(axis=0)]

    kmeans = KMeans(n_clusters=num_clusters, init='k-means++', random_state=0)
    kmeans.fit(file_vectors)
    labels = kmeans.labels_

    # 统计每个聚类的样本数量
    count_0 = np.sum(labels == 0)
    count_1 = np.sum(labels == 1)

    adjustment_count = 0
    while abs(count_0 - count_1) > 1 and adjustment_count < max_adjustments:
        print(f"Adjustment round {adjustment_count + 1} ...")

        # 获取每个聚类的样本和其对应的样本索引
        cluster_0_vectors = file_vectors[labels == 0]
        cluster_1_vectors = file_vectors[labels == 1]
        cluster_0_indices = file_indices[labels == 0]
        cluster_1_indices = file_indices[labels == 1]

        # 计算聚类中心
        center_0 = kmeans.cluster_centers_[0]
        center_1 = kmeans.cluster_centers_[1]

        # 计算每个样本到聚类中心的距离
        distance_to_center_0 = np.linalg.norm(cluster_0_vectors - center_0, axis=1) if len(cluster_0_vectors) > 0 else np.array([])
        distance_to_center_1 = np.linalg.norm(cluster_1_vectors - center_1, axis=1) if len(cluster_1_vectors) > 0 else np.array([])

        # 处理空聚类的情况
        if len(distance_to_center_0) == 0 or len(distance_to_center_1) == 0:
            print("One of the clusters is empty. Skipping adjustment.")
            break

        # 找到距离聚类中心最远的样本
        farthest_sample_idx_0 = np.argmax(distance_to_center_0)
        farthest_sample_idx_1 = np.argmax(distance_to_center_1)

        # 将较远的样本从大聚类移动到小聚类
        if count_0 > count_1:
            # Move farthest in cluster 0 to cluster 1
            file_to_move_idx = np.where(labels == 0)[0][farthest_sample_idx_0]
            labels[file_to_move_idx] = 1
        else:
            # Move farthest in cluster 1 to cluster 0
            file_to_move_idx = np.where(labels == 1)[0][farthest_sample_idx_1]
            labels[file_to_move_idx] = 0

        # 重新计算平衡后的聚类中心
        kmeans.fit(file_vectors)  # 重新拟合KMeans
        print(f"After adjustment: Cluster 0 size = {np.sum(labels == 0)}, Cluster 1 size = {np.sum(labels == 1)}")

        # 更新统计信息
        count_0 = np.sum(labels == 0)
        count_1 = np.sum(labels == 1)
        adjustment_count += 1

    # After adjustment, split file_indices into clusters
    split_clusters_indices = [file_indices[labels == i] for i in range(num_clusters)]
    cluster_centers = kmeans.cluster_centers_

    return split_clusters_indices, cluster_centers

def BKHK_select_anchors(file_vectors, labels, anchors_per_component, component_count):
    """选择锚点，确保每个类别至少有 anchors_per_component 个锚点。

    Args:
        file_vectors (numpy.ndarray): 文件的向量表示。
        labels (numpy.ndarray): 文件所属类别的标签。
        anchors_per_component (int): 每个类别选择的锚点数量。
        component_count (int): 类别总数。

    Returns:
        anchor_vectors (numpy.ndarray): 选中的锚点向量。
        anchor_indices (numpy.ndarray): 选中的锚点索引。
    """
    anchor_vectors = []
    anchor_indices = []

    for cat in range(component_count):
        # 获取当前类别的所有文件索引
        cat_indices = np.where(labels == cat)[0]
        if len(cat_indices) == 0:
            print(f"类别 {cat} 没有文件，无法选择锚点。")
            continue

        # 如果文件数量少于锚点数量，则选择所有文件作为锚点
        if len(cat_indices) <= anchors_per_component:
            anchor_vectors.extend(file_vectors[cat_indices])
            anchor_indices.extend(cat_indices)
            print(f"类别 {cat} 文件数少于或等于锚点数，选择所有文件作为锚点。")
            continue

        # 使用 KMeans 选择锚点
        kmeans = KMeans(n_clusters=anchors_per_component, random_state=0)
        kmeans.fit(file_vectors[cat_indices])
        centers = kmeans.cluster_centers_
        
        # 找到距离每个中心最近的文件
        for center in centers:
            distances = np.linalg.norm(file_vectors[cat_indices] - center, axis=1)
            closest_idx_in_split = np.argmin(distances)
            file_idx = cat_indices[closest_idx_in_split]
            if file_idx not in anchor_indices:
                anchor_vectors.append(file_vectors[file_idx])
                anchor_indices.append(file_idx)
        
        print(f"类别 {cat} 选择了 {anchors_per_component} 个锚点。")

    anchor_vectors = np.array(anchor_vectors)
    anchor_indices = np.array(anchor_indices)
    print(f"总共选择了 {len(anchor_vectors)} 个锚点。")
    return anchor_vectors, anchor_indices

# FCAG算法定义 (从样本中选取锚点)
def FCAG(component_vectors, file_vectors, component_count, file_names, labels, anchors_per_component=3, max_iter=10, tol=1e-3, alpha=0.1): 
    """
    FCAG 聚类算法，确保每个类别有指定数量的锚点，并实现平衡的聚类结果。

    Args:
        component_vectors (numpy.ndarray): 组件的向量表示。
        file_vectors (numpy.ndarray): 文件的向量表示。
        component_count (int): 类别总数。
        file_names (list): 文件名称列表。
        labels (numpy.ndarray): 文件所属类别的标签。
        anchors_per_component (int): 每个类别选择的锚点数量。
        max_iter (int): 最大迭代次数。
        tol (float): 收敛阈值。
        alpha (float): 标签更新的学习率。

    Returns:
        y (numpy.ndarray): 文件的最终类别标签。
        label (numpy.ndarray): 锚点的类别标签。
        U (numpy.ndarray): 标签矩阵。
        iter_num (int): 实际迭代次数。
        obj (list): 目标函数值的历史记录。
        anchor_vectors (numpy.ndarray): 选中的锚点向量。
        anchor_indices (numpy.ndarray): 选中的锚点索引。
    """
    n, vector_dim = file_vectors.shape
    c = component_count  # 类别数

    # 使用修改后的 BKHK_select_anchors 函数
    num_anchors = anchors_per_component * c  # 每个类别选取一定数量的锚点
    anchor_vectors, anchor_indices = BKHK_select_anchors(file_vectors, labels, anchors_per_component, c)

    if len(anchor_vectors) == 0:
        print("No anchors were selected. Exiting FCAG.")
        return np.zeros(n, dtype=int), np.array([]), np.array([]), 0, [], np.array([]), np.array([])

    # 初始化锚点的类别标签为其所属类别
    initial_labels = labels[anchor_indices]

    # 初始化标签矩阵 U0
    U0 = np.zeros((len(anchor_vectors), c))
    for i, lbl in enumerate(initial_labels):
        U0[i, lbl] = 1

    # 计算文件与锚点的相似度矩阵 B
    B = cosine_similarity(file_vectors, anchor_vectors)

    # 初始化迭代参数
    U = U0.copy()
    aa = np.sum(U, axis=0)
    label = initial_labels.copy()
    BBB = 2 * (B.T @ B)
    XX = np.diag(BBB) / 2
    BBUU = BBB @ U
    ybby = np.diag(U.T @ BBUU / 2).copy()

    # 计算初始目标函数值
    obj = [np.sum(np.sqrt(ybby))]
    print(f"初始目标函数值: {obj[-1]}")

    # 定义期望每个类别的文件数
    desired_size = n // c
    print(f"期望每个类别的文件数: {desired_size}")

    # 初始化 y
    F_initial = B @ U
    y = np.argmax(F_initial, axis=1)

    for iter_num in range(max_iter):
        print(f"\n--- 迭代 {iter_num + 1} ---")
        category_file_count = {i: np.sum(y == i) for i in range(c)}
        for i in range(num_anchors):
            mm = label[i]
            if aa[mm] == 1:
                continue

            # 计算 V2 和 V1
            V2 = ybby + (BBUU[i, :] + XX[i]) * (1 - U[i, :])
            V1 = ybby - (BBUU[i, :] - XX[i]) * U[i, :]
            delta = np.sqrt(V2) - np.sqrt(V1)
            q = np.argmax(delta)

            # 引入平衡约束：检查目标类别是否已达到期望大小
            current_size = category_file_count[q]
            if current_size >= desired_size:
                # 寻找下一个最优类别
                sorted_indices = np.argsort(-delta)
                for candidate in sorted_indices:
                    if candidate == mm:
                        continue  # 跳过当前类别
                    if np.abs(delta[candidate] - delta[mm]) <= 0.05:
                        continue  # 忽略差异过小的候选
                    candidate_size = category_file_count[candidate]
                    if candidate_size < desired_size:
                        q = candidate
                        break
                else:
                    # 如果所有候选类别都已达到期望大小，则跳过更新
                    continue

            # 更新标签
            if mm != q and np.abs(delta[q] - delta[mm]) > 0.05:
                print(f"锚点 {i} 标签从 {mm} 更新为 {q}")
                aa[q] += 1
                aa[mm] -= 1
                ybby[mm] = V1[mm]
                ybby[q] = V2[q]
                U[i, mm] = (1 - alpha) * U[i, mm]
                U[i, q] = (1 - alpha) * U[i, q] + alpha
                label[i] = q
                BBUU[:, mm] -= BBB[:, i]
                BBUU[:, q] += BBB[:, i]
                category_file_count[q] += 1
                category_file_count[mm] -= 1

        # 更新 y
        F = B @ U
        y = np.argmax(F, axis=1)

        obj.append(np.sum(np.sqrt(ybby)))
        print(f"目标函数值: {obj[-1]}")

        # 收敛条件
        if iter_num > 0:
            change = abs(obj[iter_num] - obj[iter_num -1])
            if change < tol:
                print(f"算法已收敛于第 {iter_num +1} 次迭代 (目标函数变化小于 {tol})")
                break
            if iter_num >= max_iter -1:
                print(f"算法达到最大迭代次数 ({max_iter} 次)，提前停止")
                break

    # 强制分配阶段：确保每个类别的文件数达到 desired_size
    print("\n--- 强制分配阶段 ---")
    category_file_count = {i: np.sum(y == i) for i in range(c)}
    for cat in range(c):
        current_size = category_file_count[cat]
        if current_size < desired_size:
            deficit = desired_size - current_size
            print(f"类别 {cat} 当前文件数 {current_size}，需要分配 {deficit} 个文件。")

            # 计算每个文件与该类别所有锚点的相似度总和
            anchor_indices_cat = np.where(label == cat)[0]
            if len(anchor_indices_cat) == 0:
                print(f"类别 {cat} 没有锚点，无法分配文件。")
                continue
            similarity_to_cat = B[:, anchor_indices_cat].sum(axis=1)

            # 排除已经属于该类别的文件
            similarity_to_cat[y == cat] = -np.inf

            # 按相似度从高到低排序
            sorted_file_indices = np.argsort(-similarity_to_cat)

            for file_idx in sorted_file_indices:
                if deficit == 0:
                    break
                # 选择当前文件所属类别
                current_category = y[file_idx]
                if category_file_count[current_category] > desired_size:
                    # 重新分配
                    y[file_idx] = cat
                    category_file_count[cat] += 1
                    category_file_count[current_category] -= 1
                    deficit -=1
                    print(f"强制将文件 '{file_names[file_idx]}' 从类别 {current_category} 分配到类别 {cat}")

    # 强制将锚点文件分配到其类别
    print("\n--- 强制分配锚点文件到其类别 ---")
    for i, anchor_idx in enumerate(anchor_indices):
        cat = label[i]
        if y[anchor_idx] != cat:
            old_cat = y[anchor_idx]
            y[anchor_idx] = cat
            category_file_count[cat] += 1
            category_file_count[old_cat] -=1
            print(f"锚点文件 '{file_names[anchor_idx]}' 强制分配到类别 {cat}，从类别 {old_cat} 移动。")

    # 重新计算最终的文件标签分布
    unique, counts = np.unique(y, return_counts=True)
    y_distribution = dict(zip(unique, counts))
    print("\n--- 文件标签分布 ---")
    for lbl in range(c):
        print(f"类别 {lbl}: {y_distribution.get(lbl, 0)} 个文件")

    # 返回结果
    final_category_file_count = {i: np.sum(y == i) for i in range(c)}
    print("\n--- 最终锚点聚类结果 ---")
    for cat, count in final_category_file_count.items():
        print(f"类别 {cat} 下共有文件 {count} 个")
    
    # 打印所有锚点的标签
    print("\n--- 所有锚点的标签 ---")
    for idx, lbl in enumerate(label):
        print(f"锚点 {idx}: 标签 {lbl}")

    return y, label, U, iter_num, obj, anchor_vectors, anchor_indices

# 从JSON文件中读取数据并进行embedding
def read_and_embed(json_file_components, json_file_files):
    with open(json_file_components, 'r', encoding='utf-8') as f:
        components_data = json.load(f)

    with open(json_file_files, 'r', encoding='utf-8') as f:
        files_data = json.load(f)

    # 处理组件描述向量
    component_vectors = []
    labels = []
    component_names = []
    label_index = 0
    for idx, component in enumerate(components_data['components']):
        component_names.append(component['name'])
        for indicator in component['nested']:
            content = indicator['content']
            embedding = get_sentence_vectors(content, idx, len(components_data['components']))
            component_vectors.append(embedding)
        labels.extend([label_index] * len(component['nested']))
        label_index += 1

    component_vectors = np.array(component_vectors)

    # 处理文件语义向量
    file_vectors = []
    file_names = []
    for idx, file in enumerate(files_data['summary']):
        functionality = file['Functionality']
        embedding = get_sentence_vectors(functionality, idx, len(files_data['summary']))
        file_vectors.append(embedding)
        file_names.append(file['file'])

    file_vectors = np.array(file_vectors)

    return file_vectors, np.array(labels), component_names, file_names, component_vectors

# 计算锚点向量和组件向量的相似度，并将锚点和文件归类到相应组件
def assign_files_to_components(component_names, file_names, anchor_vectors, component_vectors, label, y):
    clusters = {component_name: [] for component_name in component_names}  # 初始化每个组件的文件列表为空

    # 锚点分组：将锚点按照最终的类别标签进行分组
    label_to_anchors = {}
    for i, lbl in enumerate(label):
        lbl = int(lbl)
        if lbl not in label_to_anchors:
            label_to_anchors[lbl] = []
        label_to_anchors[lbl].append(i)

    print("根据锚点类别标签分配组件...")

    # 1. 计算每个类别锚点与所有组件的相似度
    num_components = len(component_names)
    vectors_per_component = 3  # 每个组件有3个向量
    similarity_matrix = np.zeros((len(label_to_anchors), num_components))

    for lbl, anchor_indices in label_to_anchors.items():
        anchor_group_similarities = np.zeros(num_components)

        # 针对每个类别的所有锚点，计算它们与所有组件的相似度并取平均值
        for anchor_idx in anchor_indices:
            anchor_vector = anchor_vectors[anchor_idx].reshape(1, -1)

            anchor_similarities = cosine_similarity(anchor_vector, component_vectors)

            for component_idx in range(num_components):
                start = component_idx * vectors_per_component
                end = start + vectors_per_component
                component_similarity = np.sum(anchor_similarities[0][start:end])
                anchor_group_similarities[component_idx] += component_similarity

        anchor_group_similarities /= len(anchor_indices)
        similarity_matrix[lbl] = anchor_group_similarities

    # 2. 根据相似度匹配类别和组件
    matched_components = set()
    matched_categories = set()

    while len(matched_components) < len(component_names) and len(matched_categories) < len(label_to_anchors):
        max_similarity = -1
        best_lbl = -1
        best_component_idx = -1

        for lbl in range(len(label_to_anchors)):
            if lbl in matched_categories:
                continue

            for component_idx in range(len(component_names)):
                if component_idx in matched_components:
                    continue

                if similarity_matrix[lbl, component_idx] > max_similarity:
                    max_similarity = similarity_matrix[lbl, component_idx]
                    best_lbl = lbl
                    best_component_idx = component_idx

        if best_lbl == -1 or best_component_idx == -1:
            break  # No more matches possible

        matched_categories.add(best_lbl)
        matched_components.add(best_component_idx)
        component_name = component_names[best_component_idx]

        category_file_count = 0
        for i, file_label in enumerate(y):
            if int(file_label) == best_lbl:  # 这里 file_label 是文件的类别标签
                clusters[component_name].append(file_names[i])
                category_file_count += 1

        print(f"类别 {best_lbl} 匹配到组件 {component_name}，相似度为: {max_similarity}，文件数: {category_file_count}")

    # 打印每个组件下的文件数
    for component_name, files in clusters.items():
        print(f"组件 {component_name} 最终文件数: {len(files)}")

    return clusters

# 打印聚类结果
def print_clustering_results(clusters):
    for component_name, files in clusters.items():
        print(f"{component_name}: {', '.join(files)}")

# 保存聚类结果到 JSON 文件
def save_clustering_results_to_json(clusters, prj_result_folder):
    dict1 = {"@schemaVersion": "1.0", "name": "clustering", "structure": []}
    for component_name, files in clusters.items():
        component_structure = {"@type": "component", "name": component_name, "nested": []}
        for file in files:
            component_structure["nested"].append({"@type": "item", "name": file})
        dict1["structure"].append(component_structure)

    with open(os.path.join(prj_result_folder, "cluster_result_component.json"), 'w', newline="") as fp:
        json.dump(dict1, fp, indent=4)

# if __name__ == "__main__":
#     np.random.seed(0)
    
#     # 从JSON文件中读取数据
#     json_file_components = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\pattern_llm\\jabref.json'
#     json_file_files = 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\jabref\\jabref-res.json'
    
#     file_vectors, labels, component_names, file_names, component_vectors = read_and_embed(json_file_components, json_file_files)
    
#     # 执行FCAG聚类
#     print("开始执行FCAG聚类...")
#     y, label, U, iter, obj, anchor_vectors, anchor_indices = FCAG(
#         component_vectors, file_vectors, component_count=len(component_names), 
#         file_names=file_names, anchors_per_component=3, max_iter=10, tol=1e-3, alpha=0.1
#     )
    
#     # 根据锚点和组件的相似度进行归类
#     print("开始将锚点和文件归类到组件...")
#     clusters = assign_files_to_components(component_names, file_names, anchor_vectors, component_vectors, label, y)
    
#     # 打印聚类结果
#     print_clustering_results(clusters)
    
#     # 保存聚类结果到JSON文件
#     save_clustering_results_to_json(clusters, 'E:\\XJTU\\架构逆向\\lda_demoGPT\\res\\jabref')
