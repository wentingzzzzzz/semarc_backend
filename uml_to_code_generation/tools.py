# 为了使用 gpt_academic 而创建的文件
# 实现了直接在 py 文件与 gpt 进行交互

import sys, os
from functools import wraps
from toolbox import load_chat_cookies, read_single_conf_with_lru_cache, get_conf
from request_llms.bridge_all import predict_no_ui_long_connection


# 设置配置函数
def set_conf(key, value):
    read_single_conf_with_lru_cache.cache_clear()
    get_conf.cache_clear()
    os.environ[key] = str(value)
    altered = get_conf(key)
    return altered


# 获取默认 chat 参数
def get_chat_default_kwargs():
    cookies = load_chat_cookies()
    llm_kwargs = {
        'api_key': cookies['api_key'],
        'llm_model': cookies['llm_model'],
        'top_p': 1.0,
        'max_length': None,
        'temperature': 1.0,
    }
    default_chat_kwargs = {
        "inputs": "Hello there, are you ready?",
        "llm_kwargs": llm_kwargs,
        "history": [],
        "sys_prompt": "You are AI assistant",
        "observe_window": None,
        "console_slience": False,
    }

    return default_chat_kwargs


def get_default_kwargs():
    cookies = load_chat_cookies()
    llm_kwargs = {
        'api_key': cookies['api_key'],
        'llm_model': cookies['llm_model'],
        'top_p': 1.0,
        'max_length': None,
        'temperature': 1.0,
    }

    return llm_kwargs

# 标准输出静默装饰器
# 用于临时禁用打印输出。它通过重定向sys.stdout到os.devnull（一个特殊文件，用于
# 丢弃所有写入它的数据）来实现。这对于在不需要命令行输出的情况下运行函数很有用。
def silence_stdout_fn(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        _original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        result = func(*args, **kwargs)
        sys.stdout.close()
        sys.stdout = _original_stdout
        return result

    return wrapper


# 得到 gpt_academic 所编写的与 gpt 进行交互的函数 ( 不涉及 UI 界面 )
def get_chat_handle():
    return predict_no_ui_long_connection


# 定义工具类，作为容器添加各种工具函数
class Tools():
    def __init__(self) -> None:
        pass


# 应用静默装饰器
# 这里将 silence_stdout_fn 装饰器应用于 get_chat_default_kwargs 和 set_conf 函数。
# 这意味着在调用这些函数时，标准输出将被静默。
get_chat_default_kwargs = silence_stdout_fn(get_chat_default_kwargs)
set_conf = silence_stdout_fn(set_conf)
get_default_kwargs = silence_stdout_fn(get_default_kwargs)

# 实例化工具类并添加方法
# 创建 Tools 类的实例，然后将经过装饰器处理的 get_chat_default_kwargs 和 set_conf 方法赋值给这个实例。
# 这样，可以通过这个工具类实例来访问这些方法，同时保持了它们的标准输出静默的特性。
tl = Tools()
tl.get_chat_default_kwargs = get_chat_default_kwargs
tl.set_conf = set_conf
tl.get_default_kwargs = get_default_kwargs
