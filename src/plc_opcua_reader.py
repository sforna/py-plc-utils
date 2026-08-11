# -*- coding: utf-8 -*-
import asyncio
from asyncua import Client, Node
import sys
import json
import csv
import re
from datetime import datetime

def connect_to_opcua_server(endpoint_url):
    """Connect to the OPC UA server and return the client."""
    client = Client(url=endpoint_url)
    try:
        # Perform the connection synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.connect())
        print(f"Connected to the OPC UA server: {endpoint_url}")
        return client, loop
    except Exception as e:
        print(f"Error while connecting to the OPC UA server: {e}")
        return None, None

def disconnect_from_server(client, loop):
    """Disconnect from the OPC UA server."""
    try:
        if client:
            loop.run_until_complete(client.disconnect())
            loop.close()
            print("Disconnected from the OPC UA server.")
    except Exception as e:
        print(f"Error while disconnecting: {e}")

def read_node_value(client, loop, node_id):
    """Read the value of an OPC UA node."""
    try:
        async def _read_value():
            node = client.get_node(node_id)
            value = await node.read_value()
            return value

        value = loop.run_until_complete(_read_value())
        print(f"Value read from node {node_id}: {value}")
        return value
    except Exception as e:
        print(f"Error while reading node {node_id}: {e}")
        return None

def read_node_data_type(client, loop, node_id):
    """Read the data type of an OPC UA node."""
    try:
        async def _read_data_type():
            node = client.get_node(node_id)
            data_type = await node.read_data_type()
            return data_type

        data_type = loop.run_until_complete(_read_data_type())
        return data_type
    except Exception as e:
        print(f"Error while reading the data type of node {node_id}: {e}")
        return None

def read_node_variant_type(client, loop, node_id):
    """Read the OPC UA data type of a node in a readable form."""
    try:
        async def _read_variant_type():
            node = client.get_node(node_id)
            # Read the NodeId of the data type
            data_type_node_id = await node.read_data_type()
            # Get the data type node
            data_type_node = client.get_node(data_type_node_id)
            # Read the browse name of the type (e.g. "Int16", "Int32", "Double")
            browse_name = await data_type_node.read_browse_name()
            return browse_name.Name

        type_name = loop.run_until_complete(_read_variant_type())
        return type_name
    except Exception as e:
        # On error, return None without printing (to avoid polluting the output)
        return None

def resolve_node_reference(client, node_reference):
    """Resolve a node reference into an asyncua Node object."""
    if isinstance(node_reference, Node):
        return node_reference

    if node_reference == "root":
        return client.nodes.root

    if node_reference == "objects":
        return client.nodes.objects

    node_str = str(node_reference)

    if "NodeId(" in node_str:
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
            raise ValueError(f"Unable to convert the provided NodeId: {exc}") from exc

        try:
            return client.get_node(node_reference)
        except Exception as exc:
            raise ValueError(f"Invalid NodeId: {exc}") from exc

    try:
        return client.get_node(node_reference)
    except Exception as exc:
        raise ValueError(f"Invalid NodeId: {exc}") from exc


def format_variable_value(value):
    """Format an OPC UA value compactly for the export."""
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
            return f"Array[{len(materialized)} elements]"
    except TypeError:
        pass

    return str(value)


def node_id_to_filename_fragment(node_id_str):
    """Build a readable file name fragment from a NodeId."""
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
    """Browse the child nodes of a parent node."""
    try:
        try:
            parent_node = resolve_node_reference(client, parent_node_id)
        except ValueError as exc:
            print(f"Error while resolving node {parent_node_id}: {exc}")
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

                    # If requested, also read the values of the variables
                    if show_values and node_class.name == 'Variable':
                        try:
                            value = await child.read_value()
                            node_info['value'] = value
                            node_info['value_type'] = type(value).__name__

                            # Also read the OPC UA data type
                            try:
                                data_type_node_id = await child.read_data_type()
                                data_type_node = client.get_node(data_type_node_id)
                                browse_name = await data_type_node.read_browse_name()
                                node_info['opcua_type'] = browse_name.Name
                            except:
                                node_info['opcua_type'] = "Unknown"
                        except:
                            node_info['value'] = "(not readable)"
                            node_info['value_type'] = "Unknown"
                            node_info['opcua_type'] = "Unknown"

                    nodes_info.append(node_info)
                except Exception as e:
                    print(f"Error while reading the node information: {e}")
                    continue

            return nodes_info

        nodes = loop.run_until_complete(_browse())

        if nodes:
            print(f"\nNodes found under {parent_node_id}:")
            for i, node in enumerate(nodes, 1):
                class_name = node.get('node_class_name', 'Unknown')
                display_text = f"{i}. {node['browse_name']} ({class_name})"

                if 'value' in node:
                    display_text += f" = {node['value']}"
                    if 'opcua_type' in node and node['opcua_type'] != 'Unknown':
                        display_text += f" [Type: {node['opcua_type']}]"

                print(display_text)
        else:
            print("No child node found.")

        return nodes
    except Exception as e:
        print(f"Error while browsing the nodes: {e}")
        return []

def export_variables_to_file(client, loop):
    """Export the child variables of a node to a timestamped text file."""
    default_node_id = "i=85"
    prompt = f"Enter the Node ID to export (default {default_node_id}, the Objects folder): "
    node_id_input = input(prompt).strip()
    if not node_id_input:
        node_id_input = default_node_id

    try:
        parent_node = resolve_node_reference(client, node_id_input)
    except ValueError as exc:
        print(f"Unable to resolve node '{node_id_input}': {exc}")
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
                    # Also read the OPC UA type
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
                print(f"Error while reading the child variables: {exc}")

        return entries

    try:
        variables = loop.run_until_complete(_collect_variables(parent_node))
    except Exception as exc:
        print(f"Error while collecting the variables: {exc}")
        return

    if not variables:
        print("No variable found under the specified node.")
        return

    variables = sorted(variables, key=lambda item: item['name'])

    resolved_node_id = str(parent_node.nodeid)
    namespace = getattr(parent_node.nodeid, "NamespaceIndex", None)
    identifier = getattr(parent_node.nodeid, "Identifier", None)

    if namespace is not None and identifier is not None:
        header_title = f"Variables of namespace {namespace}, node {identifier}"
    else:
        header_title = f"Variables of node {resolved_node_id}"

    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    filename_fragment = node_id_to_filename_fragment(resolved_node_id)
    filename = f"variables_{filename_fragment}_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"

    name_width = max(20, max(len(item['name']) for item in variables))
    node_id_width = max(12, max(len(item['node_id']) for item in variables))
    type_width = max(12, max(len(item.get('opcua_type', 'Unknown')) for item in variables))

    lines = [
        header_title,
        f"Generated: {timestamp_str}",
        "=" * 80,
        ""
    ]

    for index, item in enumerate(variables, 1):
        value_str = format_variable_value(item['value']) if item['readable'] else "(not readable)"
        opcua_type = item.get('opcua_type', 'Unknown')
        line = f"{index:2d}. {item['name']:<{name_width}} | {item['node_id']:<{node_id_width}} | {opcua_type:<{type_width}} = {value_str}"
        lines.append(line)

    try:
        with open(filename, "w", encoding="utf-8") as export_file:
            export_file.write("\n".join(lines) + "\n")
    except OSError as exc:
        print(f"Error while writing the file {filename}: {exc}")
        return

    print(f"Exported {len(variables)} variables to {filename}")

def parse_opcua_data(value, expected_type=None):
    """Analyse and format the value read from OPC UA."""
    if value is None:
        return "Null value"

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
            return f"Array [{len(list(value))} elements]: {list(value)}"
        else:
            return f"Type {value_type}: {value}"
    except Exception as e:
        return f"Error while parsing: {e}"

def interactive_node_navigation(client, loop):
    """Interactive hierarchical navigation of the OPC UA nodes."""
    current_node_id = "objects"
    navigation_path = ["Objects"]
    node_stack = [("objects", "Objects")]  # Stack used to navigate back

    while True:
        print(f"\n{'=' * 50}")
        print(f"Path: {' → '.join(navigation_path)}")
        print(f"{'=' * 50}")

        # Browse the current node
        nodes = browse_nodes(client, loop, current_node_id, show_values=True)

        if not nodes:
            print("No node found.")
            break

        print("\nOptions:")
        print("0. Go back")
        print("00. Back to the main menu")

        # Add options to navigate into the child nodes
        for i, node in enumerate(nodes, 1):
            if node['node_class_name'] in ['Object', 'Variable']:
                print(f"{i}. Browse/Read: {node['browse_name']}")

        try:
            choice = input(f"\nSelect (0-{len(nodes)}): ").strip()

            if choice == "0":
                # Go back
                if len(node_stack) > 1:
                    node_stack.pop()  # Remove the current node
                    navigation_path.pop()  # Remove it from the path display
                    current_node_id, _ = node_stack[-1]  # Back to the parent node
                else:
                    print("You are already at the root level.")
                continue

            elif choice == "00":
                # Back to the main menu
                break

            elif choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(nodes):
                    selected_node = nodes[index]

                    if selected_node['node_class_name'] == 'Variable':
                        # It is a variable, show the details
                        print(f"\n--- Variable details: {selected_node['browse_name']} ---")
                        print(f"Node ID: {selected_node['node_id']}")
                        print(f"Value: {selected_node.get('value', 'N/A')}")
                        print(f"Python type: {selected_node.get('value_type', 'N/A')}")
                        if 'opcua_type' in selected_node and selected_node['opcua_type'] != 'Unknown':
                            print(f"OPC UA type: {selected_node['opcua_type']}")

                        # Option to read the value in real time
                        refresh = input("\nDo you want to refresh the value? (y/n): ").lower()
                        if refresh == 'y':
                            new_value = read_node_value(client, loop, selected_node['node_id'])
                            if new_value is not None:
                                parsed_value = parse_opcua_data(new_value)
                                print(f"Updated value: {parsed_value}")
                                # Re-read the OPC UA type as well
                                variant_type = read_node_variant_type(client, loop, selected_node['node_id'])
                                if variant_type:
                                    print(f"OPC UA type: {variant_type}")

                        input("\nPress Enter to continue...")

                    elif selected_node['node_class_name'] == 'Object':
                        # It is an object, navigate into it
                        current_node_id = selected_node['node_id']
                        navigation_path.append(selected_node['browse_name'])
                        node_stack.append((current_node_id, selected_node['browse_name']))

                    else:
                        print(f"Node type not supported for navigation: {selected_node['node_class_name']}")
                        input("Press Enter to continue...")
                else:
                    print("Invalid selection.")
            else:
                print("Enter a valid number.")

        except ValueError:
            print("Enter a valid number.")
        except KeyboardInterrupt:
            print("\nNavigation interrupted by the user.")
            break
        except Exception as e:
            print(f"Error during navigation: {e}")
            input("Press Enter to continue...")

def main():
    print("=== PLC OPC UA Reader ===")

    client = None
    loop = None

    while client is None:
        user_input = input("Enter the PLC IP (e.g. 192.168.125.125) or the full URL: ")

        # If the input contains "opc.tcp://", use it as is
        if user_input.startswith("opc.tcp://"):
            endpoint_url = user_input
        else:
            # Otherwise assume it is just the IP and build the URL
            # Strip any protocol or port that may be present
            clean_ip = user_input.replace("http://", "").replace("https://", "").split(":")[0]
            endpoint_url = f"opc.tcp://{clean_ip}:4840"
            print(f"URL built: {endpoint_url}")

        if not endpoint_url.startswith("opc.tcp://"):
            print("The URL must start with 'opc.tcp://'")
            continue

        client, loop = connect_to_opcua_server(endpoint_url)

        if client is None:
            retry = input("Connection failed. Do you want to retry? (y/n): ").lower()
            if retry != 'y':
                print("Exiting the application.")
                return

    try:
        while True:
            print("\nAvailable options:")
            print("1. Read the value of a node")
            print("2. Browse nodes")
            print("3. Export variables to a file")
            print("x. Exit")

            choice = input("Select an option: ")

            if choice == '1':
                # Node value reading
                print("\nNode ID examples:")
                print("- ns=2;i=1001 (namespace 2, integer identifier 1001)")
                print("- ns=1;s=Temperature (namespace 1, string identifier)")
                print("- i=85 (Objects folder - default namespace)")

                node_id = input("Enter the Node ID to read: ")

                if not node_id:
                    print("Invalid Node ID.")
                    continue

                # Read the value
                value = read_node_value(client, loop, node_id)

                if value is not None:
                    # Read the data type as well
                    data_type = read_node_data_type(client, loop, node_id)

                    parsed_value = parse_opcua_data(value)
                    print(f"Parsed value: {parsed_value}")

                    if data_type:
                        print(f"OPC UA data type: {data_type}")

            elif choice == '2':
                # Interactive navigation
                print("\n=== Interactive Node Navigation ===")
                print("Use this option to navigate through the node hierarchy.")
                print("Browsing starts at the Objects folder; vendor-specific folders")
                print("(for example Siemens 'ServerInterfaces') appear as children of it.")
                interactive_node_navigation(client, loop)
            elif choice == '3':
                # Export the variables to a file
                export_variables_to_file(client, loop)

            elif choice == 'x':
                print("Exiting the application.")
                break

            continue_test = input("\nDo you want to continue with other operations? (y/n): ").lower()
            if continue_test != 'y':
                break

    except KeyboardInterrupt:
        print("\nInterrupted by the user.")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        disconnect_from_server(client, loop)

if __name__ == "__main__":
    main()
