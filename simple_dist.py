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
        self.shop_location = []  # safe shop longitude and latitude in the initial order
        self.shop_id = []  # save shop_id in the initial order

    def readfile(self):
        shop_f = open(self.file, 'rU')
        shop_r = csv.reader(shop_f)
        for i, row in enumerate(shop_r):
            if i > 0:
                self.shop_location.append(map(eval, row[2:4]))
                self.shop_id.append(row[0])
        shop_f.close()

        return self.shop_location, self.shop_id


class TestingData(object):
    def __init__(self):
        # AB testing data file, total 483931 rows in the AB testing dataset
        self.file = r'C:\Users\Feng\Desktop\CustomerPosition\first_evaluation_public.csv'

        # store the location of each testing user/row
        self.user_location = []  # save user longitude and latitude in the initial order
        self.row_id = []  # save row_id in the initial order

    def readfile(self):
        user_f = open(self.file, 'rU')
        user_r = csv.reader(user_f)
        for i, row in enumerate(user_r):
            if i > 0:
                self.user_location.append(map(eval, row[4:6]))
                self.row_id.append(row[0])
            if i > 10000:
                break
        user_f.close()

        return self.user_location, self.row_id


def getDistance(p1, p2):
    '''This fuction is to calculate the earth distance between two set of points given their longitudes
    and latitudes. p1=[[lon1,lat1],[lon2,lat2]]), p2=[[lon1,lat1],[lon2,lat2]] '''

    m = len(p1)
    n = len(p2)
    n_cols = np.mat(np.ones([1, n]))
    m_rows = np.mat(np.ones([m, 1]))
    r = 6371.004  # radius of earth
    pp1 = np.mat(p1)
    pp2 = np.mat(p2)

    ppp2 = pp2.transpose()
    x = math.pi * pp1 / 180.0  # transfer angle to radian
    y = math.pi * ppp2 / 180.0
    dist = r * np.arccos(
        np.multiply(np.cos(x[:, 1]) * np.cos(y[1, :]), np.cos(x[:, 0] * n_cols - m_rows * y[0, :])) + np.sin(
            x[:, 1]) * np.sin(y[1, :]))

    return dist


def simple_dist_method():
    '''This function only use the distance between users and shops to predict.'''
    result = [['row_id', 'shop_id']]
    shop = ShopInfo()
    user = TestingData()
    sh_loc, sh_id = shop.readfile()
    us_loc, us_id = user.readfile()

    cnt = 0
    print
    cnt

    dist_matr = getDistance(us_loc, sh_loc)
    print
    dist_matr[1, 10]

    # f=open(r'C:\Users\Feng\Desktop\CustomerPosition\results\simple_dist_result.csv','wb')
    # writer=csv.writer(f)
    # for rows in result:
    #     writer.writerow(rows)
    # f.close()


simple_dist_method()

# a=[[121.963045,31.653327],[116.089669,39.208731],[114.409935,30.978022]]
# b=[[116.089669,39.208731],[123.798378,42.367046]]
#
# c=getDistance(a,b)
# print c
