from fileinput import filename
from ntpath import join
import os
import numpy as np
from util import GameInfo


def load_game_log(rid, game_index, dir='./log'):
    table_info_list = []
    for dirpath, dirname, filenames in os.walk(os.path.join(dir, rid, str(game_index))):
        for filename in filenames:
            table_info = np.load(os.path.join(dirpath, filename), allow_pickle=True).item()
            table_info_list.append(table_info)
    return table_info_list

def load_log(rid, game_index_list, dir='./log/'):
    table_info_list = []
    for dirpath, dirnames, _ in os.walk(os.path.join(dir, rid)):
        for dirname in dirnames:
            if int(dirname) in game_index_list:
                cur_table_info = load_game_log(rid, int(dirname), dir)
                table_info_list.extend(cur_table_info)
    return table_info_list


table_info_list = load_log('CqGgMoPy', [1337,])
table_info = table_info_list[0]
cards_info = table_info['CardInfo']
# print(table_info.keys())

info = GameInfo(table_info, cards_info)
print(table_info['GamePlayer']['NickName'])
print(info)

