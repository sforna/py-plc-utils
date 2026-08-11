# -*- coding: utf-8 -*-
from pymodbus.client import ModbusTcpClient
import struct
import sys

def connect_to_plc(ip, port=502):
    client = ModbusTcpClient(ip, port=port)
    try:
        connection = client.connect()
        if connection:
            print(f"Connected to the Modbus PLC at IP address: {ip}:{port}")
            return client
        else:
            print(f"Error: unable to connect to the Modbus PLC {ip}:{port}")
            sys.exit(1)
    except Exception as e:
        print(f"Error while connecting to the PLC: {e}")
        sys.exit(1)

def read_coils(client, address, count, unit_id=1):
    try:
        result = client.read_coils(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Error while reading the coils: {result}")
            return None
        print(f"Coils read (Address {address}, Count {count}): {result.bits[:count]}")
        return result.bits[:count]
    except Exception as e:
        print(f"Error while reading the coils: {e}")
        return None

def read_discrete_inputs(client, address, count, unit_id=1):
    try:
        result = client.read_discrete_inputs(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Error while reading the discrete inputs: {result}")
            return None
        print(f"Discrete inputs read (Address {address}, Count {count}): {result.bits[:count]}")
        return result.bits[:count]
    except Exception as e:
        print(f"Error while reading the discrete inputs: {e}")
        return None

def read_holding_registers(client, address, count, unit_id=1):
    try:
        result = client.read_holding_registers(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Error while reading the holding registers: {result}")
            return None
        print(f"Holding registers read (Address {address}, Count {count}): {result.registers}")
        return result.registers
    except Exception as e:
        print(f"Error while reading the holding registers: {e}")
        return None

def read_input_registers(client, address, count, unit_id=1):
    try:
        result = client.read_input_registers(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Error while reading the input registers: {result}")
            return None
        print(f"Input registers read (Address {address}, Count {count}): {result.registers}")
        return result.registers
    except Exception as e:
        print(f"Error while reading the input registers: {e}")
        return None

def parse_register_data(registers, data_type, register_order='big'):
    try:
        if not registers:
            return None

        if data_type == 'int16':
            return registers[0] if len(registers) >= 1 else None
        elif data_type == 'uint16':
            value = registers[0] if len(registers) >= 1 else None
            return value if value >= 0 else value + 65536
        elif data_type == 'int32':
            if len(registers) < 2:
                return None
            if register_order == 'big':
                combined = (registers[0] << 16) | registers[1]
            else:
                combined = (registers[1] << 16) | registers[0]
            return struct.unpack('>i', struct.pack('>I', combined))[0]
        elif data_type == 'uint32' or data_type == 'dword':
            if len(registers) < 2:
                return None
            if register_order == 'big':
                return (registers[0] << 16) | registers[1]
            else:
                return (registers[1] << 16) | registers[0]
        elif data_type == 'float32':
            if len(registers) < 2:
                return None
            if register_order == 'big':
                combined = (registers[0] << 16) | registers[1]
            else:
                combined = (registers[1] << 16) | registers[0]
            return struct.unpack('>f', struct.pack('>I', combined))[0]
        elif data_type == 'string':
            string_bytes = []
            for reg in registers:
                string_bytes.extend([(reg >> 8) & 0xFF, reg & 0xFF])
            return bytes(string_bytes).decode('utf-8').strip('\x00')
        else:
            print("Unsupported data type.")
            return None
    except Exception as e:
        print(f"Error while parsing the data: {e}")
        return None

def main():
    ip = input("Enter the Modbus PLC IP address: ")
    port = int(input("Enter the port (default 502): ") or 502)
    unit_id = int(input("Enter the Unit ID/Slave ID (default 1): ") or 1)

    client = connect_to_plc(ip, port)

    while True:
        print("\nModbus register types:")
        print("1. Coils (0x)")
        print("2. Discrete Inputs (1x)")
        print("3. Holding Registers (4x)")
        print("4. Input Registers (3x)")

        register_type = input("Select the register type (1-4): ")

        address = int(input("Enter the start address: "))

        if register_type in ['1', '2']:
            count = int(input("Enter the number of bits to read: "))

            if register_type == '1':
                data = read_coils(client, address, count, unit_id)
            else:
                data = read_discrete_inputs(client, address, count, unit_id)

            if data:
                print(f"Values read: {data}")

        elif register_type in ['3', '4']:
            data_type = input("Enter the data type (int16, uint16, int32, uint32, dword, float32, string): ").lower()

            if data_type in ['int32', 'uint32', 'dword', 'float32']:
                count = 2
            elif data_type == 'string':
                string_length = int(input("Enter the string length (in characters): "))
                count = (string_length + 1) // 2
            else:
                count = 1

            if register_type == '3':
                registers = read_holding_registers(client, address, count, unit_id)
            else:
                registers = read_input_registers(client, address, count, unit_id)

            if registers:
                if data_type in ['int32', 'uint32', 'dword', 'float32']:
                    register_order = input("Register order for 32-bit data (big/little, default big): ").lower() or 'big'
                    parsed_value = parse_register_data(registers, data_type, register_order)
                else:
                    parsed_value = parse_register_data(registers, data_type)

                if parsed_value is not None:
                    print(f"Parsed value: {parsed_value}")
        else:
            print("Invalid selection.")
            continue

        continue_test = input("Do you want to keep reading other data? (y/n): ").lower()
        if continue_test != 'y':
            break

    client.close()
    print("Disconnected from the Modbus PLC.")

if __name__ == "__main__":
    main()
