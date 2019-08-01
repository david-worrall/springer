# -*- coding: utf-8 -*-
"""
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o
#--------o---------o- Class Inheritance - Python 3 Example o---------o---------o---------o---------o
#--------o---------o---------o---------o---------o---------o---------o---------o---------o---------o

DISCLAIMER:
THIS SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT 
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES 
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
CONNECTION WITH THIS SOFTWARE OR THE USE OR OTHER DEALINGS IN THIS SOFTWARE.

Copyright © 2018-2019 David Worrall 

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and 
associated documentation files (the “Software”), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial 
portions of the Software.

- An extremely simple audio-related example to demonstrate how Python class inheritance works
- Python 3 compatible

history:
v0.00   20190228 initial draft
"""
__author__      = "David Worrall  2008-2009"
__version__     = "0.0.1"
__docformat__   = "restructuredtext en"

class Audio():                      # The "()" are optional
    """For applying DSP effects on audio files and streams."""	
    _audiofileFormats=["wav", "aiff", "aifc", "mp3", "ogg", "amb"]

    def __init__(self, audiofile):
        """ Initialize instances of the Audio class."""
        self.audiofile = audiofile # instance varia-ble
        self.headroom = 0
        self.bandpassLimits = (0,0)
        # do other stuff on instantiation

    def normalize(self, headroomInDB):
        """A method to amplitude scale an audio file."""
        self.headroom = headroomInDB
        print ("Normalizing %s to %1.3f dB limit of max."  
            % (self.audiofile, self.headroom))

    def bandpassFilter (self, lowerFreq, upperFreq):
        """A method to bandpass filter an audio file"""
        self.bandpassLimits = (lowerFreq, upperFreq)
        # stuff to do

class Data():
    """For handling data files and streams."""	
    __datafileFormats=["txt", "csv", "xls", "xlsx","zip", "dhf5"]

    def __init__(self, dataFile):
        """ Initialize instances of the Data class."""
        self.dataFile = dataFile # instance variable
        # do other stuff on instantiation

    def dataStats(self):
        """Produces basic statistical analysis of the da-ta"""
        print ("Performing statistical analysis of the data")
        # stuff to do

from datetime import datetime
class Sonify (Audio, Data):
    """Child class to handle combining parents of a sonifica-tion."""
    def __init__(self, datafile, audiofile):
        """ Initialize instances of the Sonify class."""
        Audio.__init__(self, audiofile) # initialize all the variables in the parent class
        Data.__init__(self, datafile) # this initialize all the variables in the parent class
        self.audiofile = "backflip.wav" # override the Audio instance variable initialization
        self.sonTime = datetime.now()
        self.bandpassLimits = (0,0)
        self.UIdevices = []
        # do other stuff on instantiation

    def addUIdevice (self, deviceString):
        """ Define sonification output device."""
        if deviceString.strip() not in self.UIdevices:
            self.UIdevices += [deviceString]
        else:
            print ( "%s already in UI the device list" % deviceString)

    
    
"""
Example of usage
# Audio class instantiation tests:
myAudio = Audio("notDrowning.wav")
myAudio.normalizeFile (-3)
myAudio.bandPassFilter (50, 8000)
print (myAudio.audiofile)

# Data class instantiation tests:
myData = Data ("bigDataSet.csv")
myData.dataStats()

# Sonify class instantiation tests:
myson = Sonify ("swimrates.csv", "drowning.ogg")
myson.audiofile
"""




