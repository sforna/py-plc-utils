# -*- coding: utf-8 -*-
from pymodbus.client import ModbusTcpClient
import struct
import sys

def connect_to_plc(ip, port=502):
    client = ModbusTcpClient(ip, port=port)
    try:
        connection = client.connect()
        if connection:
            print(f"Connesso al PLC Modbus all'indirizzo IP: {ip}:{port}")
            return client
        else:
            print(f"Errore: Impossibile connettersi al PLC Modbus {ip}:{port}")
            sys.exit(1)
    except Exception as e:
        print(f"Errore durante la connessione al PLC: {e}")
        sys.exit(1)

def read_coils(client, address, count, unit_id=1):
    try:
        result = client.read_coils(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Errore durante la lettura delle coils: {result}")
            return None
        print(f"Coils lette (Indirizzo {address}, Quantita' {count}): {result.bits[:count]}")
        return result.bits[:count]
    except Exception as e:
        print(f"Errore durante la lettura delle coils: {e}")
        return None

def read_discrete_inputs(client, address, count, unit_id=1):
    try:
        result = client.read_discrete_inputs(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Errore durante la lettura degli input discreti: {result}")
            return None
        print(f"Input discreti letti (Indirizzo {address}, Quantita' {count}): {result.bits[:count]}")
        return result.bits[:count]
    except Exception as e:
        print(f"Errore durante la lettura degli input discreti: {e}")
        return None

def read_holding_registers(client, address, count, unit_id=1):
    try:
        result = client.read_holding_registers(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Errore durante la lettura dei registri di holding: {result}")
            return None
        print(f"Registri di holding letti (Indirizzo {address}, Quantita' {count}): {result.registers}")
        return result.registers
    except Exception as e:
        print(f"Errore durante la lettura dei registri di holding: {e}")
        return None

def read_input_registers(client, address, count, unit_id=1):
    try:
        result = client.read_input_registers(address, count=count, device_id=unit_id)
        if result.isError():
            print(f"Errore durante la lettura dei registri di input: {result}")
            return None
        print(f"Registri di input letti (Indirizzo {address}, Quantita' {count}): {result.registers}")
        return result.registers
    except Exception as e:
        print(f"Errore durante la lettura dei registri di input: {e}")
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
        elif data_type == 'uint32':
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
            print("Tipo di dato non supportato.")
            return None
    except Exception as e:
        print(f"Errore durante il parsing dei dati: {e}")
        return None

def main():
    ip = input("Inserisci l'indirizzo IP del PLC Modbus: ")
    port = int(input("Inserisci la porta (default 502): ") or 502)
    unit_id = int(input("Inserisci l'Unit ID/Slave ID (default 1): ") or 1)

    client = connect_to_plc(ip, port)

    while True:
        print("\nTipi di registro Modbus:")
        print("1. Coils (0x)")
        print("2. Discrete Inputs (1x)")
        print("3. Holding Registers (4x)")
        print("4. Input Registers (3x)")
        
        register_type = input("Seleziona il tipo di registro (1-4): ")
        
        address = int(input("Inserisci l'indirizzo di partenza: "))
        
        if register_type in ['1', '2']:
            count = int(input("Inserisci il numero di bit da leggere: "))
            
            if register_type == '1':
                data = read_coils(client, address, count, unit_id)
            else:
                data = read_discrete_inputs(client, address, count, unit_id)
                
            if data:
                print(f"Valori letti: {data}")
                
        elif register_type in ['3', '4']:
            data_type = input("Inserisci il tipo di dato (int16, uint16, int32, uint32, float32, string): ").lower()
            
            if data_type in ['int32', 'uint32', 'float32']:
                count = 2
            elif data_type == 'string':
                string_length = int(input("Inserisci la lunghezza della stringa (in caratteri): "))
                count = (string_length + 1) // 2
            else:
                count = 1
            
            if register_type == '3':
                registers = read_holding_registers(client, address, count, unit_id)
            else:
                registers = read_input_registers(client, address, count, unit_id)
            
            if registers:
                if data_type in ['int32', 'uint32', 'float32']:
                    register_order = input("Ordine dei registri per dati a 32-bit (big/little, default big): ").lower() or 'big'
                    parsed_value = parse_register_data(registers, data_type, register_order)
                else:
                    parsed_value = parse_register_data(registers, data_type)
                
                if parsed_value is not None:
                    print(f"Valore parsato: {parsed_value}")
        else:
            print("Selezione non valida.")
            continue

        continue_test = input("Vuoi continuare a leggere altri dati? (s/n): ").lower()
        if continue_test != 's':
            break

    client.close()
    print("Disconnesso dal PLC Modbus.")

if __name__ == "__main__":
    main()