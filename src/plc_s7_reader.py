import math
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
        return None

def read_plc_data(plc, area, db_number, start_offset, size):
    try:
        data = plc.read_area(area, db_number, start_offset, size)
        
        # Tentativo di ottenere un nome leggibile per l'area
        try:
            area_name = area.name
        except AttributeError:
            area_name = str(area)

        if area == snap7.Area.DB:
             print(f"Dati letti dal DB {db_number} (Offset {start_offset}, Size {size}): {data}")
        else:
             print(f"Dati letti dall'area {area_name} (Offset {start_offset}, Size {size}): {data}")
        return data
    except Exception as e:
        print(f"Errore durante la lettura dei dati: {e}")
        return None

def parse_data(data, data_type, index, string_length=None, byte_index=0):
    """
    Parsa i dati grezzi.
    'index' è l'indice del bit se data_type è 'bool',
    'byte_index' è il byte all'interno del buffer per il tipo 'bool',
    altrimenti 'index' è l'indice del byte di partenza (solitamente 0).
    """
    try:
        if data_type == 'bool':
            return get_bool(data, byte_index, index)
        elif data_type == 'int':
            return get_int(data, index)
        elif data_type == 'real':
            return get_real(data, index)
        elif data_type == 'string':
            if string_length is None:
                raise ValueError("Per il tipo 'string', è necessario specificare la lunghezza.")
            return get_string(data, index, string_length)
        elif data_type == 'udint':
            return get_udint(data, index)
        else:
            print("Tipo di dato non supportato.")
            return None
    except Exception as e:
        print(f"Errore durante il parsing dei dati: {e}")
        return None

def get_string(data, offset, length):
    """Legge una stringa dal buffer di dati."""
    return data[offset:offset + length].decode('utf-8').strip('\x00')

def scan_plc_network(ip, db_number, port=102):
    """Scansiona tutte le combinazioni rack/slot per trovare PLC online."""
    print(f"\nInizio scansione PLC su IP: {ip}")
    print("Scansione in corso... (i timeout sono normali)")
    
    online_plcs = []
    connected_plcs = []  # PLC connessi ma senza DB accessibile
    total_combinations = 8 * 11  # rack 0-7, slot 0-10
    current = 0
    
    for rack in range(8):  # rack da 0 a 7
        for slot in range(11):  # slot da 0 a 10
            current += 1
            print(f"Progresso: {current}/{total_combinations} - Testando Rack:{rack} Slot:{slot}", end='\r')
            
            plc = snap7.client.Client()
            try:
                plc.connect(ip, rack, slot, port)
                
                # Testa la connessione leggendo 1 byte dal DB specificato
                try:
                    plc.db_read(db_number, 0, 1)
                    online_plcs.append((rack, slot, f"DB{db_number} OK"))
                    print(f"\n✓ PLC ONLINE - IP:{ip} Rack:{rack} Slot:{slot} (DB{db_number} accessibile)")
                except Exception as db_error:
                    # PLC connesso ma DB non accessibile
                    connected_plcs.append((rack, slot, str(db_error)))
                    print(f"\n~ PLC CONNESSO - IP:{ip} Rack:{rack} Slot:{slot} (DB{db_number} non accessibile)")
                
                plc.disconnect()
            except Exception as conn_error:
                # Connessione fallita - silenzioso per i timeout normali
                if "timeout" not in str(conn_error).lower():
                    print(f"\nErrore connessione Rack:{rack} Slot:{slot} - {conn_error}")
    
    print(f"\nScansione completata!")
    
    # Mostra risultati
    all_found = online_plcs + connected_plcs
    if all_found:
        print(f"\nPLC trovati ({len(all_found)}):")
        for i, (rack, slot, status) in enumerate(all_found, 1):
            print(f"{i}. IP:{ip} Rack:{rack} Slot:{slot} - {status}")
        
        # Restituisce solo quelli con DB accessibile per la connessione
        if online_plcs:
            return [(rack, slot) for rack, slot, _ in online_plcs]
        else:
            print(f"\nNessun PLC con DB{db_number} accessibile trovato.")
            print("Puoi comunque provare la connessione diretta con i PLC connessi.")
            return [(rack, slot) for rack, slot, _ in connected_plcs]
    else:
        print("Nessun PLC trovato online.")
        return []

def main():
    print("=== PLC S7 Reader ===")
    print("1. Connessione diretta")
    print("2. Modalità scansione")
    
    mode = input("Seleziona modalità (1-2): ")
    
    if mode == '2':
        # Modalità scansione
        ip = input("Inserisci l'indirizzo IP del PLC: ")
        port = int(input("Inserisci la porta (default 102): ") or 102)
        db_number = int(input("Inserisci il numero del DB da testare (default 1): ") or 1)
        
        online_plcs = scan_plc_network(ip, db_number, port)
        
        if not online_plcs:
            print("Nessun PLC trovato. Uscita dall'applicazione.")
            return
        
        # Selezione PLC dalla lista
        if len(online_plcs) == 1:
            rack, slot = online_plcs[0]
            print(f"Connessione automatica al PLC trovato: Rack:{rack} Slot:{slot}")
        else:
            print("\nSeleziona il PLC a cui connettersi:")
            try:
                choice = int(input(f"Inserisci il numero (1-{len(online_plcs)}): ")) - 1
                rack, slot = online_plcs[choice]
            except (ValueError, IndexError):
                print("Selezione non valida. Uscita dall'applicazione.")
                return
        
        plc = connect_to_plc(ip, rack, slot, port)
        if plc is None:
            print("Errore nella connessione al PLC selezionato.")
            return
    else:
        # Modalità connessione diretta
        plc = None
        
        while plc is None:
            ip = input("Inserisci l'indirizzo IP del PLC: ")
            port = int(input("Inserisci la porta (default 102): ") or 102)
            rack = int(input("Inserisci il numero di rack (default 0): ") or 0)
            slot = int(input("Inserisci il numero di slot (default 0): ") or 0)

            plc = connect_to_plc(ip, rack, slot, port)
            
            if plc is None:
                retry = input("Connessione fallita. Vuoi riprovare? (s/n): ").lower()
                if retry != 's':
                    print("Uscita dall'applicazione.")
                    return

    while True:
        # Selezione Area di Memoria
        print("\n--- Selezione Area di Memoria ---")
        print("1. DB (Data Block)")
        print("2. Input (PE)")
        print("3. Output (PA)")
        print("4. Merker (MK)")
        print("5. Contatori (CT)")
        print("6. Timer (TM)")
        
        area_input = input("Seleziona area (1-6, default 1): ").strip()
        
        # Default
        area = snap7.Area.DB
        db_number = 0
        
        if area_input == '2':
            area = snap7.Area.PE
        elif area_input == '3':
            area = snap7.Area.PA
        elif area_input == '4':
            area = snap7.Area.MK
        elif area_input == '5':
            area = snap7.Area.CT
        elif area_input == '6':
            area = snap7.Area.TM
        else:
            area = snap7.Area.DB

        if area == snap7.Area.DB:
            db_number = int(input("Inserisci il numero del DB da leggere (default 200): ") or 200)

        start_offset = int(input("Inserisci l'offset di partenza: "))
        
        # Scelta del tipo di dato
        data_type = input("Inserisci il tipo di dato (bool, bool_array, int, udint, string, real): ").lower()

        bit_index = 0
        string_length = None
        bool_array_length = None

        # Calcolo della dimensione in base al tipo di dato
        if data_type == 'bool':
            size = 1  # 1 byte per un bool
            try:
                bit_index = int(input("Inserisci la posizione del bit (0-7): "))
                if not 0 <= bit_index <= 7:
                    print("Bit index deve essere tra 0 e 7. Impostato a 0.")
                    bit_index = 0
            except ValueError:
                print("Input non valido. Bit index impostato a 0.")
                bit_index = 0

        elif data_type == 'bool_array':
            try:
                bool_array_length = int(input("Inserisci il numero di elementi dell'array di bool: "))
                if bool_array_length <= 0:
                    print("Lunghezza non valida. Impostata a 1.")
                    bool_array_length = 1
            except ValueError:
                print("Input non valido. Lunghezza impostata a 1.")
                bool_array_length = 1
            size = math.ceil(bool_array_length / 8)

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
        data = read_plc_data(plc, area, db_number, start_offset, size)
        
        if data:
            if data_type == 'bool_array':
                print(f"Array di {bool_array_length} bool:")
                for i in range(bool_array_length):
                    val = parse_data(data, 'bool', i % 8, byte_index=i // 8)
                    print(f"  [{i}] = {val}")
            else:
                # Se è bool, passiamo bit_index come parametro index
                # Se è altro, passiamo 0 come index (byte offset nel buffer letto)
                parse_index = bit_index if data_type == 'bool' else 0

                parsed_value = parse_data(data, data_type, parse_index, string_length)

                if parsed_value is not None:
                    print(f"Valore parsato: {parsed_value}")

        continue_test = input("Vuoi continuare a leggere altri dati? (s/n): ").lower()
        if continue_test != 's':
            break

    if plc:
        plc.disconnect()
        print("Disconnesso dal PLC.")

if __name__ == "__main__":
    main()
