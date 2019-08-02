;----------- SAMPLING FREQUENCY-MODULATION INSTRUMENT -------------
; Reads an audio file into table so samples can be used as FreqMods
;----------- SAMPLING FREQUENCY-MODULATION INSTRUMENT -------------
; filename: codeExample7-1.csd
; Reads an audio file into table so samples can be used as FreqMods
; NB this is the a .csd version of codeExample7-1.orc in the book,
; see the file codeExample7-1.orc for the book version.
; This unified .csd file can be tested with out without a score, using
; $ csound codeExample7-1.orc
; to which a score can be added in the usual place, i.e.
; between <CsScore> </CsScore>, below



<CsoundSynthesizer>
<CsOptions>
-odac 			; write output to built-in DAC
;-Wo "testy.wav"	; write output to file ";" is a comment
</CsOptions>

<CsInstruments>
sr 	= 44100			; sample rate  / second
kr 	= 4410			; control rate / second
ksmps	= 10

ga1 init 0			; init global audio receiver/mixer

instr 1 ; ----------------------- INSTRUMENT 1  -------------------

; ------------- controller inputs/outputs -------------------------
  kgain	invalue	"gain"			; at render time-if possible
  kspread	invalue "spread"	; get pitchSpread from slider
  kCentreHz	invalue	"centreHz"	; centre freq
  ktempo	invalue	"tempo"		; get tempo from slider
  itempo 	= 60/i(ktempo)/2	; get tempo from slider
; -------------------- FM component -------------------------------
  kNoiseOffset	= 3			; listIndex of noisetypes
  kNoiseType	invalue "noiseType"	; choose type to render
  kNoiseTypet	= kNoiseType + kNoiseOffset ; weird indexing
  iNoiseType 	= 3 + i (kNoiseType)
  kNrSamples	invalue "nrSamples"	; get Nr samples to render
  iNrSamples	= 2 * i(kNrSamples)	; Nr samples in the file
  kmixpercent	invalue "reverb"	; NB also fed 2 reverb instr.
					; 2 control OP % of dry sig
; -------------------- FM component -------------------------------
  kCnt 	= 0
  ; Create index into GEN01sampleArray to be ++ed, accord to tempo
  kcps init 1/(iNrSamples * itempo)	; Nrsamples in the file; 5725
  kndx phasor kcps		; kndx=(0-1) norm(sampTable (index))
  kCnt = kCnt +1			; pick new samp every ‘beat’
  printks "\nknsx = %f, ", 10, kndx
  ktabOP tab kndx, iNoiseType, 1
  kFreq = kCentreHz * powoftwo (kspread/2 * ktabOP/12)
; printks "Cnt=%6.1f  tabVal=%5.3f Fq=%5.3f\n",kCnt,1,ktabOP, kFreq
  a1 oscili kgain, kFreq, 1	; Sine: tableValss to FMcentreHz.
  out a1 * 1-(kmixpercent/100)	; and output the result
  ga1 = ga1 + a1			; OP to global buff
endin
instr 2 ; --------------- INSTRUMENT 2  --------------------------
; ----------------- controller inputs/outputs --------------------
  kgain	invalue "gain"			; gain of FM samples
  kgainPcnt	invalue "regisGain"	; %FM samp.gain 4tick regs
  kregisGain = kgain * kgainPcnt/100 
  kregisRate 	invalue	"regisRate"	; repeat rate of ticks
  kspread	invalue "spread"	; get pitch spread in ST
  kCentreHz	invalue	"centreHz"	; centre freq
  outvalue	"lowerHz", kCentreHz - powoftwo (kspread/24)
  outvalue	"upperHz", kCentreHz + powoftwo (kspread/24)
  a1 oscil kregisGain, kregisRate,1	; FM kCentrHz by set amount
  a1 oscili a1, kCentreHz, 1		; a sine, using centreHz.
endin
instr 99 ; ----------- INSTRUMENT 99 -- REVERB  ------------------
  kreverbtime	invalue	"reverbTime"
  kmixpercent	invalue	"reverb"
  a3 reverb ga1, kreverbtime		; reverberate what is in ga1
  out a3 * (kmixpercent/100)		; and output the result
  ga1 = 0				; empty receiver for next pass
endin ;----------------------- FIN -------------------------------
</CsInstruments>

<CsScore>
</CsScore>
<CsoundSynthesizer>

