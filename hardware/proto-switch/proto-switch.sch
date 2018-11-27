EESchema Schematic File Version 4
LIBS:proto-switch-cache
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 5
Title "DAQnet Switch Prototype"
Date "2018-11-24"
Rev "1"
Comp ""
Comment1 "Drawn by: Adam Greig"
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Sheet
S 4550 3000 850  2650
U 5C2ED715
F0 "iCE40" 50
F1 "ice40.sch" 50
F2 "RD1+" I L 4550 3050 50 
F3 "RD1-" I L 4550 3150 50 
F4 "TD1+" O L 4550 3250 50 
F5 "TD1-" O L 4550 3350 50 
F6 "TD2+" O L 4550 3700 50 
F7 "TD2-" O L 4550 3800 50 
F8 "TD3+" O L 4550 4350 50 
F9 "TD3-" O L 4550 4450 50 
F10 "TD4+" O L 4550 5000 50 
F11 "TD4-" O L 4550 5100 50 
F12 "RD2+" O L 4550 3900 50 
F13 "RD2-" O L 4550 4000 50 
F14 "RD3+" O L 4550 4550 50 
F15 "RD3-" O L 4550 4650 50 
F16 "RD4+" O L 4550 5200 50 
F17 "RD4-" O L 4550 5300 50 
F18 "P1_LED1" O L 4550 3450 50 
F19 "P1_LED2" O L 4550 3550 50 
F20 "P2_LED1" O L 4550 4100 50 
F21 "P2_LED2" O L 4550 4200 50 
F22 "P3_LED1" O L 4550 4750 50 
F23 "P3_LED2" O L 4550 4850 50 
F24 "P4_LED1" O L 4550 5400 50 
F25 "P4_LED2" O L 4550 5500 50 
F26 "RXD0" I R 5400 3200 50 
F27 "RXD1" I R 5400 3300 50 
F28 "CRS_DV" I R 5400 3400 50 
F29 "REF_CLK" I R 5400 3500 50 
F30 "TXEN" O R 5400 3650 50 
F31 "TXD0" O R 5400 3750 50 
F32 "TXD1" O R 5400 3850 50 
F33 "MDIO" B R 5400 4000 50 
F34 "MDC" O R 5400 4100 50 
F35 "PHY_~RST" O R 5400 4250 50 
F36 "ETH_LED" O R 5400 4350 50 
$EndSheet
$Sheet
S 5950 3000 900  1450
U 5C2ED784
F0 "Ethernet" 50
F1 "ethernet.sch" 50
F2 "RXD1" O L 5950 3300 50 
F3 "RXD0" O L 5950 3200 50 
F4 "CRS_DV" O L 5950 3400 50 
F5 "REF_CLK" O L 5950 3500 50 
F6 "TXEN" I L 5950 3650 50 
F7 "TXD0" I L 5950 3750 50 
F8 "TXD1" I L 5950 3850 50 
F9 "MDIO" B L 5950 4000 50 
F10 "MDC" I L 5950 4100 50 
F11 "~RST" I L 5950 4250 50 
F12 "48VDC" O R 6850 3050 50 
F13 "PG" O R 6850 3250 50 
F14 "0VDC" O R 6850 3150 50 
F15 "LED" I L 5950 4350 50 
$EndSheet
$Sheet
S 3200 3000 900  2650
U 5C2ED83C
F0 "DAQnet Ports" 50
F1 "daqnet.sch" 50
F2 "P1_LED1" I R 4100 3450 50 
F3 "P1_LED2" I R 4100 3550 50 
F4 "TD1-" I R 4100 3350 50 
F5 "TD1+" I R 4100 3250 50 
F6 "RD1-" O R 4100 3150 50 
F7 "RD1+" O R 4100 3050 50 
F8 "P2_LED1" I R 4100 4100 50 
F9 "P2_LED2" I R 4100 4200 50 
F10 "TD2-" I R 4100 3800 50 
F11 "TD2+" I R 4100 3700 50 
F12 "RD2-" O R 4100 4000 50 
F13 "RD2+" O R 4100 3900 50 
F14 "P3_LED1" I R 4100 4750 50 
F15 "P3_LED2" I R 4100 4850 50 
F16 "TD3-" I R 4100 4450 50 
F17 "TD3+" I R 4100 4350 50 
F18 "RD3-" O R 4100 4650 50 
F19 "RD3+" O R 4100 4550 50 
F20 "P4_LED1" I R 4100 5400 50 
F21 "P4_LED2" I R 4100 5500 50 
F22 "TD4-" I R 4100 5100 50 
F23 "TD4+" I R 4100 5000 50 
F24 "RD4-" O R 4100 5300 50 
F25 "RD4+" O R 4100 5200 50 
$EndSheet
$Sheet
S 7450 3000 900  600 
U 5C2ED962
F0 "Power" 50
F1 "power.sch" 50
F2 "48VIN+" I L 7450 3050 50 
F3 "48VIN-" I L 7450 3150 50 
F4 "48VPG" I L 7450 3250 50 
$EndSheet
Text Notes 8300 3550 2    50   ~ 0
48v in\nIsolated:\n24v 83mA out\n3v3 500mA out\n1v2 200mA out
Wire Wire Line
	5400 3200 5950 3200
Wire Wire Line
	5950 3300 5400 3300
Wire Wire Line
	5400 3400 5950 3400
Wire Wire Line
	5950 3500 5400 3500
Wire Wire Line
	5400 3650 5950 3650
Wire Wire Line
	5950 3750 5400 3750
Wire Wire Line
	5400 3850 5950 3850
Wire Wire Line
	5950 4000 5400 4000
Wire Wire Line
	5400 4100 5950 4100
Wire Wire Line
	5950 4250 5400 4250
Wire Wire Line
	5400 4350 5950 4350
Wire Wire Line
	6850 3250 7450 3250
Wire Wire Line
	6850 3150 7450 3150
Wire Wire Line
	6850 3050 7450 3050
Wire Wire Line
	4100 3050 4550 3050
Wire Wire Line
	4100 3150 4550 3150
Wire Wire Line
	4100 3250 4550 3250
Wire Wire Line
	4550 3350 4100 3350
Wire Wire Line
	4100 3450 4550 3450
Wire Wire Line
	4550 3550 4100 3550
Wire Wire Line
	4100 3700 4550 3700
Wire Wire Line
	4550 3800 4100 3800
Wire Wire Line
	4100 3900 4550 3900
Wire Wire Line
	4550 4000 4100 4000
Wire Wire Line
	4100 4100 4550 4100
Wire Wire Line
	4550 4200 4100 4200
Wire Wire Line
	4100 4350 4550 4350
Wire Wire Line
	4550 4450 4100 4450
Wire Wire Line
	4100 4550 4550 4550
Wire Wire Line
	4550 4650 4100 4650
Wire Wire Line
	4100 4750 4550 4750
Wire Wire Line
	4550 4850 4100 4850
Wire Wire Line
	4100 5000 4550 5000
Wire Wire Line
	4550 5100 4100 5100
Wire Wire Line
	4100 5200 4550 5200
Wire Wire Line
	4550 5300 4100 5300
Wire Wire Line
	4100 5400 4550 5400
Wire Wire Line
	4550 5500 4100 5500
$Comp
L agg:PART X101
U 1 1 5C8667E8
P 6950 5600
F 0 "X101" H 7000 5700 50  0000 L CNN
F 1 "M3_MOUNT" H 7000 5600 50  0000 L CNN
F 2 "agg:M3_MOUNT" H 6950 5600 50  0001 C CNN
F 3 "" H 6950 5600 50  0001 C CNN
	1    6950 5600
	1    0    0    -1  
$EndComp
$Comp
L agg:PART X102
U 1 1 5C8675C5
P 7550 5600
F 0 "X102" H 7600 5700 50  0000 L CNN
F 1 "M3_MOUNT" H 7600 5600 50  0000 L CNN
F 2 "agg:M3_MOUNT" H 7550 5600 50  0001 C CNN
F 3 "" H 7550 5600 50  0001 C CNN
	1    7550 5600
	1    0    0    -1  
$EndComp
$Comp
L agg:PART X104
U 1 1 5C867961
P 7550 5900
F 0 "X104" H 7600 6000 50  0000 L CNN
F 1 "M3_MOUNT" H 7600 5900 50  0000 L CNN
F 2 "agg:M3_MOUNT" H 7550 5900 50  0001 C CNN
F 3 "" H 7550 5900 50  0001 C CNN
	1    7550 5900
	1    0    0    -1  
$EndComp
$Comp
L agg:PART X103
U 1 1 5C867C8A
P 6950 5900
F 0 "X103" H 7000 6000 50  0000 L CNN
F 1 "M3_MOUNT" H 7000 5900 50  0000 L CNN
F 2 "agg:M3_MOUNT" H 6950 5900 50  0001 C CNN
F 3 "" H 6950 5900 50  0001 C CNN
	1    6950 5900
	1    0    0    -1  
$EndComp
$EndSCHEMATC
