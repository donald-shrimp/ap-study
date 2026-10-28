"""Independent calculations and truth-table derivation from original AP pilot questions."""
from fractions import Fraction as F
from math import factorial
# q64: two departments have different hourly rates, same-product activities have equal rates.
quote_rate=F(60,50+100);proposal_rate=F(360,50+400)
assert (quote_rate,proposal_rate)==(F(2,5),F(4,5))
assert (50*quote_rate+50*proposal_rate)*F(20,100)==12
# q76: compare rate denominators, not absolute company sizes.
assert F(800,100)>F(1000,900)
assert F(20,100)>F(90,900)
assert F(20,800)<F(90,1000)
# q52: an internally consistent EVM example has all three given indicators.
EV=F(90);AC=F(100);PV=F(900,11);BAC=F(150)
assert EV/AC==F(9,10) and EV/PV==F(11,10) and (BAC-EV)/(BAC-AC)==F(6,5)
assert AC<BAC  # CPI<1 does not assert that total BAC has already been consumed.
# r07a-q22: all four states in the original waveform are NAND.
observed={(0,0):1,(0,1):1,(1,0):1,(1,1):0}
for (a,b),y in observed.items():assert int(not(a and b))==y
# q7: terminal1 plus recursive argument decrease, independently evaluated for0..8.
def fact(n):return 1 if n==0 else n*fact(n-1)
assert [fact(n) for n in range(9)]==[factorial(n) for n in range(9)]
print('PASS q64 activity cost, q76 all three ratios, q52 consistent EVM counterexample, logic full truth table and factorial0..8')
