# **** coding: utf-8 *****

import csv
import math
import time
import numpy as np


class ShopInfo(object):
    def __init__(self):
        # shop information file, 8477 shops in total
        self.file = r'C:\Users\Feng\Desktop\CustomerPosition\first_shop_info.csv'

        # store the location of each shop
        self.shop_location = {}  # key is the shop_id, and value is a list of longitude and latitude(float value)
        self.shop_mall = {}  # key is the shop_id, and value is the corresponding mall_id

    def readfile(self):
        shop_f = open(self.file, 'rU')
        shop_r = csv.reader(shop_f)
        for i, row in enumerate(shop_r):
            if i > 0:
                self.shop_location[row[0]] = map(eval, row[2:4])
                self.shop_mall[row[0]] = row[-1]
        shop_f.close()

        # return self.shop_location, self.shop_mall


class TestingData(object):
    def __init__(self):
        # AB testing data file, total 483931 rows
        self.file = r'C:\Users\Feng\Desktop\CustomerPosition\first_evaluation_public.csv'

        # store the location of each testing user/row
        self.user_location = {}  # key is the row_id, and value is a list of longitude and latitude(float value)

    def readfile(self):
        user_f = open(self.file, 'rU')
        user_r = csv.reader(user_f)
        for i, row in enumerate(user_r):
            if i > 0:
                self.user_location[row[0]] = map(eval, row[4:6])
        user_f.close()

        return self.user_location


def getDistance(p1, p2):
    '''This fuction is to calculate the earth distance between two points given their longitudes
    and latitudes. x=[lon,lat], y=[lon,lat] '''
    r = 6371.004  # radius of earth
    x = [math.pi * val / 180 for val in p1]  # transfer angle to radian
    y = [math.pi * val / 180 for val in p2]
    dist = r * math.acos(math.cos(x[1]) * math.cos(y[1]) * math.cos(x[0] - y[0]) + math.sin(x[1]) * math.sin(y[1]))

    return dist


'''Using only one variable--Distance'''


def simple_dist_method():
    '''This function only use the distance between users and shops to predict.'''
    result = [['row_id', 'shop_id']]
    shop = ShopInfo()
    user = TestingData()
    sh_dict = shop.readfile()
    us_dict = user.readfile()

    cnt = 0
    print
    cnt

    for row_id, us_loc in us_dict.items():
        min_dist = 1000
        min_shop = ''
        for shop_id, sh_loc in sh_dict.items():
            d = getDistance(us_loc, sh_loc)
            if d < min_dist:
                min_dist = d
                min_shop = shop_id
        result.append([row_id, min_shop])
        cnt += 1
        print
        cnt

    f = open(r'C:\Users\Feng\Desktop\CustomerPosition\results\simple_dist_result.csv', 'wb')
    writer = csv.writer(f)
    for rows in result:
        writer.writerow(rows)
    f.close()


class TrainingData(object):
    def __init__(self):
        # training data file, total 1048575 rows
        self.file = r'C:\Users\Feng\Desktop\CustomerPosition\first_user_behavior.csv'

        # store the user behavior data
        self.user_behav = []  # store the user behavior in the given list order

        self.mall_catg = {}  # group all records into 97 categories according to mall_id, {mall_id:[[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}],..]}
        self.shop_catg = {}  # group all records into 8423 categories according to shop_id, {shop_id:[[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}],..}
        self.open_time = {}  # store the open time for each shop, {shop_id:[min,max],...}
        self.shop_wifi = {}  # for each shop, get the frequency of all wifis occurred, 8336 shops left, {shop_id:{wifi1:freq,..},..}
        self.shop_top10_wifi = {}  # for each shop, get the top 10 wifi names, {shop_id:[wifi_id1,wifi_id2,...],...}

        self.model_input_data = {}  # get the lon,lat,wifi values,shop_id for each record, group by mall_id and shop_id, {mall_id:{shop_id:[[lon,lat,wifi1,..,wifi10],..],..},..}

    def readfile(self):

        sh = ShopInfo()
        sh.readfile()
        behav_time = {}

        user_f = open(self.file, 'rU')
        user_r = csv.reader(user_f)

        for i, row in enumerate(user_r):
            if i > 0:
                del row[0]  # delete user_id, not need
                tm = int(row[1][-5:-3]) * 60 + int(row[1][-2:])
                row.insert(2, tm)

                wifi = row[5].replace('|false', '')
                wifi = wifi.replace('|true', '')
                wifi = wifi.replace(';', ",'")
                wifi = wifi.replace('|', "':")
                wifi = "{'" + wifi + "}"
                wifi_dict = eval(wifi)

                row[5] = wifi_dict  # row=[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}]
                self.user_behav.append(row)

                mall_id = sh.shop_mall[row[0]]
                if mall_id not in self.mall_catg:
                    self.mall_catg[mall_id] = [row]
                else:
                    self.mall_catg[mall_id].append(row)

                shop_id = row[0]
                if shop_id not in self.shop_catg:
                    self.shop_catg[shop_id] = [row]
                else:
                    self.shop_catg[shop_id].append(row)
                if shop_id not in behav_time:
                    behav_time[shop_id] = [row[2]]
                else:
                    behav_time[shop_id].append(row[2])

        user_f.close()

        for key in behav_time:
            self.open_time[key] = [min(behav_time[key]), max(behav_time[key])]

            # return self.user_behav

    def shopWifiFreq(self):
        for key, val in self.shop_catg.items():  # 一个shop
            wifi_dict = {}
            for va in val:  # 一条记录
                temp = []  # 一条记录可能多次出现同一个WiFi，只取一个避免重复
                for k in va[5]:
                    if k not in wifi_dict:
                        wifi_dict[k] = 1
                        temp.append(k)
                    else:
                        if k not in temp:
                            wifi_dict[k] += 1

            if len(wifi_dict) >= 10:  # 剔除Wifi种类小于10的类别（店铺）
                self.shop_wifi[key] = wifi_dict

                wifi_list = []
                for key1, val1 in wifi_dict.items():
                    wifi_list.append([val1, key1])  # 把frequency值放在第一个，对应的WiFi名字放第二，以便下一步直接排序
                wifi_list.sort(reverse=True)  # order by wifi frequency in descending
                self.shop_top10_wifi[key] = [val2[1] for key2, val2 in enumerate(wifi_list) if
                                             key2 < 10]  # 取top10 WiFi的id

    def getInputData(self):  # 获取模型需要的输入数据，经纬度、top 10 WiFi的值，以及类别标签shop_id
        shop_data = {}  # 保存每一个shop下的所有记录的经纬度和top10 WiFi

        for key, val in self.shop_catg.items():
            if key in self.shop_wifi:  # 剔除Wifi种类小于10的类别（店铺）(经统计发现等同于剔除样本数小于10的店铺）
                examp1 = []  # 保存该shop下的每一条记录
                for val1 in val:
                    examp2 = [0] * 12  # 一条记录的经纬度和top10 WiFi
                    examp2[:2] = [float(val1[3]), float(val1[4])]
                    for i, wifis in enumerate(self.shop_top10_wifi[key]):  # 获取该顾客记录在该shop对应的10个WiFi值，没有信号取值-120
                        if wifis in val1[5]:
                            examp2[i + 2] = val1[5][wifis]
                        else:
                            examp2[i + 2] = -120
                    examp1.append(examp2)
                shop_data[key] = examp1

        sh_info = ShopInfo()
        sh_info.readfile()
        for key2, val2 in shop_data.items():
            mall_id = sh_info.shop_mall[key2]  # sh_info[key2] is the mall_id of this shop
            if mall_id not in self.model_input_data:
                self.model_input_data[mall_id] = {}
                self.model_input_data[mall_id][key2] = val2
            else:
                self.model_input_data[mall_id][key2] = val2


def get_open_time():
    tt = TrainingData()
    tt.readfile()
    f = open(r'C:\Users\Feng\Desktop\CustomerPosition\shop_open_time.csv', 'wb')
    writer = csv.writer(f)
    title = ['shop_id', 'min_behave_time', 'max_behave_time']
    writer.writerow(title)
    for key, value in tt.open_time.items():
        writer.writerow([key] + value)
    f.close()


class TrainingData_onemall(object):  # 只读取这一个mall_3839的数据做实验
    def __init__(self):
        # training data file, total 1048575 rows
        self.file = r'C:\Users\Feng\Desktop\CustomerPosition\first_user_behavior.csv'

        # store the user behavior data
        self.user_behav = []  # store the user behavior in the given list order

        self.mall_catg = {}  # group all records into 97 categories according to mall_id, {mall_id:[[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}],..]}
        self.shop_catg = {}  # group all records into 8423 categories according to shop_id, {shop_id:[[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}],..}
        self.open_time = {}  # store the open time for each shop, [min,max]
        self.mall_wifi = {}  # stroe all the wifis occured in this mall (combine top 10 wifi of each shop)
        self.shop_wifi = {}  # for each shop, get the frequency of all wifis occurred, 8336 shops left, {shop_id:{wifi1:freq,..},..}
        self.shop_top10_wifi = {}  # for each shop, get the top 10 wifi names, {shop_id:[wifi_id1,wifi_id2,...],...}

        self.model_input_data = {}  # get the lon,lat,wifi values,shop_id for each record, group by mall_id, {mall_id:[[lon,lat,wifi1,..,shop_id],..],..}

    def readfile(self):

        sh = ShopInfo()
        sh.readfile()
        behav_time = {}

        user_f = open(self.file, 'rU')
        user_r = csv.reader(user_f)

        for i, row in enumerate(user_r):
            if i > 0 and sh.shop_mall[row[1]] == 'm_7168':  # 只取这一个mall的数据做实验
                del row[0]  # delete user_id, not need
                tm = int(row[1][-5:-3]) * 60 + int(row[1][-2:])
                row.insert(2, tm)

                wifi = row[5].replace('|false', '')
                wifi = wifi.replace('|true', '')
                wifi = wifi.replace(';', ",'")
                wifi = wifi.replace('|', "':")
                wifi = "{'" + wifi + "}"
                wifi_dict = eval(wifi)

                row[5] = wifi_dict  # row=[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}]
                self.user_behav.append(row)

                mall_id = sh.shop_mall[row[0]]
                if mall_id not in self.mall_catg:
                    self.mall_catg[mall_id] = [row]
                else:
                    self.mall_catg[mall_id].append(row)

                shop_id = row[0]
                if shop_id not in self.shop_catg:
                    self.shop_catg[shop_id] = [row]
                else:
                    self.shop_catg[shop_id].append(row)
                if shop_id not in behav_time:
                    behav_time[shop_id] = [row[2]]
                else:
                    behav_time[shop_id].append(row[2])

        user_f.close()

        for key in behav_time:
            self.open_time[key] = [min(behav_time[key]), max(behav_time[key])]

    def shopWifiFreq(self):
        for key, val in self.shop_catg.items():  # 一个shop
            wifi_dict = {}
            for va in val:  # 一条记录
                temp = []  # 一条记录可能多次出现同一个WiFi，只取一个避免重复
                for k in va[5]:
                    if k not in wifi_dict:
                        wifi_dict[k] = 1
                        temp.append(k)
                    else:
                        if k not in temp:
                            wifi_dict[k] += 1

            self.shop_wifi[key] = wifi_dict

            wifi_list = []
            for key1, val1 in wifi_dict.items():
                wifi_list.append([val1, key1])  # 把frequency值放在第一个，对应的WiFi名字放第二，以便下一步直接排序
            wifi_list.sort(reverse=True)  # order by wifi frequency in descending
            self.shop_top10_wifi[key] = [val2[1] for key2, val2 in enumerate(wifi_list) if
                                         key2 < 10]  # 取店铺WiFi出现频率大于0.1的WiFi

    def getInputData(self):  # 获取模型需要的输入数据，经纬度、WiFi的值(该商场所有店铺tip10 Wifi的并集)，以及类别标签shop_id
        sh_info = ShopInfo()
        sh_info.readfile()
        for key0, val0 in self.shop_top10_wifi.items():
            mall_id0 = sh_info.shop_mall[key0]
            if mall_id0 not in self.mall_wifi:
                self.mall_wifi[mall_id0] = set(val0)
            else:
                self.mall_wifi[mall_id0] = self.mall_wifi[mall_id0] | set(val0)  # 取并集
        for k0, v0 in self.mall_wifi.items():
            self.mall_wifi[k0] = list(v0)  # 将集合转换为列表，顺序可控

        for key in self.shop_wifi:  # 剔除Wifi种类小于10的类别（店铺）(经统计发现等同于剔除样本数小于10的店铺）
            examp1 = []  # 保存该shop下的每一条记录
            mall_id1 = sh_info.shop_mall[key]
            for val1 in self.shop_catg[key]:
                examp2 = [0] * (3 + len(self.mall_wifi[mall_id1]))  # 经纬度加该商场WiFi总数加shop_id(label)
                examp2[:2] = [float(val1[3]), float(val1[4])]
                examp2[-1] = key  # 最后一个为shop标签
                for i, wifis in enumerate(self.mall_wifi[mall_id1]):  # 获取该顾客记录在该shop对应的10个WiFi值，没有信号取值-120
                    if wifis in val1[5]:
                        examp2[i + 2] = val1[5][wifis]
                    else:
                        examp2[i + 2] = -120
                examp1.append(examp2)
            if mall_id1 not in self.model_input_data:
                self.model_input_data[mall_id1] = {}
                self.model_input_data[mall_id1] = examp1
            else:
                self.model_input_data[mall_id1].extend(examp1)


def test():
    hd = ShopInfo()
    hd.readfile()
    al = []
    fi = open(r'C:\Users\Feng\Desktop\CustomerPosition\first_user_behavior.csv', 'rU')
    reader = csv.reader(fi)
    i = 0
    for row in reader:

        if i > 0 and hd.shop_mall[row[1]] == 'm_7168':
            al.append(row)
        i += 1
    fi.close()

    f = open(r'C:\Users\Feng\Desktop\CustomerPosition\specific_examples\mall_7168.csv', 'wb')
    writer = csv.writer(f)
    for val in al:
        writer.writerow(val)
    f.close()


'''
training data里存在一些类别（即shop_id），他们的记录数量特别少(有1283类样本数小于10)，
考虑到P(Ci)非常小时，后验概率P(Ci/X)将会非常小，样本分到该类的概率也很小；本来打算将记录数
小于10的类别的training data剔除，考虑到因此会删除一千多个类别，所以还是将WiFi种类少于10的剔除

以下是顾客连接的累计WiFi种类小于10种的店铺，{shop_id: 累计WiFi种类}
{'s_817781': 3,  's_3904425': 6,  's_3409612': 9,  's_2836741': 9,  's_17627': 3,
 's_2404711': 1,  's_725240': 7,  's_2861564': 6,  's_2033967': 6,  's_4003234': 6,
 's_117363': 6,  's_2631847': 5,  's_2790691': 8,  's_445794': 9,
 's_3640945': 5, 's_2882952': 2, 's_3985088': 9, 's_325022': 9, 's_594541': 9,
 's_2651838': 5, 's_721444': 4, 's_956492': 4, 's_3895172': 9, 's_4054936': 6,
 's_765984': 9, 's_1781825': 6, 's_3386217': 8, 's_202786': 5, 's_68944': 9,
 's_956781': 8, 's_3151568': 5, 's_3031981': 2, 's_3441993': 3, 's_519044': 6,
 's_677276': 9, 's_501451': 9, 's_433037': 5, 's_3092302': 9, 's_4039822': 3,
 's_3554967': 7, 's_490813': 6, 's_2713224': 5, 's_3109846': 8, 's_502727': 9,
 's_67056': 9, 's_329687': 9, 's_591716': 8, 's_4029990': 8, 's_2871319': 9,
 's_3368733': 8, 's_2551224': 3, 's_1449551': 7, 's_1509930': 6, 's_1187707': 4,
 's_3963444': 3, 's_614631': 9, 's_632767': 4, 's_431027': 9, 's_4059861': 6,
 's_1882105': 7, 's_573178': 6, 's_57902': 6, 's_3574027': 8, 's_4053160': 9,
 's_277531': 9, 's_2701486': 7, 's_1962458': 8, 's_2609489': 3, 's_768056': 7,
 's_3102407': 9, 's_1355338': 5, 's_849441': 3, 's_1060794': 9, 's_1044992': 1,
 's_3269568': 9, 's_1189511': 4, 's_2766041': 7, 's_760841': 8, 's_4057892': 8,
 's_474193': 8, 's_3363840': 9, 's_2205652': 6, 's_1139407': 5, 's_3880708': 4,
 's_2987052': 8, 's_3732911': 7, 's_3895726': 7}


以下是training data里面出现的记录数量很少的店铺，{shop_id: 记录出现次数},共87个，跟下面对应
{'s_817781': 1, 's_3904425': 3, 's_3409612': 1, 's_2836741': 4, 's_17627': 2,
 's_2404711': 1, 's_725240': 1, 's_2861564': 1, 's_2033967': 1, 's_4003234': 1,
 's_117363': 1, 's_760841': 3, 's_2790691': 1, 's_445794': 1, 's_3640945': 1,
 's_2882952': 1, 's_3985088': 1, 's_325022': 1, 's_594541': 2, 's_2651838': 1,
 's_721444': 1, 's_956492': 1, 's_3895172': 6, 's_4054936': 1, 's_765984': 1,
 's_1781825': 1, 's_3386217': 1, 's_4039822': 5, 's_68944': 1, 's_956781': 1,
 's_3151568': 1, 's_3031981': 1, 's_3441993': 1, 's_519044': 1, 's_677276': 3,
 's_501451': 4, 's_3554967': 1, 's_3092302': 2, 's_202786': 1, 's_433037': 1,
 's_490813': 1, 's_2713224': 1, 's_3109846': 1, 's_502727': 1, 's_67056': 1,
 's_329687': 1, 's_591716': 1, 's_4029990': 1, 's_2871319': 1, 's_3368733': 1,
 's_2551224': 1, 's_1449551': 3, 's_1509930': 1, 's_1187707': 2, 's_3963444': 1,
 's_614631': 1, 's_632767': 1, 's_431027': 2, 's_4059861': 1, 's_1882105': 1,
 's_573178': 1, 's_57902': 1, 's_3574027': 1, 's_4053160': 1, 's_277531': 1,
 's_2701486': 1, 's_2987052': 4, 's_2609489': 1, 's_768056': 1, 's_3102407': 2,
 's_1355338': 1, 's_849441': 1, 's_1060794': 7, 's_1044992': 1, 's_3269568': 2,
 's_1189511': 1, 's_2766041': 1, 's_2631847': 1, 's_4057892': 1, 's_474193': 3,
 's_3363840': 1, 's_2205652': 1, 's_1139407': 1, 's_3880708': 1, 's_1962458': 1,
 's_3732911': 1, 's_3895726': 1}
'''
