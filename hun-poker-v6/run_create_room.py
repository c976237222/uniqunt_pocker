# 第一个玩家
from client.client_lib import Player
import sys

account = "p_15010502448"

room_num = 1 if len(sys.argv) == 1 else int(sys.argv[1])


def main():
    ai = None
    _p = Player(player_username=account, ai=ai)
    _p.main_create_room(room_config={'pin':'qwe'}, room_num=room_num)
    # print(joined_rooms)
    # for room in joined_rooms['data']:
    #     print("- pin: 'qwe'")
    #     print("  rid: {}".format(room))
    exit(0)

if __name__=="__main__":
    main()