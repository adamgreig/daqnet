import numpy as np
import matplotlib.pyplot as plt
import serial


def main():
    ser = serial.Serial("/dev/ttyUSB0", 1000000)
    raw_data = ser.read(10000)
    data = np.frombuffer(raw_data, dtype=np.uint8)
    plt.plot(data, '.')
    plt.show()


if __name__ == "__main__":
    main()
