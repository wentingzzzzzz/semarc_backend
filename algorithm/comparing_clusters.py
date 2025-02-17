import os
from typing import List, Tuple, Iterable
from subprocess import Popen, PIPE
import igraph
import hashlib
import tempfile
import logging
from collections import Counter

from settings import MOJO_PATH
from utils.utils import json2cluster_dict


def _save2rsf(result: List[int], fn:str, path="./rsf") -> None:
    if not fn.endswith('.rsf'):
        fn = fn + '.rsf'
    with open(os.path.join(path, fn), 'w') as fp:
        for i, r in enumerate(result):
            l = 'contain c' + str(r) + ' ' + str(i) + '\n'
            fp.write(l)

def fun_MoJoFM_file(res_file, gt_file):
    cmd="java -jar " + MOJO_PATH + " " + res_file + " " + gt_file + " -fm"
    p=Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE)
    out, err=p.communicate(timeout=120)
    p.kill()
    result = out.strip()
    if err:
        logging.error("Failed to get MoJoFM results.")
        logging.error(err.decode())
    try:
        result = float(result) / 100
    except:
        result = -1
    return result

def fun_MoJoFM(result, result_gt, cache = False, path = './rsf'):
    if(cache):
        path = os.path.join(path, 'cache')
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        fn = hashlib.sha256(str(result).encode("utf-8")).hexdigest() + '.rsf'
        if(fn not in os.listdir(path)):
            _save2rsf(result, fn, path)
        fn_gt = hashlib.sha256(str(result_gt).encode("utf-8")).hexdigest() + '.rsf'
        if(fn_gt not in os.listdir(path)):
            _save2rsf(result_gt, fn_gt, path)
        mojo = fun_MoJoFM_file(os.path.join(path, fn), os.path.join(path, fn_gt))
    else:
        with tempfile.TemporaryDirectory() as path:
            fn = "tmp1.rsf"
            fn_gt = "tmp2.rsf"
            _save2rsf(result, fn, path)
            _save2rsf(result_gt, fn_gt, path)
            mojo = fun_MoJoFM_file(os.path.join(path, fn), os.path.join(path, fn_gt))
    return mojo

def fun_ARI(result_a, result_b) -> float:
    # Hubert, Lawrence, and Phipps Arabie. "Comparing partitions." Journal of classification 2.1 (1985): 193-218.
    try:
        if len(result_a) != len(result_b):
            raise
        a = b = c = d = 0.0
        for i in range(len(result_a)):
            for j in range(len(result_a)):
                x = (result_a[i] == result_a[j])
                y = (result_b[i] == result_b[j])
                if x:
                    if y:
                        a += 1
                    else:
                        b += 1
                else:
                    if y:
                        c += 1
                    else:
                        d += 1
        ari = (a - (a+c)*(a+b)/(a+b+c+d)) / (((a+c)+(a+b))/2 - (a+c)*(a+b)/(a+b+c+d))
    except:
        ari = -1
    return ari

def fun_ARI_2(result_a, result_b) -> float:
    # Hubert, Lawrence, and Phipps Arabie. "Comparing partitions." Journal of classification 2.1 (1985): 193-218.
    def cn2(x):
        return x*(x-1)/2
    assert len(result_a) == len(result_b)
    n = dict(Counter(zip(result_a,result_b)))
    a = dict(Counter(result_a))
    b = dict(Counter(result_b))

    sumn = sum(map(cn2, n.values()))
    suma = sum(map(cn2, a.values()))
    sumb = sum(map(cn2, b.values()))
    sumn_2 = cn2(len(result_a))
    exp = suma/sumn_2*sumb

    ari = (sumn - exp) / (0.5*(suma+sumb)-exp)
    return ari




def fun_RI(result_a, result_b) -> float:
    # Hubert, Lawrence, and Phipps Arabie. "Comparing partitions." Journal of classification 2.1 (1985): 193-218.
    try:
        if len(result_a) != len(result_b):
            raise
        a = b = c = d = 0.0
        for i in range(len(result_a)):
            for j in range(len(result_a)):
                x = (result_a[i] == result_a[j])
                y = (result_b[i] == result_b[j])
                if x:
                    if y:
                        a += 1
                    else:
                        b += 1
                else:
                    if y:
                        c += 1
                    else:
                        d += 1
        ri = (a + d) / (a+b+c+d)
    except:
        ri = -1
    return ri

def fun_a2a_file_wrong(res_file, gt_file) -> float:
    try:
        f=open(res_file,"r")
        lines=f.readlines()
        f.close()

        a1={}
        for line in lines:
            templist=line.strip().split(" ")
            if not a1.__contains__(templist[1]):
                a1[templist[1]]=[]
                pass
            a1[templist[1]].append(templist[2])


        f=open(gt_file,"r")
        lines=f.readlines()
        f.close()

        a2={}
        for line in lines:
            templist=line.strip().split(" ")
            #print templist
            if not a2.__contains__(templist[1]):
                a2[templist[1]]=[]
                pass
            a2[templist[1]].append(templist[2])

        match_type=[]
        for i in range(0,len(a1)):
            match_type.append(0)
            pass

        for i in range(0,len(a2)):
            match_type.append(1)
            pass


        edge_dict={}
        for temp1 in range(0,len(a1)):
            for temp2 in range(0,len(a2)):
                edge_dict[(temp1,temp2+len(a1))]=len(set(list(a1.values())[temp1])&set(list(a2.values())[temp2]))
                pass



        g=igraph.Graph()
        g.add_vertices(len(a1)+len(a2))

        g.add_edges(edge_dict.keys())

        matching=g.maximum_bipartite_matching(match_type, list(edge_dict.values()))

        removeA=[]
        moveAB=[]
        addB=[]

        for i in range(0,len(a1)+len(a2)):
            if i<len(a1):
                if matching.match_of(i)==None:
                    removeA.append(i)
                    pass
                else:
                    moveAB.append((i,matching.match_of(i)))
                    pass
                pass
            else:
                if matching.match_of(i)==None:
                    addB.append(i)
                pass
            pass

        mto=0

        for i in removeA:
            mto+=len(list(a1.values())[i])
            mto+=1
            pass
        for i in addB:
            mto+=len(list(a2.values())[i-len(a1)])
            mto+=1
            pass
        for temp in moveAB:
            mto+=len(list(a1.values())[temp[0]])-edge_dict[temp]+len(list(a2.values())[temp[1]-len(a1)])-edge_dict[temp]
            pass

        # print mto

        aco1=sum(map(len,a1.values()))+len(a1)
        aco2=sum(map(len,a2.values()))+len(a2)


        a2a=1-float(mto)/(float(aco1)+float(aco2))
    except:
        a2a = -1

    # print(a2a)
    return a2a

def fun_a2a_wrong(result, result_gt, cache = False, path = './rsf') -> bytes:
    if(cache):
        path = os.path.join(path, 'cache')
        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        fn = hashlib.sha256(str(result).encode("utf-8")).hexdigest() + '.rsf'
        if(fn not in os.listdir(path)):
            _save2rsf(result, fn, path)
        fn_gt = hashlib.sha256(str(result_gt).encode("utf-8")).hexdigest() + '.rsf'
        if(fn_gt not in os.listdir(path)):
            _save2rsf(result_gt, fn_gt, path)
        a2a = fun_a2a_file_wrong(os.path.join(path, fn), os.path.join(path, fn_gt))
    else:
        with tempfile.TemporaryDirectory() as path:
            fn = "tmp1.rsf"
            fn_gt = "tmp2.rsf"
            _save2rsf(result, fn, path)
            _save2rsf(result_gt, fn_gt, path)
            a2a = fun_a2a_file_wrong(os.path.join(path, fn), os.path.join(path, fn_gt))
    return a2a

def fun_a2a_zyr(result, result_gt):
    result_clusters = {}
    for i, r in enumerate(result):
        try:
            result_clusters[f'c{r}'].append(i)
        except KeyError:
            result_clusters[f'c{r}'] = [i]

    result_clusters_gt = {}
    for i, r in enumerate(result_gt):
        try:
            result_clusters_gt[f'cgt{r}'].append(i)
        except KeyError:
            result_clusters_gt[f'cgt{r}'] = [i]


    edge_dict={}
    for k in result_clusters:
        for k_gt in result_clusters_gt:
            edge_dict[(k,k_gt)] = len(set(result_clusters[k]) & set(result_clusters_gt[k_gt]))



    match_type=[0]*len(result_clusters) + [1]*len(result_clusters_gt)
    g=igraph.Graph()
    g.add_vertices(list(result_clusters.keys()))
    g.add_vertices(list(result_clusters_gt.keys()))
    g.add_edges(edge_dict.keys())
    matching=g.maximum_bipartite_matching(match_type, list(edge_dict.values()))

    removeA=[]
    moveAB=[]
    addB=[]

    for i in range(len(result_clusters)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            removeA.append(name)
        else:
            name2 = g.vs[matching.match_of(i)]['name']
            moveAB.append((name, name2))

    for i in range(len(result_clusters), len(result_clusters)+len(result_clusters_gt)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            addB.append(name)

    mto=0
    for k in removeA:
        mto += len(result_clusters[k])
        mto += 1
    for k in addB:
        # mto += len(result_clusters_gt[k])
        mto += 1
    for (k, k_gt) in moveAB:
        mto += (len(result_clusters[k]) - edge_dict[(k,k_gt)])
        pass

    aco1=sum(map(len,result_clusters.values()))+len(result_clusters)
    aco2=sum(map(len,result_clusters_gt.values()))+len(result_clusters_gt)

    try:
        a2a = 1-float(mto)/2/(float(aco1)+float(aco2))
    except ZeroDivisionError:
        a2a = -1

    return a2a

def fun_a2a_adj(result, result_gt):


    def max_distance_a2a(result, result_gt):
        a = max(result)+1
        b = max(result_gt)+1
        p = min(a,b)
        q = max(a,b)
        return len(result) - len(result)//q

    def get_exp_mto(m, n):
        t = min(m,n)
        n = max(m,n)
        m = t

        sum_now = 0
        for i in range(0,m):
            for j in range(0,m-i):
                sum_now += 1/((m-i)*(m-j))
        return sum_now

    result_clusters = {}
    for i, r in enumerate(result):
        try:
            result_clusters[f'c{r}'].append(i)
        except KeyError:
            result_clusters[f'c{r}'] = [i]

    result_clusters_gt = {}
    for i, r in enumerate(result_gt):
        try:
            result_clusters_gt[f'cgt{r}'].append(i)
        except KeyError:
            result_clusters_gt[f'cgt{r}'] = [i]


    edge_dict={}
    for k in result_clusters:
        for k_gt in result_clusters_gt:
            edge_dict[(k,k_gt)] = len(set(result_clusters[k]) & set(result_clusters_gt[k_gt]))



    match_type=[0]*len(result_clusters) + [1]*len(result_clusters_gt)
    g=igraph.Graph()
    g.add_vertices(list(result_clusters.keys()))
    g.add_vertices(list(result_clusters_gt.keys()))
    g.add_edges(edge_dict.keys())
    matching=g.maximum_bipartite_matching(match_type, list(edge_dict.values()))

    removeA=[]
    moveAB=[]
    addB=[]

    for i in range(len(result_clusters)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            removeA.append(name)
        else:
            name2 = g.vs[matching.match_of(i)]['name']
            moveAB.append((name, name2))

    for i in range(len(result_clusters), len(result_clusters)+len(result_clusters_gt)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            addB.append(name)

    mto_move=0
    mto_add=0
    mto_del=0
    for k in removeA:
        # mto_del += len(result_clusters[k])
        mto_move += len(result_clusters[k])
        mto_del += 1
    for k in addB:
        # mto_add += len(result_clusters_gt[k])
        mto_add += 1
    for (k, k_gt) in moveAB:
        mto_move += (len(result_clusters[k]) - edge_dict[(k,k_gt)])
        pass

    max_mto = max_distance_a2a(result, result_gt)
    exp_mto = get_exp_mto(len(result_clusters), len(result_clusters_gt)) * max_mto / 2




    aco1=sum(map(len,result_clusters.values()))+len(result_clusters)
    aco2=sum(map(len,result_clusters_gt.values()))+len(result_clusters_gt)


    move_factor = len(result) + min(len(result_clusters), len(result_clusters_gt))
    ar_factor = abs(len(result_clusters) - len(result_clusters_gt))

    # a2a_adj = 1 - (mto_move+mto_add+mto_del)/(max_mto-exp_mto+mto_add+mto_del)
    # a2a_adj = 1 - mto_move/(max_mto-exp_mto) - (mto_add+mto_del)/(aco1+aco2)
    a2a_adj = 1 - mto_move/max_mto/2 - (mto_add+mto_del)/(aco1+aco2) # v1

    # try:
    #     a2a = 1-float(mto)/(float(aco1)+float(aco2))
    # except ZeroDivisionError:
    #     a2a = -1

    return a2a_adj

def fun_a2a_adj_v2(result, result_gt):


    def max_distance_a2a(result, result_gt):
        a = max(result)+1
        b = max(result_gt)+1
        p = min(a,b)
        q = max(a,b)
        return len(result) - len(result)//q

    def get_exp_mto(m, n):
        t = min(m,n)
        n = max(m,n)
        m = t

        sum_now = 0
        for i in range(0,m):
            for j in range(0,m-i):
                sum_now += 1/((m-i)*(m-j))
        return sum_now

    result_clusters = {}
    for i, r in enumerate(result):
        try:
            result_clusters[f'c{r}'].append(i)
        except KeyError:
            result_clusters[f'c{r}'] = [i]

    result_clusters_gt = {}
    for i, r in enumerate(result_gt):
        try:
            result_clusters_gt[f'cgt{r}'].append(i)
        except KeyError:
            result_clusters_gt[f'cgt{r}'] = [i]


    edge_dict={}
    for k in result_clusters:
        for k_gt in result_clusters_gt:
            edge_dict[(k,k_gt)] = len(set(result_clusters[k]) & set(result_clusters_gt[k_gt]))



    match_type=[0]*len(result_clusters) + [1]*len(result_clusters_gt)
    g=igraph.Graph()
    g.add_vertices(list(result_clusters.keys()))
    g.add_vertices(list(result_clusters_gt.keys()))
    g.add_edges(edge_dict.keys())
    matching=g.maximum_bipartite_matching(match_type, list(edge_dict.values()))

    removeA=[]
    moveAB=[]
    addB=[]

    for i in range(len(result_clusters)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            removeA.append(name)
        else:
            name2 = g.vs[matching.match_of(i)]['name']
            moveAB.append((name, name2))

    for i in range(len(result_clusters), len(result_clusters)+len(result_clusters_gt)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            addB.append(name)

    mto_move=0
    mto_add=0
    mto_del=0
    for k in removeA:
        mto_del += len(result_clusters[k])
        mto_del += 1
    for k in addB:
        mto_add += len(result_clusters_gt[k])
        mto_add += 1
    for (k, k_gt) in moveAB:
        mto_move += (len(result_clusters[k]) - edge_dict[(k,k_gt)])
        pass

    max_mto = max_distance_a2a(result, result_gt)
    exp_mto = (get_exp_mto(len(result_clusters), len(result_clusters_gt)) * 1.1 - 0.95) * len(result)




    aco1=sum(map(len,result_clusters.values()))+len(result_clusters)
    aco2=sum(map(len,result_clusters_gt.values()))+len(result_clusters_gt)


    # a2a_adj = 1 - (mto_move+mto_add+mto_del)/(max_mto-exp_mto+mto_add+mto_del)
    # a2a_adj = 1 - mto_move/(max_mto-exp_mto) - (mto_add+mto_del)/(aco1+aco2)
    # a2a_adj = 1 - mto_move/max_mto/2 - (mto_add+mto_del)/(aco1+aco2) # v1

    a2a = 1-float(mto_move+mto_add+mto_del)/(float(aco1)+float(aco2))
    a2a_exp = 1-float(exp_mto+mto_add+mto_del)/(float(aco1)+float(aco2))

    a2a_exp /= 2
    a2a_adj = (a2a-a2a_exp)/(1-a2a_exp)

    # try:
    #     a2a = 1-float(mto)/(float(aco1)+float(aco2))
    # except ZeroDivisionError:
    #     a2a = -1

    return max(a2a_adj, 0)

def fun_a2a_adj_v3(result, result_gt):


    def max_distance_a2a(result, result_gt):
        a = max(result)+1
        b = max(result_gt)+1
        p = min(a,b)
        q = max(a,b)
        return len(result) - len(result)//q

    def get_exp_mto(m, n):
        t = min(m,n)
        n = max(m,n)
        m = t

        sum_now = 0
        for i in range(0,m):
            for j in range(0,m-i):
                sum_now += 1/((m-i)*(m-j))
        return sum_now

    result_clusters = {}
    for i, r in enumerate(result):
        try:
            result_clusters[f'c{r}'].append(i)
        except KeyError:
            result_clusters[f'c{r}'] = [i]

    result_clusters_gt = {}
    for i, r in enumerate(result_gt):
        try:
            result_clusters_gt[f'cgt{r}'].append(i)
        except KeyError:
            result_clusters_gt[f'cgt{r}'] = [i]


    edge_dict={}
    for k in result_clusters:
        for k_gt in result_clusters_gt:
            edge_dict[(k,k_gt)] = len(set(result_clusters[k]) & set(result_clusters_gt[k_gt]))



    match_type=[0]*len(result_clusters) + [1]*len(result_clusters_gt)
    g=igraph.Graph()
    g.add_vertices(list(result_clusters.keys()))
    g.add_vertices(list(result_clusters_gt.keys()))
    g.add_edges(edge_dict.keys())
    matching=g.maximum_bipartite_matching(match_type, list(edge_dict.values()))

    removeA=[]
    moveAB=[]
    addB=[]

    for i in range(len(result_clusters)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            removeA.append(name)
        else:
            name2 = g.vs[matching.match_of(i)]['name']
            moveAB.append((name, name2))

    for i in range(len(result_clusters), len(result_clusters)+len(result_clusters_gt)):
        name = g.vs[i]['name']
        if matching.match_of(i) == None:
            addB.append(name)

    mto_move=0
    mto_add=0
    mto_del=0
    for k in removeA:
        # mto_del += len(result_clusters[k])
        mto_move += len(result_clusters[k])
        mto_del += 1
    for k in addB:
        # mto_add += len(result_clusters_gt[k])
        mto_add += 1
    for (k, k_gt) in moveAB:
        mto_move += (len(result_clusters[k]) - edge_dict[(k,k_gt)])
        pass

    max_mto = max_distance_a2a(result, result_gt)
    exp_mto = get_exp_mto(len(result_clusters), len(result_clusters_gt)) * max_mto / 2




    aco1=sum(map(len,result_clusters.values()))+len(result_clusters)
    aco2=sum(map(len,result_clusters_gt.values()))+len(result_clusters_gt)


    move_entity = len(result) + min(len(result_clusters), len(result_clusters_gt))
    ar_entity = abs(len(result_clusters) - len(result_clusters_gt))

    move_factor = move_entity / (move_entity+ar_entity)
    ar_factor = ar_entity / (move_entity+ar_entity)

    a2a_adj = 1 - mto_move/max_mto*move_factor - (mto_add+mto_del)/(aco1+aco2)*ar_factor

    # try:
    #     a2a = 1-float(mto)/(float(aco1)+float(aco2))
    # except ZeroDivisionError:
    #     a2a = -1

    return a2a_adj

def fun_c2c_cvg(result, result_gt, thresh=0.5):

    result_clusters = {}
    for i, r in enumerate(result):
        try:
            result_clusters[f'c{r}'].append(i)
        except KeyError:
            result_clusters[f'c{r}'] = [i]

    result_clusters_gt = {}
    for i, r in enumerate(result_gt):
        try:
            result_clusters_gt[f'cgt{r}'].append(i)
        except KeyError:
            result_clusters_gt[f'cgt{r}'] = [i]

    c2c_dict = {}
    c2c_max_dict = {}
    for k1, c1 in result_clusters.items():
        c2c_max = -1
        for k2, c2 in result_clusters_gt.items():
            c2c = len(set(c1)& set(c2)) / max(len(c1), len(c2))
            c2c_dict[(k1,k2)] = c2c
            c2c_max = max(c2c_max, c2c)
        c2c_max_dict[k1] = c2c_max

    simc = len([0 for v in c2c_max_dict.values() if v > thresh])
    c2c_cvg = simc/len(result_clusters)
    return c2c_cvg

def fun_c2c_cvg_66(result, result_gt, thresh=0.66):
    return fun_c2c_cvg(result, result_gt, thresh=thresh)

def fun_c2c_cvg_33(result, result_gt, thresh=0.33):
    return fun_c2c_cvg(result, result_gt, thresh=thresh)

def fun_c2c_cvg_10(result, result_gt, thresh=0.1):
    return fun_c2c_cvg(result, result_gt, thresh=thresh)
#     pass
# fun_c2c_cvg([0,0,0,1,1,1], [1,1,0,1,0,0])
# def fun_mto(result, result_gt):


#     def max_distance_a2a(result, result_gt):
#         a = max(result)+1
#         b = max(result_gt)+1
#         p = min(a,b)
#         q = max(a,b)
#         return len(result) - len(result)//q

#     def get_exp_mto(m, n):
#         t = min(m,n)
#         n = max(m,n)
#         m = t

#         sum_now = 0
#         for i in range(0,m):
#             for j in range(0,m-i):
#                 sum_now += 1/((m-i)*(m-j))
#         return sum_now

#     result_clusters = {}
#     for i, r in enumerate(result):
#         try:
#             result_clusters[f'c{r}'].append(i)
#         except KeyError:
#             result_clusters[f'c{r}'] = [i]

#     result_clusters_gt = {}
#     for i, r in enumerate(result_gt):
#         try:
#             result_clusters_gt[f'cgt{r}'].append(i)
#         except KeyError:
#             result_clusters_gt[f'cgt{r}'] = [i]


#     edge_dict={}
#     for k in result_clusters:
#         for k_gt in result_clusters_gt:
#             edge_dict[(k,k_gt)] = len(set(result_clusters[k]) & set(result_clusters_gt[k_gt]))



#     match_type=[0]*len(result_clusters) + [1]*len(result_clusters_gt)
#     g=igraph.Graph()
#     g.add_vertices(list(result_clusters.keys()))
#     g.add_vertices(list(result_clusters_gt.keys()))
#     g.add_edges(edge_dict.keys())
#     matching=g.maximum_bipartite_matching(match_type, list(edge_dict.values()))

#     removeA=[]
#     moveAB=[]
#     addB=[]

#     for i in range(len(result_clusters)):
#         name = g.vs[i]['name']
#         if matching.match_of(i) == None:
#             removeA.append(name)
#         else:
#             name2 = g.vs[matching.match_of(i)]['name']
#             moveAB.append((name, name2))

#     for i in range(len(result_clusters), len(result_clusters)+len(result_clusters_gt)):
#         name = g.vs[i]['name']
#         if matching.match_of(i) == None:
#             addB.append(name)

#     mto_move=0
#     mto_add=0
#     mto_del=0
#     for k in removeA:
#         mto_del += len(result_clusters[k])
#         mto_del += 1
#     for k in addB:
#         mto_add += len(result_clusters_gt[k])
#         mto_add += 1
#     for (k, k_gt) in moveAB:
#         mto_move += (len(result_clusters[k]) - edge_dict[(k,k_gt)])
#         pass

#     return float(mto_move)

# def max_distance_a2a(result, result_gt):
#     a = max(result)+1
#     b = max(result_gt)+1
#     p = min(a,b)
#     q = max(a,b)
#     return float(len(result) - len(result)//q)

# def get_exp_mto(result, result_gt):
#     m = max(result)+1
#     n = max(result_gt)+1
#     t = min(m,n)
#     n = max(m,n)
#     m = t

#     sum_now = 0
#     for i in range(0,m):
#         for j in range(0,m-i):
#             sum_now += 1/((m-i)*(m-j))
#     return float(sum_now)


# a = fun_a2a_zyr([0,0,0,1,1,1], [1,1,0,1,0,0])
# b = fun_a2a([0,0,0,1,1,1], [1,1,0,1,0,0])
# assert a==b

def compare_two_cluster_results(result_dict1, result_dict2, metric_names:Iterable[str]=None)->dict:
    error_flag = False
    if metric_names == None:
        metric_names = METRICS_TO_FUNCTION
    for n in metric_names:
        if n not in METRICS_TO_FUNCTION:
            logging.error("Unsupported metric name: " + n)
            error_flag = True
    if error_flag:
        return None
    filelist = [fn for fn in result_dict1 if fn in result_dict2] #result_dict内容为文件名：簇号
    filelist = sorted(filelist)
    result1 = list(map(lambda x:result_dict1[x], filelist))
    result2 = list(map(lambda x:result_dict2[x], filelist))
    metrics_result = {}
    for metric in METRICS_TO_FUNCTION:
        try:
            metrics_result[metric] = METRICS_TO_FUNCTION[metric](result1, result2)
        except Exception as e:
            metrics_result[metric] = 0
            logging.error("Error when calculating metric " + metric + ": " + str(e))
    return metrics_result

METRICS_TO_FUNCTION = {
    'MoJoFM': fun_MoJoFM,
    'a2a': fun_a2a_zyr,
    'ARI': fun_ARI_2,
    # 'ARI': fun_ARI,
    'a2a_adj': fun_a2a_adj_v3,
    # 'c2c_cvg': fun_c2c_cvg,
    'c2c_cvg_66': fun_c2c_cvg_66,
    'c2c_cvg_50': fun_c2c_cvg,
    # 'c2c_cvg_33': fun_c2c_cvg_33,
    # 'c2c_cvg_10': fun_c2c_cvg_10,

    # 'ARI2': fun_ARI_2,
    # 'a2a': fun_a2a,
    # 'RI': fun_RI,
    # 'a2a_adj_v1': fun_a2a_adj,
    # 'a2a_adj_v2': fun_a2a_adj_v2,
    # 'mto': fun_mto,
    # 'exp': get_exp_mto,
    # 'max': max_distance_a2a,
}
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

def main():
    # 解析 RSF 文件
    result_dict = parse_rsf_file("E:\\recovery-master\\test\\bbb-acdc.rsf")
    # 将 JSON 文件转换为集群字典
    gt_dict = json2cluster_dict("E:\\recovery-master\\test\\bigbluebutton_gt.json")
    # 比较两个集群结果
    metrics_result_dict = compare_two_cluster_results(result_dict, gt_dict)
    # 打印比较结果
    print(metrics_result_dict)

if __name__ == "__main__":
    main()
