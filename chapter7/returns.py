# -*- coding: utf-8 -*-
"""
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#--------o---------o---------o- Returns class ---o---------o---------o---------o---------o---------o
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o

DISCLAIMER:
THIS SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT 
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES 
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
CONNECTION WITH THIS SOFTWARE OR THE USE OR OTHER DEALINGS IN THIS SOFTWARE.

Copyright © 2004-2019 David Worrall 

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and 
associated documentation files (the “Software”), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished
 to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

- Converts trading or similar data in .csv file to returns
- Produces correlated and decorrelated time series data
- Generates stats and graphs
- Outputs to AIFC, or other filetype
- Python 3 compatible

history:
v0.00   20040902 initial draft
v0.01   20040922 minor bugs + rework w. better stats
v0.02   20041024 add toAIFC
v0.03   20041024 minor bugs + improve toAIFC
v0.20   20051209 objectify
v0.21   20070126 reorder for np, scipy and matplotlib
v0.22   20090110 redo plotting routines
v0.23	20100228 to sonification.com.au/audification
v0.24	20190228 convert to Python 3; comment out unneeded pyaudio import
"""
__author__      = "David Worrall  2004++"
__version__     = "0.2.4"
__docformat__   = "restructuredtext en"

import  string, ctypes, struct
import  os.path as path                 # for file paths and universal separators.
from    datetime   import datetime
from    scipy      import stats
import  numpy   as np                   # hurray for arrays!

# import  aifc, pyaudio                   # for file writing and rt audio streaming
import  aifc
import  pylab 
import  matplotlib.pyplot   as plt      # interface to matplotlib plotting routines
import  matplotlib.ticker   as ticker   # for controlling the axis labelling
import  matplotlib.mlab     as mlab     # for plotting returns and histograms

EOF = ''                                # End of File ID for readline
BITS_15 = pow (2, 14)                   # for bit-shifting 

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#--------o---------o---------o-- Generic Functions --------o---------o---------o---------o---------o
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
def printStringList (listy, stringy=None, ):
    """
    Pretty-prints a list of strings.
    Good for looking for directory entries containing whatever stringy is assigned to.
    Use Eg.: printStringList (dir(), stringy = 'xxx') to find out if xxx is in the dir()
    """
    beg =''
    for i in dir(listy):
        if i[0] != beg:
            beg=i[0]
            print()
        else:
            if stringy != None: print (i , end = "" )  # don't throw a new line 
                                                       # for python 2 use  print i ,
            else:
                if stringy in i:    print (i )

def marketTimeString (dtTuple):
    """
    Converts datetime tuple to a string in the form yyyymmdd.hhmmss.
    # Eg. datetime.datetime(2009, 1, 26, 18, 20, 5, 198934) ==> '20090126.182005'
    """
    res = str([dtTuple.year, dtTuple.month, dtTuple.day, dtTuple.hour, dtTuple.minute, \
                                           dtTuple.second])[1:-1] # dtTuple elts as a single string
    res=res.split(',')
    res = [res[0]] + [('0'+i.strip(' '))[-2:] for i in res[1:]] # res = [yyyy,mm,dd,hh,ss]
    return string.join(res[:3], '')+'.'+ string.join(res[3:], '')       # returns "yyyymmdd.hhmmss"
# marketTime (now)

def scaleArray (np1array, miny=-1, maxy=1, trace=False):
    """Scales a numpy array to between miny and maxy. Typically, npArray is a row of the returnsArray
    Why isn't this a numpy method?"""
    np1array = np.array(np1array)           # just in case! redundant if already a numpy array
    newrange = abs(float(maxy-miny))        # abs range of IP.The abs could be avoided -
                                            # it's there in case max and min are swapped on IP
    scaler = newrange/abs((np1array.max() - np1array.min()))
    minAdjust=(scaler * np1array.min()) - miny
    np1array = (scaler * np1array) - minAdjust
    if trace:
        print ("newrange:", newrange, "--- scaler:", scaler, "--- minAdjust:", minAdjust )
        print ("Xchecks. scaled returnsMinMax:", (np1array.min(), np1array.max()) )      
    return (np1array)

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#--------o---------o---------o- Returns class ---o---------o---------o---------o---------o---------o
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o

class Returns:
    def __init__(self, IPdataFname, begDate=0, endDate=0, nr=None, field="close"):
        self.IPdatafile = IPdataFname   # the csv file of the market data. The shortname - extension
                                        # is used as part of the OPfilename. See returnsToAif method
        self.shortFname = self.IPdatafile.split(path.sep)[-1].split(path.extsep)[0]

        self.nrRecords = nr             # max number records to be read btwn begDate & endDate
        self.fieldName = field.lower()  # the dataField (column ) we want + drop all caps
        self.datefield = 'date'         # should be 0. asign to null to tell if it is present
        self.fieldNr =-1                # init for column nr of data to be pulled
        self.sep = ','                  # for csv files. Could be an IPvar, or more sophisticated

        self.returnsArray = None        # set later when size is known
        self.origDataIx         = 0     # self.returnsArray[0] Use named ix's for code readability
        self.returnsIx          = 1     # self.returnsArray[1] overwritten for clipped returns
        self.decorrReturnsIx    = 2     # self.returnsArray[2] for decorrelated version of [1]
        self.uniformIx          = 3     # self.returnsArray[3] for uniform distribution & returns
        self.normalIx           = 4     # self.returnsArray[4] for uniform distribution & returns

        self.returnsStats = None        # Stats for the returns. See self.calculateReturns()
        self.begDate = begDate          # default is 0, ergo first record if not set
        if endDate == 0:
            self.endDate = datetime.today() # default is current date, ergo  EOF if not set 
            self.endDate = self.endDate.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            self.endDate = self.secDateToDT(endDate) 
        try:
            self.IPfile = open(self.IPdatafile, 'r')
        except:
            print ("Unable to locate ",IPfname,". If file is not in cur. dir, use full pathname." )
            return
        self.getDataFormat()
        self.getDataFromFile()
        self.IPfile.close()

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
    def getDataFormat (self, trace=False):
        """
        Reads first line of datafile for data format. Called on class instantiation.
        self.dataFormat is not referenced outside this method - so could be a local.
        """
        try:
            self.dataFormat = self.IPfile.readline()   # read first line of file
                         # should be in <date>,<open> etc format or
                         #string of the form "Date,Open,High,Low,Close,Volume,OpenInterest"

            # convert dataFormat into a simple csv string
            if self.sep in self.dataFormat:
                self.dataFormat.replace('<', "") # toss the <fieldnme> formatting, if present ...
                self.dataFormat.replace('>', "") # no harm done if not.¿check  for empty space?
            if self.fieldName in self.dataFormat.lower(): 
                                                 # find field nr of the field (eg 'close) reqd
                self.fields = self.dataFormat.lower().split(self.sep) # drop caps, split to list

            # get the field numbers
            for i in range (len(self.fields)):
                if self.fields[i] == self.datefield:
                    self.datefield = i  # ugly type-change - but saves a var!
                if self.fields[i] == self.fieldName:
                    self.fieldNr = i
            if self.fieldNr == -1:
                print ("Unable to locate ", self.fieldName, " in ", self.dataFormat, \
                        ". Check (non case-sensitive) spelling." )
            if trace:
                print ("datafields   :", self.dataFormat )
                print ("Datafield '", self.fieldName ,"' is col ", self.fieldNr, ". File is closed." )
        except:
                print ("Problem with data read." )

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
    def secDateToDT (self, dateString):
        """
        Converts a security date to eight-digit in the form yyyymmdd to a datedtime structure
        six-digit dates are common so we have to convert 86 to 1986 and 05 to 2005
        dateString is in eithe '861025' or '19861025' or '081025' or '20081025'
        """
        dateString = dateString.replace('/','') # get rid of separators
        dateString = dateString [-6:] # toss  yyyy if present, we'll calc it.'
        if (2000 + int (dateString[:2]) )> datetime.today().year:   # it must be a 1900 date so
            dateString = int('19'+ dateString)
        else:
            dateString = int('20'+ dateString)
        tmp=divmod(dateString,10000)    # leftmost 4 digits is the year
        m, d = divmod(tmp[1],100)
        return datetime (tmp[0],m,d)                                        

    def getDataFromFile (self, trace=False):      
        """
        Reads data from file, sorts out the date and keeps the required field.
        Uses secDateToDT() to put date in datetime format.
        """
        tbuff=self.IPfile.readline()
        count = 0
        datafromFile = []   # list into which file data is read, elt by elt
        self.nrRecords = len (datafromFile)
        while tbuff != EOF and self.nrRecords < count:
            tbuff=tbuff.split(self.sep)                     # NB default for self.nrRecords = None
#            dayte = tbuff[self.datefield].replace('/',"")      # convert date string into an int
            dayte = self.secDateToDT(tbuff[self.datefield])
            datafromFile.append(string.atof(tbuff[self.fieldNr]))  # pull fielddata requird to array
            tbuff=self.IPfile.readline()                        # read 1 new line from file
            count += 1
            if trace:
                print ("record Nr:", count, dayte)                        
#       --------------- Make the np array for all the data --------------# row0 4 data, row1 4 Rnet,
        self.returnsArray=np.empty([5, len (datafromFile)], dtype=float) # row2 4 normalised
        self.nrRecords = len (datafromFile)
        if trace:
            print ("Length of returnsArray = ", self.nrRecords)     # len (datafromFile)
        self.returnsArray[self.origDataIx] = datafromFile           # transfer list to np array

    def calculateReturns (self):
        """
        Calculates the Net returns of in col0 and stores them in col1 of the np returnsArray.
        """
        self.returnsArray[self.returnsIx,0] = 0                     # set  return of zeroth sample
        for i in range (1,len(self.returnsArray[self.returnsIx])):
            self.returnsArray[self.returnsIx,i]=(self.returnsArray[self.origDataIx,i] \
                    - self.returnsArray[self.origDataIx,i-1])/self.returnsArray[self.origDataIx,i]
        self.doStats()          # set the records straight!
#        self.returnsArray[self.returnsIx] = scaleArray(self.returnsArray[self.returnsIx])

    def decorrelateReturns (self):
        """
        Stores a decorrelated form of the net returns in returnsArray[sourcecol]
        in returnsArray[targetcol].
        """
        self.returnsArray[self.decorrReturnsIx]= \
                                        np.random.permutation(self.returnsArray[self.returnsIx])
    def makeUniformReturns (self):
        """
        Generates a uniform random distribution over the interval [-1.0,1.0)
        Calcs the returns and stores in self.returnsArray[uniformIx]
        This is the base 'flat' distribution aganst which others canbe compared
        """
#        self.returnsArray[self.uniformIx] = scaleArray(np.random.uniform(low=-1.0, high = 1.0,\
#                                                        size = self.nrRecords), trace=True)
        self.returnsArray[self.uniformIx] = np.random.uniform (low=-1.0, high = 1.0,\
                                                        size = self.nrRecords)
    def makeNormalReturns (self):
        """
        Generates a normal random distribution over the interval [-1.0,1.0)
        Calcs the returns and stores in self.returnsArray[normalIx]
        This is the distribution against which random (uncorrelated) walks can be compared
        """                            
        self.returnsArray[self.normalIx] = scaleArray(np.random.normal(size = self.nrRecords),\
                                                      miny=-1.0, maxy = 1.0)

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
    def doStats (self, trace=False):
        """
        Calculates a number of common statistical properties of the returns data. Prints if nesess.
        """
        self.returnsStats = list(stats.stats.describe(self.returnsArray[self.returnsIx]))
        self.returnsStats[0] = len (self.returnsArray[self.returnsIx])
        self.returnsStats[1] = (np.min(self.returnsArray[self.returnsIx]) ,\
                                                np.max(self.returnsArray[self.returnsIx]))
        self.returnsStats[2] = np.mean(self.returnsArray[self.returnsIx])
        self.returnsStats[4] = np.var(self.returnsArray[self.returnsIx])
        self.returnsStats.append(np.median(self.returnsArray[self.returnsIx]))
        if trace:
            print ("Description\n-----------" )
            print (" nr samples ", self.returnsStats[0] )
            print (" min sample ", self.returnsStats[1][0] )
            print (" max sample  ", self.returnsStats[1][1] )
            print (" arith mean  ", self.returnsStats[2] )
            print (" median      ", self.returnsStats[6] )
            print (" mode        ", stats.stats.mode(self.returnsArray[self.returnsIx])[0][0] )
            print (" variance    ", self.returnsStats[3] )
            print (" skewness    ", self.returnsStats[4] )
            print (" kurtosis   ", self.returnsStats[5] )
#           print (" kurtosos test", stats.stats.kurtosistest(self.returnsArray[self.returnsIx]) )
#           print (" normal test", stats.stats.normaltest(self.returnsArray[self.returnsIx]) )

    def clipReturns (self, nrMin=0, nrMax=0, trace=False):
        """
        Clips all min values of the returnsArray to the size of the nr Min'th & nrMax'th vals.
        Used to 'limit' the returns to be audified. The default position is no clipping. 
        Could be used for autoclip based on the 'significant' of SNR improvment for soing so. 
        Eg clipReturns(nrMin=1,nrMax=0) limits the most neg. val to the 2nd most neg.
        Used to clip  outliers to improve SNR of sample space prior to sonification.
        If zeroing the samples is more appropriate, use threshold like this:
            tmp2array=stats.stats.threshold(tmp2array, negLimit,posLimit)
        In this usage, better to clip to nearest to maintain firmer recog. of ss.
        nrMin, nrMax are the number of samples on either end of a sorted ss to be clipped.
        """
        tmpArray = np.copy(self.returnsArray[self.returnsIx])
        tmpArray.sort()                                 # necess to make for independent sort
        negLimit = tmpArray[nrMin]                      # the value below which all are clipped
        posLimit = tmpArray[-nrMax-1]                   # the value above which all are clipped

        # fill outliers with closest inlier vals as dictated
        negIndicesToLimit = []                          # for indices of -ve vals to fix
        posIndicesToLimit = []                          # for indices of +ve vals to fix
        for index in range(len(self.returnsArray[self.returnsIx])):
            if self.returnsArray[self.returnsIx][index] < negLimit:
                negIndicesToLimit.append(index)         # find a -ve outlier
                self.returnsArray[self.returnsIx][index]=negLimit    # fill it with most -ve inlies
            if self.returnsArray[self.returnsIx][index] > posLimit:
                posIndicesToLimit.append(index)         # find a +ve outlier
                self.returnsArray[self.returnsIx][index]=posLimit    # fill it with most +ve inlies
        self.doStats()                                  # set the records straight!
        if trace:
            print ("Neg limit", nrMin, " vals to", negLimit )
            print ("Pos limit", nrMax, " vals to", posLimit )
            print ("-ve indexes to fix with %f:" % (negLimit) )
            for i in negIndicesToLimit:
                print ("\treturns [%i] is currently %f" %(i, self.returnsArray[self.returnsIx][i]) )
            print ( "+ve indexes to fix with  %f:" % (posLimit) )
            for i in posIndicesToLimit:
                print ( "\treturns [%i] is currently %f" %(i, self.returnsArray[self.returnsIx][i]) )

    def arrayToAIFC (self, np1array, OPfname,
                 nrchans    = 1,
                 SR         = 44100,
                 nrReps     = 0,
                 gapSecs     = 0,
                 buffsize   = 4096,
                 trace      = False):
        """
        Writes npArray to fname.AIFC. Filename contains original DataFilename datetime-stamp.
        buffsize is size of AIFC write buffer. File writes are in buffsize increments.
        Write the arran nrReps number of times, with gapSec seconds between
        """
        OPfileID = aifc.open(OPfname+'.aifc', 'wb')         # open the file and set up the header
        OPfileID.setnchannels(nrchans)                      # the number of channels (1=mono)
        OPfileID.setsampwidth(2)                            # the sample width in bytes(16bit fmt)
        OPfileID.setframerate(SR)                           # the frame rate. for mono, FR =SR    
                                                            # scale data -1 to 1 
                        # scale (-1,1) the np.array, shift it 15 bits and overwrite it as int16s
        npSarray=BITS_15*np1array                          # NB can be a np.array. Doesn't have 2B
        npSarray=npSarray.astype('int16')                   # cvt to 16 bit ints. 
                                                            # Use nparray.dtype say what type it is
                        # to python list - has to be a better way!!!!! ##
                        # try to pack it directly from the np1aray, as per pyAudioEg.py
        tmp = npSarray.tolist()
        dataString = "".join(struct.pack('>h', i) for i in tmp) # pack the array data into a buffer
        OPfileID.writeframes(dataString)                        # write buffer to file
                        # if the sound it to be repeated,insert a gapsSec silence b4 writing again
        if nrReps > 0:
            tmp = np.array (np.zeros(gapSecs * SR * nrchans, dtype='int16'))
            silentString = "".join(struct.pack('>h', i) for i in tmp) # pack zeros into a buff
            for i in range (nrReps):
                OPfileID.writeframes(silentString)              # write the silence buffer
                OPfileID.writeframes(dataString)                # write the non-silent buffer again
        OPfileID.close()
        if trace:
            numsamps = int(len(np1array)) + (gapSecs * SR * nrchans)
            print ( "Wrote %s.aifc, nrChans: %d, nrSamps: %d." % (OPfname, nrchans, numsamps) )

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#----------------------------unfinished -------------------
    def arrayToWAV (self, np1array, OPfname,
                 nrchans    = 1,
                 SR         = 44100,
                 nrReps     = 0,
                 gapSecs     = 0,
                 buffsize   = 4096,
                 trace      = False):
        """
        Writes npArray to fname.wav. Filename contains original DataFilename datetime-stamp.
        buffsize is size of wav write buffer. File writes are in buffsize increments.
        Write the arran nrReps number of times, with gapSec seconds between
        """
        OPfileID = aifc.open(OPfname+'.wav', 'wb')         # open the file and set up the header
        OPfileID.setnchannels(nrchans)                      # the number of channels (1=mono)
        OPfileID.setsampwidth(2)                            # the sample width in bytes(16bit fmt)
        OPfileID.setframerate(SR)                           # the frame rate. for mono, FR =SR    
                                                            # scale data -1 to 1 
                        # scale (-1,1) the np.array, shift it 15 bits and overwrite it as int16s
        npSarray=BITS_15*np1array                          # NB can be a np.array. Doesn't have 2B
        npSarray=npSarray.astype('int16')                   # cvt to 16 bit ints. 
                                                            # Use nparray.dtype say what type it is
                        # to python list - has to be a better way!!!!! ##
                        # try to pack it directly from the np1aray, as per pyAudioEg.py
        tmp = npSarray.tolist()
        dataString = "".join(struct.pack('>h', i) for i in tmp) # pack the array data into a buffer
        OPfileID.writeframes(dataString)                        # write buffer to file
                        # if the sound it to be repeated,insert a gapsSec silence b4 writing again
        if nrReps > 0:
            tmp = np.array (np.zeros(gapSecs * SR * nrchans, dtype='int16'))
            silentString = "".join(struct.pack('>h', i) for i in tmp) # pack zeros into a buff
            for i in range (nrReps):
                OPfileID.writeframes(silentString)              # write the silence buffer
                OPfileID.writeframes(dataString)                # write the non-silent buffer again
        OPfileID.close()
        if trace:
            numsamps = int(len(np1array)) + (gapSecs * SR * nrchans)
            print ("Wrote %s.wav, nrChans: %d, nrSamps: %d." % (OPfname, nrchans, numsamps) )
#----------------------------end unfinished -------------------

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o        
    def outputAudioFiles (self, OPdir=None, SR = 44100, gapSecs = 0, trace=False):
        """
        Write the corr and decorr rtns and  same size uniform and normal returns
        OPdir is a string of the directory to which the .aifc files is output.
        """
        # Maake sure the OPdir given is actually a directory
        if OPdir:
            if OPdir[-1] != path.sep:                           # '/' on unix etc, '\' on windows
                OPdir += path.sep                               # in case it has been left off 
        if not path.isdir (OPdir):
            print ("The directory to write to cannot be found." )

        # Construct the filenames
        shortFname = self.IPdatafile.split(path.sep)[-1].split(path.extsep)[0]
        now = marketTimeString(datetime.today())                # 'yyyymmdd.hhmmss'
#        now= string.split(now, '.')[0]                          # drop the mins & secs

        # Make the output file names 
        rtnFname    = OPdir + shortFname+'-ReturnsRaw_'+ now    # for rtns
        decorrFname = OPdir + shortFname+'-RtnsDecorr_'+ now    # for decorrelated rtns
        uniformFname= OPdir + shortFname+'-RtnsUniform_'+ now   # for white random rtns
        normalFname = OPdir + shortFname+'-RtnsNormal_'+ now    # for normal rtns
        CandDFname  = OPdir + shortFname+'-CorrAndDecorr_'+ now # for alternate A/B comparison
        UNDRtnFname = OPdir + shortFname+'-uniNormDecorRtn_'+ now # all 4 in sequence

        ret1dc1Fname = OPdir + shortFname+'-ret+2dcorr1_'+ now   # 1 x ret + 2 x decorr nr2
        ret1dc2Fname = OPdir + shortFname+'-ret+2dcorr2_'+ now   # 1 x ret + 2 x decorr nr2
        ret1dc3Fname = OPdir + shortFname+'-ret+2dcorr3_'+ now   # 1 x ret + 2 x decorr nr3

        # Concatenate the composite buffers (raw and Decorrelated + UNDR
        b0 = np.zeros (int(gapSecs*SR))
        b1 = scaleArray(self.returnsArray[self.returnsIx], miny=-1.0, maxy = 1.0)
        b2 = scaleArray(self.returnsArray[self.decorrReturnsIx], miny=-1.0, maxy = 1.0)
        b3 = scaleArray(self.returnsArray[self.uniformIx], miny=-1.0, maxy = 1.0)
        b4 = scaleArray(self.returnsArray[self.normalIx], miny=-1.0, maxy = 1.0)

        retAndDecorrArray = np.concatenate((b1,b0,b2))
        UNDRtnArray = np.concatenate((b3, b0, b4, b0, b2, b0, b1))

        # de-correlate the decorrelation, and again
        b5 = np.concatenate((b1, b0, np.random.permutation(b2), b0, np.random.permutation(b2)))
        b6 = np.concatenate((np.random.permutation(b2), b0, b1, b0, np.random.permutation(b2)))
        b7 = np.concatenate((np.random.permutation(b2), b0, np.random.permutation(b2), b0, b1,))
        
        if trace:
            print ("Range cross-check:" )
            print ("     Array           Min    Max" )
            print (" _____________________________________" )
            print ("     ReturnsRaw_    %.2f   %.2f" %  (b1.min(), b1.max()) )
            print ("     RtnsDecorr_    %.2f   %.2f" %  (b2.min(), b2.max()) )
            print ("    RtnsUniform_    %.2f   %.2f" %  (b3.min(), b3.max()) )
            print ("     RtnsNormal_    %.2f   %.2f" %  (b4.min(), b4.max()) )
            print ("  CorrAndDecorr_    %.2f   %.2f" %  (retAndDecorrArray.min(),
                                                        retAndDecorrArray.max()) )
            print ("uniNormDecorRtn_    %.2f   %.2f" %  (UNDRtnArray.min(), UNDRtnArray.max()) )
            print ("   ret+1xdcorr1_    %.2f   %.2f" %  (b5.min(), b5.max()) )
            print ("   ret+1xdcorr2_    %.2f   %.2f" %  (b6.min(), b6.max()) )
            print ("   ret+2xdcorr3_    %.2f   %.2f" %  (b7.min(), b7.max()) )
        
        # send multiples of the individual arrays  off to the audio OP routine
        self.arrayToAIFC (b1, rtnFname,     SR=SR, nrReps = 3, gapSecs = 1, trace=trace)
        self.arrayToAIFC (b2, decorrFname,  SR=SR, nrReps = 3, gapSecs = 1, trace=trace)
        self.arrayToAIFC (b3, uniformFname, SR=SR, nrReps = 3, gapSecs = 1, trace=trace)
        self.arrayToAIFC (b4, normalFname,  SR=SR, nrReps = 3, gapSecs = 1, trace=trace)
        # send combinations of the individual arrays   to the audio OP routine
        self.arrayToAIFC (retAndDecorrArray, CandDFname,    SR=SR, nrReps=3, gapSecs=2, trace=trace)
        self.arrayToAIFC (UNDRtnArray, UNDRtnFname,         SR=SR, nrReps=3, gapSecs=2, trace=trace)

        # send 2x different decorrelates + raw return to the audio OP routine
        self.arrayToAIFC (b5, ret1dc1Fname,  SR=SR, trace=trace)
        self.arrayToAIFC (b6, ret1dc2Fname,  SR=SR, trace=trace)
        self.arrayToAIFC (b7, ret1dc3Fname,  SR=SR, trace=trace)
        
        print ("Finished writing audio files to", OPdir + shortFname )
        # send multiples of the individual arrays  off to the audio OP routine
#        self.arrayToWAV (b1, rtnFname,     SR=SR, nrReps = 3, gapSecs = 1, trace=True)
#        self.arrayToWAV (b2, decorrFname,  SR=SR, nrReps = 3, gapSecs = 1, trace=True)
#        self.arrayToWAV (b3, uniformFname, SR=SR, nrReps = 3, gapSecs = 1, trace=True)
#        self.arrayToWAV (b4, normalFname,  SR=SR, nrReps = 3, gapSecs = 1, trace=True)
        # send combinations of the individual arrays   to the audio OP routine
#        self.arrayToWAV (retAndDecorrArray, CandDFname,    SR=SR, nrReps=3, gapSecs=2, trace=True)
#        self.arrayToWAV (UNDRtnArray, UNDRtnFname,         SR=SR, nrReps=3, gapSecs=2, trace=True)
        # send 2x different decorrelates + raw return to the audio OP routine

#--------o---------o---------o- End of Returns Class ------o---------o---------o---------o---------o

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#--------o---------o---------o---- Play Audio Routines ----o---------o---------o---------o---------o
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o

def sineTone (Fname="sine", freq=1000, dur=1,SR = 44100):
    abscissa = np.linspace(0,1,SR)                          # abscissa  is the x of y = f(x)
    data = np.sin(abscissa *2 * np.pi* freq)                # data      is the y of y = f(x)
    return data
    arrayToAIFC (data,OPdir+str(freq), trace=False)          # if Fname doesn't contain full path,
                                                            # file will be written to current dir    

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#--------o---------o---------o- Plotting Routines ---------o---------o---------o---------o---------o
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
# NB All plotting routines need a call to pylab.show() to display the plot
def plotXAO ():
    pylab.plot(xao.data, 'g.')                  # dots are '.'  ; pixels are ','
    pylab.xlabel('Contiguous Trading Days')
    pylab.ylabel('XAO Closing Value')
    pylab.grid(True)
#    pylab.savefig('XAOpix')                    # use if .png file is required

def plotXAOreturns (col=1):
    """
    Plots the returns. col=1 is the returns, col=2 is the decorrelated returns.
    """
    pylab.plot(xao.returnsArray[col],'g-')        # dots are '.'  ; pixels are ','
    pylab.xlabel('Contiguous Trading Days')
    pylab.ylabel('XAO Net Returns')
    pylab.grid(True)
#    pylab.savefig('XAOnetRtns')                # use if .png file is required
    pylab.savefig('XAOdecorrelatedReturns')     # use for decorrelated signal

def histMeanLine (color='#FF0000', linestyle='-', width = 1, yminmax=(0,100)):
    """
    Draws a vertical line t at or near the mean.
    'Near to' is there for situations where it would improve visibility of dataplots at the mean.
    """
    fudge = xao.returnsStats[2]+ 0.0002     # add a small o'set, when necess.
    meanLineX = [fudge,fudge]
    meanLineY = yminmax
    pylab.plot(meanLineX,meanLineY, color=color, linestyle=linestyle,\
                                               linewidth=1,  label='mean') # ¿ '_nolegend_' ?

def histXAOreturns (col=1, nrbins=10, color='green'):
    pylab.hist(xao.returnsArray[col], nrbins, facecolor=color, label='actual returns',alpha=0.25)
#    histMeanLine(fmat='r-', width=1, yminmax=(0,490))      # alternative to that below
    histMeanLine(color='#ff0000', linestyle='-', width=1, yminmax=(-20,480))
#    pylab.axis([-0.35,0.07, -30,890])                      # alternative to that below
    pylab.axis([-0.35,0.07, -20,500])                       # use this when there's more bins
    pylab.savefig('XAOhist+NormHist')                       # use if .png file is required

def histXAOclippedReturns (col=1, nrbins=10, color='green'):
    pylab.hist(xao.returnsArray[col], nrbins, facecolor=color, \
               label='clipped returns', align='mid', alpha=1)
    #histMeanLine(color='#FF0000', linestyle='-', width=1, yminmax=(-20,480))
    pylab.axis([-0.1,0.07, -30,450])
    pylab.savefig('XAOclipped+NormHist')             # use if .png file is required

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
def histNormal (color='000000', trace = False):
    """
    Plot a normal distribution with mu and sigma sa,e ar original or clipped dataset.
    To place mu at the centre of the abscissa space, use:
    #mu = xao.returnsStats[1][0]+ (0.5* (xao.returnsStats[1][1] - xao.returnsStats[1][0]))
    """
    mu=xao.returnsStats[2]
    sigma = np.sqrt(xao.returnsStats[3])                            # sdev-[3] is variance
    normSamps = np.random.normal(mu, sigma, xao.returnsStats[0])    # [0] is nr datapoints
    dta , smallest, binsize, ignore = stats.histogram (normSamps, nrbins)
    histy, binEdges = np.histogram (normSamps, bins=nrbins, normed=0, new=False)
#    pylab.plot(binEdges,histy, 'b-', linewidth=1, color='#888800', antialiased=True,\
#           label='normal distribution,\nwith same St.Dev.', alpha=1)
    pylab.hist(normSamps, nrbins, facecolor=color, align='mid' ,bottom=None, \
               label='simulated normal\ndistrib. with same StD.', alpha=1)
    if trace:
        print ("histy:", np.sum(histy) )							# ,histy
        print ("binEdges", np.sum(binEdges) )						#, binEdges
        print ("size of normSamps:", len(normSamps) )
        print ("sum of hist:", histy.sum() )
        print ("over same abscissa:", np.min(normSamps), np.max(normSamps) )
        print ("over SND histogram",  np.min(histy), np.max(histy) )

def xAxis ():
    ax=pylab.subplot (111)
    majLoc = pylab.MultipleLocator(0.02)
    majFmat = pylab.FormatStrFormatter('%f') # or some other format - this puts the numbers on
    ax.xaxis.set_major_locator(majLoc)
#    ax.xaxis.set_major_formatter(majFmat)
    
    minLoc = pylab.MultipleLocator(0.01)
    ax.xaxis.set_minor_locator(minLoc) #for the minor ticks, use no labels; default NullFormatter

def yAxis ():
    ay=pylab.subplot (111)
    majLoc = pylab.MultipleLocator(50)
    majFmat = pylab.FormatStrFormatter('%d') # or some other format - this puts the numbers on
    ay.yaxis.set_major_locator(majLoc)
    ay.yaxis.set_major_formatter(majFmat)
    
    minLoc = pylab.MultipleLocator(10)
    ay.yaxis.set_minor_locator(minLoc) #for the minor ticks, use no labels; default NullFormatter

#    pylab.axhline(y=-50, color='black') # draw a line - why not!

def legend ():
    pylab.legend(loc='center left') #, size='medium')
#    pylab.legend(loc='top left') #, size='medium')

def labels ():
    s = 'Decorrelated Net Returns (%d bins)' % (nrbins)
    pylab.xlabel(s)
    pylab.ylabel('Frequency of occurrence')

#--------o---------o---------o- End of Plotting Routines --o---------o---------o---------o---------o

#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#--------o---------o---------o- __main__() code -o---------o---------o---------o---------o---------o
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#def doit ():
xao = Returns ("XAO_5725.csv", field ='close') # get original dataset from file etc
#plotXAO ()                                  # plots the original dataset

xao.calculateReturns ()                     # calcs the Prob. Density Fn (pdf)
#plotXAOreturns (col=1)                     # plots the pdf of the correlated returns
xao.clipReturns (1,0)                       # the dataset with the LH datapoint removed
xao.doStats (trace=True)                    # stats have changed, so reset the record!
xao.decorrelateReturns ()                   # decorr rtns[returnsIx] into retns[decorreatedRtnsIx] 
xao.makeUniformReturns()
xao.makeNormalReturns()

#xao.outputAudioFiles (OPdir='/Users/drw/Desktop', trace=True) # output all returns to AIF files
xao.outputAudioFiles ('/Users/drw/Desktop/XAO-5725audiofiles/',
                                            SR = 16000,
                                            gapSecs = 1.0,
                                            trace = False)  # output all returns to AIF files


"""
The works and is used - just commented out for the mo. should be part of doit()
plotXAOreturns (col=2)                           # plots the pdf of the correlated returns

    # _______________________________- MAKE THE HISTOGRAMS - ________________________________o
                    #calc for space just of most -ve sample:
                    # total s.sppce = 0.333204213427 + 0.0588620748375 = 0.39206628826450002
                    # diff btw least two: 0.33320421 - 0.08807546 = 0.24512875000000001
                    # proport. of total space = 0.24512875/0.39206628826450002= 0.6252227170182727

nrbins=200                                      # nr is somewhat arbitrary,easily changed!
#nrbins = int (200/(1- 0.625))                   # use this to keep the bin size the same for
#histXAOreturns(nrbins, color='#888888')         # compute the returns from the original dataset
#histXAOreturns(col=2,nrbins=nrbins, color='#00ff00')
                                                # the raw and the clipped. 
#histXAOclippedReturns(col=1, nrbins=nrbins, color='#00ff00')
#histMeanLine(fmat='g-')
#histNormal(color='#000000')
legend()
labels()
yAxis()
#xAxis()
#pylab.grid(True)
#pylab.axhline(y=-50, color='black') # draw a line - why not!

#pylab.axis('off')
#pylab.savefig('XAOhist+NormHist')             # use if .png file is required
#pylab.savefig('XAOdecorrelatedReturns')
pylab.show()

#doit()
"""
"""
==================================

Description b4 clip
-----------
 nr samples  5725
 min sample   -0.333204213427
 max sample   0.0588620748375
 arith mean   0.000217488453128
 variance     9.56858813276e-05
 skewness    -7.64911826438
 kurtosis   241.729886112
---
calc for space just of most -ve sample:
total s.sppce = 0.333204213427 + 0.0588620748375 = 0.39206628826450002
diff btw least two: 0.33320421 - 0.08807546 = 0.24512875000000001
proport. of total space = 0.24512875/0.39206628826450002  =   0.6252227170182727
---
Description after clip
-----------
 nr samples  5725
 min sample  -0.088075456212
 max sample   0.0588620748375
 arith mean   0.000260305703297
median       0.000236144211932
mode         0.0
 variance     7.76242316164e-05
 skewness    7.76106727987e-05
 kurtosis   12.2617257637
"""

