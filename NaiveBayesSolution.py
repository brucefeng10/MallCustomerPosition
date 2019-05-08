# **** coding: utf-8 *****

import csv
import math
import time
import numpy as np



class ShopInfo(object):
    def __init__(self):
        # shop information file, 8477 shops in total
        self.file=r'C:\Users\Feng\Desktop\CustomerPosition\first_shop_info.csv'

        # store the location of each shop
        self.shop_location = {}  # key is the shop_id, and value is a list of longitude and latitude(float value)
        self.shop_mall = {}  # key is the shop_id, and value is the corresponding mall_id

    def readfile(self):
        shop_f = open(self.file, 'rU')
        shop_r = csv.reader(shop_f)
        for i,row in enumerate(shop_r):
            if i>0:
                self.shop_location[row[0]]=map(eval,row[2:4])
                self.shop_mall[row[0]]=row[-1]
        shop_f.close()

        # return self.shop_location, self.shop_mall

class TrainingData(object):
    def __init__(self):
        # training data file, total 1048575 rows
        self.file = r'C:\Users\Feng\Desktop\CustomerPosition\first_user_behavior.csv'

        # store the user behavior data
        self.user_behav = [] # store the user behavior in the given list order

        self.mall_catg = {}  # group all records into 97 categories according to mall_id, {mall_id:[[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}],..]}
        self.shop_catg = {}  # group all records into 8423 categories according to shop_id, {shop_id:[[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}],..}
        self.open_time = {}  # store the open time for each shop, [min,max]
        self.shop_wifi = {}  # for each shop, get the frequency of all wifis occurred, 8336 shops left, {shop_id:{wifi1:freq,..},..}
        self.shop_top10_wifi = {}  # for each shop, get the top 10 wifi names, {shop_id:[wifi_id1,wifi_id2,...],...}

        self.model_input_data = {}  # get the lon,lat,wifi values,shop_id for each record, group by mall_id and shop_id, {mall_id:{shop_id:[[lon,lat,wifi1,..,wifi10],..],..},..}


    def readfile(self):

        sh=ShopInfo()
        sh.readfile()
        behav_time={}

        user_f = open(self.file, 'rU')
        user_r = csv.reader(user_f)

        for i, row in enumerate(user_r):
            if i > 0:
                del row[0]  # delete user_id, not need
                tm=int(row[1][-5:-3])*60+int(row[1][-2:])
                row.insert(2,tm)

                wifi=row[5].replace('|false','')
                wifi=wifi.replace('|true','')
                wifi=wifi.replace(';', ",'")
                wifi=wifi.replace('|',"':")
                wifi="{'"+wifi+"}"
                wifi_dict=eval(wifi)

                row[5]=wifi_dict  # row=[shop_id,time_stamp,int_time,longitude,latitude,{wifi1:value,...}]
                self.user_behav.append(row)

                mall_id=sh.shop_mall[row[0]]
                if mall_id not in self.mall_catg:
                    self.mall_catg[mall_id]=[row]
                else:
                    self.mall_catg[mall_id].append(row)

                shop_id=row[0]
                if shop_id not in self.shop_catg:
                    self.shop_catg[shop_id]=[row]
                else:
                    self.shop_catg[shop_id].append(row)
                if shop_id not in behav_time:
                    behav_time[shop_id]=[row[2]]
                else:
                    behav_time[shop_id].append(row[2])

        user_f.close()

        for key in behav_time:
            self.open_time[key] = [min(behav_time[key]),max(behav_time[key])]


    def shopWifiFreq(self):
        for key,val in self.shop_catg.items():  # 一个shop
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
                for key1,val1 in wifi_dict.items():
                    wifi_list.append([val1,key1])  # 把frequency值放在第一个，对应的WiFi名字放第二，以便下一步直接排序
                wifi_list.sort(reverse=True)  # order by wifi frequency in descending
                self.shop_top10_wifi[key]=[val2[1] for key2,val2 in enumerate(wifi_list) if key2<10]  # 取top10 WiFi的id


    def getInputData(self):  # 获取模型需要的输入数据，经纬度、top 10 WiFi的值，以及类别标签shop_id
        shop_data={}  # 保存每一个shop下的所有记录的经纬度和top10 WiFi

        for key,val in self.shop_catg.items():
            if key in self.shop_wifi:  # 剔除Wifi种类小于10的类别（店铺）(经统计发现等同于剔除样本数小于10的店铺）
                examp1=[]  # 保存该shop下的每一条记录
                for val1 in val:
                    examp2=[0]*12  # 一条记录的经纬度和top10 WiFi
                    examp2[:2]=[float(val1[3]),float(val1[4])]
                    for i,wifis in enumerate(self.shop_top10_wifi[key]):  # 获取该顾客记录在该shop对应的10个WiFi值，没有信号取值-120
                        if wifis in val1[5]:
                            examp2[i+2]=val1[5][wifis]
                        else:
                            examp2[i+2]=-120
                    examp1.append(examp2)
                shop_data[key]=examp1

        sh_info=ShopInfo()
        sh_info.readfile()
        for key2,val2 in shop_data.items():
            mall_id=sh_info.shop_mall[key2]   #sh_info[key2] is the mall_id of this shop
            if mall_id not in self.model_input_data:
                self.model_input_data[mall_id]={}
                self.model_input_data[mall_id][key2]=val2
            else:
                self.model_input_data[mall_id][key2] = val2

class TestingData(object):
    def __init__(self):
        # AB testing data file, total 483931 rows
        self.file=r'C:\Users\Feng\Desktop\CustomerPosition\first_evaluation_public.csv'

        # store the testing examples
        self.test_examples = []  # [[row_id,mall_id,lon,lat,{wifi1:value1,wifi2:value2,...}],...]

    def readfile(self):
        user_f = open(self.file, 'rU')
        user_r = csv.reader(user_f)
        for i,row in enumerate(user_r):
            if i>0:
                examp1 = [0] * 5
                examp1[0]=row[0]
                examp1[1]=row[2]
                examp1[2:4]=map(eval,row[4:6])

                wifi_info=row[6]
                wifi_info=wifi_info.replace('|false','')
                wifi_info=wifi_info.replace('|true','')
                wifi_info=wifi_info.replace(';', ",'")
                wifi_info=wifi_info.replace('|',"':")
                wifi_info="{'" + wifi_info + "}"
                examp1[4] = eval(wifi_info)

                self.test_examples.append(examp1)

        user_f.close()




def muSigma(x):
    '''x is a list of example values, return the mean value and standard variation of x in a numpy array,'''
    x1=np.array(x)
    mu=np.mean(x1,0)  # get the mean value of each variable xi
    sigma=np.std(x1,0)  # get standard deviation of each variable xi
    if sigma[0]==0:
        sigma[0]=0.0001
    if sigma[1]==0:
        sigma[1]=0.000001
    for i,j in enumerate(sigma):  # in case wifi sigma equals 0 for 357 examples
        if i>1 and j==0:

            sigma[i]=10

    return mu,sigma

def getProbability(x,pc,mu,sigma):
    '''x is an input example data to be predicted, [lon,lat,wifi1,wifi2,...,wifi10]
    pc为该类别先验概率（该类频率），x,mu,sigma均为数组，返回log概率和（概率积）'''

    p=1.0/(((2*np.pi)**0.5)*sigma)*np.exp(-0.5*(x-mu)**2/(sigma**2))

    prob=pc
    log_prob=0
    for val in p:
        if val<0.00000001:  # in case p is too small(lon,lat), log(p) will cause error
            val=0.00000001
        prob*=val
        log_prob+=np.log(val)
    return log_prob



class TrainingModel(object):
    def __init__(self):
        self.parameters={}  # store the parameters of NB model, {mall_id:{shop_id:[pc,mu,sigma]},..} mu and sigma are numpy arrays

    def getParameters(self,model_input_data,mall_catg):
        td=TrainingData()
        td.readfile()
        for key,val in model_input_data.items():  # each mall
            shop_para={}
            for key1,val1 in val.items():  # each shop
                pc=(len(val1)+0.0)/len(mall_catg[key])  # calculate the frequency of a shop in its mall
                mu,sigma=muSigma(np.array(val1))
                shop_para[key1]=[pc,mu,sigma]  # pc is a float value, mu and sigma are numpy arrays
            self.parameters[key]=shop_para



def main():
    t0=time.time()

    trd=TrainingData()
    trd.readfile()
    trd.shopWifiFreq()
    trd.getInputData()

    tsd=TestingData()
    tsd.readfile()

    t1 = time.time()
    print t1 - t0

    trm=TrainingModel()
    trm.getParameters(trd.model_input_data,trd.mall_catg)

    t2=time.time()
    print t2-t1

    result=[]
    prob_list={}  # keep the first two possible shop_id with the top2 highest probability, {row_id:[[log_prob1,shop_id1],[log_prob2,shop_id2]],..}

    cnt=0
    for instance in tsd.test_examples:
        x_input=[0]*12
        x_input[0:2]=instance[2:4]
        pi = []  # keep the class(shop_id) name and probability
        for key,val in trm.parameters[instance[1]].items():  # key is shop_id and val is parameters
            for ind,wifis in enumerate(trd.shop_top10_wifi[key]):
                if wifis in instance[4]:
                    x_input[ind+2]=instance[4][wifis]
                else:
                    x_input[ind + 2] = -120
            if 0 in val[2]:
                print key,val[2]
            log_prob=getProbability(np.array(x_input),val[0],val[1],val[2])
            pi.append([log_prob,key])
        pi.sort(reverse=True)
        result.append([instance[0],pi[0][1]])  # [row_id,predict_shop_id]
        prob_list[instance[0]]=pi[:2]

        cnt+=1
        print cnt


    f = open(r"C:\Users\Feng\Desktop\CustomerPosition\results\NBresult20171112_2.csv",
             "wb")  # 'wb' instead of 'w' can remove blank rows
    writer = csv.writer(f)
    title = ['row_id', 'shop_id']
    writer.writerow(title)
    for val in result:
        writer.writerow(val)
    f.close()

    t3=time.time()
    print t3-t2


main()



def test():
    f = open(r"C:\Users\Feng\Desktop\CustomerPosition\results\NB20171112.csv",
             "wb")  # 'wb' instead of 'w' can remove blank rows
    writer = csv.writer(f)
    title = ['row_id', 'shop_id']
    writer.writerow(title)
    for key, val in aa.model_input_data.items():
        for key1, val1 in val.items():
            for val2 in val1:
                writer.writerow([key] + [key1] + val2)
    f.close()
