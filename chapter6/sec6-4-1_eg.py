myOrc = """
instr 1
; p1 = instrument number 
; p2 = start time
idur = p3  ; duration
iamp = p4  ; amplitude NB by default, 0dbfs is the max amplitude
icps = p5  ; pitch
ksig = linen(iamp,0.1,idur,0.2)
asig = oscili(ksig, icps)
out(asig)
endin 		; In the text, this line appears just before the end 
		; of this string (after 1760 here). That is a  typo!

;        p1 p2 p3	 p4	  p5
schedule 1, 0, 1,        0dbfs/3,  440
schedule 1, 1, 1,        0dbfs/3, 1100
schedule 1, 1.75, 0.5,   0dbfs/3,  660
schedule 1, 2.25, 0.25,  0dbfs/3,  880
schedule 1, 2.5,  1,     0dbfs/3, 1760
"""
import ctcsound
cs = ctcsound.Csound()
cs.setOption('-odac')
cs.compileOrc(myOrc)
cs.start()
cs.perform()


