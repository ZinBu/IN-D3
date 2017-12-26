import serial
from time import sleep
from datetime import datetime


def ask(adress, protocol_id=0x9B, packet_id=0x01, data=None):
    """ Формирование пакета для отправки и чтение ответа """
    
    if data:
        packet = bytes([protocol_id, packet_id, adress, data])
        check_sum = packet[0] ^ packet[1] ^ packet[2] ^ packet[3]
        full_packet = bytes([0x7E, protocol_id, packet_id, adress, data, check_sum, 0x7E])

    else:
        packet = bytes([protocol_id, packet_id, adress])
        check_sum = packet[0] ^ packet[1] ^ packet[2]
        full_packet = bytes([0x7E, protocol_id, packet_id, adress, check_sum, 0x7E])

    # print('packet: ', packet)
    # print('check_sum: ', hex(check_sum))
    # print('Request ', full_packet)

    ser.write(full_packet)
    buf = b''
    while True:
        byte = ser.read(1)
        buf += byte
        if buf.count(b'~') == 2:
            return buf


def get_angles(data):
    # определение дробной части
    fractional = data[0]/256.0

    # прмиенение маски для отсеива 2 старших
    # битов последнего байта для определения целой части
    integer = data[1] + (data[2] & 0x3F) * 256.0
    number = fractional + integer

    # знак числа
    sign = data[2] >> 7
    # print(sign)
    if sign == 0:
        sign = "+"
    else:
        sign = "-"

    # еденицы измерения - секунды\минуты
    units = (data[2] >> 6) & 1
    # print(units)
    if units == 0:
        units = '"'
    else:
        units = "'"

    return "{}{}{}".format(sign, round(number, 3), units)


def search_device():
    for i in range(40):
        print("Device №: ", i)
        response = ask(i)
        print(response)
        if response:
            break


def search_port():
    for i in range(5):
        try:
            ser = serial.Serial("COM{}".format(i), timeout=0.2)
            print('"COM{}" opened'.format(i))
            return ser
        except Exception as error:
            print(error)


def get_time():
    now = datetime.now()
    return now.strftime("%H:%M:%S:%f")


ser = serial.Serial("COM5", timeout=0.5)

# ТАКТЫ УСРЕДНЕНИЯ
# установка
# print(ask(adress=7, protocol_id=0x9C, packet_id=0x0D, data=1))

# запрос текущего значения
avg_ticks = "{}{}".format('Average ticks: ', hex(ask(adress=7, protocol_id=0x9C, packet_id=0x0C)[-3]))
print(avg_ticks)

# ПЕРИОД УСРЕДНЕНИЯ
# установка
# print(ask(adress=7, protocol_id=0x9C, packet_id=0x0F, data=1))

# запрос текущего значения
avg_period = "{}{}".format('Average period: ', hex(ask(adress=7, protocol_id=0x9C, packet_id=0x0E)[-3]))
print(avg_period)

date = datetime.now().strftime("%H_%M_%S")
with open("Test_log_{}.txt".format(date), "w") as f:
    f.write("Start time: " + get_time() + "\n")
    f.write(avg_ticks + "\n")
    f.write(avg_period + "\n")

with open("Test_log_{}.txt".format(date), "a") as f:
    count = 1
    while True:
        req = ask(adress=7)
        pack_req = [int(x) for x in req]
        # print(pack_req)
        # print(req)
        # print(len(req))
        data = pack_req[4:-2]

        x_data = data[:3]
        y_data = data[3:]
        
        try:
            # получение углов
            res = "{}; y; {} ; x; {} ; {} ;\n".format(count, get_angles(x_data), get_angles(y_data), get_time())
            print(res)
            # with open("Test_log_{}.txt".format(date), "a") as f:
            #     f.write(res)
            f.write(res)

        except Exception as error:
            # поэтапный вывод в случае ошибки
            print(error)
            # f.write("Error. Data length - %s\n" % len(pack_req))
            print(pack_req)
            print("Length: ", len(pack_req))
            print("Response ", req)
            print([hex(x) for x in req])            
        
        count += 1
        sleep(0.01)
