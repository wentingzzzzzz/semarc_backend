from gensim.models import Word2Vec
from nltk.tokenize import word_tokenize
import nltk
import numpy as np



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
        # 取词向量的平均值
        sentence_vector = np.mean(word_vectors, axis=0)

    return sentence_vector

# 示例用法
# sentence = "Configuration settings for the Win32 platform."
# result_vector = get_sentence_vector(sentence)
# print("句子向量:")
# print(result_vector)
