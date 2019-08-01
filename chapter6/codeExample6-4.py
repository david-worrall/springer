def makeCSevent (*args):
    """Make a csound event and play it in an already active
       Performance thread."""
    eventStr = "".join(map(str, args))
    print (eventStr)			  		# delete if necessary
#   csPerf.InputMessage(eventStr+"\n")	# alternative push method 
#   cs.ScoreEvent(eventStr)		  		# alternative push  method
    cs.ReadScore (eventStr) 			# push the score

# --------- BEGIN csound instrument definition string ------------
myOrcOptions="""
sr     = 44100
kr     = 4410
ksmps  = 10
nchnls = 2
0dbfs  = 1.0"""
pluckIt="""
instr 2
  instrNr	= p1
  istartTime	= p2
  kloc	= p9 ; location
  kbeta	= 0  ; spread … for ambi out
  ifn	= 0  ; random
  idur	= p3
  ifreq	= p4
  imeth	= p6
  imethP1	= p7
  imethP2	= p8
  asig pluck ifreq, p5, p5, ifn, imeth, imethP1, imethP2
  kres line 1, idur, 0  ; so tail does not leave DC offset hanging.
  asig = asig * kres
  if (nchnls == 2) then    ; stereo out
    aL, aR pan2 asig, (kloc % 180) * 180 ; pan stereo (0=hardL,1=hardR)
    outs aL, aR
   else out asig ; mono out
   endif
endin """
# import ctcsoud API ; instantiate & initialize the Csound() class 
import ctcsound
cs = ctcsound.Csound ()		# instantiate the Csound() class
cs.setOption("-odac")		# DAC output
cs.setOption("-b 4096")		# output buffer size
cs.setOption("-d")			# suppress displays ; test!
# --------- instantiate the RT perf thread ------------------
csPerf = ctcsound.CsoundPerformanceThread(cs.csound())
cs.readScore("f 0 z \n") 	# keep Csound running for a long time...
# -------- sound "fonts" for "rendering" ---------------------
cs.readScore("f 20 0 0 1 \"sounds/agogo1-H.wav\" 0 0 0 \n")
cs.compileOrc(myOrcOptions) # SR, NrChans 
cs.start()					# start CS synth
csPerf.play()				# start separate performance thread
cs.compileOrc(pluckIt)		# compile the pluckIt instrument
def passCallback():  
    pass					# suppress all terminal output from CS
TRACE = False
if not TRACE:
	pass	#    cs.setMessageCallback(passCallback()) get fix for ctcsound
