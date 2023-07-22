import time
from poker_ai.card import Card

class GameInfo:
    def __init__(self, table_info, cards_info) -> None:
        # Table Info
        self.rid = table_info['rid']
        self.time_stamp = table_info['UpdateTimeStamp'] / 1000
        self.game_index = table_info['GameIndex']
        self.cur_round = table_info['GameStatus']['Round']
        self.user_id = table_info['GamePlayer']['SeatId']
        self.hand_chips = table_info['TableStatus']['User']['HandChips']
        self.total_bet  = table_info['TableStatus']['User']['TotalBet']
        self.round_bet  = table_info['TableStatus']['User']['RoundBet']

        self.table_card = table_info['TableStatus']['TableCard']
        self.user_status = table_info['TableStatus']['User']['Status'] # -1没人，1等待下注,2已经下注,3allin，5弃牌
        self.cur_bet = table_info['TableStatus']['RoundNowBet']
        self.btn_seat_id = table_info['GameStatus']['DealerCur']


        # User Info
        self.my_cards = tuple(cards_info['card']) # 这个是元组表示
        if self.my_cards[0] < self.my_cards[1]:
            self.my_cards = (self.my_cards[1], self.my_cards[0])
        self.my_seat_id = cards_info['seatId']
        self.my_pos = self.get_pos(self.my_seat_id, self.btn_seat_id)
        self.my_hand = Card(self.my_cards[0]) + Card(self.my_cards[1])
        self.my_stack = self.hand_chips[self.my_seat_id]

        # Decision Info
        self.effect_stack = self.get_effective_stack() # 有效后手，包括当前轮已经打进来的
        self.pot_size = sum(self.total_bet) - sum(self.round_bet)
        effect_round_bet = [min(bet, self.effect_stack) for bet in self.round_bet]
        self.pot_size += sum(effect_round_bet)

        self.bet_limit = table_info['GameStatus']['NowAction']['BetLimit']
        self.round_now_bet = table_info['TableStatus']['RoundNowBet'] # 当前最大的下注数额 
        self.my_bet = self.round_bet[self.my_seat_id] # 本轮中，之前自己下注的金额
        self.num_not_acted = len([x for x in self.user_status if x==1]) # 尚未行动的玩家数量，=1时表示只剩自己
        self.num_alive = len([x for x in self.user_status if x in [1, 2, 3]]) # 还有牌的玩家数量,=1时表示只有自己

    # 获取有效后手
    def get_effective_stack(self):
        effective_stack = 0
        for i in range(6):
            if i == self.my_seat_id:
                continue
            if self.user_status[i] in [1,2,3]:
                effective_stack = max(effective_stack, self.hand_chips[i] + self.round_bet[i])
        effective_stack = min(self.my_stack, effective_stack)
        return effective_stack
        

    # 计算seat_id位置的文字表示
    def get_pos(self, seat_id, btn_id, user_status=None, num_players=6):
        pos_names = ['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO']
        if user_status:
            # 这里从BTN的位置开始遍历，中间跳过user_status为-1的
            j = 0
            for i in range(btn_id, btn_id + num_players):
                if i % 6 == seat_id:
                    return pos_names[j]
                elif user_status[i%6] == -1: # 座位上没人
                    continue
                else:
                    j = j + 1 

        else:
            pos = (seat_id - btn_id + num_players) % num_players
        return pos_names[pos]



    def __str__(self):
        s =  '******* GameInfo *******[{}]\n'.format(get_time_str(self.time_stamp))
        s += 'GAME_INDEX:    {}        ROUND: {}         ROOM_ID: {}\n'.format(self.game_index, self.cur_round, self.rid)
        s += 'USER_ID:       {}\n'.format(self.user_id)
        s += 'CHIP      :    {}\n'.format(self.hand_chips)
        s += 'TABLE CARD:    {}\n'.format([Card(id) for id in self.table_card])
        s += 'TOTAL BET :    {}\n'.format(self.total_bet)
        s += 'ROUND BET :    {}\n'.format(self.round_bet)
        s += 'HAND      :    [{}]   STACK: {}    EFFECTIVE STACK: {}\n'.format(self.my_hand, self.my_stack, self.effect_stack)
        # 这里加一个当前手牌类型
        s += 'POSITION:      {}     SEAT_ID:{}   BTN:{}\n'.format(self.my_pos, self.my_seat_id, self.btn_seat_id)
        s += 'BET LIMIT:     {}'.format(self.bet_limit)

        return s 


def final_info_to_str(final_info):
    winner_info = final_info['Result']['Winner']
    profits = final_info['Result']['Consume']

    for k, v in profits.items():
        profits[k] = -v
    for k, v in winner_info.items():
        profits[k] = profits[k] + v

    s = 'PROFITS: {}'.format(profits)
    return s

def final_table_info_to_str(table_info):
    # 只显示公共牌和每个玩家的手牌
    table_card = table_info['TableStatus']['TableCard']
    player_card = table_info['TableStatus']['User']['Cards']

    s =  'TABLE CARD:  {}\n'.format([Card(id) for id in table_card])
    s += 'PLAYER CARD: {}'.format([Card(c[0])+ Card(c[1]) for c in player_card])
    return s

def get_time_str(time_stamp=None):
    # 默认获取当前时间
    # 也可以传入时间戳类型
    if time_stamp is None:
        time_stamp = time.time()
    
    time_struct = time.localtime(time_stamp)
    time_str=time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
    return time_str


'''
UPDATE_TABLE_INFO 
{'GamePlayer': {
    'SeatId': [-1, 'stbgb3kt', -1, 'RfS7pb2E', -1, -1], 
    'NickName': ['', 'p_15010502448', '', 'p_15010502448_player1', '', '']
    }, 
 'TableStatus': {
    'TableCard': [-1, -1, -1, -1, -1], 
    'RoundEffectRaiseBet': 1940, 
    'RoundNowBet': 980, 
    'RoundEffectBetSeat': [1], 
    'User': {
            'HandChips': [-1, 0, -1, 16000, -1, -1], 
            'Cards': [[-1, -1], [-1, -1], [-1, -1], [-1, -1], [-1, -1], [-1, -1]], 
            'TotalBet': [0, 980, 0, 20, 0, 0], 
            'RoundBet': [0, 980, 0, 20, 0, 0], 
            'Status': [-1, 3, -1, 1, -1, -1],  # -1没人, 1等待下注, 2已经下注, 3allin, 5弃牌
            'CardVisable': [0, 0, 0, 0, 0, 0], 
            'Straddle': [-1, -1, -1, -1, -1, -1], 
            'DealTwice': [-1, -1, -1, -1, -1, -1]
        }
    }, 
 'RoomSetting': {
    'BB': 20, 
    'SB': 10, 
    'RunStatus': 'Running', 
    'AutoRoom': 1
    }, 
 'GameStatus': {
    'Round': 0, 'SBCur': 1, 'BBCur': 3, 'DealerCur': 3, 'SeatCur': 1, 
    'NowAction': {'SeatId': 3, 'BetLimit': [960, 1920, 16000], 'Type': 1}, 
    'LastAction': {'LastAction': {'Bet': 970, 'SeatId': 1, 'Type': 3}, 'Type': 20, 'Text': '下注成功'}, 
    'ExtraTime': 0, 'totalBet': -1
    }, 
 'rid': 'alZZIYVu', 
 'UpdateTimeStamp': 1683574693320, 
 'GameIndex': 116
 }

PLAY_ACTION {'SeatId': 3, 'BetLimit': [960, 1920, 16000], 'Type': 1}
'''

'''
{'uid': 'stbgb3kt', 'seatId': 1, 'card': [11, 3]}
'''

