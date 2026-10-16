"""Final Q7 verification after re-reading the original distance and rounding rules."""
from fractions import Fraction
angles=[-90+Fraction(p-1,10)*180 for p in [6,10,3]];assert angles==[0,72,-54]
# Distance is 1 m when the echo is detected; the moving robot was farther away at emission.
echo_ms=Fraction(2,1)/(340-Fraction(1,2))*1000
hundredths=-((-echo_ms*100).numerator//(-echo_ms*100).denominator)
assert hundredths==590
print('PASS PWM angles 0/72/-54; echo exact ms',echo_ms,'ceiling at two decimal places',f'{hundredths/100:.2f}')
