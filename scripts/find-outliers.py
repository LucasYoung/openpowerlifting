#!/usr/bin/env python3
# vim: set ts=8 sts=4 et sw=4 tw=99:
#
# Prints outliers in database
#

import statistics
import numpy as np
from numpy import array
import math
import pandas as pd
import nltk
from nltk.cluster.kmeans import KMeansClusterer
from nltk.cluster import euclidean_distance

# TODO federation not in openpowerlifting.csv

# 0         1      2    3   4       5       6   7          8              9           10       11       12       13         14        15      16         17     18       19          20          21          22           23            24           25     26    27    28
# MeetID,LifterID,Name,Sex,Event,Equipment,Age,Division,BodyweightKg,WeightClassKg,Squat1Kg,Squat2Kg,Squat3Kg,Squat4Kg,BestSquatKg,Bench1Kg,Bench2Kg,Bench3Kg,Bench4Kg,BestBenchKg,Deadlift1Kg,Deadlift2Kg,Deadlift3Kg,Deadlift4Kg,BestDeadliftKg,TotalKg,Place,Wilks,McCulloch

indexes = {}

norm_dict = {}

labels = []

NUM_CLUSTERS = 5
REPEATS = 10
OUTLIER_ZS = 3

def find_max(db):
    ret_dict = {}
    for column in db.columns:
        try:
            ret_dict[column] = (db[column][db[column].idxmax()])
        except:
            print("invalid type")

    return ret_dict

def serializeStr(astr):
    if not isinstance(astr, str):
        return 0

    total = 0
    multiplier = 1
    for c in astr:
        total += ord(c) * multiplier
        multiplier *= 256

    return total % 9223372036854775807

def get_data(path):
    db = pd.read_csv(path)

    global norm_dict
    norm_dict = find_max(db)

    db.drop("Deadlift1Kg", 1, inplace=True)
    db.drop("Deadlift2Kg", 1, inplace=True)
    db.drop("Deadlift3Kg", 1, inplace=True)
    db.drop("Deadlift4Kg", 1, inplace=True)
    db.drop("McCulloch", 1, inplace=True)
    db.drop("Place", 1, inplace=True)
    db.drop("LifterID", 1, inplace=True)
    db.drop("Squat1Kg", 1, inplace=True)
    db.drop("Squat2Kg", 1, inplace=True)
    db.drop("Squat3Kg", 1, inplace=True)
    db.drop("Squat4Kg", 1, inplace=True)
    db.drop("Bench1Kg", 1, inplace=True)
    db.drop("Bench2Kg", 1, inplace=True)
    db.drop("Bench3Kg", 1, inplace=True)
    db.drop("Bench4Kg", 1, inplace=True)
    db.drop("WeightClassKg", 1, inplace=True)

    global labels
    labels = db.columns

    for i in range(len(db.columns)):
        indexes[db.columns[i]] = i
    print(indexes)

    # Serialize all strings in database
    for j in range(len(db)):
        #db.set_value(j, "Month", serializeStr(db["Month"][j]))
        db.set_value(j, "Name", serializeStr(db["Name"][i]))
        db.set_value(j, "Sex", serializeStr(db["Sex"][i]))
        db.set_value(j, "Event", serializeStr(db["Event"][i]))
        db.set_value(j, "Equipment", serializeStr(db["Equipment"][i]))
        db.set_value(j, "Division", serializeStr(db["Division"][i]))

    index_remove = []
    for col in (range(len(db))):
        for row in range(len(db.columns)):
            val = (db[db.columns[row]][col])
            if not isinstance(val, str):
                if(np.isnan(val)):
                    index_remove.append(col)
                    break
    indexes_to_keep = set(range(db.shape[0])) - set(index_remove)
    db = db.take(list(indexes_to_keep))

    db = db.sample(frac=1)

    asarr = [array(f) for f in db.as_matrix()]
    return asarr

def svariate_outlier(cluster):
    global labels
    db = pd.DataFrame(data=cluster, columns=labels)
    means = {}
    stdevs = {}

    for key in indexes.keys():
        means[key] = statistics.mean(list(f for f in db[key]))
        stdevs[key] = statistics.pstdev(list(f for f in db[key]))

    print(means)
        #total = 0
        #for j in cluster:
        #    total += cluster[j][value]
        #means.append(total / len(cluster))

    for key in indexes.keys():
        for j in range(len(db)):
            zscore = abs((db[key][j] - means[key]) / stdevs[key])
            if(zscore > OUTLIER_ZS):
                print(db.iloc[[j]])


def euclid_component(a, b, normalization):
    try:
        if(np.isnan(a)):
            return 0
        if(np.isnan(b)):
            return 0
        return (float(a) - float(b)) ** 2 / (normalization ** 2)
    except:
        return 0

# u and v are vectors
def distance_func(u, v):

    if u[indexes["Sex"]] == v[indexes["Sex"]]:
        sex = 0
    else:
        sex = 1

    if u[indexes["Equipment"]] == v[indexes["Equipment"]]:
        equip = 0
    else:
        equip = 1

    if u[indexes["Division"]] == v[indexes["Division"]]:
        division = 0
    else:
        division = 1

    distance = math.sqrt(
        # categorical variables
        sex + equip + division +
        # continuous variables
        euclid_component(u[indexes["Age"]], v[indexes["Age"]], norm_dict["Age"]) +
        euclid_component(u[indexes["BodyweightKg"]], v[indexes["BodyweightKg"]], norm_dict["BodyweightKg"]) +
        euclid_component(u[indexes["BestSquatKg"]], v[indexes["BestSquatKg"]], norm_dict["BestSquatKg"]) +
        euclid_component(u[indexes["BestBenchKg"]], v[indexes["BestBenchKg"]], norm_dict["BestBenchKg"]) +
        euclid_component(u[indexes["BestDeadliftKg"]], v[indexes["BestDeadliftKg"]], norm_dict["BestDeadliftKg"])
    )

    print(distance)
    return distance

if __name__ == '__main__':
    import sys

    kclusterer = KMeansClusterer(NUM_CLUSTERS, distance=euclidean_distance, repeats=REPEATS, avoid_empty_clusters=True)
    data = get_data(sys.argv[1])

    print(data)

    assigned_clusters = kclusterer.cluster(data, assign_clusters=True)

    clusters = []
    for i in range(NUM_CLUSTERS):
        clusters.append([])

    for i in range(len(assigned_clusters)):
        clusters[assigned_clusters[i]].append(data[i])

    #print(clusters[0])
    #print(clusters[1])

    for cluster in clusters:
        svariate_outlier(cluster)