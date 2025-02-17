import json

def bunch_to_json(fn, fn_out = None):
    #!!!
    if fn_out == None:
        fn_out = fn[:-6] + '.json'
        
    dict1 = {}
    dict1["@schemaVersion"] = "1.0"
    dict1["name"] = "clustering"
    dict1["structure"] = []
    cluster_names = []
    with open(fn, 'r') as fp:
        for l in fp:
            if len(l) < 3:
                continue
            # !!!
            cluster_name, filenames = l.split('=')
            cluster_name = cluster_name[3:-2]
            filenames = filenames.split()
            if cluster_name not in cluster_names:
                cluster_names.append(cluster_name)
                dict1["structure"].append({"@type": "group", "name": cluster_name, "nested":[]})
            # dict1["structure"][-1]["nested"].append({"@type":"item", "name":filename.split('.')[-1]})
            for f in filenames:
                f = f.rstrip(',')
                dict1["structure"][-1]["nested"].append({"@type":"item", "name":f})

    with open(fn_out, 'w', newline='') as fp:
        json.dump(dict1, fp, indent = 4)
    