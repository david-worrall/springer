
<CsoundSynthesizer>
; an extremely simple Csound  .csd file, Instrument definition and Score definitions
<CsOptions>
-odac 			; write output to built-in DAC
;-Wo "testy.wav"	; write output to file ";" is a comment
</CsOptions>
<CsInstruments>
sr=48000		; sampling rate
ksmps=32		; nr of samples in an audio buffer
nchnls=2		; 2 output channels
0dbfs=1		; set the maximum db value to 1

instr 1 		; the beginning the instrument definition
iamp = 0.5		; line 2
icps = 440		; line 3
asig oscili iamp, icps 	; line 4
aout vco2 0.5, p4	; line 5
;out(asig+aout)		; for mono out
outs asig, aout         ; write aout to a stereo output buffer
endin			;  the end instrument definition 1 

</CsInstruments>
<CsScore>

i1 0     0.2 205
i1 0.75  0.3 500
i1 1.25  0.4 700
e
</CsScore>

</CsoundSynthesizer>
