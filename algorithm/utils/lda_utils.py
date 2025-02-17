import numpy as np 
import gensim
import gensim.corpora as corpora
from algorithm.cache_manager import get_cached_lda_model_path, cache_lda_model
from scipy.cluster.hierarchy import linkage, to_tree, cut_tree
from sklearn.cluster import KMeans, AffinityPropagation, DBSCAN
# import hdbscan

from settings import CACHE_PATH
import logging


#LDA
DEFAULT_NUM_TOPICS = 100
DEFAULT_NUM_CLUSTER = 'auto'
DEFAULT_NUM_LDA_PASS = 50
DEFAULT_LDA_ITER = 50
DEFAULT_VAR_WORD_WEIGHTS = 3

logger = logging.getLogger(__name__)

def get_cluster_number(file_topics_mat, min_cluster_size = 2):
    file_num = len(file_topics_mat)
    Z = linkage(
        file_topics_mat,
        metric='correlation',
        method='complete')
    root = to_tree(Z)
    hierarchy_order = root.pre_order()
    file_topics_mat_sorted = file_topics_mat.copy()
    for i, l in enumerate(file_topics_mat_sorted):
        file_topics_mat_sorted[i] = file_topics_mat[hierarchy_order[i]]
    file_corr_sorted = np.corrcoef(file_topics_mat_sorted)
    
    file_corr_vector_sorted = np.sort(file_corr_sorted.reshape(1,-1))[0]
    corr_thresh = file_corr_vector_sorted[int(0.90*len(file_corr_vector_sorted))]
    file_corr_sorted_booled = file_corr_sorted.copy()
    for i in range(file_num):
        for j in range(file_num):
            file_corr_sorted_booled[i][j] = 1 if file_corr_sorted[i][j]>corr_thresh else 0

    num_cluster = 1
    curr_mat_start = 0
    for i in range(file_num):
        if i == curr_mat_start:
            continue
        if np.sum(file_corr_sorted_booled[i][curr_mat_start:i]) == (i - curr_mat_start):
            continue
        else:
            if (i - curr_mat_start) >= min_cluster_size:
                num_cluster += 1
            curr_mat_start = i
    return num_cluster

def cluster_with_topic_mat(file_topics_mat_norm, num_cluster, cluster_method = 'hierarchy'):
    cluster_method = 'hierarchy'
    # if cluster_method not in SUPPORTED_CLUSTERING_METHODS:
    #     logging.error("Unsupported clustering method: " + cluster_method)
    #     raise 
    if cluster_method == 'hierarchy':
        Z = linkage(
            file_topics_mat_norm,
            metric='correlation',
            method='complete')
        hierarchy_res = cut_tree(Z, num_cluster)
        result = []
        for x in hierarchy_res:
            result.append(x[0])    
    elif cluster_method == 'kmeans':
        estimator = KMeans(n_clusters=num_cluster,
                        n_init = 40,
                        tol=0.0001,
                        init='k-means++')
        result = estimator.fit_predict(file_topics_mat_norm)
    elif cluster_method == 'ap':
        estimator = AffinityPropagation(random_state=5)       
        result = estimator.fit_predict(file_topics_mat_norm)
    elif cluster_method == 'dbscan':
        estimator = DBSCAN(eps = 15,
                        min_samples = 5)
        result = estimator.fit_predict(file_topics_mat_norm)
    # elif cluster_method == 'hdbscan':
    #     estimator = hdbscan.HDBSCAN(min_cluster_size=5,
    #                                cluster_selection_epsilon = 0.8)
    #     result = estimator.fit_predict(file_topics_mat_norm)
    else:
        logging.error("Unimplemented clustering method: " + cluster_method)
        raise NotImplementedError
    return result

def train_lda_model(
    data_words, 
    num_topics = DEFAULT_NUM_TOPICS,
    alpha = None,
    eta = 0.01,
    gamma_threshold = 0.00001,
    random_state = 101,
    dtype = np.float64,
    lda_passes = DEFAULT_NUM_LDA_PASS,
    lda_iter = DEFAULT_LDA_ITER,
    cache_dir = CACHE_PATH
    ):
    # Build LDA model
    if alpha == None:
        alpha = [50 / num_topics] * num_topics
    
    id2word = corpora.Dictionary(data_words)
    texts = data_words
    corpus = [id2word.doc2bow(text) for text in texts]
    
    # try to find cached model
    lda_inputs = (
        data_words, 
        num_topics,
        lda_passes,
        alpha,
        lda_iter,
        eta,
        gamma_threshold,
        random_state,
        dtype)
    cached_lda_path = get_cached_lda_model_path(lda_inputs, cache_dir)
    if cached_lda_path == None:
        logger.info("Start Training LDA.")
        lda_model = gensim.models.LdaMulticore(
            corpus=corpus,
            id2word=id2word,
            num_topics=num_topics,
            passes = lda_passes,
            alpha=alpha,
            iterations = lda_iter,
            eta=eta,
            gamma_threshold = gamma_threshold,
            random_state=random_state,
            dtype = dtype
            )
        cache_lda_model(lda_inputs, lda_model, cache_dir)
    else:
        logging.info("Found cached LDA model!")
        lda_model = gensim.models.LdaModel.load(cached_lda_path)
        id2word = lda_model.id2word
    
    return lda_model, id2word, corpus