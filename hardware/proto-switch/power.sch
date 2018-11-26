EESchema Schematic File Version 4
LIBS:proto-switch-cache
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 5 5
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
L agg:MCP1700 IC?
U 1 1 5C37DA17
P 5400 4200
AR Path="/5C37DA17" Ref="IC?"  Part="1" 
AR Path="/5C2ED962/5C37DA17" Ref="IC502"  Part="1" 
F 0 "IC502" H 5200 4300 50  0000 L CNN
F 1 "MCP1700" H 5200 4000 50  0000 L CNN
F 2 "agg:SOT-23" H 5200 3900 50  0001 L CNN
F 3 "http://www.farnell.com/datasheets/1784514.pdf" H 5200 3800 50  0001 L CNN
F 4 "1851940" H 5200 3700 50  0001 L CNN "Farnell"
	1    5400 4200
	1    0    0    -1  
$EndComp
$Comp
L agg:C C?
U 1 1 5C37DA1D
P 6000 4250
AR Path="/5C37DA1D" Ref="C?"  Part="1" 
AR Path="/5C2ED962/5C37DA1D" Ref="C504"  Part="1" 
F 0 "C504" H 6050 4320 50  0000 C CNN
F 1 "1µ" H 6050 4180 50  0000 C CNN
F 2 "agg:0402" H 6000 4250 50  0001 C CNN
F 3 "" H 6000 4250 50  0001 C CNN
	1    6000 4250
	0    1    1    0   
$EndComp
$Comp
L agg:GND #PWR?
U 1 1 5C37DA23
P 6000 4400
AR Path="/5C37DA23" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5C37DA23" Ref="#PWR0173"  Part="1" 
F 0 "#PWR0173" H 5870 4440 50  0001 L CNN
F 1 "GND" H 6000 4300 50  0000 C CNN
F 2 "" H 6000 4400 50  0001 C CNN
F 3 "" H 6000 4400 50  0001 C CNN
	1    6000 4400
	1    0    0    -1  
$EndComp
Wire Wire Line
	6000 4400 6000 4350
Wire Wire Line
	6150 4150 6150 4200
Wire Wire Line
	6150 4200 6000 4200
Wire Wire Line
	6000 4250 6000 4200
Connection ~ 6000 4200
Wire Wire Line
	6000 4200 5800 4200
$Comp
L agg:3v3 #PWR?
U 1 1 5C37DA2F
P 5050 4150
AR Path="/5C37DA2F" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5C37DA2F" Ref="#PWR0174"  Part="1" 
F 0 "#PWR0174" H 5050 4260 50  0001 L CNN
F 1 "3v3" H 5050 4240 50  0000 C CNN
F 2 "" H 5050 4150 50  0001 C CNN
F 3 "" H 5050 4150 50  0001 C CNN
	1    5050 4150
	1    0    0    -1  
$EndComp
Wire Wire Line
	5050 4150 5050 4200
Wire Wire Line
	5050 4200 5100 4200
$Comp
L agg:GND #PWR?
U 1 1 5C37DA37
P 5050 4350
AR Path="/5C37DA37" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5C37DA37" Ref="#PWR0175"  Part="1" 
F 0 "#PWR0175" H 4920 4390 50  0001 L CNN
F 1 "GND" H 5050 4250 50  0000 C CNN
F 2 "" H 5050 4350 50  0001 C CNN
F 3 "" H 5050 4350 50  0001 C CNN
	1    5050 4350
	1    0    0    -1  
$EndComp
Wire Wire Line
	5050 4350 5050 4300
Wire Wire Line
	5050 4300 5100 4300
$Comp
L agg:C C?
U 1 1 5C37DA3F
P 4850 4200
AR Path="/5C37DA3F" Ref="C?"  Part="1" 
AR Path="/5C2ED962/5C37DA3F" Ref="C503"  Part="1" 
F 0 "C503" H 4900 4270 50  0000 C CNN
F 1 "100n" H 4900 4130 50  0000 C CNN
F 2 "agg:0402" H 4850 4200 50  0001 C CNN
F 3 "" H 4850 4200 50  0001 C CNN
	1    4850 4200
	0    1    1    0   
$EndComp
$Comp
L agg:3v3 #PWR?
U 1 1 5C37DA45
P 4850 4150
AR Path="/5C37DA45" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5C37DA45" Ref="#PWR0176"  Part="1" 
F 0 "#PWR0176" H 4850 4260 50  0001 L CNN
F 1 "3v3" H 4850 4240 50  0000 C CNN
F 2 "" H 4850 4150 50  0001 C CNN
F 3 "" H 4850 4150 50  0001 C CNN
	1    4850 4150
	1    0    0    -1  
$EndComp
Wire Wire Line
	4850 4150 4850 4200
$Comp
L agg:GND #PWR?
U 1 1 5C37DA4C
P 4850 4350
AR Path="/5C37DA4C" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5C37DA4C" Ref="#PWR0177"  Part="1" 
F 0 "#PWR0177" H 4720 4390 50  0001 L CNN
F 1 "GND" H 4850 4250 50  0000 C CNN
F 2 "" H 4850 4350 50  0001 C CNN
F 3 "" H 4850 4350 50  0001 C CNN
	1    4850 4350
	1    0    0    -1  
$EndComp
Wire Wire Line
	4850 4350 4850 4300
Text Notes 5200 4050 0    50   ~ 0
1v2 200mA LDO
$Comp
L agg:TESTPAD TP?
U 1 1 5C37DA58
P 6250 4200
AR Path="/5C37DA58" Ref="TP?"  Part="1" 
AR Path="/5C2ED962/5C37DA58" Ref="TP503"  Part="1" 
F 0 "TP503" H 6250 4250 50  0000 L CNN
F 1 "TESTPAD" H 6250 4125 50  0001 L CNN
F 2 "agg:TESTPAD" H 6250 4050 50  0001 L CNN
F 3 "" H 6250 4200 50  0001 C CNN
	1    6250 4200
	1    0    0    -1  
$EndComp
Wire Wire Line
	6250 4200 6150 4200
Connection ~ 6150 4200
$Comp
L agg:CONN_01x01 J?
U 1 1 5C37DA60
P 5350 3400
AR Path="/5C37DA60" Ref="J?"  Part="1" 
AR Path="/5C2ED962/5C37DA60" Ref="J501"  Part="1" 
F 0 "J501" H 5300 3500 50  0000 L CNN
F 1 "GND" H 5300 3300 50  0000 L CNN
F 2 "agg:SIL-254P-01" H 5350 3400 50  0001 C CNN
F 3 "" H 5350 3400 50  0001 C CNN
	1    5350 3400
	1    0    0    -1  
$EndComp
$Comp
L agg:GND #PWR?
U 1 1 5C37DA66
P 5550 3400
AR Path="/5C37DA66" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5C37DA66" Ref="#PWR0178"  Part="1" 
F 0 "#PWR0178" H 5420 3440 50  0001 L CNN
F 1 "GND" H 5550 3300 50  0000 C CNN
F 2 "" H 5550 3400 50  0001 C CNN
F 3 "" H 5550 3400 50  0001 C CNN
	1    5550 3400
	0    -1   -1   0   
$EndComp
Wire Wire Line
	5550 3400 5450 3400
$Comp
L agg:1v2 #PWR?
U 1 1 5C37DA6D
P 6150 4150
AR Path="/5C37DA6D" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5C37DA6D" Ref="#PWR0179"  Part="1" 
F 0 "#PWR0179" H 6150 4260 50  0001 L CNN
F 1 "1v2" H 6150 4240 50  0000 C CNN
F 2 "" H 6150 4150 50  0001 C CNN
F 3 "" H 6150 4150 50  0001 C CNN
	1    6150 4150
	1    0    0    -1  
$EndComp
$Comp
L agg:TEC2 IC501
U 1 1 5C48779D
P 3300 3350
F 0 "IC501" H 2900 3650 50  0000 L CNN
F 1 "TEC 2-4810" H 2900 3050 50  0000 L CNN
F 2 "agg:SIP-8-DCDC" H 2900 2950 50  0001 L CNN
F 3 "" H 2900 2850 50  0001 L CNN
F 4 "2854900" H 2900 2750 50  0001 L CNN "Farnell"
	1    3300 3350
	1    0    0    -1  
$EndComp
$Comp
L agg:TEC2 IC503
U 1 1 5C48807D
P 3300 4300
F 0 "IC503" H 2900 4600 50  0000 L CNN
F 1 "TEC 2-4815" H 2900 4000 50  0000 L CNN
F 2 "agg:SIP-8-DCDC" H 2900 3900 50  0001 L CNN
F 3 "" H 2900 3800 50  0001 L CNN
F 4 "2854905" H 2900 3700 50  0001 L CNN "Farnell"
	1    3300 4300
	1    0    0    -1  
$EndComp
$Comp
L agg:3v3 #PWR0180
U 1 1 5C67B8AD
P 3950 3100
F 0 "#PWR0180" H 3950 3210 50  0001 L CNN
F 1 "3v3" H 3950 3190 50  0000 C CNN
F 2 "" H 3950 3100 50  0001 C CNN
F 3 "" H 3950 3100 50  0001 C CNN
	1    3950 3100
	1    0    0    -1  
$EndComp
NoConn ~ 3800 3350
$Comp
L agg:GND #PWR0181
U 1 1 5C67C2E9
P 3950 3300
F 0 "#PWR0181" H 3820 3340 50  0001 L CNN
F 1 "GND" H 3950 3200 50  0000 C CNN
F 2 "" H 3950 3300 50  0001 C CNN
F 3 "" H 3950 3300 50  0001 C CNN
	1    3950 3300
	1    0    0    -1  
$EndComp
$Comp
L agg:C C501
U 1 1 5C67C8A9
P 4300 3150
F 0 "C501" H 4350 3220 50  0000 C CNN
F 1 "10µ" H 4350 3080 50  0000 C CNN
F 2 "agg:0603" H 4300 3150 50  0001 C CNN
F 3 "" H 4300 3150 50  0001 C CNN
	1    4300 3150
	0    1    1    0   
$EndComp
Wire Wire Line
	3800 3150 3950 3150
Wire Wire Line
	3950 3150 3950 3100
Wire Wire Line
	3800 3250 3950 3250
Wire Wire Line
	3950 3250 3950 3300
$Comp
L agg:3v3 #PWR0182
U 1 1 5C67FC08
P 4300 3100
F 0 "#PWR0182" H 4300 3210 50  0001 L CNN
F 1 "3v3" H 4300 3190 50  0000 C CNN
F 2 "" H 4300 3100 50  0001 C CNN
F 3 "" H 4300 3100 50  0001 C CNN
	1    4300 3100
	1    0    0    -1  
$EndComp
$Comp
L agg:GND #PWR0183
U 1 1 5C680442
P 4300 3300
F 0 "#PWR0183" H 4170 3340 50  0001 L CNN
F 1 "GND" H 4300 3200 50  0000 C CNN
F 2 "" H 4300 3300 50  0001 C CNN
F 3 "" H 4300 3300 50  0001 C CNN
	1    4300 3300
	1    0    0    -1  
$EndComp
Wire Wire Line
	4300 3100 4300 3150
Wire Wire Line
	4300 3250 4300 3300
Text HLabel 2500 3150 0    50   Input ~ 0
48VIN+
Text HLabel 2500 3250 0    50   Input ~ 0
48VIN-
Text HLabel 1800 3350 0    50   Input ~ 0
48VPG
Wire Wire Line
	2500 3250 2600 3250
Wire Wire Line
	2500 3150 2700 3150
$Comp
L agg:R R501
U 1 1 5C684137
P 2000 3350
F 0 "R501" H 2050 3400 50  0000 C CNN
F 1 "1k" H 2050 3300 50  0000 C CNN
F 2 "agg:0402" H 2000 3350 50  0001 C CNN
F 3 "" H 2000 3350 50  0001 C CNN
	1    2000 3350
	1    0    0    -1  
$EndComp
Wire Wire Line
	1800 3350 1900 3350
Wire Wire Line
	2100 3350 2800 3350
$Comp
L agg:R R502
U 1 1 5C68756D
P 2000 4300
F 0 "R502" H 2050 4350 50  0000 C CNN
F 1 "1k" H 2050 4250 50  0000 C CNN
F 2 "agg:0402" H 2000 4300 50  0001 C CNN
F 3 "" H 2000 4300 50  0001 C CNN
	1    2000 4300
	1    0    0    -1  
$EndComp
Wire Wire Line
	2100 4300 2800 4300
NoConn ~ 3800 4300
$Comp
L agg:GND #PWR0184
U 1 1 5C68AC4C
P 3950 4250
F 0 "#PWR0184" H 3820 4290 50  0001 L CNN
F 1 "GND" H 3950 4150 50  0000 C CNN
F 2 "" H 3950 4250 50  0001 C CNN
F 3 "" H 3950 4250 50  0001 C CNN
	1    3950 4250
	1    0    0    -1  
$EndComp
Wire Wire Line
	3950 4250 3950 4200
Wire Wire Line
	3950 4200 3800 4200
$Comp
L agg:24v #PWR0185
U 1 1 5C68C142
P 3950 4050
F 0 "#PWR0185" H 3950 4160 50  0001 L CNN
F 1 "24v" H 3950 4140 50  0000 C CNN
F 2 "" H 3950 4050 50  0001 C CNN
F 3 "" H 3950 4050 50  0001 C CNN
	1    3950 4050
	1    0    0    -1  
$EndComp
Wire Wire Line
	3800 4100 3950 4100
Wire Wire Line
	3950 4100 3950 4050
$Comp
L agg:C C502
U 1 1 5C68CEE8
P 4300 4100
F 0 "C502" H 4350 4170 50  0000 C CNN
F 1 "10µ" H 4350 4030 50  0000 C CNN
F 2 "agg:0603" H 4300 4100 50  0001 C CNN
F 3 "" H 4300 4100 50  0001 C CNN
	1    4300 4100
	0    1    1    0   
$EndComp
$Comp
L agg:GND #PWR0186
U 1 1 5C68CEFC
P 4300 4250
F 0 "#PWR0186" H 4170 4290 50  0001 L CNN
F 1 "GND" H 4300 4150 50  0000 C CNN
F 2 "" H 4300 4250 50  0001 C CNN
F 3 "" H 4300 4250 50  0001 C CNN
	1    4300 4250
	1    0    0    -1  
$EndComp
Wire Wire Line
	4300 4050 4300 4100
Wire Wire Line
	4300 4200 4300 4250
$Comp
L agg:24v #PWR0187
U 1 1 5C690029
P 4300 4050
F 0 "#PWR0187" H 4300 4160 50  0001 L CNN
F 1 "24v" H 4300 4140 50  0000 C CNN
F 2 "" H 4300 4050 50  0001 C CNN
F 3 "" H 4300 4050 50  0001 C CNN
	1    4300 4050
	1    0    0    -1  
$EndComp
Wire Wire Line
	2000 4300 1900 4300
Wire Wire Line
	1900 4300 1900 3350
Connection ~ 1900 3350
Wire Wire Line
	1900 3350 2000 3350
Wire Wire Line
	2700 3150 2700 3750
Wire Wire Line
	2700 4100 2800 4100
Connection ~ 2700 3150
Wire Wire Line
	2700 3150 2800 3150
Wire Wire Line
	2600 3250 2600 3750
Wire Wire Line
	2600 4200 2800 4200
Connection ~ 2600 3250
Wire Wire Line
	2600 3250 2800 3250
Text Notes 3100 3000 0    50   ~ 0
3v3 500mA\nIsolated DC/DC
Text Notes 3100 3950 0    50   ~ 0
24v 83mA\nIsolated DC/DC
$Comp
L agg:TESTPAD TP?
U 1 1 5C6A4283
P 4000 4100
AR Path="/5C6A4283" Ref="TP?"  Part="1" 
AR Path="/5C2ED962/5C6A4283" Ref="TP502"  Part="1" 
F 0 "TP502" H 4000 4150 50  0000 L CNN
F 1 "TESTPAD" H 4000 4025 50  0001 L CNN
F 2 "agg:TESTPAD" H 4000 3950 50  0001 L CNN
F 3 "" H 4000 4100 50  0001 C CNN
	1    4000 4100
	1    0    0    -1  
$EndComp
Wire Wire Line
	4000 4100 3950 4100
Connection ~ 3950 4100
$Comp
L agg:TESTPAD TP?
U 1 1 5C6A67C6
P 4000 3150
AR Path="/5C6A67C6" Ref="TP?"  Part="1" 
AR Path="/5C2ED962/5C6A67C6" Ref="TP501"  Part="1" 
F 0 "TP501" H 4000 3200 50  0000 L CNN
F 1 "TESTPAD" H 4000 3075 50  0001 L CNN
F 2 "agg:TESTPAD" H 4000 3000 50  0001 L CNN
F 3 "" H 4000 3150 50  0001 C CNN
	1    4000 3150
	1    0    0    -1  
$EndComp
Wire Wire Line
	4000 3150 3950 3150
Connection ~ 3950 3150
$Comp
L agg:TESTPAD TP?
U 1 1 5C935AD0
P 2750 3750
AR Path="/5C935AD0" Ref="TP?"  Part="1" 
AR Path="/5C2ED962/5C935AD0" Ref="TP505"  Part="1" 
F 0 "TP505" H 2750 3800 50  0000 L CNN
F 1 "TESTPAD" H 2750 3675 50  0001 L CNN
F 2 "agg:TESTPAD" H 2750 3600 50  0001 L CNN
F 3 "" H 2750 3750 50  0001 C CNN
	1    2750 3750
	1    0    0    -1  
$EndComp
$Comp
L agg:TESTPAD TP?
U 1 1 5C9372D2
P 2550 3750
AR Path="/5C9372D2" Ref="TP?"  Part="1" 
AR Path="/5C2ED962/5C9372D2" Ref="TP504"  Part="1" 
F 0 "TP504" H 2550 3800 50  0000 L CNN
F 1 "TESTPAD" H 2550 3675 50  0001 L CNN
F 2 "agg:TESTPAD" H 2550 3600 50  0001 L CNN
F 3 "" H 2550 3750 50  0001 C CNN
	1    2550 3750
	-1   0    0    1   
$EndComp
Wire Wire Line
	2550 3750 2600 3750
Connection ~ 2600 3750
Wire Wire Line
	2600 3750 2600 4200
Wire Wire Line
	2750 3750 2700 3750
Connection ~ 2700 3750
Wire Wire Line
	2700 3750 2700 4100
$Comp
L agg:C C505
U 1 1 5D75A5F9
P 4550 4100
F 0 "C505" H 4600 4170 50  0000 C CNN
F 1 "10µ" H 4600 4030 50  0000 C CNN
F 2 "agg:0603" H 4550 4100 50  0001 C CNN
F 3 "" H 4550 4100 50  0001 C CNN
	1    4550 4100
	0    1    1    0   
$EndComp
$Comp
L agg:GND #PWR0502
U 1 1 5D75A603
P 4550 4250
F 0 "#PWR0502" H 4420 4290 50  0001 L CNN
F 1 "GND" H 4550 4150 50  0000 C CNN
F 2 "" H 4550 4250 50  0001 C CNN
F 3 "" H 4550 4250 50  0001 C CNN
	1    4550 4250
	1    0    0    -1  
$EndComp
Wire Wire Line
	4550 4050 4550 4100
Wire Wire Line
	4550 4200 4550 4250
$Comp
L agg:24v #PWR0501
U 1 1 5D75A60F
P 4550 4050
F 0 "#PWR0501" H 4550 4160 50  0001 L CNN
F 1 "24v" H 4550 4140 50  0000 C CNN
F 2 "" H 4550 4050 50  0001 C CNN
F 3 "" H 4550 4050 50  0001 C CNN
	1    4550 4050
	1    0    0    -1  
$EndComp
$Comp
L agg:LED D?
U 1 1 5D760AE7
P 4650 3250
AR Path="/5C2ED715/5D760AE7" Ref="D?"  Part="1" 
AR Path="/5C2ED962/5D760AE7" Ref="D501"  Part="1" 
F 0 "D501" H 4650 3350 50  0000 L CNN
F 1 "LED" H 4650 3175 50  0000 L CNN
F 2 "agg:0603-LED" H 4650 3250 50  0001 C CNN
F 3 "" H 4650 3250 50  0001 C CNN
F 4 "2290328" H 4650 3250 50  0001 C CNN "Farnell"
	1    4650 3250
	0    -1   -1   0   
$EndComp
$Comp
L agg:3v3 #PWR?
U 1 1 5D760AED
P 4650 3100
AR Path="/5C2ED715/5D760AED" Ref="#PWR?"  Part="1" 
AR Path="/5C2ED962/5D760AED" Ref="#PWR0503"  Part="1" 
F 0 "#PWR0503" H 4650 3210 50  0001 L CNN
F 1 "3v3" H 4650 3190 50  0000 C CNN
F 2 "" H 4650 3100 50  0001 C CNN
F 3 "" H 4650 3100 50  0001 C CNN
	1    4650 3100
	1    0    0    -1  
$EndComp
Wire Wire Line
	4650 3100 4650 3150
$Comp
L agg:R R?
U 1 1 5D760AF4
P 4650 3300
AR Path="/5C2ED715/5D760AF4" Ref="R?"  Part="1" 
AR Path="/5C2ED962/5D760AF4" Ref="R503"  Part="1" 
F 0 "R503" H 4700 3350 50  0000 C CNN
F 1 "1k" H 4700 3250 50  0000 C CNN
F 2 "agg:0402" H 4650 3300 50  0001 C CNN
F 3 "" H 4650 3300 50  0001 C CNN
	1    4650 3300
	0    1    1    0   
$EndComp
Wire Wire Line
	4650 3300 4650 3250
$Comp
L agg:GND #PWR0504
U 1 1 5D761726
P 4650 3450
F 0 "#PWR0504" H 4520 3490 50  0001 L CNN
F 1 "GND" H 4650 3350 50  0000 C CNN
F 2 "" H 4650 3450 50  0001 C CNN
F 3 "" H 4650 3450 50  0001 C CNN
	1    4650 3450
	1    0    0    -1  
$EndComp
Wire Wire Line
	4650 3450 4650 3400
$EndSCHEMATC