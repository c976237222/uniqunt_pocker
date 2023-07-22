import numpy as np
import random

from util import GameInfo
from poker_ai.action_record import ActionRecord

class Strategy:
    # 基本策略
    def __init__(self, name):
        self.name = name
        self.gto_preflop_range_dict = {}
        
    def preflop_aof(self, game_info:GameInfo, ar:ActionRecord, raise_num, **kwargs):
        # 适用于桌上有抽象allin的情况
        pass

    def preflop(self, game_info:GameInfo, ar:ActionRecord, raise_num, **kwargs):
        # 翻牌圈策略
        # 如果是allin桌,则使用上面的AOF策略
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

        # # 拿到AA，50%概率直接allin
        # if hand_to_rep(my_cards) == 'AA' and rand_num < 0.5:
        #     decision['Type'] = 2
        #     decision['Bet'] = bet_limit[2]

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


    def flop(self, game_info:GameInfo, ar:ActionRecord, win_rate, draw_rate, raise_num, **kwargs):
        # 翻牌圈按照价值打牌
        # 这里假定胜率已经算好了, 是非常接近的胜率计算
        # 翻牌圈的总体策略如下: 如果手牌胜率>0.8,则需要造池,争取打光
        # 因为是线性策略,所以考虑对手的赔率,例如跟注1个底池,odds=1/3,即至少33%的胜率,跟注10个底池,odds=10/11=0.90999,这里则需要接近90%的胜率
        # 我们把函数压缩到[0, k_odds], min_win_rate = k_odds * odds,其中k_odds为参数,越小越激进
        # 下注时均衡尺度为 wr*ps/(1-wr),但好像有点大,
        # 强牌在单挑池有几率过牌等偷,多人池直接打

        # 我们跟注时也同理

        rf, cf, pr = 0, 0, 0 # 加注频率，call/check频率，加注的底池比例

        bet_limit = game_info.bet_limit
        pot_size = game_info.pot_size
        num_not_acted = game_info.num_not_acted
        num_alive = game_info.num_alive # 有牌的玩家数量,=2表示单挑
        effect_stack = game_info.effect_stack # 有效后手

        spr = effect_stack / pot_size

        odds = bet_limit[0] / pot_size # 底池赔率，这里算实际有效的数额
        print('odds={:.2f}, {:.2f}/{:.2f}'.format(odds, bet_limit, pot_size))
        print('not_act={}, alive={}'.format(num_not_acted, num_alive))
        
        if bet_limit[0] <= 20 or bet_limit[0] < 0.1 * pot_size: # 小注等同于没打,至少100%跟注
            raise_num = 0
            
        if num_alive > 2: # 多人池
            if raise_num == 0 and num_not_acted > 1: # 前位,没人动
                if win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = 1
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光,这里调的大一点,争取转牌干光
                        pr = spr / 8
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池混合一定频率过牌和下注
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.1
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate
                else: # 多人池前位尽量不偷鸡
                    rf = 0
                    cf = 1
                    pr = 0
            elif raise_num == 0 and num_not_acted == 1: # 自己在后位,前面没人动
                if win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = 1
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 8
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池混合一定频率过牌和重注
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                else: # 多人小池后位小概率偷鸡
                    if pot_size < 300:
                        rf = win_rate
                        cf = 1 - rf
                        pr = 0.66
                    else:
                        rf = 0
                        cf = 1
                        pr = 0
            elif raise_num >= 1: # 前面有人打
                if win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = ( win_rate + 0.1 ) ** raise_num
                    rf = min(1, rf)
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 8
                    else:
                        pr = 2.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池面对有人打,可以call住去买
                    # 小概率raise
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = win_rate - 0.4
                        cf = 1 - rf
                        pr = win_rate + 0.1
                    else:
                        rf, cf, pr = 0, 0, 0
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = 0
                        cf = 1
                        pr = 0
                else: # 多人池有人打可以放弃
                    rf = 0
                    cf = 0
                    pr = 0

        if num_alive == 2: # 只剩两个人的情况
            if raise_num == 0 and num_not_acted > 1: # 前位
                if win_rate > 0.7: # 胜率较高时,造池,争取打光
                    rf = 0.85 
                    cf = 0.15 # 有15%的概率蹲住
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光,单挑打大点
                        pr = spr / 6
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 单挑混合一定频率过牌和下注,其中有更高频率去打
                    rf = win_rate + 0.2
                    cf = 1 - rf
                    pr = win_rate + 0.2
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate + 0.1
                    cf = 1 - rf
                    pr = win_rate + 0.4
                else: # 单挑池前位打小注
                    if pot_size < 400:
                        rf = 0.2
                        cf = 1 - rf
                        pr = 0.3
                    elif pot_size < 1000: # 大池可以偷小点
                        rf = 0.2
                        cf = 1 - rf
                        pr = 0.2
                    else: # 剩下就算了,过牌
                        rf = 0
                        cf = 1
                        pr = 0
            elif raise_num == 0 and num_not_acted == 1: # 自己在后位,前面没人动
                if win_rate > 0.7: # 胜率较高时,造池,争取打光
                    rf = 1
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 6
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池混合一定频率过牌和重注
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                else: 
                    if pot_size < 400: # 小池后位高频偷鸡
                        rf = 0.5
                        cf = 1 - rf
                        pr = 0.66
                    elif pot_size < 1000: # 大池可以偷小点
                        rf = 0.2
                        cf = 1
                        pr = 0.5
                    else: # 剩下就算了,过牌
                        rf = 0
                        cf = 1
                        pr = 0

            elif raise_num >= 1: # 对手下注
                if win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = ( win_rate + 0.1 ) ** raise_num
                    rf = min(1, rf)
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 6
                    else:
                        pr = 2.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池面对有人打,可以call住去买
                    # 小概率raise
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = win_rate - 0.4
                        cf = 1 - rf
                        pr = win_rate + 0.1
                    else:
                        rf, cf, pr = 0, 0, 0
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺,赔率合适
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = 0
                        cf = 1
                        pr = 0
                else: # 单挑池打大可以放弃
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = 0
                        cf = 1
                        pr = 0    
                    else:
                        rf = 0
                        cf = 0
                        pr = 0            

        return rf, cf, pr
        
    def turn(self, game_info:GameInfo, ar:ActionRecord, win_rate, draw_rate, raise_num, **kwargs):
        rf, cf, pr = self.flop(game_info, win_rate, draw_rate, raise_num, **kwargs)
        # 上一轮都check的时候增加偷鸡频率
        return rf, cf, pr

    def river(self, game_info:GameInfo, ar:ActionRecord, win_rate, draw_rate, raise_num, **kwargs):
        rf, cf, pr = 0, 0, 0 # 加注频率，call/check频率，加注的底池比例

        bet_limit = game_info.bet_limit
        pot_size = game_info.pot_size
        num_not_acted = game_info.num_not_acted
        num_alive = game_info.num_alive # 有牌的玩家数量,=2表示单挑
        effect_stack = game_info.effect_stack # 有效后手

        spr = effect_stack / pot_size

        odds = bet_limit[0] / pot_size # 底池赔率，这里算实际有效的数额
        print('odds={:.2f}, {:.2f}/{:.2f}'.format(odds, bet_limit, pot_size))
        print('not_act={}, alive={}'.format(num_not_acted, num_alive))
        
        if bet_limit[0] <= 20 or bet_limit[0] < 0.1 * pot_size: # 小注等同于没打,至少100%跟注
            raise_num = 0
            
        if num_alive > 2: # 多人池
            if raise_num == 0 and num_not_acted > 1: # 前位,没人动
                if win_rate + draw_rate >= 0.97: # 手持nuts
                    rf = 1
                    cf = 0
                    pr = max(spr/2, 5)

                elif win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = 1
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光,这里调的大一点,争取转牌干光
                        pr = spr / 8
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池混合一定频率过牌和下注
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.1
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate
                else: # 多人池前位尽量不偷鸡
                    rf = 0
                    cf = 1
                    pr = 0
            elif raise_num == 0 and num_not_acted == 1: # 自己在后位,前面没人动
                if win_rate + draw_rate >= 0.97: # 手持nuts
                    rf = 1
                    cf = 0
                    pr = max(spr/3, 5)
                elif win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = 1
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 8
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池混合一定频率过牌和重注
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                else: # 多人小池后位小概率偷鸡
                    if pot_size < 300:
                        rf = win_rate
                        cf = 1 - rf
                        pr = 0.66
                    else:
                        rf = 0
                        cf = 1
                        pr = 0
            elif raise_num >= 1: # 前面有人打
                if win_rate + draw_rate >= 0.97: # 手持nuts
                    rf = 1
                    cf = 0
                    pr = max(spr/3, 10) # 这里直接10倍allin
                elif win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = ( win_rate + 0.1 ) ** raise_num
                    rf = min(1, rf)
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 8
                    else:
                        pr = 2.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池面对有人打,可以call住去买
                    # 小概率raise
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = win_rate - 0.4
                        cf = 1 - rf
                        pr = win_rate + 0.1
                    else:
                        rf, cf, pr = 0, 0, 0
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = 0
                        cf = 1
                        pr = 0
                else: # 多人池有人打可以放弃
                    rf = 0
                    cf = 0
                    pr = 0

        if num_alive == 2: # 只剩两个人的情况
            if raise_num == 0 and num_not_acted > 1: # 前位
                if win_rate + draw_rate >= 0.97: # 手持nuts
                    rf = 1
                    cf = 0
                    pr = max(spr/3, 2)
                elif win_rate > 0.7: # 胜率较高时,造池,争取打光
                    rf = 0.85 
                    cf = 0.15 # 有15%的概率蹲住
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光,单挑打大点
                        pr = spr / 6
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 单挑混合一定频率过牌和下注,其中有更高频率去打
                    rf = win_rate + 0.2
                    cf = 1 - rf
                    pr = win_rate + 0.2
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate + 0.1
                    cf = 1 - rf
                    pr = win_rate + 0.4
                else: # 单挑池前位打小注
                    if pot_size < 400:
                        rf = 0.2
                        cf = 1 - rf
                        pr = 0.3
                    elif pot_size < 1000: # 大池可以偷小点
                        rf = 0.2
                        cf = 1 - rf
                        pr = 0.2
                    else: # 剩下就算了,过牌
                        rf = 0
                        cf = 1
                        pr = 0
            elif raise_num == 0 and num_not_acted == 1: # 自己在后位,前面没人动
                if win_rate + draw_rate >= 0.97: # 手持nuts
                    rf = 1
                    cf = 0
                    pr = max(spr/3, 2)
                elif win_rate > 0.7: # 胜率较高时,造池,争取打光
                    rf = 1
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 6
                    else:
                        pr = 1.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池混合一定频率过牌和重注
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺
                    rf = win_rate
                    cf = 1 - rf
                    pr = win_rate + 0.3
                else: 
                    if pot_size < 400: # 小池后位高频偷鸡
                        rf = 0.8
                        cf = 1 - rf
                        pr = 0.6
                    elif pot_size < 1000: # 大池可以偷小点
                        rf = 0.2
                        cf = 1
                        pr = 0.3
                    else: # 剩下就算了,过牌
                        rf = 0
                        cf = 1
                        pr = 0

            elif raise_num >= 1: # 对手下注
                if win_rate + draw_rate >= 0.97: # 手持nuts
                    rf = 1
                    cf = 0
                    pr = max(spr/3, 5)
                elif win_rate > 0.75: # 胜率较高时,造池,争取打光
                    rf = ( win_rate + 0.1 ) ** raise_num
                    rf = min(1, rf)
                    cf = 0
                    if spr > 16: # 翻牌圈打1/8后手就能在后两条街打光
                        pr = spr / 6
                    else:
                        pr = 2.5 * win_rate
                elif win_rate > 0.5: # 强听牌或者花顺抽,或者一些顶对的牌力,顶对牌力会在refine之后下降,所以不用太担心
                    # 这里底池权益较高, 多人池面对有人打,可以call住去买
                    # 小概率raise
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = win_rate - 0.4
                        cf = 1 - rf
                        pr = win_rate + 0.1
                    else:
                        rf, cf, pr = 0, 0, 0
                elif win_rate > 0.32: # 一些中等牌力或者听花/卡顺,赔率合适
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = 0
                        cf = 1
                        pr = 0
                else: # 单挑池打大可以放弃
                    m_odds = win_rate / (1 - win_rate)
                    if odds < m_odds:
                        rf = 0
                        cf = 1
                        pr = 0    
                    else:
                        rf = 0
                        cf = 0
                        pr = 0            

        return rf, cf, pr

    # def cal_raise_amount(self, pot_size, my_stack, bet_limit, factor=1.0) -> int:
    #     # 计算加注金额
    #     # factor: 加注的底池比例，默认为1，此时加注达到的金额为=pot_size*factor
    #     # 实际bet数额为 目标金额 - round_bet[my_seat_id]
    #     target_amount = pot_size * factor
    #     if my_stack - target_amount / pot_size < 0.5: # 后手不够了，就直接allin
    #         target_amount = bet_limit[2]
    #     return target_amount


