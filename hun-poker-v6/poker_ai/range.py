# 封装的范围表
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import random

from poker_ai.card import rep_to_comb

import copy

class Range():
    def __init__(self, filename=None, name='call0') -> None:
        self.range_exp = {} # 以手牌tuple作为key，freq作为value
        self.name = name
        if filename:
            range_str = self._load_table(filename)
            self.range_exp = self._expand_range(range_str)

    def load(self, filename):
        range_str = self._load_table(filename)
        self.range_exp = self._expand_range(range_str)

    def _load_table(self, filename):
        range_str = dict() # table[Hand]->freq
        with open(filename, 'r') as f:
            s = f.read()
            s = s.split(',')
            for ss in s:
                ss = ss.split(':')
                ss[1] = float(ss[1])
                range_str[ss[0]] = ss[1]
        return range_str

    def count_ratio(self):
        # 计算游戏的手牌比例
        freq = 0
        total = 51 * 52 / 2
        for _, f in self.range_exp.items():
            freq += f
        return freq / total 

    def remove_known_cards(self, known_cards):
        # 从范围中去除已知的手牌
        # 返回一个新的对象
        new_range = Range()
        for op_hand, freq in self.range_exp.items():
            if op_hand[0] in known_cards or op_hand[1] in known_cards:
                continue
            new_range[op_hand] = freq
        return new_range
    
    def remove_impossible_hands(self, threshold=0.1):
        # 移除一些频率过小的手牌
        new_range = Range()
        for op_hand, freq in self.range_exp.items():
            if freq >= threshold:
                new_range[op_hand] = freq
        return new_range
    
    def sample(self, k):
        # 从范围中随机抽取k个手牌
        # 返回一个新的对象
        new_range = copy.deepcopy(self)
        for _ in range(len(self) - k):
            op_hand = random.choice(list(new_range.range_exp.keys()))
            new_range.range_exp.pop(op_hand)
        return new_range
    

    def plot(self, title=None):
        data = np.zeros((13, 13), dtype=float)
        for k, v in self.range_exp.items():
            if k[0]//4 == k[1]//4:
                data[k[0]//4, k[1]//4] += v / 6  # 对子组合
            elif k[0]%4 == k[1]%4:
                data[k[0]//4, k[1]//4] += v / 4  # 同花组合
            else:
                data[k[1]//4, k[0]//4] += v / 12 # 杂色组合
                
        s = '23456789TJQKA'

        fig, ax = plt.subplots(layout='tight', figsize=(8, 6))
        sns.heatmap(data, annot=True, cmap='Blues', ax=ax)
        ax.invert_xaxis()
        ax.invert_yaxis()
        ax.set_xticklabels(s)
        ax.set_yticklabels(s)

        if title:
            ax.set_title(title)
        # plt.show()

    def plot_percent(self, title=None, threshold=0.01): # 显示百分比
        data = np.zeros((13, 13), dtype=float)
        for k, v in self.range_exp.items():
            if k[0]//4 == k[1]//4:
                data[k[0]//4, k[1]//4] += v  # 对子组合
            elif k[0]%4 == k[1]%4:
                data[k[0]//4, k[1]//4] += v  # 同花组合
            else:
                data[k[1]//4, k[0]//4] += v  # 杂色组合
        data = data / data.sum()
        data[data<threshold] = 0.0
        data = data * 100
        s = '23456789TJQKA'

        fig, ax = plt.subplots(layout='tight', figsize=(8, 6))
        sns.heatmap(data, annot=True, cmap='Blues', ax=ax)
        ax.invert_xaxis()
        ax.invert_yaxis()
        ax.set_xticklabels(s)
        ax.set_yticklabels(s)

        if title:
            ax.set_title(title)
        # plt.show()
    

    def _expand_range(self, op_range):
        exp_range = {} # 扩展后的范围
        for common_rep, freq in op_range.items():
            comb_list = rep_to_comb(common_rep)
            for op_hand in comb_list:
                exp_range[op_hand] = freq
        return exp_range

    def __getitem__(self, key):
        if type(key) == tuple:
            if key[0] < key[1]:
                key = (key[1], key[0])
            return self.range_exp[key]
        
        elif type(key) == str:
            comb_list = rep_to_comb(key)
            freq = 0
            for op_hand in comb_list:
                freq += self.range_exp[op_hand]
            return freq / len(comb_list)
        
        elif type(key) == list:
            assert len(key) == 2
            return self.range_exp[(key[0], key[1])]
    
    def __setitem__(self, k, v):
        if type(k) == tuple:
            if k[0] < k[1]:
                k = (k[1], k[0])
            self.range_exp[k] = v
        
        elif type(k) == str:
            comb_list = rep_to_comb(k)
            for hand in comb_list:
                self.range_exp[hand] = v
        
        elif type(k) == list:
            assert len(k) == 2
            self.__setitem__((k[0], k[1]), v)


    def __len__(self):
        return len(self.range_exp)
