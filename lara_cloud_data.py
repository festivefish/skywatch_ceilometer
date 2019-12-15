# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 20:29:05 2019

@author: Matt Jonas
"""

import matplotlib.pyplot as plt
import numpy as np
import urllib
from matplotlib.lines import Line2D
import datetime
from matplotlib.pyplot import cm
import calendar
import h5py
import os.path
from sys import exit as ext


    
class cloud_height:
    
    def __init__(self, date, dataset,h5 = None):   
        if h5 is None: # If "h5" keyword was not set, then we actually need to read the file from the web, rather than restoring it from the hard drive
            url = 'https://skywatch.colorado.edu/data/'
            # get julian day (requested date)
            y0=int(date[0:4]); m0=int(date[5:7]); d0= int(date[8:10])       
            jul    = [] # initialize julian day
            loc    = [] # initialize local times
            dat1    = [] # cloud base 1 [m]
            dat2    = [] # cloud base 2 [m]
            dat3    = [] # cloud base 3 [m]
            #get url based on selected dataset and date
            url=url+dataset+date[2:]+'.dat'
            print('Reading: ',url)
            hh0=0.          # incremented by 24 each time we pass midnight
            loc0previous=0. # retains current time; if time switches back below that, will increment "hh0"
            jday = (datetime.datetime(y0,m0,d0)-datetime.datetime(y0,1,1)).total_seconds()/86400.0 + 1.0
            
            try:
                lines  = urllib.request.urlopen(url).readlines()
                for line in lines[5:]: # go through all lines, ignoring first three (header)
                    entries = line.decode("utf-8").split("\t")
                    columns = []       # will contain columns
                    for entry in entries:
                        if len(entry) > 1: columns.append(entry)
                    hhmmX = columns[0] # assigns time, filling in leading '0'
                    hh    = float(hhmmX[0:2])
                    self.doy = jday
                    mm    = float(hhmmX[3:5])
                    ss    = float(hhmmX[6:8])
                    loc0  = hh+mm/60.+ss/3600.+hh0
                    if loc0<loc0previous:
                        hh0=hh0+24.
                        loc0=loc0+hh0
                    loc0previous=loc0
                    loc.append(loc0)
                    jul.append(jday+loc0/24.) 
                    dat1.append(float(columns[1]))
                    dat2.append(float(columns[2]))
                    dat3.append(float(columns[3]))
            except:
                print("website not found ",date)
                pass
            self.jul = np.array(jul)
            self.loc = np.array(loc)
            self.h1 = np.array(dat1)
            self.h2 = np.array(dat2)
            self.h3 = np.array(dat3)
            self.date = date
            self.doy  = int(jday)
            self.year = date[0:4]
        else:
           h5f = h5py.File(h5, "r")
           self.jul = h5f['jul'][...]
           self.loc = h5f['loc'][...]
           self.h1  = h5f['h1'][...]
           self.h2  = h5f['h2'][...]
           self.h3  = h5f['h3'][...]
           self.date= str(h5f['date'][...])
           self.doy = int(h5f['doy'][...])
           self.year= str(h5f['year'][...])
           try: # If statistics exist, restore them, if not set them to zero
               self.cf=float(h5f['cf'][...])
               self.min=float(h5f['min'][...])
               self.max=float(h5f['max'][...])
               self.mean=float(h5f['mean'][...])
           except:
               self.cf=0
               self.min=0
               self.max=0
               self.mean=0
           h5f.close()           

    def plot(self):
        plt.plot(self.loc,self.h1,'k.')
        plt.xlabel('Local Time [h]')
        plt.ylabel('Cloud Base Height [m]')
        plt.title(self.date+' Cloud Fraction '+str(round(self.cf,1))+'%')

        
    def stats(self): # of lowest cloud layer, calculate min, max, mean of day & cloud fraction
        tot=len(self.h1) # total number of data points
        flt=np.where(self.h1>0)
        cld=len(flt[0])  # number of cloudy data points
        if len(flt[0]>0):
            mn =np.min(self.h1[flt])
            mx =np.max(self.h1[flt])
            mm =np.mean(self.h1[flt])
            self.min=mn
            self.max=mx
            self.mean=mm            
        #filter out nonexistant data sets    
        if tot != 0:
            self.cf = float(cld)/float(tot)*100.
        else:
            self.cf = 0.
    
    def save(self):
        file = './'+self.year+'_'+str(int(self.doy)).zfill(3)+'.h5'
        print('Saving data to: '+file)
        h5 = h5py.File(file, "w")
        h5['jul'] = self.jul
        h5['loc'] = self.loc
        h5['h1']  = self.h1
        h5['h2']  = self.h2
        h5['h3']  = self.h3
        h5['date']= self.date
        h5['doy'] = self.doy
        h5['year']= self.year
        if hasattr(self,'mean'):
            h5['mean']= self.mean
            h5['min'] = self.min
            h5['max'] = self.max
            h5['cf']  = self.cf
        h5.close()
        
def jday2yyyymmdd(y,jd):
    month = 1
    while jd - calendar.monthrange(y,month)[1] > 0 and month <= 12:
        jd = jd - calendar.monthrange(y,month)[1]
        month = month + 1
    return(y,month,jd)

if __name__ == '__main__':

    # Test one day
    if False:
        doy = 345
        y,m,d = jday2yyyymmdd(2019,doy)
        date  = str(y).zfill(2)+'_'+str(m).zfill(2)+'_'+str(d).zfill(2)    
        ch=cloud_height(date,'ceil_')
        ch.stats()   
        ch.plot()   

    # Read range of dates in a year, do some simple statistics, and write everything to individual h5 files for  a day
    if True:
        year  = 2016
        m0,d0 = 1,1    # start (m,d)
        m1,d1 = 12,31  # end (m,d)
        j0    = int((datetime.datetime(year,m0,d0)-datetime.datetime(year,1,1)).total_seconds()/86400.0 + 1.0)
        j1    = int((datetime.datetime(year,m1,d1)-datetime.datetime(year,1,1)).total_seconds()/86400.0 + 1.0)
        
        doy_list = []
        cf_list  = []
        for doy in range(j0,j1+1):
            doy_list.append(doy) # keep track of days
            y,m,d = jday2yyyymmdd(year,doy)
            date  = str(y).zfill(2)+'_'+str(m).zfill(2)+'_'+str(d).zfill(2)  
            # First, check if h5 file is already in existance for this date
            h5 = './'+str(year)+'_'+str(doy).zfill(3)+'.h5'
            if os.path.isfile(h5):
                print('Open and read '+h5)
                ch = cloud_height(date,'ceil_h',h5=h5)
            else:
                ch=cloud_height(date,'ceil_')
                ch.stats()   
                ch.save()   
            print('Cloud fraction that day:',round(ch.cf,2),'%')
            cf_list.append(ch.cf) # keep track of cloud fraction
        plt.plot(doy_list,cf_list,'.')
        plt.xlabel('Day of year')
        plt.ylabel('Cloud Fraction')
                

