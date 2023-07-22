import matplotlib.pyplot as plt


import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

import util2


def num_to_idx(num:str)->int:
    s = '23456789TJQKA'
    return s.find(num)


# exp -> common_rep
def shrink_range(range_exp):
    rtable = {}
    for k, v in range_exp.items():
        rep = util2.Hand(k[0], k[1]).to_common_rep()
        cur_freq = 0
        if rep in rtable.keys():
            cur_freq = rtable[rep]

        if len(rep) == 2:
            freq = v / 6
        elif rep[2] == 's':
            freq = v / 4
        elif rep[2] == 'o':
            freq = v / 12
        rtable[rep] = cur_freq + freq
    return rtable

def plot_win_rate(hand_wr:dict, max_num=20, title='Win Rate'):
    data_list = list(hand_wr.items())
    # print(data_list)
    data_list.sort(key=lambda x:x[1], reverse=True)
    if max_num > 0:
        data_list = data_list[:max_num]
    

    x = [ str(util2.Hand(data[0][0], data[0][1])) for data in data_list]
    y = [data[1] for data in data_list]
    fig, ax = plt.subplots(layout='constrained', figsize=(12, 4))
    ax.bar(x, y)


def plot_range(range_exp, title=None):
    data = np.zeros((13, 13), dtype=float)
    rtable = shrink_range(range_exp)

    for k, v in rtable.items():
        r = num_to_idx(k[0])
        c = num_to_idx(k[1])
        
        if k[0]==k[1]:
            data[r, c] = v
        elif k[2] == 's':
            data[r, c] = v
        else:
            data[c, r] = v
            
    s = '23456789TJQKA'
    # plt.rcParams['figure.figsize'] = (12, 8)

    fig, ax = plt.subplots(layout='constrained', figsize=(12, 8))
    sns.heatmap(data, annot=True, cmap='Blues', ax=ax)
    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.set_xticklabels(s)
    ax.set_yticklabels(s)

    if title:
        ax.set_title(title)