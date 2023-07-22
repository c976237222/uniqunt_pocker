# 模拟计算胜率等操作
# TODO: 使用multiprocessing提高模拟速度

from filecmp import cmp
from os import remove
import random
from stat import ST_ATIME
from turtle import left
import util
from util import Card, Hand, SevenCard, judge_two

import itertools
import time
import numpy as np
import math
from multiprocessing import Pool


'''
# 扩展对手范围 变为 AhKs -> 1.0 的形式
'''
def expand_range(op_range, known_cards=None):
    exp_range = {} # 扩展后的范围
    for common_rep, freq in op_range.items():
        comb_list = Hand.common_rep_to_combs(common_rep)
        for op_hand in comb_list:
            if known_cards is not None:
                if op_hand[0] in known_cards or op_hand[1] in known_cards:
                    continue
            exp_range[op_hand] = freq
    return exp_range


def win_rate_hand_range(ip_hand, op_range, board_card):
    '''
    计算手牌对于估计范围的胜率
    ip:        [32, 33]
    oprange:  dict['AKo']=1.0
    board_card:table_info['TableStatus']['TableCards'], 其中-1表示未发的牌
    '''

    # 同时排除掉被阻挡掉的组合
    s_time = time.time()
    known_cards = set(ip_hand).union(set(board_card))
    exp_range = expand_range(op_range, known_cards)

    # 2. 发牌计算总体胜率
    total_freq = 0.0
    total_win, total_draw  = 0, 0
    for op_hand, freq in exp_range.items():
        total_freq += freq
        win_rate, draw_rate = cmp_on_all_possible_cards(ip_hand, op_hand, board_card, sample_factor=0.1)
        total_win += win_rate * freq
        total_draw += draw_rate * freq
        # print(f'{util.cards_to_str(ip_hand)} vs {util.cards_to_str(op_hand)}: {win_rate:.3f}')
    
    overall_win_rate = total_win / total_freq
    overall_draw_rate = total_draw / total_freq
    # print('simulate time:', time.time() - s_time)
    return overall_win_rate, overall_draw_rate


def remove_known_cards(range_exp:dict, known_cards):
    new_range = {} # 扩展后的范围
    for op_hand, freq in range_exp.items():
        if op_hand[0] in known_cards or op_hand[1] in known_cards:
            continue
        new_range[op_hand] = freq
    return new_range

def win_rate_hand_range_exp(ip_hand, op_range_exp, board_card):
    # 排除掉被阻挡掉的组合
    known_cards = board_card + list(ip_hand)
    op_range = remove_known_cards(op_range_exp, known_cards)

    # 2. 发牌计算总体胜率
    total_freq = 0.0
    total_win, total_draw  = 0, 0
    for op_hand, freq in op_range.items():
        total_freq += freq
        win_rate, draw_rate = cmp_on_all_possible_cards(ip_hand, op_hand, board_card, max_iter=100)
        total_win += win_rate * freq
        total_draw += draw_rate * freq
        # print(f'{util.cards_to_str(ip_hand)} vs {util.cards_to_str(op_hand)}: {win_rate:.3f}')
    
    overall_win_rate = total_win / total_freq
    overall_draw_rate = total_draw / total_freq
    # print('simulate time:', time.time() - s_time)
    return overall_win_rate, overall_draw_rate

# 根据桌面的牌估算ip_hand的胜率
def cmp_on_table(ip_hand, op_hand, table_card, mc_num=100):
    mc_num = min(mc_num, 1000)
    known_cards = table_card + list(ip_hand) + list(op_hand)
    left_cards = [i for i in range(52) if i not in known_cards]
    
    res_list = []

    # 翻牌圈估计

    if table_card[3]==-1 and table_card[4]==-1:
        # 这里可以穷尽所有45*44/2=990个组合
        # 这里改成用random.sample(left_cards, 2)
        s_time = time.time()
        new_table_card = table_card[:]
        for _ in range(mc_num):

            new_card = random.sample(left_cards, k=2)
            new_table_card[3:] = new_card[:]
            res = hand_cmp(ip_hand, op_hand, new_table_card)
            res_list.append(res)

        # print(f'one hand cmp time: {(time.time()-s_time)/mc_num:.7f}')
        # exit()
        win_rate  = res_list.count(1)  / len(res_list)
        draw_rate = res_list.count(0)  / len(res_list)
        # print(f'mc time used: {time.time() - s_time:2f}')
        # lose_rate = res_list.count(-1) / len(res_list)
        # print('epoch time:', (time.time() - s_time))

    elif table_card[4] == -1:
        new_table_card = table_card[:]
        if len(left_cards) > mc_num:
            left_cards = random.sample(left_cards, mc_num)
        for new_card in left_cards:
            new_table_card[4] = new_card
            res = hand_cmp(ip_hand, op_hand, new_table_card)
            res_list.append(res)
        win_rate  = res_list.count(1)  / len(res_list)
        draw_rate = res_list.count(0)  / len(res_list)
        # lose_rate = res_list.count(-1) / len(res_list)

    else:
        # 5张牌，直接比大小
        res = hand_cmp(ip_hand, op_hand, table_card)
        win_rate  = 1 if res==1 else 0
        draw_rate = 1 if res==0 else 0
        # lose_rate = 1 if res==-1 else 0

    # return win_rate
    return win_rate, draw_rate

# 手牌vs范围的翻牌胜率
def hand_range_exp_win_rate(ip_hand:tuple, op_range_exp:dict, table_card:list, mc_num=20):
    # s_time = time.time()
    op_range = remove_known_cards(op_range_exp, table_card + list(ip_hand))
    # print('remove_known_cards time:', (time.time() - s_time))

    total_freq = 0.0
    total_win, total_draw = 0, 0
    for op_hand, freq in op_range.items():

        # s_time = time.time()
        win_rate, draw_rate = cmp_on_table(ip_hand, op_hand, table_card, mc_num=mc_num)
        # print('remove_known_cards time:', (time.time() - s_time))
        total_win  += win_rate  * freq
        total_draw += draw_rate * freq
        total_freq += freq
    
    overall_win_rate =  total_win / total_freq
    overall_draw_rate = total_draw / total_freq
    return overall_win_rate, overall_draw_rate





def win_rate_ranges(ip_range_exp:dict, op_range_exp:dict, table_card:list, range_size=25, mc_num=20):
    '''
    计算ip_range相对op_range范围的胜率 \n
    按照每次模拟上限5000次设计
    返回ip_range之中每手牌的胜率, 其中概率更高的手牌采样率会更高, 估算会越准
    '''
    s_time = time.time()
    ip_range = remove_known_cards(ip_range_exp, table_card)
    op_range = remove_known_cards(op_range_exp, table_card)
    # print(f'time: remove known cards   {time.time() - s_time:.4f}')

    s_time = time.time()
    k = range_size
    sampled_ip_range = random.choices(list(ip_range.items()), weights=list((ip_range.values())), k=k)
    sampled_op_range = random.choices(list(op_range.items()), weights=list((op_range.values())), k=k)

    sampled_ip_range = dict(sampled_ip_range) 
    sampled_op_range = dict(sampled_op_range)
    # print(f'time: sample ranges   {time.time() - s_time:.4f}')

    s1_time = time.time()
    win_rate_per_hand = {}  # 估算记录每手牌的模拟胜率
    draw_rate_per_hand = {} # 打平概率
    # 计算得到每手牌的赢率字典，以及加权后的总体赢率
    win_rate, draw_rate, weight_sum = 0.0, 0.0, 0.0
    for ip_hand in sampled_ip_range.keys():
        s_time = time.time()
        hand_win_rate, hand_draw_rate = hand_range_exp_win_rate(ip_hand, sampled_op_range, table_card, mc_num=mc_num)
        win_rate_per_hand[ip_hand]  = hand_win_rate
        draw_rate_per_hand[ip_hand] = hand_draw_rate

        win_rate   += hand_win_rate * ip_range[ip_hand]
        draw_rate  += hand_draw_rate* ip_range[ip_hand]
        weight_sum += ip_range[ip_hand]
    win_rate  = win_rate  /  weight_sum
    draw_rate = draw_rate /  weight_sum

    return win_rate, draw_rate, win_rate_per_hand, draw_rate_per_hand


def win_rate_ranges2(ip_range_exp:dict, op_range_exp:dict, table_card:list, range_size=25, mc_num=20):
    '''
    计算ip_range相对op_range范围的胜率 \n
    按照每次模拟上限5000次设计
    返回ip_range之中每手牌的胜率, 其中概率更高的手牌采样率会更高, 估算会越准
    '''
    s_time = time.time()
    ip_range = remove_known_cards(ip_range_exp, table_card)
    op_range = remove_known_cards(op_range_exp, table_card)
    # print(f'time: remove known cards   {time.time() - s_time:.4f}')

    s_time = time.time()
    k = range_size
    # sampled_ip_range = random.choices(list(ip_range.items()), weights=list((ip_range.values())), k=k)
    sampled_ip_range = ip_range
    sampled_op_range = random.choices(list(op_range.items()), weights=list((op_range.values())), k=k)

    sampled_ip_range = dict(sampled_ip_range) 
    sampled_op_range = dict(sampled_op_range)
    # print(f'time: sample ranges   {time.time() - s_time:.4f}')

    s1_time = time.time()
    win_rate_per_hand = {}  # 估算记录每手牌的模拟胜率
    draw_rate_per_hand = {} # 打平概率
    # 计算得到每手牌的赢率字典，以及加权后的总体赢率
    win_rate, draw_rate, weight_sum = 0.0, 0.0, 0.0
    for ip_hand in sampled_ip_range.keys():
        s_time = time.time()
        hand_win_rate, hand_draw_rate = hand_range_exp_win_rate(ip_hand, sampled_op_range, table_card, mc_num=mc_num)
        win_rate_per_hand[ip_hand]  = hand_win_rate
        draw_rate_per_hand[ip_hand] = hand_draw_rate

        win_rate   += hand_win_rate * ip_range[ip_hand]
        draw_rate  += hand_draw_rate* ip_range[ip_hand]
        weight_sum += ip_range[ip_hand]
    win_rate  = win_rate  /  weight_sum
    draw_rate = draw_rate /  weight_sum

    return win_rate, draw_rate, win_rate_per_hand, draw_rate_per_hand


def compare_hands(paras) -> list:
    hand1, hand2, board, new_cards = paras
    new_board = board[:]
    new_board[3:] = new_cards[0:]
    res = hand_cmp(hand1, hand2, new_board)
    return res

def cmp_on_all_possible_cards(hand1, hand2, board_card, max_iter=100):
    # hand1, hand2: tuple
    # board_card: [2, 4, 6, -1, -1]
    # 这里发现sample_factor设置小一些并不很影响结果，设置为0.1基本可以满足要求，
    left_cards = []
    for i in range(52):
        if (i not in hand1) and (i not in hand2) and (i not in board_card):
            left_cards.append(i)
    
    res_list = []

    if board_card[3]==-1 and board_card[4]==-1:
        # 这里可以穷尽所有45*44/2=990个组合
        new_cards_iter = list(itertools.combinations(left_cards, 2))
        if max_iter:
            new_cards_iter = random.choices(new_cards_iter, k=max_iter)
        new_board = board_card[:]

        s_time = time.time()
        
        # 优化前的代码
        res_list = []
        for i, (new_cards) in enumerate(new_cards_iter):
            # 这里模拟每手牌大概3e-5s
            new_board[3:] = new_cards[0:]
            res = hand_cmp(hand1, hand2, new_board)
            res_list.append(res)
        
        win_rate  = res_list.count(1)  / len(res_list)
        draw_rate = res_list.count(0)  / len(res_list)
        lose_rate = res_list.count(-1) / len(res_list)
        # print('epoch time:', (time.time() - s_time))

    elif board_card[4] == -1:
        new_board = board_card[:]
        for new_card in left_cards:
            new_board[4] = new_card
            res = hand_cmp(hand1, hand2, new_board)
            res_list.append(res)
        win_rate  = res_list.count(1)  / len(res_list)
        draw_rate = res_list.count(0)  / len(res_list)
        lose_rate = res_list.count(-1) / len(res_list)

    else:
        # 5张牌，直接比大小
        res = hand_cmp(hand1, hand2, board_card)
        win_rate  = 1 if res==1 else 0
        draw_rate = 1 if res==0 else 0
        lose_rate = 1 if res==-1 else 0

    # return win_rate
    return win_rate, draw_rate


def hand_cmp(hand1, hand2, board_five_card):
    # -1: hand1 < hand2
    # 0 : hand1 = hand2
    # 1 : hand1 > hand2
    seven1 = board_five_card[:]
    seven1.extend(hand1)
    seven2 = board_five_card[:]
    seven2.extend(hand2)
    return -judge_two(seven1, seven2)