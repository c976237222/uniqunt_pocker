# 改进版的allin
# 根据位置，使用open的手牌范围直接allin
import os
from pydoc import resolve
import random

import util

class AI:
    def __init__(self) -> None:
        self.preflop_range = self.build_preflop_range()
        print('-- INIT: Preflop range loaded')

        # 每一轮次的行动记录，{'SeatId':2, 'Bet':20, 'RaiseNum': 1, 'Type':'open'}
        # BB的 RaiseNum=0
        self.action_history = []    

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
        action_list = ['open', 'callopen', '3bet', 'call3bet', '4bet', 'call4bet', '5bet', 'call5bet', 'allin']

        preflop_range = {}
        for pos in pos_list:
            pos_range = {}
            for action in action_list:
                table = self.load_range_table(os.path.join(range_dir, pos, action)+'.txt')
                pos_range[action] = table
            preflop_range[pos] = pos_range

        return preflop_range


    def resolve_table_info(self, table_info):

        print('*****************')
        util.display_table_info(table_info)

    def resolve_hand_cards(self, cards_info):
        '''
        {'uid': 'stbgb3kt', 
         'seatId': 1, 
         'card': [11, 3]}
        '''
        print('HAND_CARDS:', cards_info)

        my_cards = cards_info['card']
        my_seat_id = cards_info['seatId']

        my_hand = util.Hand(my_cards[0], my_cards[1])
        print('My Hand: ', my_hand)
        return my_hand, my_seat_id
    
    def resolve_position(self, seat_id, btn_id, num_players=6):
        # 0: BTN, 1: SB, 2: BB
        pos_names = ['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO']
        # btn_seat_id = table_info['GameStatus']['DealerCur']
        # my_seat_id = hand_cards['SeatId']
        pos = (seat_id - btn_id + num_players) % num_players
        return pos_names[pos]

    def record_action_history(self, table_info):
        # last_action: {'Bet': 980, 'SeatId': 5, 'Type': 3}

        if not table_info['GameStatus']:
            return
        
        last_action = table_info['GameStatus']['LastAction']['LastAction']
        last_id = last_action['SeatId']
        last_type = last_action['Type']
        round_bet = table_info['TableStatus']['RoundBet'] # list[i] 第i个玩家在当前轮的下注
        last_bet = round_bet[last_id]
        num_round = table_info['GameStatus']['Round']
        success_bet = table_info['GameStatus']['LastAction']['Type'] == 20
        if num_round == 0:
            MIN_BET = table_info['RoomSetting']['BB']
        else:
            MIN_BET = 0
        
        if len(self.action_history) != 0 and num_round != self.action_history[-1]['Round']:
            self.clear_action_history()
        
        # 不进行记录的情况
        if not success_bet:
            return
        if last_id == self.action_history[-1]['SeatId']:
            return
        if last_type == 5: # 弃牌不进行记录
            return

        # 记录各种情况的raise_num
        if last_bet <= MIN_BET:
            raise_num = 0
        elif len(self.action_history) == 0 and last_bet > MIN_BET:
            raise_num = 1 
        elif len(self.action_history) > 0 and last_bet > self.action_history[-1]['Bet']:
            raise_num = self.action_history[-1]['RaiseNum'] + 1
        elif len(self.action_history) > 0 and last_bet == self.action_history[-1]['Bet']:
            raise_num = self.action_history[-1]['RaiseNum'] 
        else:
            print('ERROR: CAN NOT RESOLVE RAISE NUM')
            print('History BET:', self.action_history[-1]['Bet'])
            print('Last    BET:', last_bet)
            print('Round   BET:', round_bet)
            raise_num = 0
        
        self.action_history.append({'SeatId': last_id, 'Bet': last_bet, 'RaiseNum': raise_num})
            

    def clear_action_history(self):
        self.action_history = []


    def play(self, table_info, cards_info, *args, **kwargs):
        
        self.resolve_table_info(table_info)
        my_hand, my_seat_id = self.resolve_hand_cards(cards_info)

        btn_seat_id = (table_info['GameStatus']['DealerCur'] - 1 + 6) % 6 
        print('DEALER_POS:', btn_seat_id)

        my_pos = self.resolve_position(my_seat_id, btn_seat_id)
        print(f'Position: {my_pos}')

        open_freq = 0.0
        rand_num = random.random()
        hand_rep = my_hand.to_common_rep()

        flag1 = hand_rep in self.preflop_range[my_pos]['open']
        if flag1:
            open_freq = self.preflop_range[my_pos]['open'][hand_rep]
            flag2 = open_freq > rand_num
        else:
            flag2 = False

        max_bet = table_info['GameStatus']['NowAction']['BetLimit'][2]
        if max_bet == -1:
            max_bet = table_info['GameStatus']['NowAction']['BetLimit'][0]


        print(f'freq: {open_freq:.4f}, rand_num={rand_num:.4f}')
        # 默认弃牌
        decision = {'Bet': 0, 'SeatId': table_info['GameStatus']['NowAction']['SeatId'], 'Type': 5}
        if flag1 and flag2:
            # allin
            decision['Bet'] = max_bet
            decision['Type'] = 2
        
        print('Decision:', decision)
        return decision

