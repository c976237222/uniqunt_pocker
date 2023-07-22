# 第一个玩家
from client.client_lib_no_log import Player, tester_play, start_play
from poker_ai.thehun_ai import TheHun

import sys

username = 'p_18945421836_player2'
room_idx = 0 if len(sys.argv) == 1  else int(sys.argv[1])

def main():
    print('Join Room ID = ', room_idx)
    ai = TheHun()

    start_play(username, ai, room_idx)
    

if __name__=="__main__":
    main()