import os

from toolbox import get_log_folder

default_user_name = 'default_user'
pj = os.path.join


def promote_file_to_downloadzone(file, rename_file=None):
    # 将文件复制一份到下载区
    import shutil
    user_name = default_user_name
    if not os.path.exists(file):
        raise FileNotFoundError(f'文件{file}不存在')
    user_path = get_log_folder(user_name, plugin_name=None)
    if file_already_in_downloadzone(file, user_path):
        new_path = file
    else:
        user_path = get_log_folder(user_name, plugin_name='downloadzone')
        if rename_file is None: rename_file = f'{gen_time_str()}-{os.path.basename(file)}'
        new_path = pj(user_path, rename_file)
        # 如果已经存在，先删除
        if os.path.exists(new_path) and not os.path.samefile(new_path, file): os.remove(new_path)
        # 把文件复制过去
        if not os.path.exists(new_path): shutil.copyfile(file, new_path)
    return new_path


def file_already_in_downloadzone(file, user_path):
    try:
        parent_path = os.path.abspath(user_path)
        child_path = os.path.abspath(file)
        if os.path.samefile(os.path.commonpath([parent_path, child_path]), parent_path):
            return True
        else:
            return False
    except:
        return False

def gen_time_str():
    import time
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())