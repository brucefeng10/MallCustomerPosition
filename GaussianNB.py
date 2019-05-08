# *** coding=utf-8 ***

import csv
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


class GetData(object):
    def __init__(self):
        self.trainfile = r'C:\Users\Feng\Desktop\CustomerPosition\first_user_behavior.csv'
        self.testfile=r'C:\Users\Feng\Desktop\CustomerPosition\first_evaluation_public.csv'

        self.predict_location = {}  # key is the mall_id, and value is a list of lon,lat,shop_id
        self.train_location = {}  # key is the mall_id, and value is a list of longitude,latitude(float value) and row_id

    def readtrain(self):
        sh=ShopInfo()
        sh.readfile()

        user_f = open(self.trainfile, 'rU')
        user_r = csv.reader(user_f)

        for i,row in enumerate(user_r):
            if i>0:
                mall_id=sh.shop_mall[row[1]]
                if mall_id not in self.train_location:
                    self.train_location[mall_id]=[map(eval,row[3:5])+[row[1]]]
                else:
                    self.train_location[mall_id].append(map(eval,row[3:5])+[row[1]])

        user_f.close()
        print len(self.train_location)


    def readtest(self):
        user_f = open(self.testfile, 'rU')
        user_r = csv.reader(user_f)
        for i,row in enumerate(user_r):
            if i>0:
                mall_id=row[2]
                if mall_id not in self.predict_location:
                    self.predict_location[mall_id]=[map(eval,row[4:6])+[row[0]]]
                else:
                    self.predict_location[mall_id].append(map(eval,row[4:6])+[row[0]])
        user_f.close()
        print len(self.predict_location)



def GNB(x,y,px,row_id):

    X=np.array(x)
    Y=y

    from sklearn.naive_bayes import GaussianNB
    clf = GaussianNB()
    # 拟合数据
    clf.fit(X, Y)
    PX = np.array(px)

    result = clf.predict(PX)

    result_list= list(result)
    predict=[]
    for i in range(len(px)):
        predict.append([row_id[i],result_list[i]])

    return predict


def main():
    data = GetData()
    data.readtrain()
    data.readtest()
    total_result=[]
    cnt=0
    for key in data.predict_location:

        x=[val[:2] for val in data.train_location[key]]
        y=[val[2] for val in data.train_location[key]]

        px=[val[:2] for val in data.predict_location[key]]
        row_id=[val[2] for val in data.predict_location[key]]


        result=GNB(x,y,px,row_id)
        total_result+=result

        cnt+=1
        print cnt


    f = open(r"C:\Users\Feng\Desktop\CustomerPosition\results\simple_dist_result1110.csv",
             "wb")  # 'wb' instead of 'w' can remove blank rows
    writer = csv.writer(f)
    title = ['row_id', 'shop_id']
    writer.writerow(title)
    for val in total_result:
        writer.writerow(val)
    f.close()






















def GNBExample():
    import numpy as np
    X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
    Y = np.array([1, 1, 1, 2, 2, 2])
    from sklearn.naive_bayes import GaussianNB
    clf = GaussianNB()
    # 拟合数据
    clf.fit(X, Y)
    print "==Predict result by predict=="
    print(clf.predict([[-0.8, -2]]))
    print "==Predict result by predict_proba=="
    print(clf.predict_proba([[-0.8, -1]]))
    print "==Predict result by predict_log_proba=="
    print(clf.predict_log_proba([[-0.8, -1]]))


