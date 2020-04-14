# coding: utf-8
import requests
from urllib.request import urlopen
# from urllib import urlopen # on the rpi
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from time import gmtime, strftime
from datetime import timedelta
import datetime
import smtplib
from email.mime.text import MIMEText
import os

def creatURL(idN, t):
    string = "http://ec2-54-175-179-28.compute-1.amazonaws.com/get_thinktron_data.php?device_id={}&year_month={}".format(idN,t)
    return string    

def query_data(arg1):
    r = requests.get(arg1) # URL path
    soup = BeautifulSoup(r.text,'lxml')
    a = list(soup.find_all('p'))

    # Split the list through the regular expression
    d = re.split('\s+|,|<br/>|<p>|</p>|sec',str(a))

    # Remove the '' element from the list
    d = list(filter(lambda zz: zz != '', d)) 

    # Remove the '=' element from the list
    d = list(filter(lambda zz: zz != '=', d))

    # Remove the '[' & ']' element from the list
    try:
        d.remove(']')
        d.remove('[')
    except:
        pass
    
    return d


def is_number(num):
    pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
    result = pattern.match(num)
    if result:
        return True
    else:
        return False
    

def data_Preprocess(inputqD):
    colName=['id', 'time', 'weather', 'air', 'acceleration', 'cleavage', 'incline', 'field1', 'field2', 'field3']
    df   = pd.DataFrame(columns=colName)
    _df  = pd.DataFrame(columns=colName)
    _lst = ""

    # Data preprocessing
    for ii in range(0,len(inputqD)-2):    
        if (not is_number(inputqD[ii])) & (not is_number(inputqD[ii+1])):        
            col = inputqD[ii]
            if col == "reboot":
                _df['field1'] = "reboot"
            else:
                _df[col] = None

        elif (not is_number(inputqD[ii])):
            col = inputqD[ii]
            add = 1
            while is_number(inputqD[ii + add]):
                if not (inputqD[ii + add + 1] in colName):
                    _lst += str(inputqD[ii + add]) + ","
                else:
                    _lst += str(inputqD[ii + add])                
                add += 1
            _df[col] = [_lst]        
        _lst = ""

        if (col == colName[-1]):
            col = ""
            df = df.append(_df, ignore_index=True)
            
    dates = df.time        
    df.index = pd.to_datetime(dates.astype(str), format='%Y%m%d%H%M%S')
    df.index.name = 'time'
    del df['time']
     
    return df
locationList = ["NewTaipei", "Taipei"]
# locationList = ["Taipei"]
# locationList = ["Test"]

queryFid = "{}_outlierList.txt".format(strftime("%Y%m%d%H%M%S"))

fidFlag = 0

for location in locationList:
    if (location.lower() == "newtaipei"): # List only for CF01
        idNumDict  = [{'name':'馥記山莊','id':'2015'}, # 0
                      {'name':'秀岡第一','id':'3015'}, # 1
                      {'name':'老爺山莊','id':'2011'}, # 2
                      {'name':'怡園社區','id':'3014'}, # 4
                      {'name':'台北小城','id':'3001'}, # 5
                      {'name':'秀岡陽光','id':'3029'}, # 6
                      {'name':'薇多綠雅','id':'3028'}, # 7
                      {'name':'達觀鎮B6','id':'3022'}, # 8
                      {'name':'花園點二','id':'2005'}, # 9 
                      {'name':'達觀鎮A1','id':'3019'},
                      {'name':'圓富華城','id':'3021'},              
                      {'name':'淺水灣莊','id':'3023'},
                      {'name':'詩畫大樓','id':'3016'},
                      {'name':'伯爵晶鑽','id':'3025'},
                      {'name':'花園點一','id':'2009'},
                      {'name':'勘農別墅','id':'2010'},
                      {'name':'國家別墅','id':'3017'},
                      {'name':'台北山城','id':'3024'},
                      {'name':'歡喜居易','id':'3013'},
                      {'name':'伯爵一期','id':'3020'},
                      {'name':'迎旭山莊','id':'3018'},
                      {'name':'水蓮山莊','id':'2022'},
                      {'name':'新雪梨  ','id':'3030'},                     
                      {'name':'伯爵幼兒','id':'3032'},
                      {'name':'仁愛特區','id':'3035'},
                      {'name':'詩畫管理','id':'3036'}]
        DBName = "New Taipei"
    elif (location.lower() == "taipei"): # List only for CF01
        idNumDict  = [{'name':'政大自強','id':'2007'},
                      {'name':'政大山頂','id':'2001'},
                      {'name':'中山北七','id':'2008'},
                      {'name':'公訓新牆','id':'2003'},
                      {'name':'公訓舊牆','id':'2002'},
                      {'name':'松德院北','id':'2021'},
                      {'name':'松德院南','id':'2020'},              
                      {'name':'永春高中','id':'2023'},
                      {'name':'世界山莊','id':'3031'},
                      {'name':'世說新語','id':'3037'},
                      {'name':'夏木漱石','id':'3034'},
                      {'name':'玫瑰城社','id':'3033'}]
        DBName = "Taipei"
    elif (location.lower() == "test"):
        idNumDict  = [{'name':'松德院北','id':'6001'},
                      {'name':'松德院北','id':'8001'}]
        DBName = "Taipei"
        
    else:
        print("No such name.")
    
    for ii in range(0, len(idNumDict)): 
        now    = strftime("%Y%m%d")
        # now    = "20200404"
        URLstr = creatURL(str(idNumDict[ii]["id"]), now) # Format in (id_Num, yyyymm)
        outlierFlag = False

        try:
            qD = query_data(URLstr)  
            arrDf = data_Preprocess(qD)
            arrDf = arrDf.drop(arrDf.index[arrDf.field1 == "reboot"])

            weatherDF = arrDf.weather.str.split(",", expand=True)
            plotDF = arrDf.incline.str.split(",", expand=True)    

            plotDF["T"] = weatherDF[1]
            plotDF["P"] = weatherDF[2]
            plotDF["H"] = weatherDF[3]
            plotDF["R"] = weatherDF[4]

            for col in plotDF.columns:  # Iterate over chosen columns
                plotDF[col] = pd.to_numeric(plotDF[col])

            plotDF['INC_SUM'] = plotDF.iloc[:, 0:3].sum(axis=1)

            del plotDF[0]
            del plotDF[1]
            del plotDF[2]

            avgList = list(plotDF.mean(axis = 0))
            avgList =  [round(ii, 3) for ii in avgList] # Format in temperature, pressure, humidity, rainfall, incline

            if avgList[0] > 80 or avgList[1] > 1200 or avgList[2] > 101 or avgList[4] == 0.0:
                outlierFlag = True
                
            if (fidFlag == 0):
                with open(queryFid, "a") as file:
                    file.write("---------------Device outlier---------------")                    
                    file.write("\n")
                    file.write("Query time: {}".format(strftime("%Y/%m/%d %H:%M")))
                    file.write("\n")
                    file.write("\n")
                    fidFlag = 1   

            if outlierFlag:                
                with open(queryFid, "a") as file:
                    writing = "Outlier occurred. ID: {} {}".format(idNumDict[ii]["id"], idNumDict[ii]["name"])
                    print(writing)
                    file.write(writing)
                    file.write("\n")
                    
                    writing = "Temperature: {}, Pressure: {}, Humidity: {}, Rainfall: {}, Avg Incline: {}".format(
                               avgList[0], avgList[1], avgList[2], avgList[3], avgList[4])
                    print(writing)
                    file.write(writing)
                    file.write("\n")
                    
                    writing = "-----------------------"
                    file.write(writing)
                    file.write("\n")
                    
                outlierFlag = False
            else:                
                with open(queryFid, "a") as file:
                    writing = "ID: {} {} is good.".format(idNumDict[ii]["id"], idNumDict[ii]["name"])
                    print(writing)
#                     file.write(writing)
#                     file.write("\n")
                                                          
#                     writing = "-----------------------"
#                     file.write(writing)
#                     file.write("\n")

        except:
            with open(queryFid, "a") as file:
                writing = "Outlier occurred. ID: {} {}".format(idNumDict[ii]["id"], idNumDict[ii]["name"])
                print(writing)
#                 file.write(writing)
#                 file.write("\n")
                
                writing = "Today no data received."
                print(writing)
#                 file.write(writing)
#                 file.write("\n")

#                 writing = "-----------------------"
#                 file.write(writing)
#                 file.write("\n")
smtpssl=smtplib.SMTP_SSL("smtp.gmail.com", 465)
smtpssl.ehlo()
smtpssl.login("n86024042@gmail.com", "ibovbvqwpobuofqb")

msg = ""
   
  
with open(queryFid,'r') as file:
    msg += file.read()             
        
mime = MIMEText(msg, "plain", "utf-8")
mime["Subject"] = "Icebergtek Device outlier (only for CF01)\n"
msgEmail        = mime.as_string()  

to_addr  = ["ian@icebergtek.com",
            "odie@icebergtek.com",
            "white@icebergtek.com",
            "jim@icebergtek.com",
            "meichi@thinktronltd.com",
            "james.wang@icebergtek.com"]

to_addr  = ["ian@icebergtek.com"]
          

status = smtpssl.sendmail("n86024042@gmail.com", 
                          to_addr, 
                          msgEmail)

if status == {}:
    print("Sending e-mail is done.")
    smtpssl.quit()
    
    try:
        os.remove("/home/pi/query_heartbeat/"+queryFid)
        # os.remove("/home/pi/query_heartbeat/"+saveFid[1])

    except OSError as e:
        print(e)
    else:
        print("The file is deleted successfully")

else:
    print("Failed to transmit.")
    smtpssl.quit()