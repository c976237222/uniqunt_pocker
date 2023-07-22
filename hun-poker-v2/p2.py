# 第一个玩家
from client.client_lib import Player, tester_play, start_play
from AI.thehun_v2 import TheHun_AI

import sys

username = 'p_15010502448_player2'
room_idx = 0 if len(sys.argv) == 1  else int(sys.argv[1])

def main():
    print('Join Room ID = ', room_idx)
    ai = TheHun_AI()

    start_play(username, ai, room_idx)
    

if __name__=="__main__":
    main()