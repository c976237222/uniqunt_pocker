# 第一个玩家
from operator import imod
from client.client_lib import Player, tester_play, start_play
from poker_ai.thehun_ai import TheHun
# from strategy.gto import GTO    
from strategy.base import  Strategy

import sys

username = 'p_18945421836'

room_idx = 0 if len(sys.argv) == 1  else int(sys.argv[1])

def main():
    print('Join Room ID = ', room_idx)
    strategy = Strategy('Base')
    ai = TheHun(strategy)

    start_play(username, ai, room_idx)
    
if __name__=="__main__":
    main()