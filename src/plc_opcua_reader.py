# -*- coding: utf-8 -*-
import asyncio
from asyncua import Client, Node
import sys
import json
import csv
import re
from datetime import datetime

def connect_to_opcua_server(endpoint_url):
    """Connette al server OPC UA e restituisce il client."""
    client = Client(url=endpoint_url)
    try:
        # Esegue la connessione in modo sincrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.connect())
        print(f"Connesso al server OPC UA: {endpoint_url}")
        return client, loop
    except Exception as e:
        print(f"Errore durante la connessione al server OPC UA: {e}")
        return None, None

def disconnect_from_server(client, loop):
    """Disconnette dal server OPC UA."""
    try:
        if client:
            loop.run_until_complete(client.disconnect())
            loop.close()
            print("Disconnesso dal server OPC UA.")
    except Exception as e:
        print(f"Errore durante la disconnessione: {e}")

def read_node_value(client, loop, node_id):
    """Legge il valore di un nodo OPC UA."""
    try:
        async def _read_value():
            node = client.get_node(node_id)
            value = await node.read_value()
            return value
        
        value = loop.run_until_complete(_read_value())
        print(f"Valore letto dal nodo {node_id}: {value}")
        return value
    except Exception as e:
        print(f"Errore durante la lettura del nodo {node_id}: {e}")
        return None

def read_node_data_type(client, loop, node_id):
    """Legge il tipo di dato di un nodo OPC UA."""
    try:
        async def _read_data_type():
            node = client.get_node(node_id)
            data_type = await node.read_data_type()
            return data_type

        data_type = loop.run_until_complete(_read_data_type())
        return data_type
    except Exception as e:
        print(f"Errore durante la lettura del tipo di dato del nodo {node_id}: {e}")
        return None

def read_node_variant_type(client, loop, node_id):
    """Legge il tipo di dato OPC UA di un nodo in formato leggibile."""
    try:
        async def _read_variant_type():
            node = client.get_node(node_id)
            # Leggi il NodeId del tipo di dato
            data_type_node_id = await node.read_data_type()
            # Ottieni il nodo del tipo di dato
            data_type_node = client.get_node(data_type_node_id)
            # Leggi il browse name del tipo (es: "Int16", "Int32", "Double")
            browse_name = await data_type_node.read_browse_name()
            return browse_name.Name

        type_name = loop.run_until_complete(_read_variant_type())
        return type_name
    except Exception as e:
        # In caso di errore, restituisce None senza stampare (per non inquinare l'output)
        return None

def resolve_node_reference(client, node_reference):
    """Risolvi un riferimento di nodo in un oggetto Node di asyncua."""
    if isinstance(node_reference, Node):
        return node_reference

    if node_reference == "root":
        return client.nodes.root

    if node_reference == "objects":
        return client.nodes.objects

    node_str = str(node_reference)

    if "NodeId(" in node_str:
        if "NamespaceIndex=3" in node_str and "ServerInterfaces" in node_str:
            return client.get_node("ns=3;s=ServerInterfaces")
        if "NamespaceIndex=4" in node_str and "GESTIONALE" in node_str:
            return client.get_node("ns=4;s=GESTIONALE")

        try:
            namespace_match = re.search(r'NamespaceIndex=(\d+)', node_str)
            identifier_string_match = re.search(r"Identifier='([^']+)'", node_str)
            identifier_int_match = re.search(r"Identifier=(\d+)", node_str)

            if namespace_match:
                namespace = namespace_match.group(1)
                if identifier_string_match:
                    identifier = identifier_string_match.group(1)
                    node_id_str = f"ns={namespace};s={identifier}"
                    return client.get_node(node_id_str)
                if identifier_int_match:
                    identifier = identifier_int_match.group(1)
                    node_id_str = f"ns={namespace};i={identifier}"
                    return client.get_node(node_id_str)
        except Exception as exc:
            raise ValueError(f"Impossibile convertire il NodeId fornito: {exc}") from exc

        try:
            return client.get_node(node_reference)
        except Exception as exc:
            raise ValueError(f"NodeId non valido: {exc}") from exc

    try:
        return client.get_node(node_reference)
    except Exception as exc:
        raise ValueError(f"NodeId non valido: {exc}") from exc


def format_variable_value(value):
    """Formatta un valore OPC UA in modo compatto per l'export."""
    if value is None:
        return ""

    if isinstance(value, bool):
        return "True" if value else "False"

    if isinstance(value, (int, float)):
        return f"{value}"

    if isinstance(value, str):
        return value

    if isinstance(value, (bytes, bytearray)):
        return value.hex()

    try:
        if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, bytearray)):
            materialized = list(value)
            return f"Array[{len(materialized)} elementi]"
    except TypeError:
        pass

    return str(value)


def node_id_to_filename_fragment(node_id_str):
    """Genera una porzione di nome file leggibile a partire da un NodeId."""
    if not node_id_str:
        return "node"

    match = re.match(r"ns=(\d+);(i|s)=(.+)", node_id_str)
    if match:
        namespace, identifier_type, identifier = match.groups()
        sanitized_identifier = re.sub(r"[^0-9A-Za-z]+", "_", identifier).strip("_")
        if identifier_type == "i":
            suffix = f"id{sanitized_identifier}"
        else:
            suffix = f"s{sanitized_identifier}" if sanitized_identifier else "s"
        fragment = f"ns{namespace}_{suffix}"
        return fragment.strip("_") or "node"

    sanitized = re.sub(r"[^0-9A-Za-z]+", "_", node_id_str).strip("_")
    return sanitized or "node"


def browse_nodes(client, loop, parent_node_id="i=85", show_values=False):
    """Esplora i nodi figli di un nodo padre."""
    try:
        try:
            parent_node = resolve_node_reference(client, parent_node_id)
        except ValueError as exc:
            print(f"Errore durante la risoluzione del nodo {parent_node_id}: {exc}")
            return []

        async def _browse():
            children = await parent_node.get_children()
            nodes_info = []

            for child in children:
                try:
                    browse_name = await child.read_browse_name()
                    display_name = await child.read_display_name()
                    node_class = await child.read_node_class()
                    node_id = child.nodeid

                    node_info = {
                        'node_id': str(node_id),
                        'browse_name': browse_name.Name,
                        'display_name': display_name.Text,
                        'node_class': str(node_class),
                        'node_class_name': node_class.name
                    }

                    # Se richiesto, leggi anche i valori per le variabili
                    if show_values and node_class.name == 'Variable':
                        try:
                            value = await child.read_value()
                            node_info['value'] = value
                            node_info['value_type'] = type(value).__name__

                            # Leggi anche il tipo di dato OPC UA
                            try:
                                data_type_node_id = await child.read_data_type()
                                data_type_node = client.get_node(data_type_node_id)
                                browse_name = await data_type_node.read_browse_name()
                                node_info['opcua_type'] = browse_name.Name
                            except:
                                node_info['opcua_type'] = "Unknown"
                        except:
                            node_info['value'] = "(non leggibile)"
                            node_info['value_type'] = "Unknown"
                            node_info['opcua_type'] = "Unknown"

                    nodes_info.append(node_info)
                except Exception as e:
                    print(f"Errore durante la lettura delle informazioni del nodo: {e}")
                    continue

            return nodes_info

        nodes = loop.run_until_complete(_browse())

        if nodes:
            print(f"\nNodi trovati sotto {parent_node_id}:")
            for i, node in enumerate(nodes, 1):
                class_name = node.get('node_class_name', 'Unknown')
                display_text = f"{i}. {node['browse_name']} ({class_name})"

                if 'value' in node:
                    display_text += f" = {node['value']}"
                    if 'opcua_type' in node and node['opcua_type'] != 'Unknown':
                        display_text += f" [Tipo: {node['opcua_type']}]"

                print(display_text)
        else:
            print("Nessun nodo figlio trovato.")

        return nodes
    except Exception as e:
        print(f"Errore durante l'esplorazione dei nodi: {e}")
        return []

def export_variables_to_file(client, loop):
    """Esporta le variabili figlie di un nodo in un file testuale timestampato."""
    default_node_id = "ns=4;i=1"
    prompt = f"Inserisci il Node ID da esportare (default {default_node_id}): "
    node_id_input = input(prompt).strip()
    if not node_id_input:
        node_id_input = default_node_id

    try:
        parent_node = resolve_node_reference(client, node_id_input)
    except ValueError as exc:
        print(f"Impossibile risolvere il nodo '{node_id_input}': {exc}")
        return

    async def _collect_variables(node):
        children = await node.get_children()
        entries = []

        for child in children:
            try:
                node_class = await child.read_node_class()
                if node_class.name != 'Variable':
                    continue

                browse_name = await child.read_browse_name()
                display_name = await child.read_display_name()
                name = browse_name.Name or display_name.Text or str(child.nodeid)

                readable = True
                value = None
                opcua_type = "Unknown"
                try:
                    value = await child.read_value()
                    # Leggi anche il tipo OPC UA
                    try:
                        data_type_node_id = await child.read_data_type()
                        data_type_node = client.get_node(data_type_node_id)
                        browse_name = await data_type_node.read_browse_name()
                        opcua_type = browse_name.Name
                    except:
                        pass
                except Exception:
                    readable = False

                entries.append({
                    'name': name,
                    'node_id': str(child.nodeid),
                    'value': value,
                    'readable': readable,
                    'opcua_type': opcua_type
                })
            except Exception as exc:
                print(f"Errore durante la lettura delle variabili figlie: {exc}")

        return entries

    try:
        variables = loop.run_until_complete(_collect_variables(parent_node))
    except Exception as exc:
        print(f"Errore durante la raccolta delle variabili: {exc}")
        return

    if not variables:
        print("Nessuna variabile trovata sotto il nodo specificato.")
        return

    variables = sorted(variables, key=lambda item: item['name'])

    resolved_node_id = str(parent_node.nodeid)
    namespace = getattr(parent_node.nodeid, "NamespaceIndex", None)
    identifier = getattr(parent_node.nodeid, "Identifier", None)

    if namespace is not None and identifier is not None:
        header_title = f"Variabili namespace {namespace}, nodo {identifier}"
    else:
        header_title = f"Variabili nodo {resolved_node_id}"

    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    filename_fragment = node_id_to_filename_fragment(resolved_node_id)
    filename = f"variables_{filename_fragment}_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"

    name_width = max(20, max(len(item['name']) for item in variables))
    node_id_width = max(12, max(len(item['node_id']) for item in variables))
    type_width = max(12, max(len(item.get('opcua_type', 'Unknown')) for item in variables))

    lines = [
        header_title,
        f"Generato: {timestamp_str}",
        "=" * 80,
        ""
    ]

    for index, item in enumerate(variables, 1):
        value_str = format_variable_value(item['value']) if item['readable'] else "(non leggibile)"
        opcua_type = item.get('opcua_type', 'Unknown')
        line = f"{index:2d}. {item['name']:<{name_width}} | {item['node_id']:<{node_id_width}} | {opcua_type:<{type_width}} = {value_str}"
        lines.append(line)

    try:
        with open(filename, "w", encoding="utf-8") as export_file:
            export_file.write("\n".join(lines) + "\n")
    except OSError as exc:
        print(f"Errore durante la scrittura del file {filename}: {exc}")
        return

    print(f"Esportate {len(variables)} variabili in {filename}")

def parse_opcua_data(value, expected_type=None):
    """Analizza e formatta il valore letto da OPC UA."""
    if value is None:
        return "Valore nullo"

    try:
        value_type = type(value).__name__

        if isinstance(value, bool):
            return f"Boolean: {value}"
        elif isinstance(value, int):
            return f"Integer: {value}"
        elif isinstance(value, float):
            return f"Float: {value:.6f}"
        elif isinstance(value, str):
            return f"String: '{value}'"
        elif hasattr(value, '__iter__') and not isinstance(value, str):
            return f"Array [{len(list(value))} elementi]: {list(value)}"
        else:
            return f"Tipo {value_type}: {value}"
    except Exception as e:
        return f"Errore nel parsing: {e}"

def interactive_node_navigation(client, loop):
    """Navigazione interattiva gerarchica dei nodi OPC UA."""
    current_node_id = "objects"
    navigation_path = ["Objects"]
    node_stack = [("objects", "Objects")]  # Stack per la navigazione indietro

    while True:
        print(f"\n{'=' * 50}")
        print(f"Percorso: {' → '.join(navigation_path)}")
        print(f"{'=' * 50}")

        # Esplora il nodo corrente
        nodes = browse_nodes(client, loop, current_node_id, show_values=True)

        if not nodes:
            print("Nessun nodo trovato.")
            break

        print("\nOpzioni:")
        print("0. Torna indietro")
        print("00. Torna al menu principale")

        # Aggiungi opzioni per navigare nei nodi figli
        for i, node in enumerate(nodes, 1):
            if node['node_class_name'] in ['Object', 'Variable']:
                print(f"{i}. Esplora/Leggi: {node['browse_name']}")

        try:
            choice = input(f"\nSeleziona (0-{len(nodes)}): ").strip()

            if choice == "0":
                # Torna indietro
                if len(node_stack) > 1:
                    node_stack.pop()  # Rimuovi il nodo corrente
                    navigation_path.pop()  # Rimuovi dalla visualizzazione del percorso
                    current_node_id, _ = node_stack[-1]  # Torna al nodo padre
                else:
                    print("Sei già al livello radice.")
                continue

            elif choice == "00":
                # Torna al menu principale
                break

            elif choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(nodes):
                    selected_node = nodes[index]

                    if selected_node['node_class_name'] == 'Variable':
                        # È una variabile, mostra i dettagli
                        print(f"\n--- Dettagli Variabile: {selected_node['browse_name']} ---")
                        print(f"Node ID: {selected_node['node_id']}")
                        print(f"Valore: {selected_node.get('value', 'N/A')}")
                        print(f"Tipo Python: {selected_node.get('value_type', 'N/A')}")
                        if 'opcua_type' in selected_node and selected_node['opcua_type'] != 'Unknown':
                            print(f"Tipo OPC UA: {selected_node['opcua_type']}")

                        # Opzione per leggere il valore in tempo reale
                        refresh = input("\nVuoi aggiornare il valore? (s/n): ").lower()
                        if refresh == 's':
                            new_value = read_node_value(client, loop, selected_node['node_id'])
                            if new_value is not None:
                                parsed_value = parse_opcua_data(new_value)
                                print(f"Valore aggiornato: {parsed_value}")
                                # Rileggi anche il tipo OPC UA
                                variant_type = read_node_variant_type(client, loop, selected_node['node_id'])
                                if variant_type:
                                    print(f"Tipo OPC UA: {variant_type}")

                        input("\nPremi Invio per continuare...")

                    elif selected_node['node_class_name'] == 'Object':
                        # È un oggetto, naviga dentro
                        current_node_id = selected_node['node_id']
                        navigation_path.append(selected_node['browse_name'])
                        node_stack.append((current_node_id, selected_node['browse_name']))

                    else:
                        print(f"Tipo di nodo non supportato per la navigazione: {selected_node['node_class_name']}")
                        input("Premi Invio per continuare...")
                else:
                    print("Selezione non valida.")
            else:
                print("Inserisci un numero valido.")

        except ValueError:
            print("Inserisci un numero valido.")
        except KeyboardInterrupt:
            print("\nNavigazione interrotta dall'utente.")
            break
        except Exception as e:
            print(f"Errore durante la navigazione: {e}")
            input("Premi Invio per continuare...")

def main():
    print("=== PLC OPC UA Reader ===")
    
    client = None
    loop = None
    
    while client is None:
        user_input = input("Inserisci IP del PLC (es: 192.168.125.125) o URL completo: ")

        # Se l'input contiene "opc.tcp://", usalo così com'è
        if user_input.startswith("opc.tcp://"):
            endpoint_url = user_input
        else:
            # Altrimenti, assumi che sia solo l'IP e costruisci l'URL
            # Rimuovi eventuali protocolli o porte se presenti
            clean_ip = user_input.replace("http://", "").replace("https://", "").split(":")[0]
            endpoint_url = f"opc.tcp://{clean_ip}:4840"
            print(f"URL costruito: {endpoint_url}")

        if not endpoint_url.startswith("opc.tcp://"):
            print("L'URL deve iniziare con 'opc.tcp://'")
            continue
        
        client, loop = connect_to_opcua_server(endpoint_url)
        
        if client is None:
            retry = input("Connessione fallita. Vuoi riprovare? (s/n): ").lower()
            if retry != 's':
                print("Uscita dall'applicazione.")
                return

    try:
        while True:
            print("\nOpzioni disponibili:")
            print("1. Leggi valore di un nodo")
            print("2. Esplora nodi")
            print("3. Esporta variabili su file")
            print("x. Esci")

            choice = input("Seleziona un'opzione: ")
            
            if choice == '1':
                # Lettura valore nodo
                print("\nEsempi di Node ID:")
                print("- ns=2;i=1001 (namespace 2, identificatore intero 1001)")
                print("- ns=1;s=Temperature (namespace 1, identificatore stringa)")
                print("- i=85 (Objects folder - default namespace)")
                
                node_id = input("Inserisci il Node ID da leggere: ")
                
                if not node_id:
                    print("Node ID non valido.")
                    continue
                
                # Legge il valore
                value = read_node_value(client, loop, node_id)
                
                if value is not None:
                    # Legge anche il tipo di dato
                    data_type = read_node_data_type(client, loop, node_id)
                    
                    parsed_value = parse_opcua_data(value)
                    print(f"Valore parsato: {parsed_value}")
                    
                    if data_type:
                        print(f"Tipo di dato OPC UA: {data_type}")
                
            elif choice == '2':
                # Navigazione interattiva
                print("\n=== Navigazione Interattiva Nodi ===")
                print("Usa questa opzione per navigare attraverso la gerarchia dei nodi.")
                print("Potrai trovare GESTIONALE seguendo: Objects → ServerInterfaces → GESTIONALE")
                interactive_node_navigation(client, loop)
            elif choice == '3':
                # Esportazione variabili su file
                export_variables_to_file(client, loop)
                
            elif choice == 'x':
                print("Uscita dall'applicazione.")
                break
                
            continue_test = input("\nVuoi continuare con altre operazioni? (s/n): ").lower()
            if continue_test != 's':
                break
                
    except KeyboardInterrupt:
        print("\nInterruzione dell'utente.")
    except Exception as e:
        print(f"Errore nell'applicazione: {e}")
    finally:
        disconnect_from_server(client, loop)

if __name__ == "__main__":
    main()
