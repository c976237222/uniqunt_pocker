# TheHun_AI，基于规则的德州扑克专家系统
# 翻前可以依据制定好的范围进行行动
# 翻后则是进行范围胜率的计算，并采用相应策略

# 这里封装的各项功能，均尽可能独立于游戏平台，降低耦合程度
import os
import time
import math
import random
import numpy as np

from poker_ai.action_record import ActionRecord
from poker_ai.range import Range
from poker_ai.eval import range_vs_range, hand_vs_range, hand_vs_hand
from poker_ai.card import Card, hand_to_rep
from strategy.base import Strategy
# from poker_ai.strategy import Strategy
# from strategy.dunzi import Strategy

from util import GameInfo

class TheHun():
    def __init__(self, strategy:Strategy) -> None:
        self.ar = ActionRecord()
        self.cards_info = {'uid': 'stbgb3kt', 'seatId': -1, 'card': [-1, -1]}
        self.preflop_range_dict = self.build_preflop_range(range_dir='./range/GTO/')
        self.game_range = [None, ] * 6 # 当局游戏的手牌范围
        self.strategy = strategy

    def build_preflop_range(self, range_dir = './range/'):
        # 加载翻前范围表
        pos_list = ['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO']
        action_list = ['raise0','raise1', 'raise2', 'raise3', 'raise4', 'call0', 'call1', 'call2', 'call3', 'call4', 'allin']

        preflop_range_dict = {}
        for pos in pos_list:
            pos_range = {}
            for action in action_list:
                pos_range[action] = Range(os.path.join(range_dir, pos, action)+'.txt')
            preflop_range_dict[pos] = pos_range

        return preflop_range_dict

    def refine_range(self, ip_range:Range, op_range:Range, ip_hand:tuple, op_hand:tuple,
                    table_card:list, raise_num, bet_size, pot_size, cur_round, threshold=0.05, trust_factor=1.0, mc_times=30000):
        '''
        这里认为ip玩家在底池中下注，其对手为op\n
        求解ip玩家的新范围
        '''

        ip_new_range = ip_range.remove_known_cards(table_card+list(op_hand)).remove_impossible_hands(threshold=threshold)
        op_new_range = op_range.remove_known_cards(table_card+list(ip_hand)).remove_impossible_hands(threshold=threshold)
        print('range_size:',len(ip_new_range), len(op_new_range))
        wr, dr, hand_wr, hand_dr = range_vs_range(ip_new_range, op_new_range, table_card, 
                                                  threshold=threshold, 
                                                  range_size=25, 
                                                  mc_times=mc_times)

        k_wr = 2  # 胜率因子
        k_ra = 2  # 加注次数因子
        k_br = 2  # 下注比例因子
        k_df = 0.05 # 防守比例增益
        # 下注满池，胜率接近100%
        # 下注半池，胜率50%左右
        # 如此计算，  

        bet_ratio = bet_size / (pot_size - bet_size)
        # print(f'bet_ratio={bet_ratio:.2f}')

        # print('multiplier=', ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 50) ) * trust_factor ))

        for hand, win_rate in hand_wr.items():
            freq = ip_new_range[hand]
        
            # 调整后频率 = 原始频率 * (胜率 * 2) ^ ((加注次数^2 + 下注比例 + log(绝对尺度)) * 信任比例)
            if bet_size > 0:
                # 这个公式太紧了
                new_freq = freq * ( (k_wr * max(win_rate+k_df, 0)) ** \
                    ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 50) ) * trust_factor ) ) 
                # new_freq = freq * ( (k_wr * max(win_rate+k_df, 0)) ** \
                #     ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 50) / (cur_round+1) ) * trust_factor ) ) 
                # new_freq = freq * ( ( (bet_ratio)/ (abs(win_rate-bet_ratio) + 0.01) ) ** \
                #     ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 10) / (cur_round+1) ) * trust_factor ) ) 
            # 过牌的情况
            if bet_size == 0:
                new_freq = freq * ((1 - win_rate) + 0.4)
            # if new_freq > threshold:
            ip_new_range[hand] = new_freq
        
        return ip_new_range


    def refine_range2(self, ip_range:Range, op_range:Range, ip_hand:tuple, op_hand:tuple,
                    table_card:list, raise_num, bet_size, pot_size, cur_round, threshold=0.05, trust_factor=1.0, mc_times=30000):
        '''
        这里认为ip玩家在底池中下注，其对手为op\n
        求解ip玩家的新范围
        '''

        ip_new_range = ip_range.remove_known_cards(table_card+list(op_hand)).remove_impossible_hands(threshold=threshold)
        op_new_range = op_range.remove_known_cards(table_card+list(ip_hand)).remove_impossible_hands(threshold=threshold)
        print('range_size:',len(ip_new_range), len(op_new_range))
        wr, dr, hand_wr, hand_dr = range_vs_range(ip_new_range, op_new_range, table_card, 
                                                  threshold=threshold, 
                                                  range_size=25, 
                                                  mc_times=mc_times)

        k_wr = 2  # 胜率因子
        k_ra = 2  # 加注次数因子
        k_br = 2  # 下注比例因子
        k_df = 0.05 # 防守比例增益
        # 下注满池，胜率接近100%
        # 下注半池，胜率50%左右
        # 如此计算，  

        bet_ratio = bet_size / (pot_size - bet_size)
        # print(f'bet_ratio={bet_ratio:.2f}')

        # print('multiplier=', ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 50) ) * trust_factor ))

        for hand, win_rate in hand_wr.items():
            freq = ip_new_range[hand]
        
            # 调整后频率 = 原始频率 * (胜率 * 2) ^ ((加注次数^2 + 下注比例 + log(绝对尺度)) * 信任比例)
            if bet_size > 0:
                # 这个公式太紧了
                new_freq = freq * ( (k_wr * max(win_rate+k_df, 0)) ** \
                    ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 50) ) * trust_factor ) ) 
                # new_freq = freq * ( (k_wr * max(win_rate+k_df, 0)) ** \
                #     ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 50) / (cur_round+1) ) * trust_factor ) ) 
                # new_freq = freq * ( ( (bet_ratio)/ (abs(win_rate-bet_ratio) + 0.01) ) ** \
                #     ( (raise_num ** k_ra + k_br * bet_ratio + math.log(bet_size+1, 10) / (cur_round+1) ) * trust_factor ) ) 
            # 过牌的情况
            if bet_size == 0:
                new_freq = freq * ((1 - win_rate) + 0.4)
            # if new_freq > threshold:
            ip_new_range[hand] = new_freq
        
        return ip_new_range

    # 更新范围时,需要根据对手胜率保留相应的组合

    def update_range(self, game_info:GameInfo):
        # 更新当局游戏的手牌范围
        action = self.ar.get_last_action()
        seat_id = action['SeatId']
        pos = game_info.get_pos(seat_id, game_info.btn_seat_id)
        bet = action['Bet']
        raise_num = action['RaiseNum']
        n_round = action['Round']

        # 这里获取决策时正确的table_card
        table_card = game_info.table_card
        if n_round == 0:
            table_card = [-1] * 5
        elif n_round == 1:
            table_card[3:] = [-1, -1]
        elif n_round == 2:
            table_card[4] = -1


        # 获取上一个当轮上一个玩家的行动，判断是call还是加注
        last_action = self.ar.get_last_op_bet_action(seat_id)
        if last_action is None or last_action['Round'] != n_round:
            # 当前轮次该玩家首先行动的，此前没有有效行动 
            last_raise_num = 0
        else:
            last_raise_num = last_action['RaiseNum']

        if raise_num > last_raise_num:
            action_type = 'raise' + str(raise_num)
        else:
            action_type = 'call' + str(raise_num)
        if raise_num >= 5:
            action_type = 'allin'


        if n_round == 0:
            # 翻前范围更新，直接读表
            self.game_range[seat_id] = self.preflop_range_dict[pos][action_type]
            # self.game_range[seat_id] = self.strategy.update_range(bet)
        else:
            # 暂时屏蔽
            # return
            op_seat_id = last_action['SeatId']
            op_range = self.game_range[op_seat_id]
            ip_range = self.game_range[seat_id]
            mc_times = 30000
            trust_factor = 0.5
            if op_seat_id == game_info.my_seat_id:
                # op为我自己，排除我自己的手牌
                self.game_range[seat_id] = self.refine_range(ip_range, op_range, [-1, -1], game_info.my_cards, 
                                                                game_info.table_card, raise_num, bet, game_info.pot_size, n_round,
                                                                trust_factor=trust_factor, mc_times=mc_times)
            elif seat_id == game_info.my_seat_id:
                # ip为我自己，
                self.game_range[seat_id] = self.refine_range(ip_range, op_range, game_info.my_cards, [-1, -1],
                                                                game_info.table_card, raise_num, bet, game_info.pot_size, n_round,
                                                                trust_factor=trust_factor, mc_times=mc_times)
            else:
                # 双方与我无关，这时手牌ip_hand和op_hand均未知
                self.game_range[seat_id] = self.refine_range(ip_range, op_range, [-1, -1], [-1, -1],
                                                                game_info.table_card, raise_num, bet, game_info.pot_size, n_round,
                                                                trust_factor=trust_factor, mc_times=mc_times)

        

    def record_action_history(self, table_info):
        game_info = GameInfo(table_info, self.cards_info)
        need_update = self.ar.record(table_info)
        if need_update and game_info.user_status[game_info.my_seat_id] in [1, 2,]:
            # print('my status:', game_info.user_status[game_info.my_seat_id])
            print('update range:', self.ar.get_last_action())
            # st = time.time()
            self.update_range(game_info)
            # et = time.time()
            # print(f'Time Used: {et-st:.2f}s')
            pass



    def play_preflop(self, raise_num, game_info: GameInfo):
        rand_num = random.random()    # [0, 1)的实数
        # self.is_range_refined = False

        # 局面解析
        my_cards, my_seat_id = tuple(game_info.my_cards), game_info.my_seat_id
        btn_seat_id = game_info.btn_seat_id
        my_pos = game_info.my_pos
        # raise_num = self.ar.get_raise_num(0)
        bet_limit = game_info.bet_limit
        cur_bet = game_info.cur_bet
        pot_size = game_info.pot_size
        my_stack = game_info.my_stack

        decision = {'Bet': 0, 'SeatId': my_seat_id, 'Type': 5}

        # 为了避免后期翻车，在当前对手下注过大时，提升两个级别防守
        if cur_bet >= 10000:
            raise_num = max(4, raise_num)
        elif cur_bet >= 1000:
            raise_num = max(2, raise_num)


        rf, cf, pr = 0.0, 0.0, 0.0

        # RaiseNum=0, no one open
        if raise_num == 0:
            raise_range = self.preflop_range_dict[my_pos]['raise0']
            if my_cards in raise_range.range_exp.keys() :
                rf = raise_range[my_cards]
                pr = 1.5

        # RaiseNum>=1，前位有行动
        # TODO: 相应不同位置对手所作动作
        elif raise_num in [1, 2, 3, 4]:
            raise_range = self.preflop_range_dict[my_pos]['raise' + str(raise_num)]
            call_range  = self.preflop_range_dict[my_pos]['call'  + str(raise_num)]

            if my_cards in raise_range.range_exp.keys():
                rf = raise_range[my_cards] 
            if my_cards in call_range.range_exp.keys():
                cf = call_range[my_cards]
            if rf + cf > 1.0:
                rf = rf 
                cf  = 1 - rf 
            pr = 2

        # raise 4次(6bet)之后直接使用allin范围
        else:
            raise_range = self.preflop_range_dict[my_pos]['raise4']
            rf, cf = 0.0, 0.0
            if my_cards in raise_range.keys():
                rf = raise_range[my_cards] 
            pr = 4

        # 拿到AA，50%概率直接allin
        if hand_to_rep(my_cards) == 'AA' and rand_num < 0.5:
            decision['Type'] = 2
            decision['Bet'] = bet_limit[2]

        # 如果赔率很好，odds < 1/3且跟注数额小于100，并且自己是可以open或者call的手牌
        # 无脑call进去

        odds = bet_limit[0] / pot_size
        print(f'odds = {odds:.2f}')
        if odds < 0.33 and bet_limit[0] < 150:
            raise_range = self.preflop_range_dict[my_pos]['raise'  + str(0)]
            call_range  = self.preflop_range_dict[my_pos]['call'  + str(1)]
            if my_cards in raise_range.range_exp.keys() or \
                           my_cards in call_range.range_exp.keys():
                cf = max(cf, 1)
        return rf, cf, pr


    def guess_win_rate(self, game_info:GameInfo):
        win_rate_list, draw_rate_list = [], []
        user_status = game_info.user_status
        my_cards = game_info.my_cards
        table_card = game_info.table_card
        for i in range(6):
            if user_status[i] in [1, 2, 3]:
                win_rate, draw_rate = hand_vs_range(my_cards, self.game_range[i], table_card, mc_times=20000)
                win_rate_list.append(win_rate)
                draw_rate_list.append(draw_rate)
        min_win_rate   = min(win_rate_list)
        min_draw_rate  = min(draw_rate_list)
    
        return min_win_rate, draw_rate

    def play_flop(self, game_info:GameInfo):
        win_rate, draw_rate = self.guess_win_rate(game_info)        

        raise_num = self.ar.get_raise_num(game_info.cur_round)
        rf, cf, pr = self.strategy.flop(game_info, self.ar, win_rate, draw_rate, raise_num)

        return rf, cf, pr, win_rate, draw_rate


    def play_turn(self, game_info:GameInfo):
        
        win_rate, draw_rate = self.guess_win_rate(game_info)        
        raise_num = self.ar.get_raise_num(game_info.cur_round)
        rf, cf, pr = self.strategy.turn(game_info, self.ar, win_rate, draw_rate, raise_num)

        return rf, cf, pr, win_rate, draw_rate

    def play_river(self, game_info:GameInfo):
        win_rate, draw_rate = self.guess_win_rate(game_info)        
        raise_num = self.ar.get_raise_num(game_info.cur_round)
        rf, cf, pr = self.strategy.river(game_info, self.ar, win_rate, draw_rate, raise_num)

        return rf, cf, pr, win_rate, draw_rate

    def play(self, game_info:GameInfo):
        
        s_time = time.time()
        print(f'[{time.asctime()}]')
        print(game_info)
        self.ar.display()

        pot_size = game_info.pot_size
        my_seat_id = game_info.my_seat_id
        bet_limit = game_info.bet_limit
        my_stack = game_info.my_stack
        my_hand = game_info.my_hand


        cur_round = game_info.cur_round
        raise_num = self.ar.get_raise_num(cur_round)
        wr, dr = np.nan, np.nan
        if game_info.cur_round == 0:
            # rf, cf, pr = self.strategy.preflop(game_info, self.ar, raise_num)
            rf, cf, pr = self.play_preflop(raise_num, game_info)
        elif game_info.cur_round == 1:
            rf, cf, pr, wr, dr = self.play_flop(game_info)
        elif game_info.cur_round == 2:
            rf, cf, pr, wr, dr = self.play_turn(game_info)
        elif game_info.cur_round == 3:
            rf, cf, pr, wr, dr = self.play_river(game_info)
        else:
            rf, cf, pr, wr, dr = self.play_river(game_info)
            # print('ERROR TPYE!')
            # # return {'Bet': 0, 'SeatId': my_seat_id, 'Type': 5}


        rand_num = random.random()
        decision = {'Bet': 0, 'SeatId': my_seat_id, 'Type': 5}


        if bet_limit[0] == 0 and rf == 0.0: # check
            bet_amount = 0   
            decision['Bet'] = bet_amount 
            decision['Type'] = 2
        elif rand_num < rf:     # raise
            bet_amount = self.strategy.cal_raise_amount(pot_size, my_stack, bet_limit, pr)
            decision['Bet'] = bet_amount          
            decision['Type'] = 2
        elif rf < rand_num and rand_num < (rf+cf):
            bet_amount = bet_limit[0]   # call
            decision['Bet'] = bet_amount 
            decision['Type'] = 2

        print('HAND:[{}],  WIN={:.2f}, DRAW={:.2f} r={:.2f}, c={:.2f}, pr={:.2f} rand={:.2f}'.format(
            my_hand,
            wr,
            dr,
            rf,
            cf,
            pr,
            rand_num
        ))

        decision = self.revise_decision(decision, game_info)
        print('Decision:', decision)
        print(f'Time Used: {time.time() - s_time:.2f}s', )
        return decision    


    def revise_decision(self, decision, game_info: GameInfo):
        # 修复下注不正确的情况
        bet_limit = game_info.bet_limit
        bet_amount = int(decision['Bet'])
        pot_size = game_info.pot_size
        my_stack = game_info.my_stack
        # 下注之后，后手不足0.5个底池，则直接allin
        if decision['Type'] == 2 and bet_amount!=0 and (my_stack - bet_amount) / pot_size < 0.5:
            bet_amount = bet_limit[2]

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


    def cal_raise_amount(self, pot_size, my_stack, bet_limit, factor=1.0) -> int:
        # 计算加注金额
        # factor: 加注的底池比例，默认为1，此时加注达到的金额为=pot_size*factor
        # 实际bet数额为 目标金额 - round_bet[my_seat_id]
        target_amount = pot_size * factor
        if my_stack - target_amount / pot_size < 0.5: # 后手不够了，就直接allin
            target_amount = bet_limit[2]
        return target_amount