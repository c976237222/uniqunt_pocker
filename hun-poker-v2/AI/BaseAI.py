
from ast import Raise
import os
import random

import util


class ActionHistory:
    def __init__(self) -> None:
        self.round = 0
        self.action_seat = 0
        self.game_index = 0
        self.action_list = []

    def is_raise(self, seat_id, table_info):
        total_bet = table_info['TableStatus']['User']['TotalBet']
        cur_bet = total_bet[seat_id]
        for i in range(6):
            if i!=seat_id and cur_bet <= total_bet[i]:
                return False
        return True

    def record(self, table_info):
        action_type = table_info['GameStatus']['LastAction']['Type']
        game_index  = table_info['GameIndex']

        # 新一局游戏，清空action_list
        if game_index != self.game_index:
            self.action_list.clear()
            # 添加一条小盲注的信息
            sb_pos = table_info['GameStatus']['SBCur']
            action_record = {'SeatId': sb_pos, 'Bet': 10, 'RaiseNum':0, 'Round': 0, 'GameIndex': game_index}
            self.action_list.append(action_record)

        # 记录信息
        if action_type == 31: # Bet Value不合法，自动fold
            # 这时记录一条fold
            action_record = {'SeatId': self.action_seat, 'Bet': 0, 'RaiseNum': -1, 'Round': self.round, 'GameIndex': game_index}
            self.action_list.append(action_record)
        elif action_type == 20:
            action = table_info['GameStatus']['LastAction']['LastAction']
            if action['Type'] == 5: # 弃牌的情况
                action_record = {'SeatId': self.action_seat, 'Bet': 0, 'RaiseNum': -1, 'Round': self.round, 'GameIndex': game_index}
                self.action_list.append(action_record)
            else:
                bet = self.get_last_bet(self.action_seat, self.round)
                bet = bet + action['Bet']
                raise_num = self.get_raise_num(self.round)
                if self.is_raise(self.action_seat, table_info):
                    raise_num= raise_num + 1
                action_record = {'SeatId': self.action_seat, 'Bet': bet, 'RaiseNum': raise_num, 'Round': self.round, 'GameIndex': game_index}
                self.action_list.append(action_record)
        
        # 更新对象自身的信息
        self.round = table_info['GameStatus']['Round']
        self.game_index = table_info['GameIndex']
        self.action_seat = table_info['GameStatus']['NowAction']['SeatId']
        # print('RECORD: ', self.action_list[-1])

    def display_action_history(self):
        print('ACTION HISTORY')
        for action in self.action_list:
            print('-', action)

    def get_raise_num(self, n_round):
        raise_num = 0
        for action in self.action_list:
            if action['Round'] == n_round:
                raise_num = max(raise_num, action['RaiseNum'])
        return raise_num
    
    def get_last_bet(self, seat_id, n_round):
        bet = 0
        for action in self.action_list:
            if action['Round'] == n_round and action['SeatId'] == seat_id:
                bet = action['Bet']
        return bet
    
    def get_last_effect_action(self, n_round):
        for action in reversed(self.action_list):
            if action['RaiseNum'] != -1 and action['Round'] == n_round: 
                return action
        return None




# 基本的AI工具
class BaseAI:
    def __init__(self) -> None:
        self.preflop_range_dict = self.build_preflop_range()
        print('-- INIT: Preflop range loaded')
        self.ah = ActionHistory()

    def load_range_table(self, filename):
        table = dict() # table[Hand]->freq
        with open(filename, 'r') as f:
            s = f.read()
            s = s.split(',')
            for ss in s:
                ss = ss.split(':')
                ss[1] = float(ss[1])
                table[ss[0]] = ss[1]
        return table
    
    def build_preflop_range(self):
        range_dir = './range/'
        pos_list = ['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO']
        action_list = ['raise0','raise1', 'raise2', 'raise3', 'raise4', 'call1', 'call2', 'call3', 'call4', 'allin']

        preflop_range = {}
        for pos in pos_list:
            pos_range = {}
            for action in action_list:
                table = self.load_range_table(os.path.join(range_dir, pos, action)+'.txt')
                pos_range[action] = table
            preflop_range[pos] = pos_range

        return preflop_range

    def record_action_history(self, table_info):
        self.ah.record(table_info)

    def play(self, table_info, cards_info, *args, **kwargs):
        # 默认弃牌
        decision = {'Bet': 0, 'SeatId': table_info['GameStatus']['NowAction']['SeatId'], 'Type': 5}
        return decision

