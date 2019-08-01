myOrc = """
instr 1
   idur = p3
   iamp = p4
   icps = p5
   ksig = linen(iamp,0.1,idur,0.2)
   asig = oscili(ksig, icps)
   out(asig)
endin
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


