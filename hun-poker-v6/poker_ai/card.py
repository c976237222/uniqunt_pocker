# 实现card->id, id->card的转换


class Card():
    '''
    黑桃、方片、红心、梅花
    spade, diamond, heart, club
    ♠♦♥♣
    ♤♢♡♧
    ♠♢♡♣
    '''
    num_list  = '23456789TJQKA'
    type_list = '♠♢♥♧'  
    type_list2 = 'sdhc'
    def __init__(self, id) -> None:
        if type(id) == str:
            assert len(id) == 2
            self.id = self.num_list.index(id[0]) * 4 + self.type_list2.index(id[1])

        elif type(id) == int:
            self.id = id # 0-51
        
        self.card_num  = self.id // 4
        self.card_type = self.id % 4
    
    def get_num(self):
        return self.num_list[self.card_num]
    
    def get_type(self):
        return self.type_list[self.card_type]

    def __str__(self) -> str:
        if self.id not in range(52):
            return '--'
        return self.num_list[self.card_num] + self.type_list[self.card_type]

    def __repr__(self) -> str:
        return self.__str__()

    def __add__(self, other):
        return str(self) + str(other)

def hand_to_rep(hand):
    '''
    将手牌的数字表示转换为AA, AKs, AKo的表示
    '''
    assert len(hand) == 2
    if hand[0] // 4 == hand[1] // 4:
        return Card(hand[0]).get_num() + Card(hand[1]).get_num()
    elif hand[0] % 4 ==  hand[1] % 4:
        return Card(hand[0]).get_num() + Card(hand[1]).get_num() + 's'
    else:
        return Card(hand[0]).get_num() + Card(hand[1]).get_num() + 'o'

def rep_to_comb(rep):
    '''
    将AA, AKs的表示扩展为实际组合的数字表示
    例如AA -> [(48, 49), (48, 50), (48, 51), (49, 50), (49, 51), (50, 51)]
    AA有6种组合，AKs有4种，AKo有12种
    '''

    num_list  = '23456789TJQKA'
    c1 = num_list.find(rep[0]) * 4
    c2 = num_list.find(rep[1]) * 4
    c1_list = [c1, c1+1, c1+2, c1+3]
    c2_list = [c2, c2+1, c2+2 ,c2+3]

    comb_list = []

    if len(rep) == 2:
        # 手对
        for i in range(0, 3):
            for j in range(i+1, 4):
                comb = (c1_list[i], c1_list[j])
                comb_list.append(comb)
        assert len(comb_list) == 6
    elif rep[2] == 's':
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

    # 调整所有comb_list中的顺序，使得第一个数字大于第二个数字
    for i in range(len(comb_list)):
        if comb_list[i][0] < comb_list[i][1]:
            comb_list[i] = (comb_list[i][1], comb_list[i][0])
    
    return comb_list

