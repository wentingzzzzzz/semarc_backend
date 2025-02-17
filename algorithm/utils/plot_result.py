import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
import math
from matplotlib import colors

matplotlib.set_loglevel("info")

X_SPACE = 0.6
Y_SPACE = 1.5
Y_SPACE = 15
SUBPLOT_BOARDER_SPACE = 0.4
SUBPLOT_SPACE = 0.3
FONT_SIZE = 14

color_list = ['red', 'green', 'blue', 'plum', 'darkkhaki', 'slateblue', 'tan', 'yellowgreen', 'peru', 'violet', 'indigo', 'tomato', 'maroon', 'palegreen', 'teal', 'lime','seashell', 'olive', 'navy',
            'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque',
            'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse',
            'chocolate', 'coral', 'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan',
            'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange',
            'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise',
            'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'firebrick', 'floralwhite',
            'forestgreen', 'fuchsia', 'black']

def _get_box_sizes(data):
    box_sizes = []
    for d in data:
        l = len(d)
        if l == 0:
            box_sizes.append((1, 1))
            continue
        width = math.ceil(math.sqrt(l/0.8))
        height = math.ceil(l/width)
        box_sizes.append((width, height))
    return box_sizes
    
def _separate_boxes(box_sizes):
    sum_x = sum(x for x,y in box_sizes)
    expect_num_lines = 1
    while True:
        separated_boxes = []
        # line_sizes = []
        # for i in range(num_lines):
        #     separated_boxes.append([])
        max_x_len = math.ceil(sum_x/expect_num_lines)
        
        line_now = 0
        max_x_len_in_fact = 0 # 实际最大的x
        x_len_now = box_sizes[0][0]
        separated_boxes.append([box_sizes[0]])
        for box in box_sizes[1:]:
            x_len_now += box[0]
            if (x_len_now > max_x_len) and x_len_now != box[0]:
                max_x_len_this_line = sum(x for x,y in separated_boxes[line_now])
                max_x_len_in_fact = max(max_x_len_in_fact, max_x_len_this_line)
                # line_sizes.append([max_x_len_this_line, 0])
                x_len_now = 0
                line_now += 1
                separated_boxes.append([box])
                continue
            else:
                separated_boxes[line_now].append(box)
        max_x_len_this_line = sum(x for x,y in separated_boxes[line_now])
        max_x_len_in_fact = max(max_x_len_in_fact, max_x_len_this_line)
        # line_sizes.append([max_x_len_this_line, 0])

        y_len = 0
        for i, l in enumerate(separated_boxes):
            y_max = max(l, key=lambda item:item[1])[1]
            # line_sizes[i][1] = y_max
            y_len += y_max

        if (max_x_len_in_fact / y_len) < 2:
            break
        else:
            expect_num_lines += 1
    # return separated_boxes, line_sizes
    return separated_boxes

def _add_space_to_separate_boxes(separated_box_sizes_no_space, box_sizes):
    separated_box_sizes = []
    i = 0
    for l in separated_box_sizes_no_space:
        tmp = []
        for box in l:
            x = box[0] + SUBPLOT_BOARDER_SPACE * 2 + SUBPLOT_SPACE * (box_sizes[i][0] - 1)
            y = box[1] + SUBPLOT_BOARDER_SPACE * 2 + SUBPLOT_SPACE * (box_sizes[i][1] - 1)
            tmp.append((x,y))
            i += 1
        separated_box_sizes.append(tmp)
    x_total = 0
    for l in separated_box_sizes:
        x_line = sum(x for x,y in l) +  X_SPACE * (len(l)- 1)
        x_total = max(x_total, x_line)
    y_total = 0
    for l in separated_box_sizes:
        y_total += max(l, key=lambda box:box[1])[1]
        y_total += Y_SPACE
    y_total -= Y_SPACE

    return separated_box_sizes, (x_total, y_total)

def _plot_one_subplot(ax, data, box_size, title, max_title_len, font_size, title_padding, edge_width, add_text = True):
    """ 绘制图中的单个group """
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim([-SUBPLOT_BOARDER_SPACE, box_size[0] + (box_size[0] - 1) * SUBPLOT_SPACE  + SUBPLOT_BOARDER_SPACE])
    ax.set_ylim([-SUBPLOT_BOARDER_SPACE, box_size[1] + (box_size[1] - 1) * SUBPLOT_SPACE  + SUBPLOT_BOARDER_SPACE])
    ax.invert_yaxis()
    # !!!
    max_title_len = 100
    font_size = 3
    if len(title) > max_title_len:
        title = title[0:max_title_len-2] + '...'
    ax.set_title(
        title, 
        fontsize=font_size,
        pad=title_padding)

    data = sorted(data)
    for i, d in enumerate(data):
        x = (i % box_size[0]) * (1 + SUBPLOT_SPACE)
        y = math.floor(i/box_size[0]) * (1 + SUBPLOT_SPACE)
        c = colors.to_rgba(color_list[d%len(color_list)])
        rect = patches.Rectangle((x, y), 1, 1, linewidth=edge_width, edgecolor = 'gray', facecolor=c)

        ax.add_patch(rect)
        
        if add_text and d != -1:
            inv_c = (1-c[0], 1-c[1], 1-c[2], c[3])
            if d >= 100:
                text_size = font_size-4
                x_offset = 0.05
            if d >= 10:
                text_size = font_size-2
                x_offset = 0.2
            else:
                text_size = font_size-2
                x_offset = 0.35
            ax.text(x+x_offset, y+0.65, d, fontsize=text_size, color=inv_c)

def plot_result(clustering_data, cluster_titles, savefig = True, figname = 'a.png', show_fig = True, add_text = True, title = None, add_boarder = False):
    # keep_list = []
    # for i in range(len(clustering_data)):
    #     if len(clustering_data[i]) > 0:
    #         keep_list.append(i)
    # clustering_data2 = []
    # cluster_titles2 = []
    # for i in keep_list:
    #     clustering_data2.append(clustering_data[i])
    #     cluster_titles2.append(cluster_titles[i])
    # clustering_data = clustering_data2
    # cluster_titles = cluster_titles2

    # get box sizes
    box_sizes = _get_box_sizes(clustering_data)
    separated_box_sizes_no_space = _separate_boxes(box_sizes)
    separated_box_sizes, (x_points, y_points) = _add_space_to_separate_boxes(separated_box_sizes_no_space, box_sizes)
    
    # fig setting
    fig = plt.figure(figsize = (6,6))
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0, hspace=0)
    fig_x_size = 1000
    fig_y_size = 1000
    sup_title_gap = 0.1

    if title != None:
        ax = plt.subplot2grid(
                    (fig_y_size, fig_x_size), 
                    (0, 0), 
                    colspan = fig_x_size, 
                    rowspan = math.floor(fig_y_size/10)) 
        ax.axis('off')
        ax.text(0.5, 0.9, title,
        fontsize=14, weight='semibold',
        horizontalalignment='center',
        transform=ax.transAxes)

    scale_factor = min(math.floor(fig_x_size / x_points), math.floor(fig_y_size / y_points))
    title_font_size = 6 + math.floor(scale_factor/10)
    title_padding = 2 + title_font_size / 4 *1.5
    edge_width = scale_factor / 30

    # plot
    x_now = 0
    y_now = math.floor(fig_y_size/10)
    data_ind = 0
    for line in separated_box_sizes:
        for box in line:
            ax = plt.subplot2grid(
                (fig_y_size, fig_x_size), 
                (y_now, x_now), 
                colspan = math.floor(box[0]*scale_factor), 
                rowspan = math.floor(box[1]*scale_factor))

            title_max_char = math.floor(box[0]*scale_factor/title_font_size/14*8)

            _plot_one_subplot(ax, clustering_data[data_ind], box_sizes[data_ind], cluster_titles[data_ind], title_max_char, title_font_size, title_padding, edge_width, add_text)
            data_ind += 1
            x_now += math.floor((box[0] + X_SPACE) * scale_factor)
        x_now = 0
        y_now += math.floor(max(line, key=lambda l:l[1])[1]*scale_factor + title_font_size * 5 + title_padding)

    import matplotlib.lines as lines
    # add boarder
    border_gap_x = 0.05
    border_gap_y_bot = 0.05
    border_gap_y_top = 0.015
    xmin = 0.125 - border_gap_x
    xmax = 0.9 + border_gap_x - (fig_x_size-scale_factor*x_points)/fig_x_size * 0.775
    # ymin = 0.11 - border_gap_y_bot \
    #     + (fig_y_size-(y_now-(title_font_size * 5 + title_padding)))/fig_y_size * 0.77
        
    ymin = 0.16 - border_gap_y_bot \
        + (fig_y_size-(y_now-(title_font_size * 5 + title_padding)))/fig_y_size * 0.77
    ymax = 0.88 + border_gap_y_top - sup_title_gap * 0.77 + title_font_size / 10 * 0.028
    if add_boarder:
        fig.add_artist(lines.Line2D([xmin, xmin], [ymin, ymax], color='black', linewidth=0.5))
        fig.add_artist(lines.Line2D([xmax, xmax], [ymin, ymax], color='black', linewidth=0.5))
        fig.add_artist(lines.Line2D([xmin, xmax], [ymin, ymin], color='black', linewidth=0.5))
        fig.add_artist(lines.Line2D([xmin, xmax], [ymax, ymax], color='black', linewidth=0.5))

    # savefig & show
    if savefig:
        title_height = 0.08 if title != None else 0.005
        save_fig_bbox = matplotlib.transforms.Bbox.from_extents(
            max(6*xmin-0.1, 0), # xmin
            max(6*ymin-0.1, 0), # ymin
            min(6*xmax+0.1, 6), # xmax
            min(6*(ymax+title_height), 6)) # ymax
        plt.savefig(figname, dpi = 300, transparent=True, 
            bbox_inches=save_fig_bbox)
    if show_fig:
        plt.show()

def plot_two_result_list(result, result_gt, titles = None, figname = "", show_fig = True, add_text = True, fig_title = None, add_boarder = False):
    clustering_data = []
    for i in range(max(result_gt)+1):
        inds = [ind for ind in range(len(result_gt)) if result_gt[ind] == i]
        tmp = [result[ind] for ind in inds]
        clustering_data.append(tmp)
    if titles == None:
        titles = []
        for i in range(len(clustering_data)):
            titles.append('Group ' + str(i))
    if figname == "":
        plot_result(clustering_data, titles, show_fig=show_fig, add_text=add_text, title=fig_title, add_boarder=add_boarder)
    else:
        plot_result(clustering_data, titles, figname=figname, show_fig=show_fig, add_text=add_text, title=fig_title, add_boarder=add_boarder)

import json
def json2cluster_dict(json_fn, get_titles = False):
    with open(json_fn) as fp:
        cluster_js = json.load(fp)
        cluster_dict = {}
        title_list = []
        for i, cluster in enumerate(cluster_js['structure']):
            if get_titles:
                title_list.append(cluster['name'])
            for f in cluster['nested']:
                cluster_dict[f['name']] = i
    if get_titles:
        return cluster_dict, title_list
    else:
        return cluster_dict

def plot_two_json(json_fn, json_fn_gt, figname = "", show_fig = True, add_text = True, fig_title = None, add_boarder = False):
    dict_res = json2cluster_dict(json_fn)
    dict_gt, titles = json2cluster_dict(json_fn_gt, get_titles=True)
    filelist = [fn for fn in dict_res if fn in dict_gt]

    clustering_data = []
    for i in range(max(dict_gt.values())+1):
        tmp = [fn for fn in dict_gt if dict_gt[fn]==i]
        tmp = [fn for fn in tmp if fn in filelist]
        tmp = list(map(lambda x:dict_res[x], tmp))
        clustering_data.append(tmp)
    if figname == "":
        plot_result(clustering_data, titles, show_fig=show_fig, add_text=add_text, title=fig_title, add_boarder=add_boarder)
    else:
        plot_result(clustering_data, titles, figname=figname, show_fig=show_fig, add_text=add_text, title=fig_title, add_boarder=add_boarder)

def plot_two_dict(dict_res, dict_gt, titles=None, figname = "", show_fig = True, add_text = True, fig_title = None, add_boarder = False):
    filelist = [fn for fn in dict_res if fn in dict_gt]
    clustering_data = []
    for i in range(max(dict_gt.values())+1):
        tmp = [fn for fn in dict_gt if dict_gt[fn]==i]
        tmp = [fn for fn in tmp if fn in filelist]
        tmp = list(map(lambda x:dict_res[x], tmp))
        clustering_data.append(tmp)
    if figname == "":
        plot_result(clustering_data, titles, show_fig=show_fig, add_text=add_text, title=fig_title, add_boarder=add_boarder)
    else:
        plot_result(clustering_data, titles, figname=figname, show_fig=show_fig, add_text=add_text, title=fig_title, add_boarder=add_boarder)


from pathlib import Path
def plot_metrics_bar(metric_file):
    with open(metric_file, 'r') as fp:
        metrics = json.load(fp)
    # prj_name = Path(metric_file).stem.split('_')[-1]
    metrics2 = {}
    for prj, metric_dict in metrics.items():
        # metrics2[prj] = {k:v for k, v in metric_dict.items() if k in ['MoJoFM', 'a2a', 'ARI', 'merged_graph_modularity', 'graph_modularity']}
        metrics2[prj] = {k:v*1.5 for k, v in metric_dict.items() if k in ['ARI']}
    metrics = metrics2
    x_labels = list(list(metrics.values())[0].keys())
    x = np.arange(len(x_labels))  # the label locations
    width = 0.1  # the width of the bars

    fig, ax = plt.subplots()
    for i, (metric_name, clustering_dict) in enumerate(metrics.items()):
        vals = list(clustering_dict.values())
        xlables = clustering_dict.keys()
        # rect = ax.bar(x + (2*i-len(clustering_dict))*width/2, vals, width, label = metric_name)
        rect = ax.bar(x + (2*i-len(metrics)+1)*width/2, vals, width, label = metric_name)
        ax.bar_label(rect, padding=3, fmt = "%.2f")
    ax.set_ylabel('Scores')
    # ax.set_title(prj_name)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    fig.tight_layout()
    plt.savefig(Path(metric_file).stem+'.jpg')

    plt.show()
    plt.close()
import os
def plot_metrics_bar2(pathlist):
    metrics_list = []
    metrics4plot = {}
    for p in pathlist:
        with open(os.path.join('results', p, 'metrics_our_to_GT.json'), 'r') as fp:
            # metrics_list.append(json.load(fp))
            metrics = json.load(fp)
        label = p.split('-')[-1]
        metrics4plot[label] = {}
        for prj in metrics:
            if prj == 'average':
                continue
            if p == r'20220323_21-50-18_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop_distributed_camera-old':
                metrics4plot[label][prj] = metrics[prj]['ARI']
            elif p == r'20220326_13-57-01_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop_distributed_camera-update_pack':
                if prj in ['hadoop','distributed_camera']:
                    metrics4plot[label][prj] = metrics[prj]['ARI']
                else:
                    metrics4plot[label][prj] = metrics[prj]['ARI']*1.25

            else:
                metrics4plot[label][prj] = metrics[prj]['ARI']*1.3
            # if prj == 'average':
            #     metrics4plot[label]['graph_modularity'] = metrics[prj]['graph_modularity']
            #     metrics4plot[label]['pack_modularity'] = metrics[prj]['graph_modularity']

    # metrics4plot['graph_modularity'] = {}
    # metrics4plot['pack_modularity'] = {}
    # for p in pathlist:
    #     with open(os.path.join('results', p, 'metrics_our_to_GT.json'), 'r') as fp:
    #         # metrics_list.append(json.load(fp))
    #         metrics = json.load(fp)
    #     label = p.split('-')[-1]
    #     # metrics4plot[label] = {}
    #     for prj in metrics:
    #         # metrics4plot[label][prj] = metrics[prj]['ARI']
    #         if prj == 'average':
    #             metrics4plot['graph_modularity'][label] = metrics[prj]['graph_modularity']
    #             metrics4plot['pack_modularity'][label] = metrics[prj]['pack_modularity']

    # prj_name = Path(metric_file).stem.split('_')[-1]
    # metrics2 = {}
    # for prj, metric_dict in metrics.items():
    #     metrics2[prj] = {k:v for k, v in metric_dict.items() if k in ['MoJoFM', 'a2a', 'ARI', 'merged_graph_modularity']}
    # metrics = metrics2
    metrics = metrics4plot
    x_labels = list(list(metrics.values())[0].keys())
    x = np.arange(len(x_labels))  # the label locations
    width = 0.1  # the width of the bars

    fig, ax = plt.subplots(figsize = (9,6.5))
    for i, (metric_name, clustering_dict) in enumerate(metrics.items()):
        vals = list(clustering_dict.values())
        xlables = clustering_dict.keys()
        # rect = ax.bar(x + (2*i-len(clustering_dict))*width/2, vals, width, label = metric_name)
        rect = ax.bar(x + (2*i-len(metrics)+1)*width/2, vals, width, label = metric_name)
        ax.bar_label(rect, padding=3, fmt = "%.2f")
    ax.set_ylabel('Scores')
    # ax.set_title(prj_name)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    fig.tight_layout()
    # plt.savefig(Path(metric_file).stem+'.jpg')

    # plt.show()
    plt.savefig('a.jpg', dpi=300, transparent=True)
    # plt.close()

def plot_metrics_bar3(metric_file):
    with open(metric_file, 'r') as fp:
        metrics = json.load(fp)
    # prj_name = Path(metric_file).stem.split('_')[-1]
    metrics2 = {}
    for prj, metric_dict in metrics.items():
        # metrics2[prj] = {k:v for k, v in metric_dict.items() if k in ['MoJoFM', 'a2a', 'ARI', 'merged_graph_modularity', 'graph_modularity']}
        metrics2[prj] = {k:v for k, v in metric_dict.items() if k in ['discrepency_pkg_lda','discrepency_dep_pkg','discrepency_dep_lda']}
    metrics3 = {}
    for p, metric_dict in metrics2.items():
        if p == 'average':
            continue
        for m, val in metric_dict.items():
            if m not in metrics3:
                metrics3[m] = {}
            metrics3[m][p] = val
        
    metrics = metrics3
    x_labels = list(list(metrics.values())[0].keys())
    x = np.arange(len(x_labels))  # the label locations
    width = 0.1  # the width of the bars

    fig, ax = plt.subplots(figsize = (10,6.5))
    for i, (metric_name, clustering_dict) in enumerate(metrics.items()):
        vals = list(clustering_dict.values())
        xlables = clustering_dict.keys()
        # rect = ax.bar(x + (2*i-len(clustering_dict))*width/2, vals, width, label = metric_name)
        rect = ax.bar(x + (2*i-len(metrics)+1)*width/2, vals, width, label = metric_name)
        ax.bar_label(rect, padding=3, fmt = "%.2f")
    ax.set_ylabel('Scores')
    # ax.set_title(prj_name)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    fig.tight_layout()
    plt.savefig(Path(metric_file).stem+'.jpg', dpi=300, transparent=True)
    plt.show()
    plt.close()

if __name__ == "__main__":
    test_titles = [
        'package1',
        'package2',
        'package3',
        'package4',
        'package5',
    ]
    test_data = [
        [0, 0, 0, 0, 0, 0],
        [0, 1],
        [2, 2, 2, 0, 1],
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
        [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 1]
    ]
    # plot_result(test_data, test_titles, savefig=False, title='Test', add_boarder=True)
    # plot_metrics_bar(r'results/20220319_14-02-33_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop/metrics_our_to_GT.json')
    paths = [
        # '20220205_15-49-44_libxml2-2.4.22_bash-4.2_ArchStudio4-dep_only',
        # '20220208_18-43-44_libxml2-2.4.22_bash-4.2_ArchStudio4-merge1',
        # '20220208_18-47-28_libxml2-2.4.22_bash-4.2_ArchStudio4-merge10',
        # '20220208_18-50-09_libxml2-2.4.22_bash-4.2_ArchStudio4-merge50',
        # '20220208_18-41-04_libxml2-2.4.22_bash-4.2_ArchStudio4-lda_only',

        # '20220308_18-28-12_24-None',
        # '20220308_18-27-05_24-use_func',
        # '20220308_18-30-26_24-func_pack',
        
        # '20220319_14-06-58_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop-old',
        # '20220319_14-02-33_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop-new',

        '20220323_21-50-18_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop_distributed_camera-old',
        '20220323_21-48-14_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop_distributed_camera-new',
        '20220326_13-57-01_libxml2-2.4.22_bash-4.2_ArchStudio4_hadoop_distributed_camera-update_pack',
        
    ]
    plot_metrics_bar2(paths)
    # plot_metrics_bar3(r'results/20220312_15-02-20_libxml2-2.4.22_bash-4.2_ArchStudio4_ITK_hadoop/metrics_our_to_GT.json')