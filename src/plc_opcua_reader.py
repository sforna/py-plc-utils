# -*- coding: utf-8 -*-
import asyncio
from asyncua import Client, Node
from asyncua.common.node import Node as NodeClass
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

def browse_nodes(client, loop, parent_node_id="i=85", show_values=False):
    """Esplora i nodi figli di un nodo padre."""
    try:
        async def _browse():
            if parent_node_id == "root":
                parent_node = client.nodes.root
            elif parent_node_id == "objects":
                parent_node = client.nodes.objects
            else:
                # Se parent_node_id contiene "NodeId(" significa che è già un oggetto NodeId
                if "NodeId(" in str(parent_node_id):
                    # Estrai i componenti dal NodeId
                    node_str = str(parent_node_id)
                    if "NamespaceIndex=3" in node_str and "ServerInterfaces" in node_str:
                        parent_node = client.get_node("ns=3;s=ServerInterfaces")
                    elif "NamespaceIndex=4" in node_str and "GESTIONALE" in node_str:
                        parent_node = client.get_node("ns=4;s=GESTIONALE")
                    else:
                        # Prova a convertire il NodeId in formato standard
                        try:
                            # Estrai namespace e identifier
                            ns_match = re.search(r'NamespaceIndex=(\d+)', node_str)

                            # Gestisci sia stringhe che interi
                            id_string_match = re.search(r"Identifier='([^']+)'", node_str)
                            id_int_match = re.search(r"Identifier=(\d+)", node_str)

                            if ns_match:
                                namespace = ns_match.group(1)

                                if id_string_match:
                                    # Identifier stringa
                                    identifier = id_string_match.group(1)
                                    node_id_str = f"ns={namespace};s={identifier}"
                                elif id_int_match:
                                    # Identifier intero
                                    identifier = id_int_match.group(1)
                                    node_id_str = f"ns={namespace};i={identifier}"
                                else:
                                    parent_node = client.get_node(parent_node_id)
                                    return

                                parent_node = client.get_node(node_id_str)
                            else:
                                parent_node = client.get_node(parent_node_id)
                        except Exception as e:
                            print(f"Errore conversione NodeId: {e}")
                            parent_node = client.get_node(parent_node_id)
                else:
                    parent_node = client.get_node(parent_node_id)

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
                        except:
                            node_info['value'] = "(non leggibile)"
                            node_info['value_type'] = "Unknown"

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

                print(display_text)
        else:
            print("Nessun nodo figlio trovato.")

        return nodes
    except Exception as e:
        print(f"Errore durante l'esplorazione dei nodi: {e}")
        return []

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

def export_all_nodes_to_json(client, loop, filename=None):
    """Esporta tutte le informazioni dei nodi in formato JSON."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"opcua_export_{timestamp}.json"

    async def _collect_all_data():
        server_data = {
            "server_info": {
                "export_timestamp": datetime.now().isoformat(),
                "endpoint_url": client.server_url.geturl()
            },
            "namespaces": [],
            "nodes": []
        }

        try:
            # Ottieni i namespace
            server_node = client.get_node("i=2253")  # Server node
            namespace_array = await server_node.get_child("0:NamespaceArray").read_value()
            server_data["namespaces"] = namespace_array
        except:
            pass

        # Funzione ricorsiva per esplorare tutti i nodi
        async def explore_node_recursive(node, level=0, max_level=10):
            if level > max_level:
                return []

            nodes_data = []
            try:
                node_info = {
                    "node_id": str(node.nodeid),
                    "namespace_index": node.nodeid.NamespaceIndex,
                    "identifier": str(node.nodeid.Identifier),
                    "identifier_type": str(node.nodeid.NodeIdType),
                    "level": level
                }

                # Informazioni base del nodo
                try:
                    browse_name = await node.read_browse_name()
                    node_info["browse_name"] = browse_name.Name
                    node_info["browse_namespace"] = browse_name.NamespaceIndex
                except:
                    node_info["browse_name"] = "Unknown"
                    node_info["browse_namespace"] = 0

                try:
                    display_name = await node.read_display_name()
                    node_info["display_name"] = display_name.Text
                except:
                    node_info["display_name"] = "Unknown"

                try:
                    node_class = await node.read_node_class()
                    node_info["node_class"] = str(node_class)
                    node_info["node_class_name"] = node_class.name
                except:
                    node_info["node_class"] = "Unknown"
                    node_info["node_class_name"] = "Unknown"

                # Se è una variabile, leggi il valore e il tipo di dato
                if node_info.get("node_class_name") == "Variable":
                    try:
                        value = await node.read_value()
                        node_info["value"] = str(value) if value is not None else None
                        node_info["value_type"] = type(value).__name__

                        # Se è un array, aggiungi informazioni sulla dimensione
                        if hasattr(value, '__len__') and not isinstance(value, str):
                            node_info["array_length"] = len(value)
                    except:
                        node_info["value"] = "Non leggibile"
                        node_info["value_type"] = "Unknown"

                    try:
                        data_type = await node.read_data_type()
                        node_info["data_type"] = str(data_type)
                    except:
                        node_info["data_type"] = "Unknown"

                nodes_data.append(node_info)

                # Esplora i figli se il livello non è troppo profondo
                if level < max_level:
                    try:
                        children = await node.get_children()
                        for child in children:
                            child_nodes = await explore_node_recursive(child, level + 1, max_level)
                            nodes_data.extend(child_nodes)
                    except:
                        pass

            except Exception as e:
                # Nodo con errore
                nodes_data.append({
                    "node_id": str(node.nodeid) if hasattr(node, 'nodeid') else "Unknown",
                    "error": str(e),
                    "level": level
                })

            return nodes_data

        # Inizia l'esplorazione dal nodo Objects
        try:
            objects_node = client.nodes.objects
            server_data["nodes"] = await explore_node_recursive(objects_node, 0, 5)  # Max 5 livelli
        except Exception as e:
            server_data["error"] = str(e)

        return server_data

    try:
        data = loop.run_until_complete(_collect_all_data())

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Dati esportati in formato JSON: {filename}")
        print(f"Totale nodi esportati: {len(data.get('nodes', []))}")
        return filename

    except Exception as e:
        print(f"Errore durante l'esportazione JSON: {e}")
        return None

def export_all_nodes_to_csv(client, loop, filename=None):
    """Esporta le variabili GESTIONALE in formato CSV."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gestionale_export_{timestamp}.csv"

    async def _collect_gestionale_data():
        csv_data = []
        try:
            # Esporta solo GESTIONALE per evitare timeout
            gestionale_node = client.get_node('ns=4;i=1')  # GESTIONALE
            children = await gestionale_node.get_children()

            for i, child in enumerate(children):
                try:
                    browse_name = await child.read_browse_name()
                    node_class = await child.read_node_class()

                    row = {
                        'numero': i + 1,
                        'nome_variabile': browse_name.Name,
                        'node_id': str(child.nodeid),
                        'namespace': child.nodeid.NamespaceIndex,
                        'identifier': child.nodeid.Identifier,
                        'tipo_nodo': node_class.name,
                        'node_id_semplice': f"ns={child.nodeid.NamespaceIndex};i={child.nodeid.Identifier}"
                    }

                    # Se è una variabile, leggi il valore
                    if node_class.name == 'Variable':
                        try:
                            value = await child.read_value()
                            if value is not None:
                                # Per array grandi, mostra solo sommario
                                if hasattr(value, '__len__') and not isinstance(value, str) and len(value) > 10:
                                    row['valore'] = f"Array di {len(value)} elementi"
                                else:
                                    row['valore'] = str(value)
                                row['tipo_valore'] = type(value).__name__
                            else:
                                row['valore'] = 'NULL'
                                row['tipo_valore'] = 'NoneType'
                        except Exception as e:
                            row['valore'] = f'Errore: {str(e)[:50]}...'
                            row['tipo_valore'] = 'Error'
                    else:
                        row['valore'] = ''
                        row['tipo_valore'] = ''

                    csv_data.append(row)

                except Exception as e:
                    # Aggiungi riga di errore
                    csv_data.append({
                        'numero': i + 1,
                        'nome_variabile': f'Errore_nodo_{i}',
                        'node_id': 'Error',
                        'namespace': 4,
                        'identifier': i,
                        'tipo_nodo': 'Error',
                        'node_id_semplice': 'Error',
                        'valore': str(e)[:50],
                        'tipo_valore': 'Error'
                    })

        except Exception as e:
            print(f"Errore accesso GESTIONALE: {e}")
            return []

        return csv_data

    try:
        print("Raccolta dati GESTIONALE...")
        data = loop.run_until_complete(_collect_gestionale_data())

        if data:
            fieldnames = ['numero', 'nome_variabile', 'node_id_semplice', 'namespace', 'identifier', 'tipo_nodo', 'valore', 'tipo_valore', 'node_id']

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            print(f"Dati esportati in formato CSV: {filename}")
            print(f"Totale variabili esportate: {len(data)}")
            return filename
        else:
            print("Nessun dato da esportare")
            return None

    except Exception as e:
        print(f"Errore durante l'esportazione CSV: {e}")
        return None

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
                        print(f"Tipo: {selected_node.get('value_type', 'N/A')}")

                        # Opzione per leggere il valore in tempo reale
                        refresh = input("\nVuoi aggiornare il valore? (s/n): ").lower()
                        if refresh == 's':
                            new_value = read_node_value(client, loop, selected_node['node_id'])
                            if new_value is not None:
                                parsed_value = parse_opcua_data(new_value)
                                print(f"Valore aggiornato: {parsed_value}")

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
            print("3. Elenca variabili da namespace specifico")
            print("4. Esci")

            choice = input("Seleziona un'opzione (1-4): ")
            
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
                # Elenca variabili da namespace specifico
                print("\n=== Elenca Variabili da Namespace ===")
                print("Namespace comuni:")
                print("- 0: Standard OPC UA")
                print("- 2: Device Information")
                print("- 3: Server Interfaces (contiene GESTIONALE)")
                print("- 4: GESTIONALE (variabili di processo)")

                try:
                    namespace = input("Inserisci namespace (es: 4): ").strip()
                    node_id = input("Inserisci identificatore nodo (es: 1 per GESTIONALE): ").strip()

                    if not namespace or not node_id:
                        print("Namespace e identificatore sono obbligatori")
                        continue

                    # Costruisci il node ID
                    full_node_id = f"ns={namespace};i={node_id}"
                    print(f"Esplorando nodo: {full_node_id}")

                    # Esplora il nodo
                    nodes = browse_nodes(client, loop, full_node_id, show_values=True)

                    if nodes:
                        print(f"\n=== Trovate {len(nodes)} variabili ===")
                        for i, node in enumerate(nodes, 1):
                            try:
                                # Estrai namespace e identifier dal node_id completo
                                node_str = node['node_id']
                                ns_match = re.search(r'NamespaceIndex=(\d+)', node_str)
                                id_match = re.search(r'Identifier=(\d+)', node_str)

                                if ns_match and id_match:
                                    node_id_simple = f"ns={ns_match.group(1)};i={id_match.group(1)}"
                                else:
                                    node_id_simple = "Error_parsing"

                                value_info = ""
                                if 'value' in node:
                                    if hasattr(node['value'], '__len__') and not isinstance(node['value'], str) and len(node['value']) > 10:
                                        value_info = f" = Array[{len(node['value'])} elementi]"
                                    else:
                                        value_info = f" = {node['value']}"

                                print(f"{i:2d}. {node['browse_name']:25} | {node_id_simple:15} | {node.get('node_class_name', 'Unknown'):10}{value_info}")
                            except:
                                print(f"{i:2d}. {node.get('browse_name', 'Unknown'):25} | Error parsing")

                        # Opzione per salvare in file
                        save_file = input("\nVuoi salvare l'elenco in un file? (s/n): ").lower()
                        if save_file == 's':
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"variables_ns{namespace}_id{node_id}_{timestamp}.txt"

                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(f"Variabili namespace {namespace}, nodo {node_id}\n")
                                f.write(f"Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                f.write("="*60 + "\n\n")

                                for i, node in enumerate(nodes, 1):
                                    try:
                                        # Estrai namespace e identifier dal node_id completo
                                        node_str = node['node_id']
                                        ns_match = re.search(r'NamespaceIndex=(\d+)', node_str)
                                        id_match = re.search(r'Identifier=(\d+)', node_str)

                                        if ns_match and id_match:
                                            node_id_simple = f"ns={ns_match.group(1)};i={id_match.group(1)}"
                                        else:
                                            node_id_simple = "Error_parsing"

                                        value_info = ""
                                        if 'value' in node:
                                            if hasattr(node['value'], '__len__') and not isinstance(node['value'], str) and len(node['value']) > 10:
                                                value_info = f" = Array[{len(node['value'])} elementi]"
                                            else:
                                                value_info = f" = {node['value']}"

                                        f.write(f"{i:2d}. {node['browse_name']:25} | {node_id_simple:15} | {node.get('node_class_name', 'Unknown'):10}{value_info}\n")
                                    except:
                                        f.write(f"{i:2d}. {node.get('browse_name', 'Unknown'):25} | Error parsing node_id\n")

                            print(f"File salvato: {filename}")
                    else:
                        print("Nessuna variabile trovata in questo nodo.")

                except ValueError:
                    print("Inserisci valori numerici validi")
                except Exception as e:
                    print(f"Errore: {e}")

            elif choice == '4':
                break
            else:
                print("Selezione non valida.")
                
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