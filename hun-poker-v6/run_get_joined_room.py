# 第一个玩家
from client.client_lib import Player

account = "p_15010502448"

def main():
    ai = None
    _p = Player(player_username=account, ai=ai)
    joined_rooms = _p.get_joined_room_list()
    print(joined_rooms)
    for room in joined_rooms['data']:
        print("- pin: 'qwe'")
        print("  rid: {}".format(room))
    exit(0)

if __name__=="__main__":
    main()