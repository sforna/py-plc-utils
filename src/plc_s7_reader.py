import math
import snap7
from snap7.util import *
import sys

def connect_to_plc(ip, rack, slot, port=102):
    plc = snap7.client.Client()
    try:
        plc.connect(ip, rack, slot, port)
        print(f"Connected to the PLC at IP address: {ip}")
        return plc
    except Exception as e:
        print(f"Error while connecting to the PLC: {e}")
        return None

def read_plc_data(plc, area, db_number, start_offset, size):
    try:
        data = plc.read_area(area, db_number, start_offset, size)

        # Try to get a readable name for the area
        try:
            area_name = area.name
        except AttributeError:
            area_name = str(area)

        if area == snap7.Area.DB:
             print(f"Data read from DB {db_number} (Offset {start_offset}, Size {size}): {data}")
        else:
             print(f"Data read from area {area_name} (Offset {start_offset}, Size {size}): {data}")
        return data
    except Exception as e:
        print(f"Error while reading the data: {e}")
        return None

def parse_data(data, data_type, index, string_length=None, byte_index=0):
    """
    Parse the raw data.
    'index' is the bit index if data_type is 'bool',
    'byte_index' is the byte within the buffer for the 'bool' type,
    otherwise 'index' is the starting byte index (usually 0).
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
                raise ValueError("For the 'string' type, the length must be specified.")
            return get_string(data, index, string_length)
        elif data_type == 'udint':
            return get_udint(data, index)
        else:
            print("Unsupported data type.")
            return None
    except Exception as e:
        print(f"Error while parsing the data: {e}")
        return None

def get_string(data, offset, length):
    """Read a string from the data buffer."""
    return data[offset:offset + length].decode('utf-8').strip('\x00')

def scan_plc_network(ip, db_number, port=102):
    """Scan every rack/slot combination to find PLCs that are online."""
    print(f"\nStarting PLC scan on IP: {ip}")
    print("Scan in progress... (timeouts are normal)")

    online_plcs = []
    connected_plcs = []  # PLCs connected but without an accessible DB
    total_combinations = 8 * 11  # rack 0-7, slot 0-10
    current = 0

    for rack in range(8):  # rack from 0 to 7
        for slot in range(11):  # slot from 0 to 10
            current += 1
            print(f"Progress: {current}/{total_combinations} - Testing Rack:{rack} Slot:{slot}", end='\r')

            plc = snap7.client.Client()
            try:
                plc.connect(ip, rack, slot, port)

                # Test the connection by reading 1 byte from the specified DB
                try:
                    plc.db_read(db_number, 0, 1)
                    online_plcs.append((rack, slot, f"DB{db_number} OK"))
                    print(f"\n✓ PLC ONLINE - IP:{ip} Rack:{rack} Slot:{slot} (DB{db_number} accessible)")
                except Exception as db_error:
                    # PLC connected but DB not accessible
                    connected_plcs.append((rack, slot, str(db_error)))
                    print(f"\n~ PLC CONNECTED - IP:{ip} Rack:{rack} Slot:{slot} (DB{db_number} not accessible)")

                plc.disconnect()
            except Exception as conn_error:
                # Connection failed - silent for the usual timeouts
                if "timeout" not in str(conn_error).lower():
                    print(f"\nConnection error Rack:{rack} Slot:{slot} - {conn_error}")

    print(f"\nScan complete!")

    # Show the results
    all_found = online_plcs + connected_plcs
    if all_found:
        print(f"\nPLCs found ({len(all_found)}):")
        for i, (rack, slot, status) in enumerate(all_found, 1):
            print(f"{i}. IP:{ip} Rack:{rack} Slot:{slot} - {status}")

        # Return only the ones with an accessible DB for the connection
        if online_plcs:
            return [(rack, slot) for rack, slot, _ in online_plcs]
        else:
            print(f"\nNo PLC with an accessible DB{db_number} was found.")
            print("You can still try a direct connection with the connected PLCs.")
            return [(rack, slot) for rack, slot, _ in connected_plcs]
    else:
        print("No PLC found online.")
        return []

def main():
    print("=== PLC S7 Reader ===")
    print("1. Direct connection")
    print("2. Scan mode")

    mode = input("Select mode (1-2): ")

    if mode == '2':
        # Scan mode
        ip = input("Enter the PLC IP address: ")
        port = int(input("Enter the port (default 102): ") or 102)
        db_number = int(input("Enter the DB number to test (default 1): ") or 1)

        online_plcs = scan_plc_network(ip, db_number, port)

        if not online_plcs:
            print("No PLC found. Exiting the application.")
            return

        # Select a PLC from the list
        if len(online_plcs) == 1:
            rack, slot = online_plcs[0]
            print(f"Automatically connecting to the PLC found: Rack:{rack} Slot:{slot}")
        else:
            print("\nSelect the PLC to connect to:")
            try:
                choice = int(input(f"Enter the number (1-{len(online_plcs)}): ")) - 1
                rack, slot = online_plcs[choice]
            except (ValueError, IndexError):
                print("Invalid selection. Exiting the application.")
                return

        plc = connect_to_plc(ip, rack, slot, port)
        if plc is None:
            print("Error while connecting to the selected PLC.")
            return
    else:
        # Direct connection mode
        plc = None

        while plc is None:
            ip = input("Enter the PLC IP address: ")
            port = int(input("Enter the port (default 102): ") or 102)
            rack = int(input("Enter the rack number (default 0): ") or 0)
            slot = int(input("Enter the slot number (default 0): ") or 0)

            plc = connect_to_plc(ip, rack, slot, port)

            if plc is None:
                retry = input("Connection failed. Do you want to retry? (y/n): ").lower()
                if retry != 'y':
                    print("Exiting the application.")
                    return

    while True:
        # Memory area selection
        print("\n--- Memory Area Selection ---")
        print("1. DB (Data Block)")
        print("2. Input (PE)")
        print("3. Output (PA)")
        print("4. Merker (MK)")
        print("5. Counters (CT)")
        print("6. Timers (TM)")

        area_input = input("Select an area (1-6, default 1): ").strip()

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
            db_number = int(input("Enter the DB number to read (default 200): ") or 200)

        start_offset = int(input("Enter the start offset: "))

        # Data type choice
        data_type = input("Enter the data type (bool, bool_array, int, udint, string, real): ").lower()

        bit_index = 0
        string_length = None
        bool_array_length = None

        # Compute the size based on the data type
        if data_type == 'bool':
            size = 1  # 1 byte for a bool
            try:
                bit_index = int(input("Enter the bit position (0-7): "))
                if not 0 <= bit_index <= 7:
                    print("Bit index must be between 0 and 7. Set to 0.")
                    bit_index = 0
            except ValueError:
                print("Invalid input. Bit index set to 0.")
                bit_index = 0

        elif data_type == 'bool_array':
            try:
                bool_array_length = int(input("Enter the number of elements in the bool array: "))
                if bool_array_length <= 0:
                    print("Invalid length. Set to 1.")
                    bool_array_length = 1
            except ValueError:
                print("Invalid input. Length set to 1.")
                bool_array_length = 1
            size = math.ceil(bool_array_length / 8)

        elif data_type == 'int':
            size = 2  # 2 bytes for an int
        elif data_type == 'real':
            size = 4  # 4 bytes for a real
        elif data_type == 'udint':
            size = 4  # 4 bytes for a udint
        elif data_type == 'string':
            string_length = int(input("Enter the string length (in bytes): "))
            size = string_length  # The size equals the string length
        else:
            print("Invalid data type.")
            continue

        # Read the data
        data = read_plc_data(plc, area, db_number, start_offset, size)

        if data:
            if data_type == 'bool_array':
                print(f"Array of {bool_array_length} bools:")
                for i in range(bool_array_length):
                    val = parse_data(data, 'bool', i % 8, byte_index=i // 8)
                    print(f"  [{i}] = {val}")
            else:
                # For bool, pass bit_index as the index parameter
                # Otherwise pass 0 as the index (byte offset within the buffer read)
                parse_index = bit_index if data_type == 'bool' else 0

                parsed_value = parse_data(data, data_type, parse_index, string_length)

                if parsed_value is not None:
                    print(f"Parsed value: {parsed_value}")

        continue_test = input("Do you want to keep reading other data? (y/n): ").lower()
        if continue_test != 'y':
            break

    if plc:
        plc.disconnect()
        print("Disconnected from the PLC.")

if __name__ == "__main__":
    main()
