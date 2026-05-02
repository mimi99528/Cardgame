from time import *
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
import hashlib, sys, base64
from math import *
from random import *
from copy import *
from PIL import Image, ImageTk

#加载图片
with open("picoutput.txt", "w") as f:
    f.write("""ap_16.png
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA9UlEQVQ4jZVTMQ6CQBAclC8stbWJnRQUtJZWNDY+gEQeQEJl4gM04QE2NlaWthQW2JlQU3NvIFoch8fdCTLV7WRvZvdu1yIiMMZARGjwRj8sAGCMAQBscZCxf1TGm4nnaJwtObfInoC/1DkZ4p79q05/1i/QVoDhnlV08m1A7zmMcsSBi/mUx0UNXM45UiUv8RwuIHoWZb9urmYrc1n5bcn4BsJZjYtaz52YBMbAWIFw6nPWBMIob8n06GrfuFjnnXiz5W9iEZH2jatThTjococrcN8ZJhHNbEv4axdkASOyckBGFlC2kQv8GF0BsYSWYZlGrfMHfhxJszK4CRUAAAAASUVORK5CYII=
ap_32.png
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAQRJREFUWEdjZCAAREVF/xNSg0/+9evXjPjk8UqCNA4aBzQff0VSQNRaioHVUy0EBtwBbpMhIWBrgj8gDp+ByO/KpXIIDBoHVIXgD4G2NTQOAao7gNhsBosCUh1AKOswDhoHEMpmWXmnwZ65vMkUTGsxo/rt2l8IX9cPom7aJIg6XABWTsBDYMAdgJ7NbBXwxx6uEMCl6/ADiAx6OQEPgUHvAHQfE0rdsDQBU0dxCIw6YMBDAD3Oh28uWL4IUpKhA1jJBisfCJWEuHJJZBykhIS1FzDKgQFzAKF8PXxrQ0I+h1XX5IYA1VrFg8YBo61iQmkGJk+zfsGAOYBYi9HVUS0X0MoBAHggEBBVOySIAAAAAElFTkSuQmCC
card_test.png
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
def.png
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAATdJREFUWEfVlTEOgkAQReUQ3IHChBtQ21pxBxMKWw9ga0HiHahsrbkBiQVngEOomeSTMOEzixF3tVkjCO+/mZ2N4jh+bjx+omAAuq5b1UPbtvL8pmlkLYpC1sHA3wJUVTVpLk3Tyd+/bmA1ANQsSZLZ3tAASI6k2oSzgZ8D1HU9SorkFggMWMnxcGrAO0BZlgKZ57msVnIkYj3AGocaCAYAtfx5D8CAN4Dtbi9lu56Ok7uB1VTPeDYB8f/D+SJfH/fb+CzwBgAyHMt6O+I6m4h6DsyOzffFLMvklr7vIzkNgwNY2ozoASu53v/UgDcAqxSsB1wN6NrjfUMPBAegS8F2g2WA1d404A1Al8ICYQas5NRAMAAWiD4tcb9rctNAMAAWyKfJnQ0EA6BB2OzHjLfOhsUG1gJ4AS23dBBO+6DiAAAAAElFTkSuQmCC
phy.png
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
""")
with open("picoutput.txt", "r") as f:
    c = 0
    for l in f.readlines():
        if not c:
            n = l
            c = 1
        else:
            with open(n[:-1], "wb") as f:
                f.write(base64.b64decode(bytes(l, encoding = "utf-8")))
            c = 0
tlist = []
# from win32 import win32api, win32gui, win32print
# from win32.lib import win32con
#
# from win32.win32api import GetSystemMetrics


def get_real_resolution():
    """获取真实的分辨率"""
    # hDC = win32gui.GetDC(0)
    # # 横向分辨率
    # w = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    # # 纵向分辨率
    # h = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    w, h = 1920, 1080
    return w, h



win = tk.Tk()  # 实例化窗口
win.attributes('-fullscreen', True)
win.configure(bg="white")
width, height = get_real_resolution()
# width, height = 1080, 720
win.geometry(f"{width}x{height}+0+0")  # 设置窗口大小

# 稀有度颜色合集
colors = ["black", "skyblue", "indigo", "gold"]

# 卡牌类型合集
card_types = {"atk": "攻击", "blk": "防御", "hel": "治疗", "skl": "技能", "pas": "被动", "buf": "技能"}

# buff合集
buffsdict = {"buffs": [], "debuffs": ["pot_3"]}

# 实例化图片
ap_16 = tk.PhotoImage(file="ap_16.png")
ap_32 = tk.PhotoImage(file="ap_32.png")
card_test = tk.PhotoImage(file="card_test.png")
phy = tk.PhotoImage(file="phy.png")
blk = tk.PhotoImage(file="def.png")

# 定义字体
headtitle = ("Purisa", 24)
title = ("Purisa", 18)
text = ("Purisa", 12)
number = ("Purisa", 18)


# 时间处理
def handler_adaptor(fun, **kwds):
    """事件处理函数的适配器，相当于中介，那个event是从那里来的呢，我也纳闷，这也许就是python的伟大之处吧"""
    return lambda event, fun=fun, kwds=kwds: fun(event, **kwds)


# 版权声明：本段代码参考CSDN博主「ck3207」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
# 原文链接：https://blog.csdn.net/ck3207/article/details/80836955

def d(f):
    return randint(0, f)


# 实体基类
class obj:
    __slots__ = "name", "hp_max", "ap_max", "enqips", "cards", "hand_max", "hp", "ap", "enqips", "block", "hand", "stats", "buffs"

    def __init__(o, name, hp_max, ap_max, enqips, cards=[], hand_max=4,
                 stats={"力量": 14, "敏捷": 14, "耐力": 10, "智力": 8, "感知": 14, "魅力": 8}):
        o.name = name  # 名称
        o.hp_max = hp_max  # hp上限
        # o.hp = hp_max #初始满血
        o.ap_max = ap_max  # ap上限并设置为满ap
        o.cards = cards  # 卡组
        o.hand_max = hand_max  # 回合最大手牌量
        o.enqips = enqips  # 装备
        o.block = 0  # 格挡值
        o.hand = []  # 手牌列表
        o.stats = stats  # 六维
        o.buffs = {}  # buff字典
        # 卡组非列表，抛出异常
        if type(cards) != list:
            raise Exception("牌库必须是一个列表，而传入了一个" + str(type(cards)))
            # 设置卡牌拥有者为自己
        for c in o.cards:
            c.owner = o

    # 打出卡牌
    def playcard(o, c, t):
        global varpause, var_log
        # 如果满足卡牌在手牌中，且ap足够就打出卡牌
        if c in o.cards and c in o.hand and o.ap >= c.apcost:
            c.play(1, target=t)
        # 更新打牌提示
        win.update()
        check()

    def onbattle(self):
        self.hp = self.hp_max  # 初始满血
        self.ap = self.ap_max  # 初始满ap
        return self

    # 自动显示名字
    def __repr__(self):
        return self.name


# 卡牌类
class card:
    __slots__ = "owner", "name", "tp", "apcost", "affects", "pic", "intro", "rarity", "w", "h", "win", "canvas"

    def __init__(c, name, tp, apcost, affects, pic, intro, rarity):
        c.name, c.tp, c.apcost, c.affects = name, tp, apcost, affects  # 初始属性设置
        # print(c.tp[:3])
        c.owner = None
        c.pic = pic
        c.intro, c.rarity = intro, rarity
        # 效果非字典，抛异常
        if type(affects) != dict:
            raise Exception("效果必须是一个字典，而传入了一个" + str(type(affects)))

    # 打出
    def play(c, event, target=0):
        # ap足够
        varpause.set(varpause.get() + 1)
        o = c.owner
        if c.owner.ap >= c.apcost:
            # 扣ap
            c.owner.ap -= c.apcost
            # 手牌中移除
            c.owner.hand.remove(c)
            # 更新窗口
            win.update()
            check()
            # 应用效果
            for i in c.affects:
                if i == "hp":
                    # 获取武器加成
                    addvalue = c.owner.enqips["weapon"].addvalue[c.tp[-3:]]
                    # 第一次计算伤害
                    dmg = c.affects[i] - addvalue
                    # 更新战斗日志
                    strinf.set(strinf.get() + f"\n{c.owner}对{target}进行了{c.name}攻击，造成{abs(dmg)}点伤害")
                    # 计算护盾值影响
                    if target.block > abs(dmg):
                        target.block += dmg
                        dmg = 0
                    elif target.block:
                        target.block = 0
                        dmg = 0
                    # 伤害应用
                    target.hp += dmg
                if i == "block":
                    # 格挡直接加成
                    c.owner.block += c.affects[i]
                    strinf.set(strinf.get() + f"\n{c.owner}进行{c.name}，增加{c.affects[i]}点格挡")
                if i in buffsdict["buffs"]:
                    c.owner.buffs[i] = c.affects[i]
                    strinf.set(strinf.get() + f"\n{c.owner}对自己上了{c.affects[i]}点{i}增益效果")
                if i in buffsdict["debuffs"]:
                    target.buffs[i] = c.affects[i]
                    strinf.set(strinf.get() + f"\n{c.owner}对{target}上了{c.affects[i]}点{i}减益效果")
            return True
        return False

    def getcanvas(self, win, target, w=240, h=320):
        # 实例化canvas
        self.w, self.h = w, h
        self.win = win
        Ccanvas = tk.Canvas(win, width=w, height=h, highlightthickness=0, bd=0)
        # 卡牌背景图
        Ccanvas.create_image(10, 5, anchor='nw', image=self.pic)

        # 卡牌名称
        Ccanvas.create_rectangle(w // 2 - 100, h - 145, w // 2 + 100, h - 105, fill="DarkGray", width=5,
                                 outline="white")
        Ccanvas.create_text(w // 2, h - 130, anchor='center', text=self.name, font=title, fill="white")

        # 卡牌类型
        Ccanvas.create_rectangle(w // 2 - 50, h - 100, w // 2 + 50, h - 70, fill="DarkGray", width=0)
        Ccanvas.create_text(w // 2, h - 85, anchor='center', text=card_types[self.tp[:3]], font=title, fill="white")

        # ap消耗
        for i in range(self.apcost):
            Ccanvas.create_image(w - 10, 10 + i * 32, anchor='ne', image=ap_32)

        if "hp" in self.affects:
            # 攻击力显示
            Ccanvas.create_rectangle(10, 10, 65, 40, fill="white", width=2, outline="black")
            Ccanvas.create_image(10, 10, anchor='nw', image=globals()[self.tp[-3:]])
            Ccanvas.create_text(53, 26, anchor='center', text=abs(self.affects["hp"]), font=number, fill="black")
        if "block" in self.affects:
            # 防御显示
            Ccanvas.create_rectangle(10, 10, 65, 40, fill="white", width=2, outline="black")
            Ccanvas.create_image(10, 10, anchor='nw', image=globals()[self.tp[-3:]])
            Ccanvas.create_text(53, 26, anchor='center', text=abs(self.affects["block"]), font=number, fill="black")

        # 边框
        Ccanvas.create_rectangle(0, 0, w, h, width=10, outline=colors[self.rarity])

        # 绑定函数
        Ccanvas.bind('<Enter>', self.showinf)
        Ccanvas.bind('<Leave>', self.hideinf)
        Ccanvas.bind('<Button-1>', handler_adaptor(self.play, target=target))

        self.canvas = Ccanvas
        return Ccanvas

    def showinf(self, event):
        self.canvas.create_rectangle(5, 41, self.w - 5, self.h - 46, fill="DarkGray", tag=("mask"))
        self.canvas.create_text(self.w // 2 - 3, self.h // 2 - 18, text=self.intro, font=text, fill="white",
                                tag=("mask"))
        self.animate(0)

    def hideinf(self, event):
        self.canvas.delete("mask")
        self.animate(1)

    def animate(self, mode):
        x = self.canvas.winfo_x()
        y = self.canvas.winfo_y()
        if y != mode * 60:
            if mode:
                self.canvas.place(x=x, y=y + 6)
            else:
                self.canvas.place(x=x, y=y - 6)
            self.canvas.after(10, self.animate, mode)


# 武器类
class weapon():
    __slots__ = "name", "intro", "rarity", "addvalue"

    def __init__(self, name, intro, rarity, addvalue):
        self.name = name
        self.intro = intro
        self.rarity = rarity
        self.addvalue = {}
        self.addvalue["phy"] = addvalue[0]
        self.addvalue["mag"] = addvalue[1]


# 防具类
class defenqip():
    __slots__ = "name", "intro", "rarity", "blockvalue"

    def __init__(self, name, intro, rarity, blockvalue):
        self.name = name
        self.intro = intro
        self.rarity = rarity
        self.blockvalue = blockvalue


carddict = {
    "秒杀": card("秒杀", "atk_phy", 3, {"hp": -999999}, card_test, "隐藏测试卡牌：秒杀", 3),
    "普攻": card("普攻", "atk_phy", 1, {"hp": -10}, card_test, "隐藏测试卡牌：普攻", 0),
    "认真攻击": card("认真一击", "atk_phy", 2, {"hp": -25}, card_test, "隐藏测试卡牌：认真攻击", 1),
    "格挡": card("格挡", "blk", 1, {"block": 25}, card_test, "隐藏测试卡牌：格挡", 0),
    "投毒": card("投毒", "buf", 1, {"pot_3": 3}, card_test, "隐藏测试卡牌：投毒", 2)
}

weapondict = {
    "空": weapon("", "", "", (0, 0)),
    "训练木剑": weapon("训练木剑", "你是怎么拿到这东西的（警觉）", "normal", (10, 5))
}

enqipdict = {
    "空": defenqip("", "", "", 0),
    "布衣": defenqip("布衣", "111", "normal", 15)
}


def check():
    global varpause
    # 解除暂停
    varpause.set(varpause.get() + 1)


# md5加密（存档用）
def md5(password):
    m = hashlib.md5()
    m.update(password.encode(encoding='utf-8'))
    password_md5 = m.hexdigest()
    return password_md5


# 战斗类
class battle():
    def __init__(self, win, c1, c2):
        global varpause, button_start, var_log, strinf
        self.win = win
        for i, c in enumerate(c1):
            c1[i] = c.onbattle()
        for i, c in enumerate(c2):
            c2[i] = c.onbattle()
        self.c2 = c2
        self.c1 = c1
        # 设定回合数为0
        self._round = 0
        # 将开始游戏按钮摧毁
        try:
            button_start.destroy()
        except:
            pass
        # 各种函数的初始化
        self.infbars = tk.Canvas(self.win, bg="white", height=40, width=width)
        self.infbars.pack()
        self.checkhpbar()
        self.showround()
        frame_btn = tk.Frame(frame_main, width=width, height=380)
        frame_btn.pack(side="bottom")
        strinf.set("战斗开始")
        while self.battleon():
            # 是否跳过重置
            self.passround = False
            # 每回合回合数+1
            self._round += 1
            # 显示回合等信息
            self.showround()
            self.showlog()
            self.c1[0].hand = sample(self.c1[0].cards, self.c1[0].hand_max)
            self.c1[0].block += self.c1[0].enqips["armour"].blockvalue
            self.c2[0].block += self.c2[0].enqips["armour"].blockvalue
            if self.c1[0].block > self.c1[0].hp_max:
                self.c1[0].block = self.c1[0].hp_max
            if self.c2[0].block > self.c2[0].hp_max:
                self.c2[0].block = self.c2[0].hp_max
            self.checkhpbar()
            self.check_buff()
            # 如果ap没空且战斗未结束，继续出牌环节
            while self.c1[0].ap > 0 and self.battleon():
                self.templist = []
                # 读取玩家卡组并显示
                for n, c in enumerate(self.c1[0].hand):
                    b = c.getcanvas(frame_btn, self.c2[0])
                    self.templist.append(b)
                for b in self.templist:
                    l = len(self.templist)
                    # print(self.templist.index(b)-l/2)
                    b.place(x=width / 2 - ((self.templist.index(b) + 1 - l / 2) * 240), y=60)
                b = tk.Button(self.win, text="跳过", command=self.passr)
                b.pack(side="right", anchor="nw")
                self.templist.append(b)
                # 显示ap
                self.checkap()
                self.win.wait_variable(varpause)
                self.checkhpbar()
                self.showlog()
                # 摧毁卡牌按钮
                for b in self.templist:
                    b.destroy()
                if self.passround:
                    break
                # 重绘血条

            # 敌人自动打牌（AI会写的）
            while self.c2[0].ap > 0 and self.battleon():
                self.c2[0].hand = sample(self.c2[0].cards, self.c2[0].hand_max)
                # 目前是随机打牌
                card_play = choice(self.c2[0].hand)
                played = self.c2[0].playcard(card_play, self.c1[0])
                # 同上
                self.checkap()
                self.checkhpbar()
                self.showlog()
                # 这里是自动出牌所以要刷新
                self.win.update()
                for b in self.templist:
                    b.destroy()
                sleep(1)
            # 回ap
            self.c1[0].ap, self.c2[0].ap = self.c1[0].ap_max, self.c2[0].ap_max
        # 提示战斗结束
        strinf.set("战斗结束，胜者为%s, 用时%d回合" % (self.check_winner().name, self._round))
        # 回hp
        self.c1[0].hp, self.c2[0].hp = self.c1[0].hp_max, self.c2[0].hp_max

    # 获取回合数
    def getround(self, _round):
        return "第%d回合\n" % (_round)

    # 跳过
    def passr(self):
        global varpause
        self.passround = True
        check()

    # 重绘血，盾条
    def checkhpbar(self):
        self.infbars.delete("all")
        # 血条
        self.infbars.create_rectangle(0, 20, width // 4, 40, width=2, fill="darkgrey")
        self.infbars.create_rectangle(width - width // 4, 20, width, 40, width=2, fill="darkgrey")
        self.infbars.create_rectangle(0, 20, (width // 4) * self.c1[0].hp / self.c1[0].hp_max, 40, fill="green",
                                      width=0)
        self.infbars.create_text(width // 8, 20, fill="white", text=f"{int(self.c1[0].hp)}/{self.c1[0].hp_max}",
                                 anchor="n", font=text)
        self.infbars.create_rectangle(width - (width // 4) * self.c2[0].hp / self.c2[0].hp_max, 20, width, 40,
                                      fill="green", width=0)
        self.infbars.create_text(width - width // 8, 20, fill="white", text=f"{int(self.c2[0].hp)}/{self.c2[0].hp_max}",
                                 anchor="n", font=text)
        # 盾条
        self.infbars.create_rectangle(0, 0, (width // 4) * self.c1[0].block / self.c1[0].hp_max, 20, fill="grey",
                                      width=0)
        self.infbars.create_rectangle(width - (width // 4) * self.c2[0].block / self.c2[0].hp_max, 0, width, 20,
                                      fill="grey", width=0)
        self.infbars.create_text(width // 8, 0, fill="black", text=f"{int(self.c1[0].block)}/{self.c1[0].hp_max}",
                                 anchor="n", font=text)
        self.infbars.create_text(width - width // 8, 0, fill="black",
                                 text=f"{int(self.c2[0].block)}/{self.c2[0].hp_max}", anchor="n", font=text)
        self.win.update()

    # 绘制ap
    def checkap(self, ):
        for i in range(self.c1[0].ap):
            l = tk.Label(self.win, image=ap_16)
            l.pack(side="left", anchor="nw")
            self.templist.append(l)
        for i in range(self.c2[0].ap):
            l = tk.Label(self.win, image=ap_16)
            l.pack(side="right", anchor="ne")
            self.templist.append(l)

    # 判断战斗是否结束
    def battleon(self):
        # 是否空血
        for c in self.c1:
            if c.hp <= 0:
                return False
        for c in self.c2:
            if c.hp <= 0:
                return False
        return True

    # 检查胜者
    def check_winner(self):
        if self.c1[0].hp < self.c2[0].hp:
            return self.c2[0]
        else:
            return self.c1[0]

    # 应用buff
    def check_buff(self):
        for i in self.c1 + self.c2:
            for k, v in i.buffs.items():
                if i.buffs[k]:
                    if k.split("_")[0] == "pot":
                        dmg = 5 * int(k.split("_")[1])
                        i.hp -= dmg * i.hp_max / 100
                        strinf.set(strinf.get() + f"\n{i}毒发，造成{dmg}点伤害")

    # 绘制基础信息
    def showround(self):
        canva_inf.delete("all")
        # 回合数
        canva_inf.create_text(width // 2, 30, anchor="center", font=headtitle, text=f"第{self._round}回合")
        # 名字
        canva_inf.create_text(width, 30, anchor="e", font=title, text=self.c2[0].name)
        canva_inf.create_text(0, 30, anchor="w", font=title, text=self.c1[0].name)

    # 绘制战斗情况
    def showlog(self):
        canva_log.delete("all")
        canva_log.create_text(4, canva_log.winfo_reqheight() - 20 - 16 * strinf.get().count("\n"), anchor="nw",
                              font=text, text=strinf.get())
        canva_log.pack(side="bottom")
        # print(strinf.get())


def do_job():
    print("激活函数")


# 显示&关闭属性界面
status_shown = False
frame_status = tk.Frame(win)


def check_status():
    global status_shown
    # 隐藏属性界面
    if status_shown:
        frame_status.pack_forget()
        status_shown = False
        frame_main.pack()
    # 显示属性界面
    else:
        frame_main.pack_forget()
        c = tk.Canvas(frame_status, width=width, height=height)
        c.config(highlightthickness=0)
        # 背景
        c.create_rectangle(0, 0, width, height, fill="DarkGray", width=0)
        # 角色名
        c.create_text(width // 2, 10, anchor="n", fill="white", text=mainc.name, font=title)
        ct = 0
        # 属性
        for n, i in mainc.stats.items():
            c.create_text(width // 2, 40 + 30 * ct, anchor="n", fill="white", text="%s : %d" % (n, i), font=title)
            addp = (i - 10) // 2
            # 加值
            if addp > 0:
                color = "greenyellow"
                addp = "+%d" % (addp)
            elif addp == 0:
                color = "white"
                addp = "+%d" % (addp)
            else:
                color = "red"
            c.create_text(width // 2 + 120, 40 + 30 * ct, anchor="n", fill=color, text=addp, font=title)
            ct += 1
        c.pack()
        frame_status.pack()
        status_shown = True


# 主函数
# 几个tk变量
strinf = tk.StringVar()
strinf.set("欢迎进入无名卡牌游戏\n物品")
varpause = tk.IntVar()
varpause.set(0)
mainc = obj("mimi", 200, 3, {"weapon": weapondict["训练木剑"], "armour": enqipdict["布衣"]},
            cards=[copy(carddict["普攻"]), copy(carddict["普攻"]), copy(carddict["普攻"]), copy(carddict["普攻"]),
                   copy(carddict["认真攻击"]), copy(carddict["格挡"]), copy(carddict["格挡"]), copy(carddict["投毒"]),
                   copy(carddict["投毒"]), copy(carddict["投毒"])])
enemy = obj("meowcake", 200, 3, {"weapon": weapondict["训练木剑"], "armour": enqipdict["布衣"]},
            cards=[copy(carddict["普攻"]), copy(carddict["普攻"]), copy(carddict["普攻"]), copy(carddict["普攻"])])
frame_main = tk.Frame(win, width=width, height=height)
# 菜单栏
menubar = tk.Menu(frame_main)

savemenu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='存档（制作中）', menu=savemenu)
savemenu.add_command(label='保存', command=do_job)
savemenu.add_separator()
savemenu.add_command(label='加载', command=do_job)

bagmenu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='背包（制作中）', menu=bagmenu)
bagmenu.add_command(label='查看背包', command=do_job)
bagmenu.add_separator()
bagmenu.add_command(label='更换装备', command=do_job)

statusmenu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='属性（制作中）', menu=statusmenu)
statusmenu.add_command(label='属性', command=check_status)
statusmenu.add_separator()
statusmenu.add_command(label='技能树', command=do_job)
win.config(menu=menubar)

# 开始游戏菜单
button_start = tk.Button(frame_main, text="开始游戏（测试战斗）", command=lambda: battle(frame_main, [mainc], [enemy]))
button_start.pack(side="bottom", anchor="center", fill="x")
title = ("Purisa", 15)
# 主要信息canvas
canva_inf = tk.Canvas(frame_main, width=width, height=height // 12, highlightthickness=0, bg="white")
canva_inf.create_text(width // 2, 30, anchor="center", font=headtitle, text=strinf.get())
# 日志canvas
canva_log = tk.Canvas(frame_main, width=width, height=height // 2 - 40, highlightthickness=0)
canva_log.create_rectangle(1, 1, canva_log.winfo_reqwidth() - 2, canva_log.winfo_reqheight() - 2, width=2,
                           outline="black")
canva_inf.pack()
frame_main.pack()
frame_main.pack_propagate(0)
win.mainloop()