#!/usr/bin/env python3
# heizkurve.py
 
_VERSION     = '0.1.0' 
_DESCRIPTION = 'Erzeugt Daten für plot.heatingcurve für Samson Trovis Regler für ATs -25..20 °C'
 
# {{ plot.heatingcurve('heizkurve', 'heizung.rk1.heizkurve.wertepaare', 'heizung.sensoren.af1', 'heizung.sensoren.vf1',
# {
#  chart: {height:'28%', zoomType:'xy'},
#  title: {text:''},
#  legend:{enabled:false},
#  xAxis: {title: {x:0, y:-25}, labels:{y:-5}, min: -25, tickPosition:'inside', tickLength:'2', showLastLabel:false, tickInterval:5, reversed: true},
#  yAxis: {title: {x:40, y:15}, labels:{x:20,y:15}, tickPosition:'inside', tickLength:'2', showFirstLabel:false, max: 40},
#  plotOptions: {series: {color:'#FF0000'}},
#  series:[{className: 'series-1-custom-css'}]
# }
# ) }}
 
# Ausgangsformel:
# 24+Niveau+2*Steigung*(RTsoll-20) - (0,1+0,9*Steigung) * (1,5*(AT-20)+0,01*(AT-20)^2)
 
# Dummy Items, bitte ignorieren
# heizung.sensoren.af1 = 6.2
# heizung.rk1.status.tagbetrieb_rk1 = 1
# heizung.rk1.status.nachtbetrieb_rk1 = 0
# heizung.rk1.heizkurve.niveau = -1
# heizung.rk1.heizkurve.steigung = 0.2
# heizung.rk1.heizkurve.tag_soll = 22
# heizung.rk1.heizkurve.nacht_soll = 19
# heizung.rk1.heizkurve.vorlauf_min = 20
# heizung.rk1.heizkurve.vorlauf_max = 37
 
def heizkurve(sh):
  AT = -25
  KURVE = '['
  if sh.heizung.rk1.status.tagbetrieb_rk1(): SOLL = sh.heizung.rk1.heizkurve.tag_soll()
  else: SOLL = sh.heizung.rk1.heizkurve.nacht_soll()
  while AT < 21:
    VL = 24 + sh.heizung.rk1.heizkurve.niveau() + \
    2 * sh.heizung.rk1.heizkurve.steigung() * (SOLL-20) - \
    (0.1 + 0.9 * sh.heizung.rk1.heizkurve.steigung()) * \
    (1.5*(AT-20) + 0.01 * pow(AT-20,2))
    if VL<sh.heizung.rk1.heizkurve.vorlauf_min(): VL=sh.heizung.rk1.heizkurve.vorlauf_min()
    if VL>sh.heizung.rk1.heizkurve.vorlauf_max(): VL=sh.heizung.rk1.heizkurve.vorlauf_max()
    KURVE=KURVE+'['+str(AT)+','+str(round(VL,1))+'],'
    AT += 1
  KURVE = KURVE[:-1] + ']'
  # sh.heizung.rk1.heizkurve.wertepaare(KURVE)
  return KURVE
