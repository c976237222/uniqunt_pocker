# 第一个玩家
from client.client_lib import Player, tester_play
from multiprocessing import Process, Queue

from AI.AOF_v1 import AOF
from AI.thehun_v4 import TheHun_AI

def main():

    testers = ["p_15010502448", 
                "p_15010502448_player1", 
                "p_15010502448_player2", 
                "p_15010502448_player3", 
                "p_15010502448_player4", 
                "p_15010502448_player5"]

    start_id = 0
    num_testers = 5

    #通过这个脚本创建房间的话，将将房主权限账号单独起Player，调用_create_room()即可，之后将房间信息填充到yaml中
    testers = testers[start_id:start_id + num_testers]

    #上面有几个testers下面就跑几个进程，会同时打印log，可以写到对应用户的log里看起来会比较舒服，也可以把它拆到多个terminal里面跑，一个选手进程跑一个就行
    ps= []
    qs = [Queue() for _ in range(len(testers))]
    tasks = ["join_room"]
    for i, tester in enumerate(testers):
        # ai = TheHun_AI()
        ai = AOF()
        p = Process(target=tester_play, args=(tester, qs[i], ai))
        p.start()
        ps.append(p)
    for task in tasks:
        for q in qs:
            q.put(task)

if __name__=="__main__":
    main()
