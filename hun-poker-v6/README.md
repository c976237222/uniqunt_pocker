# 开发日志：
## TODO LIST:

- [x] 更好的日志系统：手牌信息记录，大底池保存完整计算过程
- [x] op_range_refine：缩减对手手牌范围，对手下注越大（与底池比例），强牌范围越多，弱牌范围越少
- [x] 大盲位置也是open or fold
- [ ] 新的翻前策略, limp
- [x] 面对松的选手，胜率80+的牌，一定频率前位过牌埋伏allin
- [ ] 拿到AA，30%概率正常open，剩下的提高到10-30倍open均匀分布
- [ ] 有效筹码越深，范围越紧
- [ ] 加入range_bet：利用优势范围进攻对手
- [x] 更激进的下注策略，在对手过牌时有更高概率下注，增加偷鸡频率，
- [x] 面对小注要call进去
- [x] 面对小注的情况
- [x] 顶对牌力计算的问题

- [x] 还是按照价值打牌，大牌大底池，小牌小底池，
- [x] 跑一个蒙特卡洛模拟, 获取1326种组合的胜率排行

选手ID标记：
- toddler tB47sdls p_18805195767 vpip=0.54 94/174
- A0      WQFI2CAu p_13521663920 vpip=0.27 48/176
- TopLove rNfNpdED p_13718802869 vpip=0.80 98/122
- 吃饭啦   gCgph2Dt p_15622770443 vpip=0.34 43/126
- None    jJ2M9iuq p_15974075460 vpip=0.27 35/129
- Maze    LViTAmao p_13808183055 vpip=0.56 137/244
- 酸梅汤   Gur2JsLK p_13146191266 

吃饭了感觉会拿顶对按照后手比例下注，过牌的时候多数没牌，能打必打，后位大概率偷鸡，我过牌他就allin，这就拿大牌蹲
针对方法：
- 翻牌圈：没牌打，有牌蹲，有人打就raise个5倍pot
- 转牌河牌：倾向于相信，对手打出来


## 05-16
一些翻前策略的入池率计算方法
总组合数=1326

- 强范围    90个组合(6.89%)，AA-TT, 99-66, AKs-AJs, AKo, AQo
- 小口袋对  24个组合(1.81%)，22，33，44，55
- 边缘牌    44个组合(3.32%)，ATs, KQs, AJo, KQo, KJs, QJs, JTs,
上述共11.92%
- 中等同花连张 89s 


- 本地开个字典，记录玩家信息
dict['user_id']->{'nick_name':nick_name, 
                  'num_hands':总手数，
                  'num_vpip': 翻前支付超过盲注进入底池的次数，
                  'num_wins': 赢下底池次数，
                  ‘num_3bet': 翻前进行3bet加注次数，
                  'num_4bet': 翻前进行4bet加注次数
                  }






- 完善加入指定房间的code
- AI方面：
    - 翻前行动规则（完成）
    - 手牌胜率估计策略（完成）
    - 根据手牌胜率的行动策略（完成1.0）

- 特定手牌策略方面：加入一些人工策略

- 相对牌力、绝对牌力 https://www.zhihu.com/question/294350803

- 加注不大的时候，要用一些弱范围call进去

- 大盲位置check开牌

# TheHun.AI

- 翻前策略：
    - 计算不同位置的策略表：
    - 每手牌fold, open, 3-bet, 4-bet, 5-bet, 6-bet allin的频率
    - 同时估算对手范围

- 翻牌
    - 蒙特卡洛模拟，发多次牌，计算对于对手范围的综合胜率
    - 根据对手行动进行调整范围
        - 利用自身范围，估算对手每手牌的胜率阈值，设定策略过滤一些手牌
    - 不同胜率阈值的策略：     
    - Semi-bluff

- 转牌+河牌：
    - CFR求解（TODO）

测试246到247的日志


# 环境问题
```
pip install --upgrade setuptools
pip install python-socketio
```

选手分析：
- 素晴会经常拿一些中等牌力的手牌打出大注
针对方法：面对素晴，增加拿强牌过牌的频率，下注尺度从底池倍数变成有效后手的比例，拿强牌寻求和他打光