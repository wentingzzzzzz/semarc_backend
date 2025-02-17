from flask import Flask, request, jsonify
from flask_cors import CORS
from uml_to_code_generation import tools as tl
from md2json import md2json_sum, md2json
from arch_pattern_analysis import execute_parsing_and_analysis
from semantic_analysis import code_semantic_analysis, get_semantic
from cluster_project import cluster_project
from module_naming import module_naming
import os

app = Flask(__name__)

CORS(app)

# 确保results目录存在，路径基于app.py文件所在目录
result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(result_dir, exist_ok=True)

# 封装 code_semantic_analysis 成 Flask API
@app.route('/code_semantic_analysis', methods=['POST'])
def code_semantic_analysis_api():
    input_data = request.json
    project_folder = input_data.get('project_folder')
    language = input_data.get('language', 'python')  # 默认Python
    llm_kwargs = tl.get_default_kwargs()

    if not project_folder:
        return jsonify({"error": "Missing required parameters: project_folder"}), 400

    try:
        # 调用 code_semantic_analysis 函数
        code_sem_res = code_semantic_analysis(language, project_folder, llm_kwargs, plugin_kwargs={}, history=[], system_prompt="")

        # 保存结果到results目录
        code_sem_path = os.path.join(result_dir, f"{os.path.basename(project_folder)}_CodeSem.json")
        os.makedirs(os.path.dirname(code_sem_path), exist_ok=True)
        md2json_sum(code_sem_res, code_sem_path)
        print(f"Code semantic information saved to: {code_sem_path}")

        # 返回结果
        return jsonify({"message": "Code semantic analysis completed", "result_file": code_sem_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 封装 get_semantic 成 Flask API
@app.route('/get_semantic', methods=['POST'])
def get_semantic_api():
    input_data = request.json
    project_folder = input_data.get('project_folder')

    if not project_folder:
        return jsonify({"error": "Missing required parameters: project_folder"}), 400

    try:
        project_name = os.path.basename(project_folder)
        llm_kwargs = tl.get_default_kwargs()

        # 调用 get_semantic 函数
        code_sem_res = code_semantic_analysis("python", project_folder, llm_kwargs, plugin_kwargs={}, history=[], system_prompt="")

        # 保存语义信息到results目录
        code_sem_path = os.path.join(result_dir, project_name, f'{project_name}_CodeSem.json')
        os.makedirs(os.path.dirname(code_sem_path), exist_ok=True)
        md2json_sum(code_sem_res, code_sem_path)
        print(f"Code semantic information saved to: {code_sem_path}")

        arch_sem_res = execute_parsing_and_analysis(txt_json=code_sem_path, llm_kwargs=llm_kwargs, plugin_kwargs={}, history=[], system_prompt="")
        arch_sem_path = os.path.join(result_dir, project_name, f'{project_name}_ArchSem.json')
        os.makedirs(os.path.dirname(arch_sem_path), exist_ok=True)
        md2json(arch_sem_res, arch_sem_path)
        print(f"Architecture semantic information saved to: {arch_sem_path}")

        # 返回结果
        return jsonify({
            "message": "Semantic analysis completed",
            "code_sem_file": code_sem_path,
            "arch_sem_file": arch_sem_path
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/run_clustering', methods=['POST'])
def run_clustering():
    data = request.get_json()

    project_folder = data.get('project_folder')
    project_name = os.path.basename(project_folder)

    if not project_folder:
        return jsonify({"error": "project_folder is required"}), 400

    # 构建文件路径
    code_sem_file = os.path.join(result_dir, project_name, f'{project_name}_CodeSem.json')
    arch_sem_file = os.path.join(result_dir, project_name, f'{project_name}_ArchSem.json')

    # 如果没有生成必要的 .json 文件，则先调用 /get_semantic 接口
    if not os.path.exists(code_sem_file) or not os.path.exists(arch_sem_file):
        # 调用 get_semantic 生成文件
        get_semantic(project_folder)
        if not os.path.exists(code_sem_file) or not os.path.exists(arch_sem_file):
            return jsonify({"error": "Failed to generate semantic files"}), 500

    # 运行聚类功能
    stopwords_path = 'stopwords.txt'
    pattern_file_path = os.path.join(result_dir, project_name, f'{project_name}_ArchSem.json')
    llm_file_path = os.path.join(result_dir, project_name, f'{project_name}_CodeSem.json')

    try:
        # 调用 cluster_project 函数执行聚类操作
        cluster_project(
            data_paths=[project_folder],
            gt_json_paths=None,
            resolution=1.7,
            result_folder_name=None,
            cache_dir='./cache',
            save_to_csvfile=True,
            stopword_files=[stopwords_path],
            generate_figures=True,
            pattern_file=[pattern_file_path],
            llm_file=[llm_file_path]
        )
        module_naming(result_dir,project_name, os.path.join(result_dir, project_name, f'cluster_result.json'), llm_file_path)

        return jsonify({"message": "Clustering completed successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
