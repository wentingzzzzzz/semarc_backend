from transformers import BertTokenizer, BertModel
import torch
from sklearn.decomposition import PCA

# 加载预训练的BERT模型和分词器
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# 示例句子
sentence = "Try to get cached csv data."

# 分词并添加特殊标记
tokens = tokenizer(sentence, return_tensors='pt')

# 获取BERT模型的输出
outputs = model(**tokens)

# 提取句子向量
bert_embedding = torch.mean(outputs.last_hidden_state, dim=1).squeeze().detach().numpy()

# 将一维数组转换为二维数组
# bert_embedding_2d = bert_embedding.reshape(1, -1)

# # 使用PCA降维到100维
# pca = PCA(n_components=100)
# sentence_vector = pca.fit_transform(bert_embedding_2d)

print("句子向量:")
print(bert_embedding)
