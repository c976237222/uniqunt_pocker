# 玩家行动的历史记录
# 包括当局游戏的行动历史
# 当前游戏中，每位玩家的各项数据指标统计
# 同时有记录所参与的大底池手牌的功能，当盈利/损失超过1000时，保存当前手牌的完整信息
import os
import numpy as np

class ActionRecord:
    def __init__(self) -> None:
        self.round = 0
        self.action_seat = 0
        self.game_index = -1
        self.action_list = []

    def load_user_data(self, filename='./data/user_info.npy'):
        if os.path.exists(filename):
            user_data = np.load(filename, allow_pickle=True).item()
        else:
            user_data = {}
        return user_data

        
    def record_user_info(self, table_info):

        rid = table_info['rid']
        user_ids = table_info['GamePlayer']['SeatId']
        nick_names = table_info['GamePlayer']['NickName']
        # game_index  = table_info['GameIndex']
        # total_bet = table_info['TableStatus']['User']['TotalBet']
        # 统计入池率：翻前进入raise_num >= 1:
        in_the_pot = [0, 0, 0, 0, 0, 0]
        for action in self.action_list:
            id = action['SeatId']
            bet = action['Bet']
            if bet > 20:
                in_the_pot[id] = 1

        user_data = self.load_user_data(f'./data/{rid}.npy')
        
        for i in range(len(user_ids)):
            if user_ids[i] == -1:
                continue
            if user_ids[i] not in user_data.keys():
                user_data[user_ids[i]] = {'nick_name':nick_names[i],
                                            'inpot_hands':0,
                                            'total_hands':0,
                                            }
            user_data[user_ids[i]]['inpot_hands'] += in_the_pot[i]
            user_data[user_ids[i]]['total_hands'] += 1
        np.save(f'./data/{rid}.npy', user_data)
        
        # 打印入池率信息
        for k, v in user_data.items():
            print(k, f"{v['nick_name']}", f"vpip={v['inpot_hands']/v['total_hands']:.2f}", f"{v['inpot_hands']}/{v['total_hands']}")


    def record(self, table_info):
        action_type = table_info['GameStatus']['LastAction']['Type']
        game_index  = table_info['GameIndex']

        need_update = True   # 是否需要更新范围，True需要更新，False无需更新
        # need_restart = False # 是否需要重置范围，True需要重置

        # Round 101，结算界面：
        # if table_info['GameStatus']['Round'] == 101:
        #     need_update = False
        #     self.round = 0
        #     self.game_index = -1
        #     self.record_user_info(table_info)
        #     self.action_list.clear()
        #     return need_update

        # 新一局游戏，清空action_list
        if game_index != self.game_index:
            self.record_user_info(table_info)
            self.round = 0
            self.action_seat = table_info['GameStatus']['BBCur']
            self.action_list.clear()
            # 添加一条小盲注的信息
            sb_pos = table_info['GameStatus']['SBCur']
            action_record = {'SeatId': sb_pos, 'Add': 10, 'Bet': 10, 'RaiseNum':0, 'Round': 0, 'GameIndex': game_index}
            self.action_list.append(action_record)
            # need_restart = True

        # 记录信息
        if action_type == 31: # Bet Value不合法，自动fold
            # 这时记录一条fold
            action_record = {'SeatId': self.action_seat, 'Add': 0, 'Bet': 0, 'RaiseNum': -1, 'Round': self.round, 'GameIndex': game_index}
            self.action_list.append(action_record)
            need_update = False 

        elif action_type == 20:
            action = table_info['GameStatus']['LastAction']['LastAction']
            if action['Type'] == 5: # 弃牌的情况
                action_record = {'SeatId': self.action_seat, 'Add': 0, 'Bet': 0, 'RaiseNum': -1, 'Round': self.round, 'GameIndex': game_index}
                self.action_list.append(action_record)
                need_update = False
            else:
                last_bet = self.get_last_bet(self.action_seat, self.round)
                bet = last_bet + action['Bet']
                raise_num = self.get_raise_num(self.round)
                if self.is_raise(self.action_seat, table_info) and bet > 20:
                    raise_num = raise_num + 1
                # 大盲注和limp不算做加注
                action_record = {'SeatId': self.action_seat, 'Add': action['Bet'], 'Bet': bet, 'RaiseNum': raise_num, 'Round': self.round, 'GameIndex': game_index}
                self.action_list.append(action_record) 
        
        # 更新对象自身的信息
        self.round = table_info['GameStatus']['Round']
        self.game_index = table_info['GameIndex']
        self.action_seat = table_info['GameStatus']['NowAction']['SeatId']
        return need_update # 返回True表示需要更新范围

    def is_raise(self, seat_id, table_info):
        total_bet = table_info['TableStatus']['User']['TotalBet']
        cur_bet = total_bet[seat_id]
        for i in range(6):
            if i!=seat_id and cur_bet <= total_bet[i]:
                return False
        return True

    def display(self):
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
        # 获取某个位置的玩家当轮的下注额度
        bet = 0
        for action in self.action_list:
            if action['Round'] == n_round and action['SeatId'] == seat_id:
                bet = action['Bet']
        return bet
    
    def get_last_op_bet_action(self, my_seat_id):
        # 获取上一个对手的行动，至少为check
        for action in reversed(self.action_list):
            if action['SeatId'] != my_seat_id and action['RaiseNum'] != -1:
                return action
        return None

    def get_last_action(self, n_round=None):
        if n_round is None: # 默认返回最后一条action
            return self.action_list[-1]
