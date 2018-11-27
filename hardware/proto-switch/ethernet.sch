EESchema Schematic File Version 4
LIBS:proto-switch-cache
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 3 5
Title "TBGe Switch Prototype"
Date "2018-11-24"
Rev "1"
Comp ""
Comment1 "Drawn by: Adam Greig"
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L agg:RJHSE-538x J302
U 1 1 5C475CF2
P 1800 2900
F 0 "J302" H 1400 3400 50  0000 L CNN
F 1 "RJHSE-538x" H 1400 2400 50  0000 L CNN
F 2 "agg:RJHSE-538X" H 1400 2300 50  0001 L CNN
F 3 "" H 1400 2200 50  0001 L CNN
F 4 "1462758" H 1400 2100 50  0001 L CNN "Farnell"
	1    1800 2900
	1    0    0    1   
$EndComp
$Comp
L agg:749010012A T301
U 1 1 5C47818D
P 3750 3000
F 0 "T301" H 3550 3600 50  0000 L CNN
F 1 "749013011A" H 3550 2400 50  0000 L CNN
F 2 "agg:749010012A" H 3550 2300 50  0001 L CNN
F 3 "" H 3550 2200 50  0001 L CNN
F 4 "2422553" H 3550 2100 50  0001 L CNN "Farnell"
	1    3750 3000
	-1   0    0    -1  
$EndComp
$Comp
L Diode_Bridge:MB2S D302
U 1 1 5C4792BD
P 2150 5600
F 0 "D302" H 2250 5875 50  0000 L CNN
F 1 "MB2S" H 2250 5800 50  0000 L CNN
F 2 "agg:TO-269AA" H 2300 5725 50  0001 L CNN
F 3 "http://www.vishay.com/docs/88661/mb2s.pdf" H 2150 5600 50  0001 C CNN
F 4 "9550003" H 2150 5600 50  0001 C CNN "Farnell"
	1    2150 5600
	0    -1   -1   0   
$EndComp
$Comp
L Diode_Bridge:MB2S D303
U 1 1 5C47A00B
P 3300 5600
F 0 "D303" H 3400 5875 50  0000 L CNN
F 1 "MB2S" H 3400 5800 50  0000 L CNN
F 2 "agg:TO-269AA" H 3450 5725 50  0001 L CNN
F 3 "http://www.vishay.com/docs/88661/mb2s.pdf" H 3300 5600 50  0001 C CNN
F 4 "9550003" H 3300 5600 50  0001 C CNN "Farnell"
	1    3300 5600
	0    -1   -1   0   
$EndComp
$Comp
L agg:C C307
U 1 1 5C4807DF
P 4550 3300
F 0 "C307" H 4600 3370 50  0000 C CNN
F 1 "100n" H 4600 3230 50  0000 C CNN
F 2 "agg:0603" H 4550 3300 50  0001 C CNN
F 3 "" H 4550 3300 50  0001 C CNN
F 4 "431989" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    4550 3300
	0    1    1    0   
$EndComp
$Comp
L agg:C C308
U 1 1 5C481163
P 4800 3300
F 0 "C308" H 4850 3370 50  0000 C CNN
F 1 "100n" H 4850 3230 50  0000 C CNN
F 2 "agg:0603" H 4800 3300 50  0001 C CNN
F 3 "" H 4800 3300 50  0001 C CNN
F 4 "431989" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    4800 3300
	0    1    1    0   
$EndComp
$Comp
L agg:MAX5969x IC303
U 1 1 5C482C06
P 5450 5600
F 0 "IC303" H 5150 6100 50  0000 L CNN
F 1 "MAX5969x" H 5150 5100 50  0000 L CNN
F 2 "agg:DFN-10-EP-MAX" H 5150 5000 50  0001 L CNN
F 3 "" H 5150 4900 50  0001 L CNN
F 4 "2514586" H 5150 4800 50  0001 L CNN "Farnell"
	1    5450 5600
	1    0    0    -1  
$EndComp
$Comp
L agg:R R316
U 1 1 5C48382C
P 4550 5300
F 0 "R316" H 4600 5350 50  0000 C CNN
F 1 "24k9" H 4600 5250 50  0000 C CNN
F 2 "agg:0402" H 4550 5300 50  0001 C CNN
F 3 "" H 4550 5300 50  0001 C CNN
F 4 "1469699" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    4550 5300
	0    1    1    0   
$EndComp
$Comp
L agg:R R317
U 1 1 5C483AC6
P 4550 5750
F 0 "R317" H 4600 5800 50  0000 C CNN
F 1 "619" H 4600 5700 50  0000 C CNN
F 2 "agg:0402" H 4550 5750 50  0001 C CNN
F 3 "" H 4550 5750 50  0001 C CNN
F 4 "2302613" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    4550 5750
	0    1    1    0   
$EndComp
$Comp
L agg:SCHOTTKY D301
U 1 1 5C486150
P 4050 5550
F 0 "D301" H 4100 5620 50  0000 C CNN
F 1 "SMAJ58A" H 4100 5480 50  0000 C CNN
F 2 "agg:DO-214AC-SMA" H 4000 5520 50  0001 C CNN
F 3 "http://www.farnell.com/datasheets/2076055.pdf" H 4100 5620 50  0001 C CNN
F 4 "1899460" H 4050 5550 50  0001 C CNN "Farnell"
	1    4050 5550
	0    1    1    0   
$EndComp
$Comp
L agg:C C313
U 1 1 5C486828
P 4300 5550
F 0 "C313" H 4350 5620 50  0000 C CNN
F 1 "100n 60V" H 4350 5480 50  0000 C CNN
F 2 "agg:0805" H 4300 5550 50  0001 C CNN
F 3 "http://www.farnell.com/datasheets/1958513.pdf" H 4300 5550 50  0001 C CNN
F 4 "2496941" H 4300 5550 50  0001 C CNN "Farnell"
	1    4300 5550
	0    1    1    0   
$EndComp
$Comp
L agg:C C301
U 1 1 5C48CB5B
P 4800 1500
F 0 "C301" H 4850 1570 50  0000 C CNN
F 1 "22µ" H 4850 1430 50  0000 C CNN
F 2 "agg:1206" H 4800 1500 50  0001 C CNN
F 3 "" H 4800 1500 50  0001 C CNN
F 4 "2320923" H 0   0   50  0001 C CNN "Farnell"
F 5 "16" H 0   0   50  0001 C CNN "Voltage"
	1    4800 1500
	0    1    1    0   
$EndComp
$Comp
L agg:C C302
U 1 1 5C48D0D0
P 5050 1500
F 0 "C302" H 5100 1570 50  0000 C CNN
F 1 "100n" H 5100 1430 50  0000 C CNN
F 2 "agg:0402" H 5050 1500 50  0001 C CNN
F 3 "" H 5050 1500 50  0001 C CNN
F 4 "2528765" H 0   0   50  0001 C CNN "Farnell"
F 5 "16" H 0   0   50  0001 C CNN "Voltage"
	1    5050 1500
	0    1    1    0   
$EndComp
$Comp
L agg:L L301
U 1 1 5C48D3B3
P 4850 1300
F 0 "L301" V 4950 1350 50  0000 L CNN
F 1 "FB" V 4850 1350 50  0000 L CNN
F 2 "agg:0603" H 4850 1300 50  0001 C CNN
F 3 "" H 4850 1300 50  0001 C CNN
F 4 "1463451" H 0   0   50  0001 C CNN "Farnell"
	1    4850 1300
	0    1    1    0   
$EndComp
$Comp
L agg:3v3 #PWR0135
U 1 1 5C48DD5D
P 4850 1250
F 0 "#PWR0135" H 4850 1360 50  0001 L CNN
F 1 "3v3" H 4850 1340 50  0000 C CNN
F 2 "" H 4850 1250 50  0001 C CNN
F 3 "" H 4850 1250 50  0001 C CNN
	1    4850 1250
	1    0    0    -1  
$EndComp
$Comp
L agg:C C303
U 1 1 5C48E0E8
P 4600 2000
F 0 "C303" H 4650 2070 50  0000 C CNN
F 1 "22µ" H 4650 1930 50  0000 C CNN
F 2 "agg:1206" H 4600 2000 50  0001 C CNN
F 3 "" H 4600 2000 50  0001 C CNN
F 4 "2320923" H 0   0   50  0001 C CNN "Farnell"
F 5 "16" H 0   0   50  0001 C CNN "Voltage"
	1    4600 2000
	0    1    1    0   
$EndComp
$Comp
L agg:C C304
U 1 1 5C48E5C4
P 4850 2000
F 0 "C304" H 4900 2070 50  0000 C CNN
F 1 "100n" H 4900 1930 50  0000 C CNN
F 2 "agg:0402" H 4850 2000 50  0001 C CNN
F 3 "" H 4850 2000 50  0001 C CNN
F 4 "2528765" H 0   0   50  0001 C CNN "Farnell"
F 5 "16" H 0   0   50  0001 C CNN "Voltage"
	1    4850 2000
	0    1    1    0   
$EndComp
$Comp
L agg:C C305
U 1 1 5C48EA19
P 5000 2200
F 0 "C305" H 5050 2270 50  0000 C CNN
F 1 "2µ2" H 5050 2130 50  0000 C CNN
F 2 "agg:0603" H 5000 2200 50  0001 C CNN
F 3 "" H 5000 2200 50  0001 C CNN
F 4 "2320817" H 0   0   50  0001 C CNN "Farnell"
F 5 "10" H 0   0   50  0001 C CNN "Voltage"
	1    5000 2200
	0    1    1    0   
$EndComp
$Comp
L agg:C C306
U 1 1 5C48ED9E
P 5250 2200
F 0 "C306" H 5300 2270 50  0000 C CNN
F 1 "100n" H 5300 2130 50  0000 C CNN
F 2 "agg:0402" H 5250 2200 50  0001 C CNN
F 3 "" H 5250 2200 50  0001 C CNN
F 4 "2528765" H 0   0   50  0001 C CNN "Farnell"
F 5 "16" H 0   0   50  0001 C CNN "Voltage"
	1    5250 2200
	0    1    1    0   
$EndComp
$Comp
L agg:R R301
U 1 1 5C48F71A
P 6700 1850
F 0 "R301" H 6750 1900 50  0000 C CNN
F 1 "33" H 6750 1800 50  0000 C CNN
F 2 "agg:0402" H 6700 1850 50  0001 C CNN
F 3 "" H 6700 1850 50  0001 C CNN
F 4 "2302472" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6700 1850
	1    0    0    -1  
$EndComp
$Comp
L agg:R R302
U 1 1 5C4913C6
P 6850 1950
F 0 "R302" H 6900 2000 50  0000 C CNN
F 1 "33" H 6900 1900 50  0000 C CNN
F 2 "agg:0402" H 6850 1950 50  0001 C CNN
F 3 "" H 6850 1950 50  0001 C CNN
F 4 "2302472" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6850 1950
	1    0    0    -1  
$EndComp
$Comp
L agg:R R303
U 1 1 5C49174E
P 6700 2050
F 0 "R303" H 6750 2100 50  0000 C CNN
F 1 "33" H 6750 2000 50  0000 C CNN
F 2 "agg:0402" H 6700 2050 50  0001 C CNN
F 3 "" H 6700 2050 50  0001 C CNN
F 4 "2302472" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6700 2050
	1    0    0    -1  
$EndComp
$Comp
L agg:R R304
U 1 1 5C4919F0
P 6850 2150
F 0 "R304" H 6900 2200 50  0000 C CNN
F 1 "33" H 6900 2100 50  0000 C CNN
F 2 "agg:0402" H 6850 2150 50  0001 C CNN
F 3 "" H 6850 2150 50  0001 C CNN
F 4 "2302472" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6850 2150
	1    0    0    -1  
$EndComp
$Comp
L agg:R R308
U 1 1 5C491F66
P 7500 2600
F 0 "R308" H 7550 2650 50  0000 C CNN
F 1 "1k" H 7550 2550 50  0000 C CNN
F 2 "agg:0402" H 7500 2600 50  0001 C CNN
F 3 "" H 7500 2600 50  0001 C CNN
F 4 "2331474" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    7500 2600
	0    1    1    0   
$EndComp
$Comp
L agg:R R309
U 1 1 5C4928D3
P 6800 3050
F 0 "R309" H 6850 3100 50  0000 C CNN
F 1 "6k49" H 6850 3000 50  0000 C CNN
F 2 "agg:0402" H 6800 3050 50  0001 C CNN
F 3 "" H 6800 3050 50  0001 C CNN
F 4 "2302722" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6800 3050
	-1   0    0    1   
$EndComp
NoConn ~ 6600 3150
Wire Wire Line
	3450 2500 2900 2500
Wire Wire Line
	2900 2500 2900 2600
Wire Wire Line
	2900 2600 2300 2600
Wire Wire Line
	2300 2700 3450 2700
Wire Wire Line
	2300 2800 2900 2800
Wire Wire Line
	2900 2800 2900 2900
Wire Wire Line
	2900 2900 3450 2900
Wire Wire Line
	2300 3100 3450 3100
$Comp
L agg:CHASSIS #PWR0136
U 1 1 5C49B5B7
P 1250 2700
F 0 "#PWR0136" H 1120 2740 50  0001 L CNN
F 1 "CHASSIS" H 1250 2600 50  0000 C CNN
F 2 "" H 1250 2700 50  0001 C CNN
F 3 "" H 1250 2700 50  0001 C CNN
	1    1250 2700
	0    1    1    0   
$EndComp
Wire Wire Line
	1250 2700 1300 2700
Wire Wire Line
	2300 3200 2500 3200
Wire Wire Line
	2300 3300 2500 3300
Wire Wire Line
	2500 3200 2500 3300
Connection ~ 2500 3300
Wire Wire Line
	2500 3300 2650 3300
Text Label 2650 3300 0    50   ~ 0
VB1
Wire Wire Line
	2300 3000 2500 3000
Text Label 2650 3000 0    50   ~ 0
VB2
Wire Wire Line
	2300 2900 2500 2900
Wire Wire Line
	2500 2900 2500 3000
Connection ~ 2500 3000
Wire Wire Line
	2500 3000 2650 3000
Wire Wire Line
	3450 3000 3150 3000
Text Label 3150 3000 2    50   ~ 0
VA2
Wire Wire Line
	3450 2600 3150 2600
Text Label 3150 2600 2    50   ~ 0
VA1
Wire Wire Line
	4550 3300 4550 3000
Wire Wire Line
	4800 2600 4800 3300
$Comp
L agg:GND #PWR0137
U 1 1 5C4A00A2
P 4550 3500
F 0 "#PWR0137" H 4420 3540 50  0001 L CNN
F 1 "GND" H 4550 3400 50  0000 C CNN
F 2 "" H 4550 3500 50  0001 C CNN
F 3 "" H 4550 3500 50  0001 C CNN
	1    4550 3500
	1    0    0    -1  
$EndComp
Wire Wire Line
	4550 3500 4550 3400
$Comp
L agg:GND #PWR0138
U 1 1 5C4A05AA
P 4800 3500
F 0 "#PWR0138" H 4670 3540 50  0001 L CNN
F 1 "GND" H 4800 3400 50  0000 C CNN
F 2 "" H 4800 3500 50  0001 C CNN
F 3 "" H 4800 3500 50  0001 C CNN
	1    4800 3500
	1    0    0    -1  
$EndComp
Wire Wire Line
	4800 3500 4800 3400
Wire Wire Line
	4050 2500 4300 2500
Wire Wire Line
	4050 2700 4300 2700
Wire Wire Line
	4050 2900 4300 2900
Wire Wire Line
	4050 2600 4800 2600
Wire Wire Line
	4050 3000 4550 3000
Wire Wire Line
	4050 3100 4300 3100
Text Label 4300 3100 0    50   ~ 0
RD-
Text Label 4300 2500 0    50   ~ 0
TD+
Text Label 4300 2700 0    50   ~ 0
TD-
Text Label 4300 2900 0    50   ~ 0
RD+
Wire Wire Line
	5400 2650 5300 2650
Wire Wire Line
	5300 2750 5400 2750
Wire Wire Line
	5400 2850 5300 2850
Wire Wire Line
	5300 2950 5400 2950
Text Label 5300 2950 2    50   ~ 0
TD+
Text Label 5300 2850 2    50   ~ 0
TD-
Text Label 5300 2750 2    50   ~ 0
RD+
Text Label 5300 2650 2    50   ~ 0
RD-
$Comp
L agg:GND #PWR0139
U 1 1 5C4BFA84
P 5000 2500
F 0 "#PWR0139" H 4870 2540 50  0001 L CNN
F 1 "GND" H 5000 2400 50  0000 C CNN
F 2 "" H 5000 2500 50  0001 C CNN
F 3 "" H 5000 2500 50  0001 C CNN
	1    5000 2500
	1    0    0    -1  
$EndComp
Wire Wire Line
	5000 2500 5000 2450
Wire Wire Line
	5000 2450 5250 2450
Wire Wire Line
	5400 2350 5300 2350
Wire Wire Line
	5300 2350 5300 2450
Connection ~ 5300 2450
Wire Wire Line
	5300 2450 5400 2450
Wire Wire Line
	5400 2150 5250 2150
Wire Wire Line
	5000 2150 5000 2200
Wire Wire Line
	5250 2150 5250 2200
Connection ~ 5250 2150
Wire Wire Line
	5250 2150 5000 2150
Wire Wire Line
	5250 2300 5250 2450
Connection ~ 5250 2450
Wire Wire Line
	5250 2450 5300 2450
Wire Wire Line
	5000 2300 5000 2450
Connection ~ 5000 2450
$Comp
L agg:GND #PWR0140
U 1 1 5C4C6A71
P 4600 2200
F 0 "#PWR0140" H 4470 2240 50  0001 L CNN
F 1 "GND" H 4600 2100 50  0000 C CNN
F 2 "" H 4600 2200 50  0001 C CNN
F 3 "" H 4600 2200 50  0001 C CNN
	1    4600 2200
	1    0    0    -1  
$EndComp
Wire Wire Line
	4600 2200 4600 2150
Wire Wire Line
	4600 2150 4850 2150
Wire Wire Line
	4850 2150 4850 2100
Connection ~ 4600 2150
Wire Wire Line
	4600 2150 4600 2100
Wire Wire Line
	5400 1950 4850 1950
Wire Wire Line
	4600 1950 4600 2000
Wire Wire Line
	4850 2000 4850 1950
Connection ~ 4850 1950
Wire Wire Line
	4850 1950 4600 1950
$Comp
L agg:3v3 #PWR0141
U 1 1 5C4C9EEA
P 4600 1900
F 0 "#PWR0141" H 4600 2010 50  0001 L CNN
F 1 "3v3" H 4600 1990 50  0000 C CNN
F 2 "" H 4600 1900 50  0001 C CNN
F 3 "" H 4600 1900 50  0001 C CNN
	1    4600 1900
	1    0    0    -1  
$EndComp
Wire Wire Line
	4600 1900 4600 1950
Connection ~ 4600 1950
$Comp
L agg:GND #PWR0142
U 1 1 5C4CC5BB
P 4800 1700
F 0 "#PWR0142" H 4670 1740 50  0001 L CNN
F 1 "GND" H 4800 1600 50  0000 C CNN
F 2 "" H 4800 1700 50  0001 C CNN
F 3 "" H 4800 1700 50  0001 C CNN
	1    4800 1700
	1    0    0    -1  
$EndComp
Wire Wire Line
	4800 1700 4800 1650
Wire Wire Line
	4800 1650 5050 1650
Wire Wire Line
	5050 1650 5050 1600
Connection ~ 4800 1650
Wire Wire Line
	4800 1650 4800 1600
Wire Wire Line
	4850 1250 4850 1300
Wire Wire Line
	4800 1500 4800 1450
Wire Wire Line
	4800 1450 4850 1450
Wire Wire Line
	5050 1450 5050 1500
Wire Wire Line
	4850 1400 4850 1450
Connection ~ 4850 1450
Wire Wire Line
	4850 1450 5050 1450
Wire Wire Line
	5050 1450 5150 1450
Wire Wire Line
	5250 1450 5250 1850
Wire Wire Line
	5250 1850 5400 1850
Connection ~ 5050 1450
$Comp
L agg:PWR #FLG0105
U 1 1 5C4D7568
P 5150 1400
F 0 "#FLG0105" H 5150 1560 50  0001 C CNN
F 1 "PWR" H 5150 1490 50  0001 C CNN
F 2 "" H 5150 1400 50  0001 C CNN
F 3 "" H 5150 1400 50  0001 C CNN
	1    5150 1400
	1    0    0    -1  
$EndComp
Wire Wire Line
	5150 1400 5150 1450
Connection ~ 5150 1450
Wire Wire Line
	5150 1450 5250 1450
Wire Wire Line
	6600 1850 6700 1850
Wire Wire Line
	6600 1950 6850 1950
Wire Wire Line
	6600 2050 6700 2050
Wire Wire Line
	6600 2150 6850 2150
NoConn ~ 6600 2250
Text HLabel 7100 1850 2    50   Output ~ 0
RXD1
Text HLabel 7100 1950 2    50   Output ~ 0
RXD0
Text HLabel 7100 2050 2    50   Output ~ 0
CRS_DV
Text HLabel 7100 2150 2    50   Output ~ 0
REF_CLK
Text HLabel 7100 2350 2    50   Input ~ 0
TXEN
Text HLabel 7100 2450 2    50   Input ~ 0
TXD0
Text HLabel 7100 2550 2    50   Input ~ 0
TXD1
Wire Wire Line
	7100 2350 6800 2350
Wire Wire Line
	6600 2450 6850 2450
Wire Wire Line
	7100 2550 6800 2550
Text Notes 7550 2150 0    50   ~ 0
Series termination resistors must\nbe placed near corresponding source;\nRX*, CRS_DV, REF_CLK near PHY;\nTX* near MAC.
Wire Wire Line
	6800 1850 7100 1850
Wire Wire Line
	7100 1950 6950 1950
Wire Wire Line
	6800 2050 7100 2050
Wire Wire Line
	7100 2150 6950 2150
$Comp
L agg:3v3 #PWR0143
U 1 1 5C4EB561
P 7500 2550
F 0 "#PWR0143" H 7500 2660 50  0001 L CNN
F 1 "3v3" H 7500 2640 50  0000 C CNN
F 2 "" H 7500 2550 50  0001 C CNN
F 3 "" H 7500 2550 50  0001 C CNN
	1    7500 2550
	1    0    0    -1  
$EndComp
Wire Wire Line
	7500 2550 7500 2600
Wire Wire Line
	6600 2750 7500 2750
Wire Wire Line
	7500 2750 7500 2700
Text HLabel 7650 2750 2    50   BiDi ~ 0
MDIO
Wire Wire Line
	7650 2750 7500 2750
Connection ~ 7500 2750
Text HLabel 7650 2850 2    50   Input ~ 0
MDC
Wire Wire Line
	7650 2850 6600 2850
$Comp
L agg:GND #PWR0144
U 1 1 5C4F3035
P 6900 3050
F 0 "#PWR0144" H 6770 3090 50  0001 L CNN
F 1 "GND" H 6900 2950 50  0000 C CNN
F 2 "" H 6900 3050 50  0001 C CNN
F 3 "" H 6900 3050 50  0001 C CNN
	1    6900 3050
	0    -1   -1   0   
$EndComp
Wire Wire Line
	6900 3050 6800 3050
Wire Wire Line
	6700 3050 6600 3050
Wire Wire Line
	6900 3250 6600 3250
$Comp
L agg:R R311
U 1 1 5C4F8DE9
P 6700 3500
F 0 "R311" H 6750 3550 50  0000 C CNN
F 1 "10k" H 6750 3450 50  0000 C CNN
F 2 "agg:0402" H 6700 3500 50  0001 C CNN
F 3 "" H 6700 3500 50  0001 C CNN
F 4 "2302739" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6700 3500
	0    -1   -1   0   
$EndComp
$Comp
L agg:GND #PWR0145
U 1 1 5C4F9675
P 6700 3550
F 0 "#PWR0145" H 6570 3590 50  0001 L CNN
F 1 "GND" H 6700 3450 50  0000 C CNN
F 2 "" H 6700 3550 50  0001 C CNN
F 3 "" H 6700 3550 50  0001 C CNN
	1    6700 3550
	1    0    0    -1  
$EndComp
Wire Wire Line
	6700 3550 6700 3500
Wire Wire Line
	6600 3350 6700 3350
Wire Wire Line
	6700 3350 6700 3400
Text HLabel 6900 3350 2    50   Input ~ 0
~RST
Wire Wire Line
	6900 3350 6700 3350
Connection ~ 6700 3350
$Comp
L agg:C C309
U 1 1 5C501D20
P 1450 3800
F 0 "C309" H 1500 3870 50  0000 C CNN
F 1 "DNF" H 1500 3730 50  0000 C CNN
F 2 "agg:0805" H 1450 3800 50  0001 C CNN
F 3 "" H 1450 3800 50  0001 C CNN
	1    1450 3800
	0    1    1    0   
$EndComp
$Comp
L agg:R R312
U 1 1 5C503DE8
P 1450 4000
F 0 "R312" H 1500 4050 50  0000 C CNN
F 1 "DNF" H 1500 3950 50  0000 C CNN
F 2 "agg:0603" H 1450 4000 50  0001 C CNN
F 3 "" H 1450 4000 50  0001 C CNN
	1    1450 4000
	0    1    1    0   
$EndComp
$Comp
L agg:C C310
U 1 1 5C5055D0
P 1700 3800
F 0 "C310" H 1750 3870 50  0000 C CNN
F 1 "DNF" H 1750 3730 50  0000 C CNN
F 2 "agg:0805" H 1700 3800 50  0001 C CNN
F 3 "" H 1700 3800 50  0001 C CNN
	1    1700 3800
	0    1    1    0   
$EndComp
$Comp
L agg:R R313
U 1 1 5C5055DA
P 1700 4000
F 0 "R313" H 1750 4050 50  0000 C CNN
F 1 "DNF" H 1750 3950 50  0000 C CNN
F 2 "agg:0603" H 1700 4000 50  0001 C CNN
F 3 "" H 1700 4000 50  0001 C CNN
	1    1700 4000
	0    1    1    0   
$EndComp
$Comp
L agg:C C311
U 1 1 5C507F0B
P 2000 3800
F 0 "C311" H 2050 3870 50  0000 C CNN
F 1 "DNF" H 2050 3730 50  0000 C CNN
F 2 "agg:0805" H 2000 3800 50  0001 C CNN
F 3 "" H 2000 3800 50  0001 C CNN
	1    2000 3800
	0    1    1    0   
$EndComp
$Comp
L agg:R R314
U 1 1 5C507F15
P 2000 4000
F 0 "R314" H 2050 4050 50  0000 C CNN
F 1 "DNF" H 2050 3950 50  0000 C CNN
F 2 "agg:0603" H 2000 4000 50  0001 C CNN
F 3 "" H 2000 4000 50  0001 C CNN
	1    2000 4000
	0    1    1    0   
$EndComp
$Comp
L agg:C C312
U 1 1 5C507F1F
P 2250 3800
F 0 "C312" H 2300 3870 50  0000 C CNN
F 1 "DNF" H 2300 3730 50  0000 C CNN
F 2 "agg:0805" H 2250 3800 50  0001 C CNN
F 3 "" H 2250 3800 50  0001 C CNN
	1    2250 3800
	0    1    1    0   
$EndComp
$Comp
L agg:R R315
U 1 1 5C507F29
P 2250 4000
F 0 "R315" H 2300 4050 50  0000 C CNN
F 1 "DNF" H 2300 3950 50  0000 C CNN
F 2 "agg:0603" H 2250 4000 50  0001 C CNN
F 3 "" H 2250 4000 50  0001 C CNN
	1    2250 4000
	0    1    1    0   
$EndComp
Wire Wire Line
	1450 4100 1450 4200
Wire Wire Line
	1450 4200 1700 4200
Wire Wire Line
	2250 4200 2250 4100
Wire Wire Line
	2000 4100 2000 4200
Connection ~ 2000 4200
Wire Wire Line
	2000 4200 2250 4200
Wire Wire Line
	1700 4100 1700 4200
$Comp
L agg:CHASSIS #PWR0146
U 1 1 5C511DB1
P 1850 4300
F 0 "#PWR0146" H 1720 4340 50  0001 L CNN
F 1 "CHASSIS" H 1850 4200 50  0000 C CNN
F 2 "" H 1850 4300 50  0001 C CNN
F 3 "" H 1850 4300 50  0001 C CNN
	1    1850 4300
	1    0    0    -1  
$EndComp
Wire Wire Line
	1700 4200 1850 4200
Connection ~ 1700 4200
Wire Wire Line
	1850 4300 1850 4200
Connection ~ 1850 4200
Wire Wire Line
	1850 4200 2000 4200
Wire Wire Line
	1450 3900 1450 4000
Wire Wire Line
	1700 3900 1700 4000
Wire Wire Line
	2000 3900 2000 4000
Wire Wire Line
	2250 3900 2250 4000
Wire Wire Line
	1450 3800 1450 3700
Wire Wire Line
	1450 3700 1400 3700
Wire Wire Line
	1700 3800 1700 3700
Wire Wire Line
	1700 3700 1650 3700
Wire Wire Line
	2000 3800 2000 3700
Wire Wire Line
	2000 3700 2050 3700
Wire Wire Line
	2250 3800 2250 3700
Wire Wire Line
	2250 3700 2300 3700
Text Label 1400 3700 2    50   ~ 0
VB1
Text Label 1650 3700 2    50   ~ 0
VB2
Text Label 2300 3700 0    50   ~ 0
VA2
Text Label 2050 3700 0    50   ~ 0
VA1
Text Notes 1350 4800 0    50   ~ 0
Modified Bob Smith terminations.\nDo not fit unless required.\nCapacitors: 10nF 200V\nResistors: 75R
Text Label 1750 5600 2    50   ~ 0
VA1
Text Label 2550 5600 0    50   ~ 0
VA2
Text Label 2900 5600 2    50   ~ 0
VB1
Text Label 3700 5600 0    50   ~ 0
VB2
Wire Wire Line
	1750 5600 1850 5600
Wire Wire Line
	2550 5600 2450 5600
Wire Wire Line
	2900 5600 3000 5600
Wire Wire Line
	3700 5600 3600 5600
Wire Wire Line
	2150 5200 3300 5200
Wire Wire Line
	4300 5200 4300 5550
Wire Wire Line
	2150 5200 2150 5300
Wire Wire Line
	2150 5900 2150 6000
Wire Wire Line
	2150 6000 3300 6000
Wire Wire Line
	4300 6000 4300 5650
Wire Wire Line
	4050 5650 4050 6000
Connection ~ 4050 6000
Wire Wire Line
	4050 6000 4300 6000
Wire Wire Line
	4050 5550 4050 5200
Connection ~ 4050 5200
Wire Wire Line
	4050 5200 4300 5200
Wire Wire Line
	3300 5300 3300 5200
Connection ~ 3300 5200
Wire Wire Line
	3300 5200 4050 5200
Wire Wire Line
	3300 5900 3300 6000
Connection ~ 3300 6000
Wire Wire Line
	3300 6000 4050 6000
$Comp
L agg:PWR #FLG0106
U 1 1 5C5AE454
P 4300 5150
F 0 "#FLG0106" H 4300 5310 50  0001 C CNN
F 1 "PWR" H 4300 5240 50  0001 C CNN
F 2 "" H 4300 5150 50  0001 C CNN
F 3 "" H 4300 5150 50  0001 C CNN
	1    4300 5150
	1    0    0    -1  
$EndComp
Wire Wire Line
	4300 5150 4300 5200
Connection ~ 4300 5200
$Comp
L agg:PWR #FLG0107
U 1 1 5C5B3471
P 4300 6050
F 0 "#FLG0107" H 4300 6210 50  0001 C CNN
F 1 "PWR" H 4300 6140 50  0001 C CNN
F 2 "" H 4300 6050 50  0001 C CNN
F 3 "" H 4300 6050 50  0001 C CNN
	1    4300 6050
	-1   0    0    1   
$EndComp
Wire Wire Line
	4300 6050 4300 6000
Connection ~ 4300 6000
Wire Wire Line
	4300 6000 4550 6000
Wire Wire Line
	4550 6000 4550 5850
Wire Wire Line
	4550 5750 4550 5700
Wire Wire Line
	4550 5700 5050 5700
Wire Wire Line
	4550 5400 4550 5600
Wire Wire Line
	4550 5600 5050 5600
Wire Wire Line
	5050 5300 4850 5300
Wire Wire Line
	4850 5300 4850 5400
Wire Wire Line
	4850 6000 4550 6000
Connection ~ 4550 6000
Wire Wire Line
	5050 5400 4850 5400
Connection ~ 4850 5400
Wire Wire Line
	4850 5400 4850 6000
Wire Wire Line
	4300 5200 4550 5200
Wire Wire Line
	4850 5050 4850 5200
Connection ~ 4850 5200
Wire Wire Line
	4850 5200 5050 5200
Text HLabel 6200 4850 2    50   Output ~ 0
48VDC
Wire Wire Line
	4850 4950 4850 4850
$Comp
L agg:PWR #FLG0108
U 1 1 5C609AAB
P 4850 4800
F 0 "#FLG0108" H 4850 4960 50  0001 C CNN
F 1 "PWR" H 4850 4890 50  0001 C CNN
F 2 "" H 4850 4800 50  0001 C CNN
F 3 "" H 4850 4800 50  0001 C CNN
	1    4850 4800
	1    0    0    -1  
$EndComp
Wire Wire Line
	4850 4800 4850 4850
Connection ~ 4850 4850
Text HLabel 6200 5500 2    50   Output ~ 0
PG
NoConn ~ 5850 5200
Text HLabel 6200 5600 2    50   Output ~ 0
0VDC
Wire Wire Line
	5850 5600 5900 5600
Wire Wire Line
	5850 5300 5900 5300
Wire Wire Line
	5900 5300 5900 5600
Connection ~ 5900 5600
Wire Wire Line
	5900 5600 6200 5600
Wire Wire Line
	4550 5300 4550 5200
Connection ~ 4550 5200
Wire Wire Line
	4550 5200 4850 5200
$Comp
L agg:L L302
U 1 1 5C672F8A
P 4850 4950
F 0 "L302" V 4950 5000 50  0000 L CNN
F 1 "FB" V 4850 5000 50  0000 L CNN
F 2 "agg:0603" H 4850 4950 50  0001 C CNN
F 3 "" H 4850 4950 50  0001 C CNN
F 4 "1463451" H 0   3650 50  0001 C CNN "Farnell"
	1    4850 4950
	0    1    1    0   
$EndComp
Wire Wire Line
	4850 4850 6200 4850
Wire Wire Line
	5850 5500 6200 5500
Text Label 6900 3250 0    50   ~ 0
LINK_LED
Text Label 850  3300 2    50   ~ 0
LINK_LED
$Comp
L agg:3v3 #PWR0147
U 1 1 5C6C6D8B
P 850 3150
F 0 "#PWR0147" H 850 3260 50  0001 L CNN
F 1 "3v3" H 850 3240 50  0000 C CNN
F 2 "" H 850 3150 50  0001 C CNN
F 3 "" H 850 3150 50  0001 C CNN
	1    850  3150
	1    0    0    -1  
$EndComp
$Comp
L agg:R R310
U 1 1 5C6C7BB4
P 900 3200
F 0 "R310" H 950 3250 50  0000 C CNN
F 1 "1k" H 950 3150 50  0000 C CNN
F 2 "agg:0402" H 900 3200 50  0001 C CNN
F 3 "" H 900 3200 50  0001 C CNN
F 4 "2331474" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    900  3200
	1    0    0    -1  
$EndComp
Wire Wire Line
	1300 3200 1000 3200
Wire Wire Line
	850  3300 1300 3300
Wire Wire Line
	900  3200 850  3200
Wire Wire Line
	850  3200 850  3150
$Comp
L agg:GND #PWR0148
U 1 1 5C6DDDC0
P 1200 3050
F 0 "#PWR0148" H 1070 3090 50  0001 L CNN
F 1 "GND" H 1200 2950 50  0000 C CNN
F 2 "" H 1200 3050 50  0001 C CNN
F 3 "" H 1200 3050 50  0001 C CNN
	1    1200 3050
	1    0    0    -1  
$EndComp
Wire Wire Line
	1200 3050 1200 3000
Wire Wire Line
	1200 3000 1300 3000
Wire Wire Line
	1300 2900 1050 2900
Text HLabel 800  2900 0    50   Input ~ 0
LED
$Comp
L agg:R R305
U 1 1 5C78D99E
P 6700 2350
F 0 "R305" H 6750 2400 50  0000 C CNN
F 1 "33" H 6750 2300 50  0000 C CNN
F 2 "agg:0402" H 6700 2350 50  0001 C CNN
F 3 "" H 6700 2350 50  0001 C CNN
F 4 "2302472" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6700 2350
	1    0    0    -1  
$EndComp
Wire Wire Line
	6700 2350 6600 2350
$Comp
L agg:R R306
U 1 1 5C78E1BD
P 6850 2450
F 0 "R306" H 6900 2500 50  0000 C CNN
F 1 "33" H 6900 2400 50  0000 C CNN
F 2 "agg:0402" H 6850 2450 50  0001 C CNN
F 3 "" H 6850 2450 50  0001 C CNN
F 4 "2302472" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6850 2450
	1    0    0    -1  
$EndComp
Wire Wire Line
	6950 2450 7100 2450
$Comp
L agg:R R307
U 1 1 5C78E6FF
P 6700 2550
F 0 "R307" H 6750 2600 50  0000 C CNN
F 1 "33" H 6750 2500 50  0000 C CNN
F 2 "agg:0402" H 6700 2550 50  0001 C CNN
F 3 "" H 6700 2550 50  0001 C CNN
F 4 "2302472" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    6700 2550
	1    0    0    -1  
$EndComp
Wire Wire Line
	6700 2550 6600 2550
$Comp
L agg:R R318
U 1 1 5C93A52C
P 950 2900
F 0 "R318" H 1000 2950 50  0000 C CNN
F 1 "1k" H 1000 2850 50  0000 C CNN
F 2 "agg:0402" H 950 2900 50  0001 C CNN
F 3 "" H 950 2900 50  0001 C CNN
F 4 "2331474" H 0   0   50  0001 C CNN "Farnell"
F 5 "50" H 0   0   50  0001 C CNN "Voltage"
	1    950  2900
	1    0    0    -1  
$EndComp
Wire Wire Line
	950  2900 800  2900
$Comp
L agg:KSZ8081RNx IC301
U 1 1 5C4816F0
P 6000 2650
F 0 "IC301" H 5500 3550 50  0000 L CNN
F 1 "KSZ8081RNA" H 5500 1750 50  0000 L CNN
F 2 "agg:QFN-24-EP-MICREL" H 5500 1650 50  0001 L CNN
F 3 "http://www.farnell.com/datasheets/2310338.pdf" H 5500 1550 50  0001 L CNN
F 4 "2509802" H 5500 1450 50  0001 L CNN "Farnell"
	1    6000 2650
	1    0    0    -1  
$EndComp
$Comp
L agg:PWR #FLG0109
U 1 1 5CB6E82D
P 2250 4250
F 0 "#FLG0109" H 2250 4410 50  0001 C CNN
F 1 "PWR" H 2250 4340 50  0001 C CNN
F 2 "" H 2250 4250 50  0001 C CNN
F 3 "" H 2250 4250 50  0001 C CNN
	1    2250 4250
	-1   0    0    1   
$EndComp
Wire Wire Line
	2250 4250 2250 4200
Connection ~ 2250 4200
NoConn ~ 1300 2600
$Comp
L agg:GND #PWR?
U 1 1 5D7C14BA
P 4550 4200
AR Path="/5D7C14BA" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED715/5D7C14BA" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED784/5D7C14BA" Ref="#PWR0127"  Part="1" 
F 0 "#PWR0127" H 4420 4240 50  0001 L CNN
F 1 "GND" H 4550 4100 50  0000 C CNN
F 2 "" H 4550 4200 50  0001 C CNN
F 3 "" H 4550 4200 50  0001 C CNN
	1    4550 4200
	1    0    0    -1  
$EndComp
Wire Wire Line
	4550 4200 4550 4150
Wire Wire Line
	4550 4150 4600 4150
Wire Wire Line
	4550 4000 4550 4050
Wire Wire Line
	4550 4050 4600 4050
$Comp
L agg:C C?
U 1 1 5D7C14C4
P 4350 4050
AR Path="/5D7C14C4" Ref="C?"  Part="1" 
AR Path="/5C2ED715/5D7C14C4" Ref="C?"  Part="1" 
AR Path="/5C2ED784/5D7C14C4" Ref="C314"  Part="1" 
F 0 "C314" H 4400 4120 50  0000 C CNN
F 1 "100n" H 4400 3980 50  0000 C CNN
F 2 "agg:0402" H 4350 4050 50  0001 C CNN
F 3 "" H 4350 4050 50  0001 C CNN
F 4 "2528765" H 0   0   50  0001 C CNN "Farnell"
F 5 "16" H 0   0   50  0001 C CNN "Voltage"
	1    4350 4050
	0    1    1    0   
$EndComp
$Comp
L agg:GND #PWR?
U 1 1 5D7C14CA
P 4350 4200
AR Path="/5D7C14CA" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED715/5D7C14CA" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED784/5D7C14CA" Ref="#PWR0149"  Part="1" 
F 0 "#PWR0149" H 4220 4240 50  0001 L CNN
F 1 "GND" H 4350 4100 50  0000 C CNN
F 2 "" H 4350 4200 50  0001 C CNN
F 3 "" H 4350 4200 50  0001 C CNN
	1    4350 4200
	1    0    0    -1  
$EndComp
Wire Wire Line
	4350 4200 4350 4150
Wire Wire Line
	4350 4050 4350 4000
$Comp
L agg:3v3 #PWR?
U 1 1 5D7C14D3
P 4550 4000
AR Path="/5D7C14D3" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED715/5D7C14D3" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED784/5D7C14D3" Ref="#PWR0155"  Part="1" 
F 0 "#PWR0155" H 4550 4110 50  0001 L CNN
F 1 "3v3" H 4550 4090 50  0000 C CNN
F 2 "" H 4550 4000 50  0001 C CNN
F 3 "" H 4550 4000 50  0001 C CNN
	1    4550 4000
	1    0    0    -1  
$EndComp
$Comp
L agg:3v3 #PWR?
U 1 1 5D7C14D9
P 4350 4000
AR Path="/5D7C14D9" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED715/5D7C14D9" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED784/5D7C14D9" Ref="#PWR0167"  Part="1" 
F 0 "#PWR0167" H 4350 4110 50  0001 L CNN
F 1 "3v3" H 4350 4090 50  0000 C CNN
F 2 "" H 4350 4000 50  0001 C CNN
F 3 "" H 4350 4000 50  0001 C CNN
	1    4350 4000
	1    0    0    -1  
$EndComp
Text Notes 4700 3900 0    50   ~ 0
25MHz XO
$Comp
L agg:TCXO_ST Y?
U 1 1 5D7C14E2
P 4900 4050
AR Path="/5D7C14E2" Ref="Y?"  Part="1" 
AR Path="/5C2ED715/5D7C14E2" Ref="Y?"  Part="1" 
AR Path="/5C2ED784/5D7C14E2" Ref="Y301"  Part="1" 
F 0 "Y301" H 4700 4150 50  0000 L CNN
F 1 "25M" H 4700 3850 50  0000 L CNN
F 2 "agg:XTAL-25x20" H 4700 4050 50  0001 C CNN
F 3 "http://www.farnell.com/datasheets/2581435.pdf" H 4700 4050 50  0001 C CNN
F 4 "2849479" H 4700 3750 50  0001 L CNN "Farnell"
	1    4900 4050
	1    0    0    -1  
$EndComp
$Comp
L agg:3v3 #PWR?
U 1 1 5D7C14E8
P 5300 4150
AR Path="/5D7C14E8" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED715/5D7C14E8" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED784/5D7C14E8" Ref="#PWR0188"  Part="1" 
F 0 "#PWR0188" H 5300 4260 50  0001 L CNN
F 1 "3v3" H 5300 4240 50  0000 C CNN
F 2 "" H 5300 4150 50  0001 C CNN
F 3 "" H 5300 4150 50  0001 C CNN
	1    5300 4150
	0    1    1    0   
$EndComp
Wire Wire Line
	5300 4150 5200 4150
Wire Wire Line
	5400 3250 5300 3250
Wire Wire Line
	5300 3250 5300 4050
Wire Wire Line
	5200 4050 5300 4050
NoConn ~ 5400 3150
$EndSCHEMATC
