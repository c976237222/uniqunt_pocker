from gevent import monkey
monkey.patch_all()
import yaml
import requests
import threading
from multiprocessing import Queue, Process
from enum import Enum
import psutil
import json
import os
import time
import traceback
import sys
from atexit import register
import socketio
from typing import Dict, List, Union

import random
import numpy as np
from util import GameInfo


# ************* 网络设置 ******************************
URL = "http://47.101.158.57:30001"
BASE_DIR = "./log/"
PATH = os.path.join(BASE_DIR, "client_log")
if not os.path.exists(PATH):
    os.makedirs(PATH)

class AttrEnum(str, Enum):
    info = "info"
    players = "players"
    watchers = "watchers"
    cards = "cards"
    info_message = "info_message"
    error_message = "error_message"
    apply_buy_in = "apply_buy_in"
    apply_join_game = "apply_join_game"
    room_chat = "room_chat"
    table_info = "table_info"


class SendEventEnum(str, Enum):
    INFO_MESSAGE = "INFO_MESSAGE"
    ERROR_MESSAGE = "ERROR_MESSAGE"
    UPDATE_ROOM = "UPDATE_ROOM" #房间信息
    UPDATE_ROOM_USERS = "UPDATE_ROOM_USERS"#房间users
    #房间行为相关
    APPLY_BUY_IN = "APPLY_BUY_IN"
    APPLY_JOIN_GAME = "APPLY_JOIN_GAME"
    JOIN_ROOM_INFO="JOIN_ROOM_INFO" #系统通知进入房间
    JOIN_ROOM_MATCH_INFO = "JOIN_ROOM_MATCH_INFO"  # 匹配进去了房间，会在这里推送进入的房间信息

    #聊天相关
    UPDATE_ROOM_CHAT = "UPDATE_ROOM_CHAT"
    #主游戏相关
    PLAY_ACTION = "PLAY_ACTION"#下注
    UPDATE_ACTION="UPDATE_ACTION" #牌桌更新动态
    UPDATE_TABLE_INFO="UPDATE_TABLE_INFO"
    UPDATE_USER_CARDS = "UPDATE_USER_CARDS"

# 客户端封装
class Socker:
    def __init__(self, player: object, ai) -> None:

        self.client = socketio.Client(http_session=player.session)
        self.__user: Dict = player.current_user
        self.__player: Player = player
        if not player.current_user:
            raise Exception("用户没有登录")
        self.room_namespace = "/user_message"
        self.namespace="/server"
        self.current_username = player.current_user.get('username')
        self.current_user_uid = player.current_user.get('uid')
        self.URL = URL
        
        self.ai = ai
        # 程序推出的时候强制结束连接
        register(self.on_exit)

    @property
    def player(self):
        return self.__player

    @property
    def user(self):
        return self.__user

    def set_user(self, user: Dict):
        self.__user = user

    def on_exit(self):
        self.client.disconnect()

    def disconnect(self):
        try:
            self.client.disconnect()
        except Exception as e:
            print(traceback.print_exc(), e)

    def write_log(self, data: Dict, _type: str):
        with open(os.path.join(PATH, f"{self.current_username}.txt"), "a+", encoding="utf-8") as f:
            f.write(f"{_type}-----{json.dumps(data)}\n\n")

    # 响应处理服务器推给指定房间的信息
    def handle_room_message(self, event: str, data: Dict, rid: str):
        match event:
            case SendEventEnum.UPDATE_ROOM_CHAT:
                self.player.set_joined_rooms(rid, AttrEnum.room_chat, data)
                self.write_log(
                    data, f"{SendEventEnum.UPDATE_ROOM_CHAT} on_room_message")

            case SendEventEnum.UPDATE_ROOM:
                self.player.set_joined_rooms(rid, AttrEnum.info, data)
                self.write_log(
                    data, f"{SendEventEnum.UPDATE_ROOM} on_room_message")

            case SendEventEnum.INFO_MESSAGE:
                pass

            case SendEventEnum.ERROR_MESSAGE:
                pass

            case SendEventEnum.UPDATE_ROOM_USERS:
                pass
            

            case SendEventEnum.UPDATE_TABLE_INFO:
                self.player.set_joined_rooms(rid, AttrEnum.table_info, data)
                print('UPDATA TABLE INFO:')
                if type(data) != dict:
                    print(data)
                else:
                    game_index = data['GameIndex']
                    time_stamp = data['UpdateTimeStamp']
                    np.save(f'./log/test_log/{game_index}_{time_stamp}.npy', data)
                    print('file saved: ', f'./log/test_log/{game_index}_{time_stamp}.npy')
                # print(f'牌桌信息更新：{self.current_username} {rid} |Room| ', event, data)
                return

            case SendEventEnum.UPDATE_ACTION:
                #如果需要牌桌每一步的动态和结算信息，读取这个信息
                # print(f'牌桌动态信息：{self.current_username} {rid} |Room| ', event, data)
                return

    # 响应处理服务器定向推给个人的
    def handle_user_message(self, event: str, data: Dict, rid: str):
        #print(f'服务器推送{self.current_username} {rid}', event, data)
        match event:
            case SendEventEnum.PLAY_ACTION:
                '''
                在此进行决策逻辑
                收到的信息格式：
                - SeatId: int
                - BetLimit: [跟注大小，加注下限，加注上限]
                - Type: 1
                注：加注下限、加注上限可能为负数，此时不允许加注
                '''
                table_info=self.player.get_joined_room_attr(rid, AttrEnum.table_info)#此方式调用最新收到的牌桌情况，需要历史信息时，可以改装118行的接受函数，把他变为list之类的
                cards_info=self.player.get_joined_room_attr(rid, AttrEnum.cards)# {'Rid': 'kMY4yXOg', 'Cards': [{'uid': 'stbgb3kt', 'seatId': 1, 'card': [11, 3]}]}
                cards_info=cards_info['Cards'][0]

                # game_info = util2.GameInfo(table_info, cards_info)
                # decision = self.ai.play(game_info)
                # self.player.play_game(rid, decision)
                return

            case SendEventEnum.JOIN_ROOM_INFO:
                # print(f'{self.current_username} {rid} JOIN_ROOM_INFO 已成功进入房间', event, data)
                print(f'{self.current_username} {rid} JOIN_ROOM_INFO 已成功进入房间')
                return

            case SendEventEnum.UPDATE_TABLE_INFO:
                self.player.set_joined_rooms(rid, AttrEnum.table_info, data)
                print(f'{self.current_username} {rid} UPDATE_TABLE_INFO 已成功进入房间', event, data)
                # print(f'{self.current_username} {rid} UPDATE_TABLE_INFO 已成功进入房间')
                return


            case SendEventEnum.UPDATE_ACTION:#个人下单的确认信息
                # print(f'{self.current_username} {rid} ', event, data)
                if data['Type'] == 20:
                    print('bet succeed!', flush=True)
                else:
                    print('invalid bet!', flush=True)
                return

            case SendEventEnum.INFO_MESSAGE:
                pass

            case SendEventEnum.ERROR_MESSAGE:
                pass

            case SendEventEnum.UPDATE_ROOM:
                self.player.set_joined_rooms(rid, AttrEnum.info, data)
                self.write_log(
                    data, f"{SendEventEnum.UPDATE_ROOM} on_user_message") #可以使用write_log或者print

            case SendEventEnum.UPDATE_ROOM_USERS:
                print(f'{self.current_username} {rid} UPDATE_ROOM_USERS')
                self.player.set_joined_rooms(
                    rid, AttrEnum.players, data.get(AttrEnum.players))
                self.write_log(
                    data, f"{SendEventEnum.UPDATE_ROOM_USERS} on_user_message")
                return

            case SendEventEnum.UPDATE_USER_CARDS:
                self.player.set_joined_rooms(rid, AttrEnum.cards, data)
                self.write_log(
                    data, f"{SendEventEnum.UPDATE_USER_CARDS} on_user_message")
                return

    #socket加入或退出房间，与实际退出房间无关
    def send_join(self, rid: str):
        self.client.emit("join", dict(uid=self.current_user_uid, username=self.current_username, rid=rid,
                                      token=self.user.get("token")),
                         namespace=self.room_namespace)
        time.sleep(2)

    def send_leave(self, rid: str):
        self.client.emit("leave", dict(uid=self.current_user_uid,
                                       username=self.current_username,
                                       rid=rid, token=self.user.get("token")),
                         namespace=self.room_namespace)
        time.sleep(2)

    def create_conn(self, uid: Union[str, None] = None):
        if not uid:
            uid = self.current_user_uid
            print(uid)

        def print_msg(fun, message):
            print(f"{fun} {self.current_username} 收到消息:", message, "\n")

        @self.client.on('connect')
        def on_connect():
            print(f"{self.current_username} socket 已经连接上")

        @self.client.on('disconnect')
        def on_disconnect():
            print(f"{self.current_username} socket 已经断开连接")

        # 监听的服务器公共信息
        @self.client.on("server_message", namespace=self.namespace)
        def on_server_message(message: Dict):
            print_msg("on_server_message", message)

        # 房间指定用户信息
        @self.client.on(uid, namespace=self.room_namespace)
        def on_user_message(message: Dict):
            # print_msg("on_user_message", message)
            if message and message.get("event"):
                self.handle_user_message(
                    message.get("event"), message.get("data"), message.get("rid"))

        # 房间公共信息
        @self.client.on("from_room", namespace=self.room_namespace)
        def on_room_message(message: Dict):
            # print_msg("on_room_message", message)

            if message and message.get("event"):
                self.handle_room_message(
                    message.get("event"), message.get("data"), message.get("rid"))

        # 连接服务端 IP+端口
        ns_list = [  self.namespace,self.room_namespace]
        print(ns_list)
        self.client.connect(self.URL, namespaces=ns_list)
        print(f"{self.current_username} 开始等待通信")

        self.client.wait()



class Room:
    def __init__(self) -> None:
        self.info = {}
        self.players = []
        self.cards = []
        self.info_message = None
        self.error_message = None
        self.apply_buy_in = []
        self.apply_join_game = []
        self.play_action = []
        self.room_chat = []
        self.table_info=[]



class Player:
    '''
    启动socet的前提是用户进入了房间
    '''

    def __init__(self, player_username: str, ai) -> None:
        self.player_username = player_username
        self.init_args()
        self.session = requests.Session()
        self.session.verify = False
        self.sock_list: Dict[str, Socker] = {"server_msg": None}
        self.sock_thread: threading.Thread = None
        self.current_user: Dict = None
        self.current_user_uid: str = None
        self.current_username: str = None
        self.open_room_num=1#此处设置
        self.config_file="config.yaml"

        with open(self.config_file, encoding='utf-8') as f:
            self.config: Dict = yaml.load(f, Loader=yaml.FullLoader)

        self.login()
        self.sock = Socker(self, ai)
        self.create_user_socket()
        time.sleep(5)

        # 用户进入的房间信息
        self.__joined_rooms: Dict[str, Dict] = dict()




    def init_args(self) -> None:
        return

    @property
    def joined_rooms(self):
        return self.__joined_rooms

    def get_joined_room_attr(self, rid: str, attr: str):
        return getattr(self.joined_rooms.get(rid, Room()),  f"{attr}")

    def set_joined_rooms(self, rid: str, attr: AttrEnum, data: Dict[str, Dict]):
        if rid not in self.joined_rooms:
            self.__joined_rooms[rid] = Room()
        setattr(self.__joined_rooms[rid], f"{attr}", data)
        return self.joined_rooms


    def post_has_token(self, url: str, data: Dict = None, return_all=False) -> Union[Dict, List, str, int, float, None]:
        try:
            headers = {'Content-Type': 'application/json;charset=UTF-8',
                       "uid": self.current_user.get("uid"),
                       "token": self.current_user.get("token")}

            resp: requests.Response = self.session.post(
                url, data=json.dumps(data), headers=headers)

            if resp.status_code != 200:
                raise Exception("请求失败")
            res: Dict = resp.json()
            if res.get("code"):
                if res.get("code") == 1006:
                    if return_all:
                        return res
                    else:
                        return res.get("data")
                else:
                    raise Exception(res.get("msg") or "请求失败")
            if return_all:
                return res
            else:
                return res.get("data")
        except Exception as e:
            print(traceback.print_exc(), e, url)

    def get_config_user(self) -> Dict:
        users: List[Dict] = self.config.get("test_users")
        user = [i for i in users if i.get(
            "username") == self.player_username]
        if not user:
            raise Exception("--player_username的用户账号密码没有配置")
        return user[0]

    def get_room_info(self, rid: str):
        return self.post_has_token(f"{URL}/api/get_room_info", dict(rid=rid))

    def login(self) -> None:
        user = self.get_config_user()
        try:
            data = json.dumps(user)
            res = self.session.post(
                f"{URL}/api/login", data, headers={'Content-Type': 'application/json;charset=UTF-8'})
            if res.status_code != 200:
                raise Exception("请求失败")
            self.current_user: Dict = res.json().get("data")
            self.current_user_uid = self.current_user.get("uid")
            self.current_username = self.current_user.get("username")
        except Exception as e:
            print(traceback.print_exc(), e)

    def create_room(self,room_config:None) -> Union[bool, None]:
        data = self.post_has_token(f"{URL}/api/create_room",  dict( **room_config))
        if data is None:
            return
        rid = data.get("rid")
        # 用户创建完房间就自动进入房间
        self.join_room(rid, data.get('pin'))
        return rid

    # 进入房间
    def join_room(self, rid: str, pin: Union[str, None] = None) -> Union[bool, None]:
        data = self.post_has_token(
            f"{URL}/api/join_room", dict(rid=rid, pin=pin), return_all=True)
        if data.get('code') == 1006:
            match data['msg']:
                case '已在房间中':
                    self.sock.send_join(rid)
                case '房间已满':
                    print(f'{self.current_username} {rid}房间已满')
                case _:
                    print(f'{self.current_username}进入房间失败 {data["msg"]}')
            return True
        else:
            self.sock.send_join(rid)
            self.set_joined_rooms(rid, AttrEnum.info, data['data'])
        return True

    def main_tested_create_room(self,room_config):
        data=self.get_joined_room_list()
        if (res_room_num:=self.open_room_num-len(data['data']))>0:
            for i in range(res_room_num):
                self.create_room(room_config)
            print(f'房间数不够直接多开{res_room_num}个')
        data=self.get_joined_room_list()
        self.config['join_rooms']=[{'rid':rid, 'pin':room_config['pin']} for rid in data['data']]
        with open(self.config_file,'w',encoding='utf-8') as f:
            yaml.dump(data=self.config,stream=f,allow_unicode=True)
        return True
    
    # 创建单个房间
    def create_single_room(self, room_config):
        data=self.get_joined_room_list()
        self.create_room(room_config)
        data=self.get_joined_room_list()
        print(f'房间创建完毕: rid={data["data"][0]}, pin={room_config["pin"]}')

        self.config['join_rooms']=[{'rid':rid, 'pin':room_config['pin']} for rid in data['data'][:1]]
        with open(self.config_file,'w',encoding='utf-8') as f:
            yaml.dump(data=self.config,stream=f,allow_unicode=True)
        return True

    def get_joined_room_list(self) -> Union[bool, None]:
        data = self.post_has_token(
            f"{URL}/api/get_joined_room_list", return_all=True)
        return data


    def get_room_list(self) -> Union[bool, None]:
        # 进入房间就启动socket
        data = self.post_has_token(
            f"{URL}/api/get_room_list", dict(rid='', pin=''))
        return data

    def join_joined_room(self):
        data = self.get_joined_room_list()
        for rid in data['data']:
            if rid in self.__joined_rooms.keys():
                self.join_room(rid, pin='qwe')
            else:
                self.join_room(rid, pin='qwe')
                self.set_joined_rooms(rid, AttrEnum.info, data)
        return True

    def print_msg(self, res, action, data):
        if res is None:
            print(f'{self.current_username} 处理{action}：{data} 失败')
        else:
            print(f'{self.current_username}处理{action}：{data} 成功')

    def play_game(self, rid: str, action: dict):
        res = self.post_has_token(
            f"{URL}/api/play_game",
            dict(rid=rid, player_action=action))

    # 用户进入房间后，创建用户针对房间的socket,默认监听公共消息
    def create_user_socket(self):
        self.sock_thread = threading.Thread(target=self.sock.create_conn)
        self.sock_thread.start()
        print(f"{self.current_username}初始完成,3s后开始")
        # time.sleep(3)
    def test_join_room(self):
        rooms: List[Dict] = self.config.get("join_rooms")
        for room in rooms:
            rid = room.get("rid")
            pin = room.get("pin")
            print("开始进入房间")
            self.join_room(rid, pin)


def tester_play(username: str, queue: Queue, ai):
    p = Player(username, ai)
    while True:
        if queue.empty():
            time.sleep(.5)
        else:
            msg = queue.get()
            try:
                print(msg)
                match msg:
                    case "join_room":
                        p.test_join_room()
                    case "join_joined_room":
                        p.join_joined_room()
            except Exception as e:
                print(traceback.print_exc(), e)

@register
def on_exit():
    kill_process_and_its_children(os.getpid())

def kill_process(p: psutil.Process):
    try:
        p.terminate()
        _, alive = psutil.wait_procs([p, ], timeout=0.1)  # 先等 100ms
        if len(alive):
            _, alive = psutil.wait_procs(alive, timeout=3.0)  # 再等 3s
            if len(alive):
                for p in alive:
                    p.kill()
    except Exception as e:
        print(e)

def kill_process_and_its_children(p: psutil.Process):
    if not isinstance(p, psutil.Process):
        return
    p = psutil.Process(p.pid)
    if len(p.children()) > 0:
        for child in p.children():
            if hasattr(child, 'children') and len(child.children()) > 0:
                kill_process_and_its_children(child)
            else:
                kill_process(child)
    kill_process(p)

def main():
    #通过这个脚本创建房间的话，将将房主权限账号单独起Player，调用_create_room()即可，之后将房间信息填充到yaml中
    testers = ["p_15010502448", "p_15010502448_player1", "p_15010502448_player2", "p_15010502448_player3", "p_15010502448_player4", "p_15010502448_player5"][:2]#第一个为拥有创建房间权限的账号，这里需要与yaml文件中对应，不然会找不到yaml文件中配置的密码
    _p = Player(player_username=testers[0]) #这里是使用房主先创建房间，然后用房主加入的房间更新config，其他测试号会跟着进去跑，yaml文件中的房间信息基本不用手动更改
    _p.main_tested_create_room(room_config={'pin':'qwe'})
    del _p
    #上面有几个testers下面就跑几个进程，会同时打印log，可以写到对应用户的log里看起来会比较舒服，也可以把它拆到多个terminal里面跑，一个选手进程跑一个就行
    ps= []
    qs = [Queue() for _ in range(len(testers))]
    tasks = ["join_room","join_joined_room"]
    for i, tester in enumerate(testers):
        p = Process(target=tester_play, args=(tester, qs[i]))
        p.start()
        ps.append(p)
    for task in tasks:
        for q in qs:
            q.put(task)

if __name__ == "__main__":
    main()