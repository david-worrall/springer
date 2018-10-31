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




