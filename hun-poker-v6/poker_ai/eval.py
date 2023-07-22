# 牌力大小评估器

from poker_ai.range import Range
from poker_ai.card import Card
import random

import multiprocessing as mp
from multiprocessing import Process

def worker(queue, queue_return, op_new_range, board, mc_times):
    while True:
        key = queue.get()
        if key is None:
            break
        my_hand, weight = key
        hand_wr, hand_dr = hand_vs_range(my_hand, op_new_range, board, mc_times=mc_times)
        queue_return.put((my_hand, weight, hand_wr, hand_dr))
        # return my_hand, weight, hand_wr, hand_dr

def range_vs_range_multiprocessed(my_range:Range, op_range:Range, board:list, threshold=0.1, my_range_size=150, range_size=20, mc_times=30000, num_processes=4):
    '''
    计算my_range相对op_range范围的胜率 \n
    - wr: 胜率
    - dr: 平局率
    - hand_wr_dict: 每手牌的胜率
    - hand_dr_dict: 每手牌的平局率
    '''

    CORE_NUM = 2 # 多进程核数，最好与CPU核数相同
    my_new_range = my_range.remove_known_cards(board).remove_impossible_hands(threshold=threshold)
    op_new_range = op_range.remove_known_cards(board).remove_impossible_hands(threshold=threshold)

    if -1 in board: # 如果还有没发完的牌，则抽样对手的范围和自己的范围
        op_new_range = op_new_range.sample(k=my_range_size)
        op_new_range = op_new_range.sample(k=range_size)
    else:
        op_new_range = op_new_range.sample(k=5*range_size)

    queue = mp.Queue(CORE_NUM)
    queue_return = mp.Queue()
    processes = [Process(target=worker, args=(queue, queue_return, op_new_range, board, mc_times//len(my_new_range)+1),) for _ in range(CORE_NUM)]

    hand_wr_dict = {}  # 估算记录每手牌的模拟胜率
    hand_dr_dict = {}  # 打平概率
    # 计算得到每手牌的赢率字典，以及加权后的总体赢率
    win_rate, draw_rate, weight_sum = 0.0, 0.0, 0.0

    for each in processes:
        each.start()

    queue_len = 0
    for my_hand, weight in my_new_range.range_exp.items():
        queue.put((my_hand, weight))
        queue_len += 1

    while not queue.empty():
        pass

    for i in range(CORE_NUM):
        queue.put(None)
    for each in processes:
        each.join()

    while not queue_return.empty():
        my_hand, weight, hand_wr, hand_dr = queue_return.get()
        hand_wr_dict[my_hand] = hand_wr


def is_draw_hand(my_hand, op_range, board, mc_times=5000):
    '''
    在当前胜率小于50%时，判断是否为听牌
    模拟发一张牌(40)，如果胜率显著提升，计算胜率提升至0.75+的可能性，
    '''
    # 从对手的手牌里面随机选择胜率>0.6的30种组合

    # 模拟发牌40次牌，计算自己手牌面对对手的胜率

    # 



def hand_cmp(hand1, hand2, board_five_card):
    '''
    比较手牌大小 \n
    # -1: hand1 < hand2 \n
    # 0 : hand1 = hand2 \n
    # 1 : hand1 > hand2 \n
    '''
    seven1 = board_five_card[:] + list(hand1)
    seven2 = board_five_card[:] + list(hand2)
    return -judge_two(seven1, seven2)

def range_vs_range(my_range:Range, op_range:Range, board:list, threshold=0.1, my_range_size=150, range_size=20, mc_times=30000):
    '''
    计算my_range相对op_range范围的胜率 \n
    - wr: 胜率
    - dr: 平局率
    - hand_wr_dict: 每手牌的胜率
    - hand_dr_dict: 每手牌的平局率
    '''
    my_new_range = my_range.remove_known_cards(board).remove_impossible_hands(threshold=threshold)
    op_new_range = op_range.remove_known_cards(board).remove_impossible_hands(threshold=threshold)

    if -1 in board: # 如果还有没发完的牌，则抽样对手的范围和自己的范围
        op_new_range = op_new_range.sample(k=my_range_size)
        op_new_range = op_new_range.sample(k=range_size)
    else:
        op_new_range = op_new_range.sample(k=5*range_size)

    hand_wr_dict = {}  # 估算记录每手牌的模拟胜率
    hand_dr_dict = {}  # 打平概率
    # 计算得到每手牌的赢率字典，以及加权后的总体赢率
    win_rate, draw_rate, weight_sum = 0.0, 0.0, 0.0
    for my_hand, weight in my_new_range.range_exp.items():

        hand_wr, hand_dr = hand_vs_range(my_hand, op_new_range, board, mc_times=mc_times//len(my_new_range)+1)
        hand_wr_dict[my_hand] = hand_wr
        hand_dr_dict[my_hand] = hand_dr

        win_rate   += hand_wr * weight
        draw_rate  += hand_dr * my_new_range[my_hand]
        weight_sum += weight
    wr = win_rate  /  weight_sum
    dr = draw_rate /  weight_sum

    return wr, dr, hand_wr_dict, hand_dr_dict

def hand_vs_range(my_hand: tuple, op_range: Range, board:list, threshold=0.05, mc_times=5000):
    '''
    比较手牌与范围的胜率和平局率 \n
    '''
    known_cards = board + list(my_hand)
    op_new_range = op_range.remove_known_cards(known_cards).remove_impossible_hands(threshold=threshold)

    total_freq = 0.0
    total_win, total_draw  = 0, 0
    for op_hand, freq in op_new_range.range_exp.items():
        total_freq += freq
        win_rate, draw_rate = hand_vs_hand(my_hand, op_hand, board, mc_times=mc_times//len(op_new_range)+1 )
        total_win += win_rate * freq
        total_draw += draw_rate * freq

    overall_win_rate = total_win / total_freq
    overall_draw_rate = total_draw / total_freq
    return overall_win_rate, overall_draw_rate

def hand_vs_hand(ip_hand, op_hand, board, mc_times=100):
    '''
    比较手牌与手牌的胜率 \n
    '''
    known_cards = board + list(ip_hand) + list(op_hand)
    left_cards = [i for i in range(52) if i not in known_cards]

    if board[3]==-1 and board[4]==-1:
        # 翻牌圈
        res_list = []
        new_table_card = board[:]
        for _ in range(mc_times):
            new_card = random.sample(left_cards, k=2)
            new_table_card[3:] = new_card[:]
            res = hand_cmp(ip_hand, op_hand, new_table_card)
            res_list.append(res)

        wr = res_list.count(1)  / len(res_list) # 胜率
        dr = res_list.count(0)  / len(res_list) # 平局率

    elif board[4] == -1:
        # 转牌
        res_list = []
        new_table_card = board[:]
        if len(left_cards) > mc_times:
            left_cards = random.sample(left_cards, mc_times)
        for new_card in left_cards:
            new_table_card[4] = new_card
            res = hand_cmp(ip_hand, op_hand, new_table_card)
            res_list.append(res)
        wr = res_list.count(1)  / len(res_list)
        dr = res_list.count(0)  / len(res_list)

    else:
        # 河牌，直接比大小
        res = hand_cmp(ip_hand, op_hand, board)
        wr = 1.0 if res==1 else 0.0
        dr = 1.0 if res==0 else 0.0

    return wr, dr

def hand_wr_to_list(hand_wr:dict):
    res = list(hand_wr.items())
    res.sort(key=lambda x:x[1], reverse=True)
    return res

def display_wr_list(hand_wr_list:list):
    for i in range(len(hand_wr_list)):
        if i % 5 == 0 and i != 0:
            print(' ')
        print(f'{[Card(c) for c in hand_wr_list[i][0]]}:{hand_wr_list[i][1]:.2f}', end=', ')


# *************************************************************

# alter the card id into color
def id2color(card):
    return card % 4

# alter the card id into number
def id2num(card):
    return card // 4

# alter the string into card id
def str2id(card_str):
    # Ah
    num_list  = '23456789TJQKA'
    type_list = 'sdhc'  # 黑桃、方片、红心、梅花
    assert len(card_str)==2 and (card_str=='NA' or (card_str[0] in num_list and card_str[1] in type_list))
    if card_str == 'NA':
        return -1

    c_num = num_list.find(card_str[0])
    t_num = type_list.find(card_str[1])
    id = c_num * 4 + t_num
    return id

def judge_exist(x):
    if x >= 1:
        return True
    return False

class SevenCard(object):
    def __init__(self, cards_list):
        cards = cards_list[:]
        self.level = 0
        self.cnt_num = [0] * 13
        self.cnt_color = [0] * 4
        self.cnt_num_eachcolor = [[0 for col in range(13)] for row in range(4)]
        self.maxnum = -1
        self.single = []
        self.pair = []
        self.tripple = []
        self.nums = []
        for x in cards:
            self.cnt_num[id2num(x)] += 1
            self.cnt_color[id2color(x)] += 1
            self.cnt_num_eachcolor[id2color(x)][id2num(x)] += 1
            self.nums.append(id2num(x))

        self.judge_num_eachcolor = [[] for i in range(4)]

        for i in range(4):
            self.judge_num_eachcolor[i] = list(map(judge_exist, self.cnt_num_eachcolor[i]))


        self.nums.sort(reverse=True)
        for i in range(12, -1, -1):
            if self.cnt_num[i] == 1:
                self.single.append(i)
            elif self.cnt_num[i] == 2:
                self.pair.append(i)
            elif self.cnt_num[i] == 3:
                self.tripple.append(i)
        self.single.sort(reverse=True)
        self.pair.sort(reverse=True)
        self.tripple.sort(reverse=True)

        # calculate the level of the poker hand
        for i in range(4):
            if self.judge_num_eachcolor[i][8:13].count(True) == 5:
                self.level = 10
                return


        for i in range(4):

            for j in range(7, -1, -1):
                if self.judge_num_eachcolor[i][j:j+5].count(True) == 5:
                    self.level = 9
                    self.maxnum = j + 4
                    return
            if self.judge_num_eachcolor[i][12] and self.judge_num_eachcolor[i][:4].count(True) == 4:
                    self.level = 9
                    self.maxnum = 3
                    return



        for i in range(12, -1, -1):
            if self.cnt_num[i] == 4:
                self.maxnum = i
                self.level = 8
                for j in range(4):
                    self.nums.remove(i)
                return


        tripple = self.cnt_num.count(3)
        if tripple > 1:
            self.level = 7
            return
        elif tripple > 0:
            if self.cnt_num.count(2) > 0:
                self.level = 7
                return

        for i in range(4):
            if self.cnt_color[i] >= 5:
                self.nums = []
                for card in cards:
                    if id2color(card) == i:
                        self.nums.append(id2num(card))
                self.nums.sort(reverse=True)
                self.nums = self.nums[:5]
                self.maxnum = self.nums[0]
                self.level = 6
                return

        for i in range(8, -1, -1):
            flag = 1
            for j in range(i, i + 5):
                if self.cnt_num[j] == 0:
                    flag = 0
                    break
            if flag == 1:
                self.maxnum = i + 4
                self.level = 5
                return
        if self.cnt_num[12] and list(map(judge_exist, self.cnt_num[:4])).count(True) == 4:
            self.maxnum = 3
            self.level = 5
            return


        for i in range(12, -1, -1):
            if self.cnt_num[i] == 3:
                self.maxnum = i
                self.level = 4
                self.nums.remove(i)
                self.nums.remove(i)
                self.nums.remove(i)
                self.nums = self.nums[:min(len(self.nums), 2)]
                return


        if self.cnt_num.count(2) > 1:
            self.level = 3
            return


        for i in range(12, -1, -1):
            if self.cnt_num[i] == 2:
                self.maxnum = i
                self.level = 2

                self.nums.remove(i)
                self.nums.remove(i)
                self.nums = self.nums[:min(len(self.nums), 3)]
                return


        if self.cnt_num.count(1) == 7:
            self.level = 1
            self.nums = self.nums[:min(len(self.nums), 5)]
            return

        self.level = -1

    def __str__(self):
        return 'level = %s' % self.level


def cmp(x,y):  # x < y return 1
    if x > y: return -1
    elif x == y: return 0
    else: return 1


def judge_two(cards0, cards1):
    hand0 = SevenCard(cards0)
    hand1 = SevenCard(cards1)
    if hand0.level > hand1.level:
        return -1
    elif hand0.level < hand1.level:
        return 1
    else:
        if hand0.level in [5, 9]:
            return cmp(hand0.maxnum, hand1.maxnum)
        elif hand0.level in [1, 2, 4]:
            t = cmp(hand0.maxnum, hand1.maxnum)
            if t == 1: return 1
            elif t == -1: return -1
            else:
                if hand0.nums < hand1.nums:
                    return 1
                elif hand0.nums == hand1.nums:
                    return 0
                else:
                    return -1

        elif hand0.level == 6:
            if hand0.nums < hand1.nums:
                return 1
            elif hand0.nums > hand1.nums:
                return -1
            else:
                return 0

        elif hand0.level == 8:
            t = cmp(hand0.maxnum, hand1.maxnum)
            if t == 1:
                return 1
            elif t == -1:
                return -1
            else:
                return cmp(hand0.nums[0], hand1.nums[0])

        elif hand0.level == 3:
            if cmp(hand0.pair[0], hand1.pair[0]) != 0:
                return cmp(hand0.pair[0], hand1.pair[0])
            elif cmp(hand0.pair[1], hand1.pair[1]) != 0:
                return cmp(hand0.pair[1], hand1.pair[1])
            else:
                hand0.pair = hand0.pair[2:]
                hand1.pair = hand1.pair[2:]
                tmp0 = hand0.pair + hand0.pair + hand0.single
                tmp0.sort(reverse=True)
                tmp1 = hand1.pair + hand1.pair + hand1.single
                tmp1.sort(reverse=True)
                if tmp0[0] < tmp1[0]:
                    return 1
                elif tmp0[0] == tmp1[0]:
                    return 0
                else:
                    return -1

        elif hand0.level == 7:
            if cmp(hand0.tripple[0], hand1.tripple[0]) != 0:
                return cmp(hand0.tripple[0], hand1.tripple[0])
            else:
                tmp0 = hand0.pair
                tmp1 = hand1.pair
                if len(hand0.tripple) > 1:
                    tmp0.append(hand0.tripple[1])
                if len(hand1.tripple) > 1:
                    tmp1.append(hand1.tripple[1])
                tmp0.sort(reverse=True)
                tmp1.sort(reverse=True)
                if tmp0[0] < tmp1[0]:
                    return 1
                elif tmp0[0] == tmp1[0]:
                    return 0
                else:
                    return -1
        else:
            pass
            # assert 0
        return 0