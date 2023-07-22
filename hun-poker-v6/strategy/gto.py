import numpy as np
import random


class GTO:
    def __init__(self, name):
        self.name = name

    def preflop(self, game_info):
        pass

    def flop(self, win_rate, draw_rate, raise_num, my_stack, pot_size, bet_limit, my_seat_id, num_not_acted):
        rf, cf, pr = 0, 0, 0 # 加注频率，call/check频率，加注的底池比例
        # 偷鸡频率设定为0.25
        over_bet_ratio = 0.5
        odds = bet_limit[0] / pot_size + 0.01 # 底池赔率，这里不能这样算，要算实际有效的数额

        print('odds =', odds, bet_limit, pot_size)
        print('not_act =', num_not_acted)

        # 
        if win_rate > 0.75:
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


        return rf, cf, pr
        
    def turn(self, win_rate, draw_rate, raise_num, my_stack, pot_size, bet_limit, my_seat_id, num_not_acted):
        rf, cf, pr = 0, 0, 0 # 加注频率，call/check频率，加注的底池比例
        over_bet_ratio = 0.5
        odds = bet_limit[0] / pot_size + 0.01 # 底池赔率，这里不能这样算，要算实际有效的数额
        print('odds =', odds, bet_limit, pot_size)
        print('not_act =', num_not_acted)

        if win_rate + draw_rate > 0.8:
            # 80+ set,天nuts等手牌
            # 加注，过牌平衡
            if raise_num == 0 and num_not_acted > 1:
                # 第一个动
                rf = 0.6
                cf = 0.4
                pr = win_rate + 0.2 + np.random.randn() * 0.1
            elif raise_num == 0 and num_not_acted == 1:
                # 最后一个动
                rf = min(1.1 * win_rate, 1.0)
                pr = (win_rate + np.random.randn() * 0.1) * (1 + np.random.rand())
            else:
                # 前面有人打
                rf = min(1.2 * win_rate, 1)
                pr = 1.5 + win_rate / raise_num
                if random.random() < over_bet_ratio:
                    over_bet_ratio = 0.5
                    pr = 5 
            cf  = 1 - rf

        elif win_rate + draw_rate > 0.6:
            # 60-80 中等强牌,顶对/两队
            if raise_num == 0 and num_not_acted > 1:
                rf = 0.5
                cf = 0.5
                pr = win_rate + 0.2 + np.random.randn() * 0.1
            else:
                rf = win_rate * (1 / raise_num)
                pr = 0.66 + win_rate / raise_num
            cf  = 1 - rf

        elif win_rate + draw_rate > 0.45: 
            # 40-60 中等成牌,部分买牌
            if raise_num == 0:
                # 没人下注则可以自己打一个轻注
                rf = win_rate * 1.5
                cf = 1 - rf
                pr = win_rate + np.random.randn() * 0.1
            else:
                # 有人打出来,混合少量加注和call
                if win_rate / odds < 1.0:
                    cf = win_rate / odds
                    rf = 0
                    pr = 0
                else:
                    rf = win_rate
                    cf = 1 - win_rate
                
        elif win_rate + draw_rate > 0.20: 
            # 没人打可以自己打轻注
            # 赔率合适就冲锋
            # if raise_num == 0 and num_not_acted == 1:
            if raise_num == 0:
                # 没人下注则可以自己打一个轻注
                rf = win_rate * 1.5
                pr = 0.75 + win_rate + np.random.randn() * 0.1
                cf = 1 - rf
            else:
                # 有人打出来,混合跟注和弃牌
                cf = min(win_rate/ (odds+0.1), 1.0)
                rf = 0
                pr = 0 

        else:
            # 15- 弱牌,按照MDF处理
            rf = 0.0
            pr = 0
            if bet_limit[0] <= 40 and num_not_acted == 1:
                # 只剩下自己，有100%概率偷一枪2/3
                rf = 1.0
                pr = 0.75 + np.random.randn() * 0.1
                cf = 1 - rf
            elif bet_limit[0] <= 40:
                cf = 1.0
            else:
                odds = bet_limit[0] / (pot_size) # 底池赔率
                if win_rate > odds:
                    cf = 1.0
                else:
                    cf = 0.0

        return rf, cf, pr

    def river(self, win_rate, draw_rate, raise_num, my_stack, pot_size, bet_limit, my_seat_id, num_not_acted):
        rf, cf, pr = 0, 0, 0 # 加注频率，call/check频率，加注的底池比例
        over_bet_ratio = 0.5
        odds = bet_limit[0] / pot_size + 0.01 # 底池赔率，这里不能这样算，要算实际有效的数额
        print('odds =', odds, bet_limit, pot_size)
        print('not_act =', num_not_acted)
        
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


        return rf, cf, pr

    def cal_raise_amount(self, pot_size, my_stack, bet_limit, factor=1.0) -> int:
        # 计算加注金额
        # factor: 加注的底池比例，默认为1，此时加注达到的金额为=pot_size*factor
        # 实际bet数额为 目标金额 - round_bet[my_seat_id]
        target_amount = pot_size * factor
        if my_stack - target_amount / pot_size < 0.5: # 后手不够了，就直接allin
            target_amount = bet_limit[2]
        return target_amount


