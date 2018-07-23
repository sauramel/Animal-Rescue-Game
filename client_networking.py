from game_functions import restrictive_input, encode_DP, decode_DP
from game_classes import DataPacket
import socket
import pickle
import zlib
import re

def query_host_port(default=(None,None)):

    HOST = restrictive_input(
        "Enter host IP: ",
        lambda x: x,
        lambda x: re.match("([0-9]{1,3}\.){3}[0-9]{1,3}", x),
        default=default[0])

    PORT = restrictive_input(
        "Enter host port: ",
        lambda x: int(x),
        lambda x: 0 < x < 65536,
        default=default[1]
    )
    return (HOST,PORT)

def sendDataPacket(DP, HOST, PORT):

    compressed_DP = encode_DP(DP)
    data_length = len(compressed_DP)
    length_bytes = data_length.to_bytes(2, 'big')

    s = socket.socket()
    s.connect((HOST, PORT))
    length_bytes_sent = 0
    while length_bytes_sent < 2:
        length_bytes_sent += s.send(length_bytes[length_bytes_sent:])
    print("Sent handshake length to server ({})".format(data_length))
    ack = s.recv(4096) # Wait for acknowledgement from the server
    if len(ack) != 1:
        print("BAD ACK FROM SERVER")
        return False
    print("Server says it acknowledges handshake length")
    sent_length = 0
    while sent_length < data_length:
        length_to_send = min(data_length - sent_length, 4096) # How large should the next chunk be
        current_chunk = compressed_DP[sent_length:sent_length+length_to_send]
        chunk_length_sent = s.send(current_chunk)
        sent_length += chunk_length_sent
        print("{} bytes sent in current chunk.".format(chunk_length_sent))
    print("Data Packet sent Successfully! ({})".format(DP.type))

    print("Waiting for end_ack length from server...")
    end_ack_length_bytes = s.recv(4096)
    end_ack_length = int.from_bytes(end_ack_length_bytes, 'big')
    print("Received ack length in bytes ({})".format(end_ack_length))

    send_ack(s, basic=True) # Tell server that length is received
    print("Ready to receive end ack packet.")

    end_ack_data = b''
    while len(end_ack_data) < end_ack_length:
        end_ack_data += s.recv(4096)
        print("Received {} bytes so far.".format(len(end_ack_data)))

    end_ack = decode_DP(end_ack_data)
    if end_ack.type == "GOODBYE":
        s.shutdown("SHUT_RDWR")
        s.close()
        return None
    else:
        print("{} Acknowledgement received from server.".format(end_ack.type))
        return end_ack, s

def recvDataPacket(conn):
    print("Waiting for length of new message")
    length_bytes = conn.recv(4096)
    print("Length received: {} bytes.".format(length_bytes))

    message_length = int.from_bytes(length_bytes, 'big')

    conn.send(b'A') # Send acknowledgement of message length received
    print("Acknowledgement of length sent to server")

    message = b''
    while len(message) < message_length:
        message += conn.recv(4096)
    DP = decode_DP(message)
    print("Received and decoded data packet ({})".format(DP.type))

    ### Do some processing with DP maybe?

    ack = DataPacket("GOODBYE", b'')
    encoded_ack = encode_DP(ack)

    len_message = len(encoded_ack)
    sent_bytes = 0
    while sent_bytes < len_message:
        sent_bytes += conn.send(encoded_ack)

    return DP

def send_ack(conn, type=None, basic=False):
    if basic:
        conn.send(b"A")
    else:
        ack_packet = DataPacket(type, b'')
        encoded_ack = encode_DP(ack_packet)
        encoded_ack_length = len(encoded_ack)
        encoded_ack_length_bytes = encoded_ack_length.to_bytes(2, 'big')
        conn.send(encoded_ack_length_bytes)

        bytes_sent = 0
        while bytes_sent < encoded_ack_length:
            bytes_sent += conn.send(encoded_ack[bytes_sent:])

def send_handshake(HOST, PORT):
    handshake = DataPacket("HAND","GorDaeMert")
    try:
        result = sendDataPacket(handshake, HOST, PORT)
    except:
        print("Cannot connect to this server!")
        return False
    if result:
        server_response, conn = result
        while server_response:
            server_response, conn = interpret_DataPacket(server_response, conn)
    else:
        print("The server received but didn't reciprocate your handshake :'(")
    return True

def interpret_DataPacket(DP, conn=None):
    packet_type = DP.type
    packet_data = DP.data
    if packet_type == "NEED_INPUT":
        send_ack(conn, "GOODBYE")
        query = packet_data[0]
        max_length = packet_data[1]
        response_ID = packet_data[2]
        print("THE SERVER ASKS:")
        x = input("{} [Max Length: {}]: ".format(query, max_length))
        x = x[:max_length]
        response = DataPacket("RESPONSE", [[x], response_ID])
        server_response = sendDataPacket(response, HOST, PORT)
        return server_response
    elif packet_type == "MESSAGE":
        send_ack(conn, "GOODBYE")
        message = packet_data
        print("MESSAGE FROM SERVER:")
        print("'{}'".format(message))
    elif packet_type == "ACK_KEEP_ALIVE":
        DP = recvDataPacket(conn)
        return DP, conn
    else:
        print("Trying to interpret unknown packet type '{}'".format(packet_type))
        return None
