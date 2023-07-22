
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

def write_file(filename, *args):
    with open(filename, mode='a') as f:
        for msg in args:
            f.write(str(msg) + '\n')

class Card():

    num_list  = '23456789TJQKA'
    type_list = 'sdhc'  # 黑桃、方片、红心、梅花

    def __init__(self, id) -> None:
        self.id = id # 0-51
        self.card_num = id // 4
        self.card_type = id % 4
    
    def get_num(self):
        return self.num_list[self.card_num]
    
    def get_type(self):
        return self.type_list[self.card_type]

    def __str__(self) -> str:
        if self.id == -1:
            return 'NA'
        return self.num_list[self.card_num] + self.type_list[self.card_type]

    def __repr__(self) -> str:
        return self.__str__()

# 一副手牌
class Hand():

    def __init__(self, id1, id2):
        # 较大的手牌在前表示
        if id1 < id2:
            id1, id2 = id2, id1

        self.id1 = id1
        self.id2 = id2
        self.card1 = Card(id1)
        self.card2 = Card(id2)

    # 用AA，AKs，AKo等表示手牌
    def to_common_rep(self) -> str:
        if self.card1.card_num == self.card2.card_num:
            return self.card1.get_num() + self.card2.get_num()
        elif self.card1.card_type == self.card2.card_type:
            return self.card1.get_num() + self.card2.get_num() + 's'
        else:
            return self.card1.get_num() + self.card2.get_num() + 'o'

    def __str__(self) -> str:
        return str(self.card1) + str(self.card2)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def get_tuple(self) -> tuple:
        return (self.id1, self.id2)

    @staticmethod
    def common_rep_to_combs(common_rep) -> list:
        # 将AA, AKs的表示扩展为实际组合的数字表示
        # 例如AA -> [(48, 49), (48, 50), (48, 51), (49, 50), (49, 51), (50, 51)]
        # AA有6种组合，AKs有4种，AKo有12种
        num_list  = '23456789TJQKA'
        c1 = num_list.find(common_rep[0]) * 4
        c2 = num_list.find(common_rep[1]) * 4
        c1_list = [c1, c1+1, c1+2, c1+3]
        c2_list = [c2, c2+1, c2+2 ,c2+3]

        comb_list = []

        if len(common_rep) == 2:
            # 手对
            for i in range(0, 3):
                for j in range(i+1, 4):
                    comb = (c1_list[i], c1_list[j])
                    comb_list.append(comb)
            assert len(comb_list) == 6
        elif common_rep[2] == 's':
            # 同色牌
            for i in range(0, 4):
                comb = (c1_list[i], c2_list[i])
                comb_list.append(comb)
            assert len(comb_list) == 4
        else:
            # 杂色牌
            c1_list = [c1, c1+1, c1+2, c1+3]
            c2_list = [c2, c2+1, c2+2 ,c2+3]
            for i in range(0, 4):
                for j in range(0, 4):
                    if i == j:
                        continue
                    comb = (c1_list[i], c2_list[j])
                    comb_list.append(comb)
            assert len(comb_list) == 12
        return comb_list


class GameInfo:
    def __init__(self, table_info, cards_info) -> None:
        # Table Info
        self.rid = table_info['rid']
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
        self.pot_size = sum(self.total_bet)

        # User Info
        self.my_cards = cards_info['card'] # 这个是元组表示
        self.my_seat_id = cards_info['seatId']
        self.my_pos = self.resolve_position(self.my_seat_id, self.btn_seat_id)
        self.my_hand = Hand(self.my_cards[0], self.my_cards[1]) 
        self.my_stack = self.hand_chips[self.my_seat_id]

        # Decision Info
        self.effective_stack = self.get_effective_stack() # 有效后手，包括当前轮已经打进来的
        self.bet_limit = table_info['GameStatus']['NowAction']['BetLimit']
        self.round_now_bet = table_info['TableStatus']['RoundNowBet'] # 当前最大的下注数额 
        self.my_bet = self.round_bet[self.my_seat_id] # 本轮中，之前自己下注的金额


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
    def resolve_position(self, seat_id, btn_id, user_status=None, num_players=6):
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
        s =  '******* GameInfo *******\n'
        s += 'GAME_INDEX:    {}        ROUND: {}         ROOM_ID: {}\n'.format(self.game_index, self.cur_round, self.rid)
        # s += 'USER_ID:       {}\n'.format(self.user_id)
        s += 'CHIP      :    {}\n'.format(self.hand_chips)
        s += 'TABLE CARD:    {}\n'.format([Card(id) for id in self.table_card])
        s += 'TOTAL BET :    {}\n'.format(self.total_bet)
        s += 'ROUND BET :    {}\n'.format(self.round_bet)
        s += 'HAND      :    [{}]   STACK: {}    EFFECTIVE STACK: {}\n'.format(self.my_hand, self.my_stack, self.effective_stack)
        # 这里加一个当前手牌类型
        s += 'POSITION:      {}     SEAT_ID:{}   BTN:{}\n'.format(self.my_pos, self.my_seat_id, self.btn_seat_id)
        s += 'BET LIMIT:     {}'.format(self.bet_limit)

        return s 

'''
结算信息的格式
{'Type': 101, 
 'Result': {
    'Winner': {'5': 21736}, 
    'WinnerDetails': [{'WinnerPool': [[0, 5], 10084, [42, 50, 37, 27, 20]], 
                        'CardLevel': {'0': 2, '5': 2}, 
                        'WinResult': {'5': 10084}, 
                        'WinCard': [[51, 47]]}, 
                      {'WinnerPool': [[5], 11652, [42, 50, 37, 27, 20]], 
                        'CardLevel': {'5': 2}, 
                        'WinResult': {'5': 11652}, 
                        'WinCard': [[51, 47]]}], 
    'Consume': {'0': 4995, '1': 20, '2': 74, '3': 0, '4': 0, '5': 16647}
    }
}
'''

def final_info_tostr(final_info):
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
    s += 'PLAYER CARD: {}'.format([Hand(c[0], c[1]) for c in player_card])
    return s


def display_range(data, max_num=-1):
    data_list = list(data.items())
    # print(data_list)
    data_list.sort(key=lambda x:x[1], reverse=True)
    # print(data_list)

    if max_num > 0:
        data_list = data_list[:max_num]
    for k, v in data_list:
        print(f'{Hand(k[0], k[1])} -> {v:.2f}, ', end='')
    print('')
    


def display_table_info(table_info):
    TableStatus = table_info['TableStatus']
    GameStatus = table_info['GameStatus']
    print('HAND: {}, ROUND: {}, RID: {}'.format(table_info['GameIndex'], GameStatus['Round'], table_info['rid']))
    print('CHIP:          {}'.format(TableStatus['User']['HandChips']))
    print('TOTAL BET:     {}'.format(table_info['TableStatus']['User']['TotalBet'])) 
    print('ROUND BET:     {}'.format(table_info['TableStatus']['User']['RoundBet'])) 
    print('TABLE CARD:    {}'.format([Card(id) for id in TableStatus['TableCard']]))
    
    # print('GAME STATUS:   {}'.format(GameStatus))

def display_final_info(final_info):
    print(final_info)

# V1.4
# 0 黑桃 1 红桃 2 方片 3 草花
# 牌的id: 0-51

'''
牌面level编号
    皇家同花顺：10
    同花顺    ：9
    四条      ：8
    葫芦      ：7
    同花      ：6
    顺子      ：5
    三条      ：4
    两对      ：3
    一对      ：2
    高牌      ：1
'''

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


'''
hand.level
牌面等级：高牌 1	一对 2	两对 3	三条 4	顺子 5	同花 6	葫芦 7	四条 8	同花顺 9 皇家同花顺 10
'''
def judge_exist(x):
    if x >= 1:
        return True
    return False

# poker hand of 7 card
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

# find the bigger of two poker hand(7 cards), if cards0 < cards1 then return 1, cards0 > cards1 return -1, else return 0
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


def cards_to_str(cards_list):
    res_str = ''
    for c in cards_list:
        res_str = res_str + str(Card(c)) + ' '
    return res_str

def test_judge_two():
    hand1, hand2 = (51, 50), (49, 47)
    board = [48, 46, 40, 36, 37]

    
    seven1 = board[:]
    seven1.extend(hand1)
    seven2 = board[:]
    seven2.extend(hand2)



    res = judge_two(seven1, seven2)    
    print(res)
    print('board:  ', cards_to_str(board))
    print('hand1:  ', cards_to_str(hand1))
    print('hand2:  ', cards_to_str(hand2))



if __name__ == '__main__':
    # test()
    pass