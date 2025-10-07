
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp

def scan_local_network(network="192.168.1.1/24"):  # Define the function with a default network range
    # Create an ARP request packet for the specified IP range
    arp = ARP(pdst=network)
    
    # Create an Ethernet frame with a broadcast destination address (to reach all devices in the network)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    
    # Combine the Ethernet frame and ARP request into a single packet
    packet = ether/arp

    # Send the packet and receive responses (srp sends packets at the data link layer and returns responses)
    # We set timeout=2 to avoid waiting too long for responses and verbose=0 to suppress output
    result = srp(packet, timeout=2, verbose=0)[0]

    # Initialize an empty list to store information about active devices
    devices = []
    
    # Loop through each response packet (sent, received pairs)
    for sent, received in result:
        # Append device information as a dictionary with IP and MAC addresses
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})

    # Return the list of discovered devices
    return devices

# Example usage of the function
network = "192.168.1.1/24"  # Specify the IP range for the local network to scan
devices = scan_local_network(network)  # Call the function and store the result in 'devices'

# Print each found device with its IP and MAC address
print("Devices found on the network:")
for device in devices:
    print(f"IP: {device['ip']}, MAC: {device['mac']}")
