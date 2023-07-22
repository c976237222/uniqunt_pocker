# 第一个玩家
from client.client_lib import Player
from AI.AOF_v1 import AOF

account = "p_15010502448"

def main():
    ai = AOF()
    _p = Player(player_username=account, ai=ai) #这里是使用房主先创建房间，然后用房主加入的房间更新config，其他测试号会跟着进去跑，yaml文件中的房间信息基本不用手动更改
    _p.main_tested_create_room(room_config={'pin':'123'})
    _p.create_single_room(room_config={'pin':'123'})
    del _p
    exit(0)

if __name__=="__main__":
    main()