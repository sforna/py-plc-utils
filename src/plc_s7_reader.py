import snap7
from snap7.util import *
import sys

def connect_to_plc(ip, rack, slot, port=102):
    plc = snap7.client.Client()
    try:
        plc.connect(ip, rack, slot, port)
        print(f"Connesso al PLC all'indirizzo IP: {ip}")
        return plc
    except Exception as e:
        print(f"Errore durante la connessione al PLC: {e}")
        sys.exit(1)

def read_plc_data(plc, db_number, start_offset, size):
    try:
        data = plc.db_read(db_number, start_offset, size)
        print(f"Dati letti dal DB {db_number} (Offset {start_offset}, Size {size}): {data}")
        return data
    except Exception as e:
        print(f"Errore durante la lettura dei dati: {e}")
        return None

def parse_data(data, data_type, offset, string_length=None):
    try:
        if data_type == 'bool':
            return get_bool(data, 0, offset)
        elif data_type == 'int':
            return get_int(data, offset)
        elif data_type == 'real':
            return get_real(data, offset)
        elif data_type == 'string':
            if string_length is None:
                raise ValueError("Per il tipo 'string', è necessario specificare la lunghezza.")
            return get_string(data, offset, string_length)
        elif data_type == 'udint':
            return get_udint(data, offset)
        else:
            print("Tipo di dato non supportato.")
            return None
    except Exception as e:
        print(f"Errore durante il parsing dei dati: {e}")
        return None

def get_string(data, offset, length):
    """Legge una stringa dal buffer di dati."""
    return data[offset:offset + length].decode('utf-8').strip('\x00')

def main():
    ip = input("Inserisci l'indirizzo IP del PLC: ")
    port = int(input("Inserisci la porta (default 102): ") or 102)
    rack = int(input("Inserisci il numero di rack (default 0): ") or 0)
    slot = int(input("Inserisci il numero di slot (default 0): ") or 0)

    plc = connect_to_plc(ip, rack, slot, port)

    while True:
        db_number = int(input("Inserisci il numero del DB da leggere (default 200): ") or 200)
        start_offset = int(input("Inserisci l'offset di partenza: "))
        
        # Scelta del tipo di dato
        data_type = input("Inserisci il tipo di dato (bool, int, string, real): ").lower()
        
        # Calcolo della dimensione in base al tipo di dato
        if data_type == 'bool':
            size = 1  # 1 byte per un bool
        elif data_type == 'int':
            size = 2  # 2 byte per un int
        elif data_type == 'real':
            size = 4  # 4 byte per un real
        elif data_type == 'udint':
            size = 4  # 4 byte per un udint
        elif data_type == 'string':
            string_length = int(input("Inserisci la lunghezza della stringa (in byte): "))
            size = string_length  # La dimensione è uguale alla lunghezza della stringa
        else:
            print("Tipo di dato non valido.")
            continue

        # Lettura dei dati
        data = read_plc_data(plc, db_number, start_offset, size)
        
        if data:
            if data_type == 'string':
                parsed_value = parse_data(data, data_type, 0, string_length)
            else:
                parsed_value = parse_data(data, data_type, 0)
            
            if parsed_value is not None:
                print(f"Valore parsato: {parsed_value}")

        continue_test = input("Vuoi continuare a leggere altri dati? (s/n): ").lower()
        if continue_test != 's':
            break

    plc.disconnect()
    print("Disconnesso dal PLC.")

if __name__ == "__main__":
    main()