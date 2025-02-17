from gensim.models import Word2Vec
from nltk.tokenize import word_tokenize
import nltk
import numpy as np
import json
from transformers import BertTokenizer, BertModel
import torch
from sklearn.decomposition import PCA
import os
from sentence_transformers import SentenceTransformer


def get_sentence_vector(sentence, vector_size=100, window=5, min_count=1, workers=4):
    nltk.download('punkt')
    # 分词
    tokenized_sentence = word_tokenize(sentence.lower())  # 使用小写字母，确保一致性

    # Word2Vec模型训练
    model = Word2Vec([tokenized_sentence], vector_size=vector_size, window=window, min_count=min_count, workers=workers)

    # 获取句子向量
    word_vectors = [model.wv[word] for word in tokenized_sentence if word in model.wv]

    if not word_vectors:
        # 如果句子中的所有词都没有对应的词向量，则返回全零向量
        sentence_vector = np.zeros(vector_size)
    else:
        # 取词向量的平均值（待优化）
        sentence_vector = np.mean(word_vectors, axis=0)

    return sentence_vector

def get_sentence_vector_bert(sentence):
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10809'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10809'
    # 加载预训练的BERT模型和分词器
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased',force_download=True, resume_download=False)
    model = BertModel.from_pretrained('bert-base-uncased',force_download=True, resume_download=False)
    # 分词并添加特殊标记
    tokens = tokenizer(sentence, return_tensors='pt')
    # 获取BERT模型的输出
    outputs = model(**tokens)
    # 提取句子向量
    bert_embedding = torch.mean(outputs.last_hidden_state, dim=1).squeeze().detach().numpy()
    return bert_embedding

def get_sentence_vector_sentence_transformer(sentence):
    # 加载预训练的SentenceTransformer模型
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # 获取句子向量
    sentence_embedding = model.encode(sentence)
    return sentence_embedding

def generate_matrix_from_json(json_path):
    # 读取 JSON 文件
    with open(json_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # 初始化空矩阵
    matrix = []
    

    # 遍历每个条目
    for entry in data['summary']:
        # 获取文件名和功能描述
        print("\nentry:",entry)
        file_name = entry['file']
        functionality = entry['Functionality']

        # 向量化功能描述
        functionality_vector = get_sentence_vector(functionality)

        # 将向量添加到矩阵
        matrix.append(functionality_vector)

    # 转换为NumPy数组
    matrix = np.array(matrix)

    # 返回最终矩阵
    return matrix

# json_path = 'E:\XJTU\架构逆向\lda_demoGPT\experiment\summary.json'
# result_matrix = generate_matrix_from_json(json_path)
# print("最终矩阵:")
# print(result_matrix)