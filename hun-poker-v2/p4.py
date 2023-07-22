# 第一个玩家
from client.client_lib import Player, tester_play
from multiprocessing import Process, Queue

from AI.AOF_v1 import AOF
from AI.thehun_v2 import TheHun_AI

username = "p_15010502448_player4"

def main():
    q = Queue()
    ai = TheHun_AI()
    p = Process(target=tester_play, args=(username, q, ai))
    p.start()

    q.put("join_room")
    # q.put("join_joined_room")

if __name__=="__main__":
    main()
