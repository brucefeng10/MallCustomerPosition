# coding: utf-8
import time, csv
from sklearn import preprocessing
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


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


class TrainingData3839(object):  # 只读取这一个mall_3839的数据做实验
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
                                         (val2[0] + 0.0) / len(val) >= 0.1]  # 取店铺WiFi出现频率大于0.1的WiFi

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


def main1():
    t0 = time.time()
    trd = TrainingData3839()
    trd.readfile()
    trd.shopWifiFreq()
    trd.getInputData()
    temp = trd.model_input_data['m_7168']
    x = [val[:-1] for val in temp]

    # temp = []  # m_3839的所有样本,539
    # f = open(r"C:\Users\Feng\Desktop\CustomerPosition\m_3839_examples.csv", "rU")
    # reader = csv.reader(f)
    # for rw in reader:
    #     temp.append(rw)
    # f.close()
    # x = [map(float, val[:-1]) for val in temp]

    print
    len(x[0])
    y = [val[-1] for val in temp]
    scaler = preprocessing.StandardScaler().fit(x)
    x = scaler.transform(x)

    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=2)
    mlp = MLPClassifier(solver='lbfgs', alpha=1e-5,
                        hidden_layer_sizes=(731), random_state=1)
    mlp.fit(X_train, y_train)

    prediction = mlp.predict(X_test)

    print("accuracy score: ")
    print(accuracy_score(y_test, prediction))
    print(classification_report(y_test, prediction))
    # print "Score:", adb_clf.score(X_train, y_train)
    t1 = time.time()
    print
    t1 - t0


main1()
