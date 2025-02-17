from toolbox import write_history_to_file, promote_file_to_downloadzone
import glob
import os
import json
import re
import os, glob,copy,sys
from crazy_utils_no_ui import request_gpt_model_in_new_thread_with_no_ui
from uml_to_code_generation.toolbox_no_ui import promote_file_to_downloadzone
from uml_to_code_generation import tools as tl
from toolbox import write_history_to_file
from md2json import md2json

def execute_parsing_and_analysis(txt_json, llm_kwargs, plugin_kwargs, history, system_prompt):
    from pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
    from request_llms.bridge_all import model_info
    overall_summary = []

    # Parse the SAP.txt file to extract architecture pattern descriptions
    file_path = '.\\SAP.txt'
    if not os.path.exists(file_path):
        raise RuntimeError(f'Cannot find SAP.txt file: {file_path}')

    with open(file_path, 'r', encoding='utf-8') as f:
        sap_content = f.read()

    # Split architecture patterns by double hashtags "##"
    architecture_patterns = re.split(r'\n##\s*', sap_content)
    architecture_patterns = [pattern.strip() for pattern in architecture_patterns if pattern.strip()]

    architecture_fragments = architecture_patterns  # Each pattern is treated as a separate fragment

    # Check and retrieve the JSON project folder
    if os.path.exists(txt_json):
        json_project_folder = txt_json
    else:
        if txt_json == "":
            txt_json = 'Empty input'
        raise RuntimeError(f"Cannot find or access the specified path: {txt_json}")

    # Retrieve the list of JSON files to process
    if txt_json.endswith('.json'):
        file_manifest = [txt_json]
    else:
        file_manifest = [f for f in glob.glob(f'{json_project_folder}/**/*.json', recursive=True)]

    # Check if any JSON files were found
    if len(file_manifest) == 0:
        raise RuntimeError(f"No JSON files found at {txt_json}")

    # Parse the JSON files to extract project functionality summaries
    for fp in file_manifest:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
        except Exception as e:
            raise RuntimeError(f'Failed to read JSON file: {fp}, Error: {str(e)}')

        summaries = json_content.get('summary', [])
        functionalities = [item.get('Functionality', '') for item in summaries if item.get('Functionality', '')]

        # Segment functionality descriptions to avoid exceeding token limits
        functionality_fragments = breakdown_text_to_satisfy_token_limit(
            txt='\n'.join(functionalities),
            limit=model_info[llm_kwargs['llm_model']]['max_token'] * 3 // 4,
            llm_model=llm_kwargs['llm_model']
        )

        summary_fragments = []
        total_fragments = len(functionality_fragments)
        for idx, fragment in enumerate(functionality_fragments, start=1):
            i_say = f'Here are some functionality descriptions of files. Please summarize the main functionalities of the project based on these descriptions: ```{fragment}```'
            gpt_say = request_gpt_model_in_new_thread_with_no_ui(
                inputs=i_say,
                inputs_show_user="Summarizing the main functionalities of the project...",
                llm_kwargs=llm_kwargs,
                history=[],
                sys_prompt="Summarize the main functionalities of the project."
            )
            summary_fragments.append(gpt_say)

        # Directly use the project functionality summaries provided by the GPT model without further summarization
        project_summary = '\n'.join(summary_fragments)

        overall_summary.append({
            'project_summary': project_summary
        })

    # Combine all architecture pattern descriptions for model context
    architecture_descriptions = '\n'.join(architecture_fragments)

    # First prompt: Identify the architecture type
    first_prompt = (
        f"Below are descriptions of known software architecture patterns:\n{architecture_descriptions}\n\n"
        "Based on these descriptions, identify the only one best matched architecture pattern for this project."
    )

    i_say_1 = f"Identify the architecture type: ```{first_prompt}```"
    gpt_response_1 = request_gpt_model_in_new_thread_with_no_ui(
        inputs=i_say_1,
        inputs_show_user="Identifying the best matched architecture pattern...",
        llm_kwargs=llm_kwargs,
        history=[],
        sys_prompt="Identify the best matched architecture pattern."
    )

        # Second prompt: Provide detailed analysis with reasoning
    second_prompt = (
        f"Below is the functionality summary of the project:\n" +
        "\n".join([item['project_summary'] for item in overall_summary]) +
        f"\n\nThe identified architecture pattern is: {gpt_response_1}\n\n"
        "Using the identified architecture pattern and the project information, analyze why this pattern is suitable for the project and provide reasoning."
    )

    i_say_2 = f"Analyze the architecture pattern: ```{second_prompt}```"
    gpt_response_2 = request_gpt_model_in_new_thread_with_no_ui(
        inputs=i_say_2,
        inputs_show_user="Analyzing the architecture pattern with reasoning...",
        llm_kwargs=llm_kwargs,
        history=[],
        sys_prompt="Analyze the architecture pattern with reasoning."
    )

    # Third prompt: Generate JSON output for components
    third_prompt = (
        f"The identified architecture pattern is: {gpt_response_2}.\n"
        f"Based on the only one best matched architecture pattern, create a JSON-formatted output describing the key components of the project.\n"
        "Each component should have three detailed indicators and each indicator should include 3-5 sentences: functionality characteristics, non-functional characteristics, and interactions with other components.\n"
        "The components must cover the entire project without overlapping.\n"
        "Use the following format:\n"
        "```\n"
        "{\n"
        "  \"architecture pattern\":... ,\n"
        "  \"components\": [\n"
        "    {\n"
        "      \"nested\": [\n"
        "        {\"@type\": \"indicator\", \"content\": \"...\"},\n"
        "        {\"@type\": \"indicator\", \"content\": \"...\"},\n"
        "        {\"@type\": \"indicator\", \"content\": \"...\"}\n"
        "      ],\n"
        "      \"@type\": \"component\",\n"
        "      \"name\": \"...\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "```"
    )
    i_say_3 = f"Generate JSON output for components: ```{third_prompt}```"
    gpt_response_3 = request_gpt_model_in_new_thread_with_no_ui(
        inputs=i_say_3,
        inputs_show_user="Generating a JSON-formatted component description...",
        llm_kwargs=llm_kwargs,
        history=[],
        sys_prompt="Generate a JSON-formatted component description."
    )

    # Return combined analysis results and JSON output
    analysis_result = f"Identified Architecture Pattern: {gpt_response_1}\n\nDetailed Analysis:\n{gpt_response_2}\n\nComponent JSON:\n{gpt_response_3}"
    res = write_history_to_file([gpt_response_3])
    promote_file_to_downloadzone(res)
    print("架构模式分析完成")
    return res

def get_arch_semantic():
    folder_path=sys.argv[1]
    project_name = os.path.basename(folder_path)

    llm_kwargs = tl.get_default_kwargs()
    res=execute_parsing_and_analysis(txt_json=folder_path, llm_kwargs=llm_kwargs, plugin_kwargs={}, history=[], system_prompt="")

    json_file_path = f"{project_name}_ArchSem.json"
    md2json(res,json_file_path)
    print(f"架构语义信息已保存到文件: {json_file_path}")

if __name__ == "__main__":
    get_arch_semantic()