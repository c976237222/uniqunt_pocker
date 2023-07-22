# 改进版的allin
# 根据位置，使用open的手牌范围直接allin
import os
import random
import math
import time
import numpy as np

import util
from util import GameInfo

from AI.BaseAI import BaseAI
from simulator import expand_range, win_rate_hand_range, win_rate_hand_range_exp, win_rate_ranges, remove_known_cards, win_rate_ranges2

class TheHun_AI(BaseAI):
    def __init__(self) -> None:
        super().__init__()
        self.game_ranges = [None, ] * 6  # 当局范围，统一使用 [51, 47] -> 0.6
        self.cards_info = {'uid': 'NotSet', 'seatId': 1, 'card': [11, 3]}

    def play_preflop(self, game_info: util.GameInfo):
        rand_num = random.random()    # [0, 1)的实数
        self.is_range_refined = False
        # 局面解析
        my_hand, my_seat_id = game_info.my_hand, game_info.my_seat_id
        btn_seat_id = game_info.btn_seat_id
        my_pos = game_info.my_pos
        raise_num = self.ah.get_raise_num(0)
        
        # 规则解析
        bet_limit = game_info.bet_limit
        # 进行决策
        decision = {'Bet': 0, 'SeatId': my_seat_id, 'Type': 5}

        # 为了避免后期翻车，在当前对手下注过大时，提升两个级别防守
        if game_info.cur_bet >= 10000:
            raise_num = 5
        elif game_info.cur_bet >= 1000:
            raise_num = 2

        # RaiseNum=0, no one open
        if raise_num == 0:
            raise_range = self.preflop_range_dict[my_pos]['raise0']
            raise_freq, call_freq = 0.0, 0.0
            if my_hand.to_common_rep() in raise_range.keys():
                raise_freq = raise_range[my_hand.to_common_rep()] 
            fold_freq = 1 - raise_freq - call_freq
            if rand_num < raise_freq:
                bet_amount = self.cal_raise_amount(game_info, factor=2)
                decision['Bet'] = bet_amount # raise
                decision['Type'] = 2

        # RaiseNum>=1，前位有行动
        # TODO: 相应不同位置对手所作动作
        elif raise_num in [1, 2, 3, 4]:
            raise_range = self.preflop_range_dict[my_pos]['raise' + str(raise_num)]
            call_range  = self.preflop_range_dict[my_pos]['call'  + str(raise_num)]

            raise_freq, call_freq = 0.0, 0.0
            if my_hand.to_common_rep() in raise_range.keys():
                raise_freq = raise_range[my_hand.to_common_rep()] 
            if my_hand.to_common_rep() in call_range.keys():
                call_freq = call_range[my_hand.to_common_rep()]
            if raise_freq + call_freq > 1.0:
                raise_freq = raise_freq 
                call_freq  = 1 - call_freq 
            fold_freq = 1- raise_freq - call_freq

            if rand_num < raise_freq:
                bet_amount = self.cal_raise_amount(game_info, factor=2.5)
                decision['Bet'] = bet_amount # raise
                decision['Type'] = 2
            elif raise_freq < rand_num and rand_num < (raise_freq+call_freq):
                bet_amount = bet_limit[0]   # call
                decision['Bet'] = bet_amount 
                decision['Type'] = 2
        # raise 4次(6bet)之后直接使用allin范围
        else:
            raise_range = self.preflop_range_dict[my_pos]['raise4']
            raise_freq, call_freq = 0.0, 0.0
            if my_hand.to_common_rep() in raise_range.keys():
                raise_freq = raise_range[my_hand.to_common_rep()] 
            fold_freq = 1- raise_freq - call_freq
            if rand_num < raise_freq:
                bet_amount = bet_limit[2] if bet_limit[2] > 0 else bet_limit[0]
                decision['Bet'] = bet_amount # raise
                decision['Type'] = 2

        # 拿到AA，50%概率直接allin
        if game_info.my_hand.to_common_rep() == 'AA':
            decision['Type'] = 2
            decision['Bet'] = bet_limit[2]

        print(f'HAND INFO: {my_hand} {my_pos} raise={raise_freq:.2f} call={call_freq:.2f} fold={fold_freq:.2f}')
        print(f'DECISION:  rand={rand_num:.1f}   {decision}')

        return decision

    def set_preflop_ranges(self, game_info:util.GameInfo) -> list:
        btn_seat_id = game_info.btn_seat_id
        preflop_range_list = [None, ] * 6
        raise_num = self.ah.get_raise_num(0)

        flag = True
        for action in self.ah.action_list:
            if action['RaiseNum'] == raise_num:
                seat_id = action['SeatId']
                pos = game_info.resolve_position(seat_id, game_info.btn_seat_id, game_info.user_status)
                if flag:
                    preflop_range_list[seat_id] = self.preflop_range_dict[pos]['raise'+str(raise_num)]
                    flag = False
                else:
                    preflop_range_list[seat_id] = self.preflop_range_dict[pos]['call'+str(raise_num)]

        # 转换为扩展形式
        for i in range(len(preflop_range_list)):
            if preflop_range_list[i] is not None:
                preflop_range_list[i] = expand_range(preflop_range_list[i])
        return preflop_range_list

    def refine_range(self, game_info:GameInfo, trust_factor:float=1.0):
        '''
        根据对手下注尺度、加注次数、当前范围，形成调整后的范围
        这里只考虑上一个对手即可
        trush_factor: 信任程度，[0-1]
        '''
        # 若翻牌第一个行动，则不需要精炼范围
        if game_info.cur_round == 1 and self.ah.action_list[-1]['Round'] == 0:
            return
        # 获取当前轮次上一个下注的人的信息
        # 当然这里可能不太合理，因为可能存在多人池，多人池里面范围不同
        # 且他加注针对的对象可能也不一样，这里只是作为一种牌力评估的方法，简单近似一下
        # TODO：把他放到record_action里面去跑，不占用自己的决策时间

        last_action = None
        for action in reversed(self.ah.action_list):
            if action['SeatId'] != self.cards_info['seatId']:
                last_action = action
                break
        if last_action is None:
            print('ERROR: LAST ACTION IS NOT FOUND!!!')
            return

        bet_size   = last_action['Bet']      # 加注大小
        raise_num  = last_action['RaiseNum'] # 加注次数
        op_seat_id = last_action['SeatId']   # 座位编号
        cur_round  = last_action['Round']    # 当前轮次

        print('last action:', last_action)

        op_range   = self.game_ranges[op_seat_id]            # 对手范围
        my_range   = self.game_ranges[game_info.my_seat_id]  # 自己范围
        # 移除block掉的牌
        op_range   = remove_known_cards(op_range, game_info.table_card + list(game_info.my_cards))

        # 估算对手手牌中的一些牌的胜率
        # wr: win_rate, dr: draw_rate
        op_wr, op_dr, op_wr_hands, op_dr_hands = win_rate_ranges2(op_range, my_range, game_info.table_card,
                                                            range_size=20, mc_num=10)
        print(f'op_win_rate: {op_wr:.3f}, op_draw_rate: {op_dr:.4f}')
        print(f'op hands win rate:')
        util.display_range(op_wr_hands, 10)
        


        print(f'op old range:')
        util.display_range(op_range, 10)
        # 进行范围中频率的调整
        for hand, win_rate in op_wr_hands.items():
            freq = op_range[hand]
            bet_ratio = bet_size / game_info.pot_size
            # 调整后频率 = 原始频率 * (胜率 + 0.6) ^ ((加注次数 + 下注比例) * 信任比例)
            new_freq = freq * ( (win_rate + 0.6) ** ( (raise_num + bet_ratio) * trust_factor ) ) 
            op_range[hand] = new_freq
        self.game_ranges[op_seat_id] = op_range

        print(f'op new range:')
        util.display_range(op_range, 10)



    def guess_win_rate(self, game_info:util.GameInfo):
        win_rate_list, draw_rate_list = [], []
        user_status = game_info.user_status
        my_cards = game_info.my_cards
        table_card = game_info.table_card
        for i in range(6):
            if user_status[i] in [1, 2, 3]:
                win_rate, draw_rate = win_rate_hand_range_exp(my_cards, self.game_ranges[i], table_card)
                win_rate_list.append(win_rate)
                draw_rate_list.append(draw_rate)
        min_win_rate   = min(win_rate_list)
        min_draw_rate  = min(draw_rate_list)
    
        return min_win_rate, draw_rate

    def play_flop(self, game_info:util.GameInfo):
        '''翻牌圈策略：\n
        - 范围胜率
        - 翻前激进+范围符合程度
        - 牌型: 成牌类型、听牌类型
        - 诈胡概率
        '''
        # 1. 估算范围
        self.game_ranges = self.set_preflop_ranges(game_info)
        self.refine_range(game_info)
        win_rate, draw_rate = self.guess_win_rate(game_info)        

        # 3. 根据胜率做出决策
        decision = self.simple_win_rate_strategy(win_rate, game_info)
        return decision

    def play_turn(self, game_info:util.GameInfo):
        self.refine_range(game_info)
        win_rate, draw_rate = self.guess_win_rate(game_info)        
        decision = self.simple_win_rate_strategy(win_rate, game_info)
        return decision

    def play_river(self, game_info:util.GameInfo):
        self.refine_range(game_info)
        win_rate, draw_rate = self.guess_win_rate(game_info)        
        decision = self.simple_win_rate_strategy(win_rate, game_info)
        return decision


    def simple_win_rate_strategy(self, win_rate, game_info: util.GameInfo):
        # 下注目标=底池/（1-胜率）
        # 下注率随raise_num增加而减小

        rand_num = random.random()    # [0, 1)的实数
        raise_num = self.ah.get_raise_num(game_info.cur_round)

        decision = {'Bet': 0, 'SeatId': game_info.my_seat_id, 'Type': 5}

        odds = game_info.bet_limit[0] / (game_info.pot_size) # 底池赔率
        m_odds = win_rate / (1 - win_rate)

        if game_info.cur_round in [1, 2, ]:
            if win_rate > 0.75:
                # win_rate加注，跟注
                raise_freq = win_rate ** raise_num
                raise_factor = win_rate if raise_num==0 else 1 + 1.5 / raise_num
                call_freq  = 1 - raise_freq
                fold_freq  = 1 - raise_freq - call_freq
            elif win_rate > 0.45:
                # 强听牌范围，混合重注、call
                raise_freq = win_rate ** (raise_num + 1)
                raise_factor = 1.5 + 1 / (raise_num + 1)
                call_freq  = 1 - raise_freq
                fold_freq  = 1 - raise_freq - call_freq
            elif win_rate > 0.20:
                # 听花、两头顺范围，混合轻注、过牌、弃牌
                raise_freq = win_rate if raise_num==0 else win_rate ** (raise_num + 1)
                raise_factor = 0.5
                if game_info.bet_limit[0] == 0: # 允许过牌的情形
                    call_freq = 1 - raise_freq
                else: # 有人下注，计算底池赔率，合适就上

                    if m_odds < odds:
                        call_freq = 1
                    else:
                        call_freq = 0
                fold_freq = 1 - raise_freq - call_freq
            else:
                raise_freq = 0.0
                if game_info.bet_limit[0] == 0:
                    call_freq = 1.0
                else:
                    call_freq = 0.0
                fold_freq = 1 - raise_freq - call_freq
        
        elif game_info.cur_round in [3, ]:
            # 河牌
            if win_rate > 0.7:
                # win_rate加注，跟注
                raise_freq = win_rate ** raise_num
                raise_factor = win_rate + 0.3 if raise_num==0 else 1 + 1.5 / raise_num
                call_freq  = 1 - raise_freq
                fold_freq  = 1 - raise_freq - call_freq
            elif win_rate > 0.4:
                # 中等牌力成牌，just call就行，或者打半池
                raise_freq = win_rate ** (raise_num + 2)
                raise_factor = 0.5
                call_freq  = 1 - raise_freq
                fold_freq  = 1 - raise_freq - call_freq
            else:
                # 垃圾牌弃牌
                raise_freq = 0.0
                if game_info.bet_limit[0] == 0:
                    call_freq = 1.0
                else:
                    call_freq = 0.0
                fold_freq = 1 - raise_freq - call_freq

        if rand_num < raise_freq:
            bet_amount = self.cal_raise_amount(game_info, factor=raise_factor)
            decision['Bet'] = bet_amount # raise
            decision['Type'] = 2
        elif raise_freq < rand_num and rand_num < (raise_freq+call_freq):
            bet_amount = game_info.bet_limit[0]   # call
            decision['Bet'] = bet_amount 
            decision['Type'] = 2

        print(f'WIN  RATE: {win_rate:.3f}')
        print(f'HAND INFO: {game_info.my_hand} {game_info.my_pos} raise={raise_freq:.2f} call={call_freq:.2f} fold={fold_freq:.2f}')
        print(f'DECISION:  rand={rand_num:.1f}   {decision}')
        return decision


    
    
    
    def cal_raise_amount(self, game_info: util.GameInfo, factor=1.0) -> int:
        # 计算加注金额
        # factor: 加注的底池比例，默认为1，此时加注达到的金额为=pot_size*factor
        # 实际bet数额为 目标金额 - round_bet[my_seat_id]

        pot_size = np.sum( game_info.total_bet)
        target_amount = pot_size * factor

        raise_amount = target_amount - game_info.round_bet[game_info.my_seat_id]
        raise_amount = int(raise_amount)

        # 翻前，决定加注时若后手不足翻牌圈底池的1倍，则直接allin
        if game_info.cur_round == 0:
            spr_flop = (game_info.my_stack - raise_amount) / (pot_size + 2*raise_amount)
            if spr_flop <= 1.0:
                raise_amount = game_info.bet_limit[2]

        else:
            # 若下注时，spr < 1, 则直接allin
            spr = game_info.my_stack / pot_size
            if spr <= 1.0:
                raise_amount = game_info.bet_limit[2]

        return raise_amount

    def revise_decision(self, decision, game_info: util.GameInfo):
        # 修复下注不正确的情况
        bet_limit = game_info.bet_limit
        bet_amount = decision['Bet']
        if decision['Type'] == 5 or decision['Bet']==0:
            return decision 
        
        # 超过上限
        if bet_limit[2] > 0 and bet_amount > bet_limit[2]:
            bet_amount = bet_limit[2]
        # 因为无法加注而造成的-1，重置为跟注数额
        elif bet_amount < 0:
            bet_amount = bet_limit[0]
        # 加注数额不足，改为call
        elif bet_amount > bet_limit[0] and bet_amount < bet_limit[1]:
            bet_amount = bet_limit[0]

        new_decision = decision
        new_decision['Bet'] = bet_amount
        return new_decision


    def play(self, game_info):

        s_time = time.time()
        print(game_info)
        self.ah.display_action_history()

        decision = {'Bet': 0, 'SeatId': game_info.my_seat_id, 'Type': 5}
        if game_info.cur_round == 0:
            decision = self.play_preflop(game_info)
        elif game_info.cur_round == 1:
            decision = self.play_flop(game_info)
        elif game_info.cur_round == 2:
            decision = self.play_turn(game_info)
        elif game_info.cur_round == 3:
            decision = self.play_river(game_info)
        
        decision = self.revise_decision(decision, game_info)

        print('Decision:', decision)
        print(f'Time Used: {time.time() - s_time:.2f}s', )
        return decision


