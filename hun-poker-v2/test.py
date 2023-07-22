from AI.BaseAI import BaseAI
from util import *
from simulator import *

import time
import math

def load_range_table(filename):
    table = dict() # table[Hand]->freq
    with open(filename, 'r') as f:
        s = f.read()
        s = s.split(',')
        for ss in s:
            ss = ss.split(':')
            ss[1] = float(ss[1])
            table[ss[0]] = ss[1]
    return table

def test_hand_range():
    allin_range = load_range_table(filename='./range/BTN/raise1.txt')
    # print('allin range:', allin_range)

    ip_hand = [31, 28]
    board_card = [3, 7, 30, -1, -1]

    print('ip_hand:', cards_to_str(ip_hand))
    print('board_card:', cards_to_str(board_card))
    print('op_range:', allin_range)

    for i in range(1):
        s_time = time.time()
        win_rate = win_rate_hand_range(ip_hand, allin_range, board_card)

        print('win_rate', win_rate)
        
        e_time = time.time()
        print('time used:', e_time - s_time)

def display_card_list(card_list):
    tmp = [Card(id) for id in card_list]
    print(tmp)

def display_range(data, max_num=-1):
    data_list = list(data.items())
    # print(data_list)
    data_list.sort(key=lambda x:x[1], reverse=True)
    # print(data_list)

    if max_num > 0:
        data_list = data_list[:max_num]
    for k, v in data_list:
        print(f'{Hand(k[0], k[1])} -> {v:.2f}, ', end='')
    

def test_hand_ranges():
    op_range = load_range_table(filename='./range/UTG/call1.txt')
    ip_range = load_range_table(filename='./range/BTN/raise2.txt')


    # table_card = [9, 13, 18, -1, -1]    # [4d, 5d, 6h, NA, NA] 此时UTG open面对BTN call的胜率在60左右
    table_card = [48, 45, 34, -1, -1]   # [As, Kd, Th, NA, NA] 此时胜率则在75+
    ip_range_exp = expand_range(ip_range, known_cards=table_card)
    op_range_exp = expand_range(op_range, known_cards=table_card)

    display_card_list(table_card)
    win_rate_list = []

    s_time = time.time()

    # 这样模拟，标准差大概在5%左右
    # 定义优势范围为胜率>75%的情况
    # 翻牌设定range_size=50, mc_num=10，所需时间0.3s
    # 转牌设定range_size=20，所需时间0.3s
    win_rate, draw_rate, win_per_hand, draw_per_hand = win_rate_ranges2(ip_range_exp, op_range_exp, table_card, range_size=50, mc_num=10)
    print('win_rate :', win_rate, 'draw_rate :', draw_rate)
    win_rate_list.append(win_rate)
    
    mean_v = sum(win_rate_list) / len(win_rate_list)
    std_v  = math.sqrt( sum([ (wr - mean_v)**2 for wr in win_rate_list]) / len(win_rate_list))

    print(f'result :{mean_v:.4f} + {std_v:.4f}')
    # print(f'avg time: {(time.time()-s_time)/20:.2f}')
    print(f'time used: {time.time() - s_time:.2f}')
    display_range(win_per_hand)

    # print('win_rate :', win_rate)
    # print('draw_rate:', draw_rate)


def test_algorithm():
    hand = (49, 50)

    op_range = load_range_table(filename='./range/UTG/call1.txt')
    ip_range = load_range_table(filename='./range/BTN/raise2.txt')

    table_card = [48, 45, 34, -1, -1]   # [As, Kd, Th, NA, NA] 此时胜率则在75+

    freq = 0 
    bet_ratio = 0
    raise_num = 0
    win_rate = 0.5
    trust_factor = 1
    # 调整后频率 = 原始频率 * (胜率 + 0.6) ^ ((加注次数 + 下注比例) * 信任比例)
    new_freq = freq * ( (win_rate + 0.6) ** ( (raise_num + bet_ratio) * trust_factor ) ) 
    
    print(new_freq)

def test_ah():
    table_info = {}
    table_info['GameStatus'] = {
        'LastAction': {'LastAction': {'Bet': 970, 'SeatId': 1, 'Type': 3}, 'Type': 20, 'Text': '下注成功'},
        'SBCur': 1,
        'Round': 0,
    }
    table_info['GameIndex'] = 10


    # table_info['GameStatus']['LastAction']['LastAction']
    # sb_pos = table_info['GameStatus']['SBCur']
    # action_type = table_info['GameStatus']['LastAction']['Type']
    # game_index  = table_info['GameIndex']
    # self.round = table_info['GameStatus']['Round']
    # self.game_index = table_info['GameIndex']
    # self.action_seat = table_info['GameStatus']['SeatCur']
    # total_bet = table_info['TableStatus']['User']['TotalBet']

if __name__ == '__main__':
    # test_hand_ranges()
    test_algorithm()

    # pass