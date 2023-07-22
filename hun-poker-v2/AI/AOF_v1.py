# 改进版的allin
# 根据位置，使用open的手牌范围直接allin
from bdb import effective
import os
from pydoc import resolve
import random
from time import sleep

import util
from AI.BaseAI import BaseAI

class AOF(BaseAI):
    def __init__(self) -> None:
        super().__init__()

    def play(self, table_info, cards_info, *args, **kwargs):
        
        self.resolve_table_info(table_info)
        self.display_action_history()
        my_hand, my_seat_id = self.resolve_hand_cards(cards_info)

        my_seat_id = cards_info['seatId']
        total_bet  = table_info['TableStatus']['User']['TotalBet']
        round_bet  = table_info['TableStatus']['User']['RoundBet']
        my_stack   = table_info['TableStatus']['User']['HandChips'][my_seat_id]

        # 计算实际有效后手
        hand_chips = table_info['TableStatus']['User']['HandChips']
        alive_players = self.get_alive_players_list(table_info)
        effective_stack = 0
        for i in range(6):
            if i == my_seat_id:
                continue
            if alive_players[i] == 1:
                effective_stack = max(effective_stack, hand_chips[i] + total_bet[i])
        effective_stack = min(my_stack, effective_stack)
        print('ALIVE: ', alive_players)
        print('有效后手', effective_stack)

        if effective_stack <= 2000:
            aof_range = 'raise0'
        elif effective_stack <= 5000:
            aof_range = 'raise1'
        elif effective_stack <= 20000:
            aof_range = 'raise2'
        elif effective_stack <= 50000:
            aof_range = 'raise3'
        else:
            aof_range = 'raise4'

        btn_seat_id = (table_info['GameStatus']['DealerCur'] + 6) % 6 
        my_pos = self.resolve_position(my_seat_id, btn_seat_id)
        print(f'Position: {my_pos}   AOF Range: {aof_range}')

        open_freq = 0.0
        rand_num = random.random()
        hand_rep = my_hand.to_common_rep()

        flag1 = hand_rep in self.preflop_range_dict[my_pos][aof_range]
        if flag1:
            open_freq = self.preflop_range_dict[my_pos][aof_range][hand_rep]
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

