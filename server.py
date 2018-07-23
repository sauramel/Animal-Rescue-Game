from game_classes import *
import threading
import os.path
import random
import socket
import pickle
import sched
import zlib
import time

HOST = ''  # Symbolic of the local host address
PORT = 222 # This can be whatever we want

save_lock = threading.Lock()
save_scheduler = sched.scheduler()

class Game_Data:
    def __init__(self, map=None, client_chars={}):
        self.map = map
        self.client_chars = client_chars

    def __hash__(self):
        return hash(
            str(len(self.client_chars)) + '|' + str(hash(self.map))
        )

# Naming convention for saved games:
# S_<Time>_<Checksum>.mdq
def Save_Game(game_data):
    save_lock.acquire()

    game_hash = hash(game_data)
    hash_end = str(game_hash)[-6:]
    encoded_game_data = zlib.compress(pickle.dumps(game_data),9)
    cur_time = round(time.time())
    with open("saved_games/S_{}_{}.mdq".format(cur_time, hash_end), "wb") as f:
        f.write(encoded_game_data)
    print("Game Saved Successfully")

    save_lock.release()

def Load_Game(filename, check_hash=True):
    hash_end = filename.split("_")[-1].split(".")[0]
    with open(filename, "rb") as f:
        encoded_game_data = f.read()
    decoded_game_data = pickle.loads(zlib.decompress(encoded_game_data))
    game_hash = hash(decoded_game_data)
    if check_hash and str(game_hash)[-6:] != hash_end:
        print("ERROR LOADING GAME DATA: HASH DOES NOT MATCH")
        print("HASH_END IN FILENAME: {}".format(hash_end))
        print("CALCULATED HASH: {}".format(game_hash))
        print(decoded_game_data.map.locations[0].name)
        return None
    else:
        return decoded_game_data

if os.path.isdir("saved_games"):
    saves = os.listdir("saved_games")
    # Change below when ready to fix saved-games
    if True: #len(saves) == 0:
        print("No saved games found... Creating new game...")
        map = Map(size_x=7, size_y=7)
        client_chars = {}
        game_data = Game_Data(map, client_chars)
        Save_Game(game_data)
    else:
        saves.sort(reverse=True)
        print("Saved games: {}".format(saves))
        print("Loading most recent saved game.")
        game_data = Load_Game("saved_games/{}".format(saves[0]))
else:
    os.mkdir("saved_games")

####### DATA FORMAT #######:
# 2 bytes for message length (N)
# N bytes for encoded packet

def sendDataPacket(conn, DP):





    ### ADD DEBUG MESSAGES HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!





    compressed_DP = encode_DP(DP)
    data_length = len(compressed_DP)
    length_bytes = data_length.to_bytes(2, 'big')

    conn.send(length_bytes)
    ack = conn.recv(4096) # Wait for acknowledgement from the client
    if len(ack) != 1:
        print("BAD ACK FROM CLIENT")
    sent_length = 0
    while sent_length < data_length:
        to_send = min(data_length - sent_length, 4096) # How large should the next chunk be
        chunk_length_sent = conn.send(compressed_DP[sent_length:sent_length+to_send])
        sent_length += chunk_length_sent
    print("Data Packet sent Successfully! ({})".format(DP.type))
    end_ack_length_bytes = conn.recv(4096)
    end_ack_length = int.from_bytes(end_ack_length_bytes, 'big')

    ack_data = b''
    while len(ack_data) < end_ack_length:
        ack_data += conn.recv(4096)

    end_ack = decode_DP(end_ack)
    if end_ack.type == "GOODBYE":
        conn.shutdown("SHUT_RDWR")
        conn.close()
        return None
    else:
        return ack_data # FYI the Connection stays alive here

def send_ack(conn, type=None, basic=False):
    if basic:
        conn.send(b"A")
        print("Sent basic ack")
    else:
        ack_packet = DataPacket(type, b'')
        encoded_ack = encode_DP(ack_packet)
        enc_ack_length = len(encoded_ack)
        enc_ack_length_bytes = enc_ack_length.to_bytes(2, 'big')
        conn.send(enc_ack_length_bytes)
        print("Sent ack length ({})".format(enc_ack_length))

        ready_ack = conn.recv(4096)
        print("Received ready acknowledgement from client.")

        bytes_sent = 0
        while bytes_sent < enc_ack_length:
            len_to_send = min(enc_ack_length - bytes_sent, 4096)
            bytes_sent += conn.send(
                encoded_ack[bytes_sent:bytes_sent + len_to_send])
            print("Sent {} bytes in this ack frame.".format(len_to_send))
        print("Finished sending {} ack".format(type))

class Awaited_Response:
    def __init__(self, address="", target=None, ID=None):
        self.address = address
        self.target = target
        self.ID = ID

# Responses the server is waiting on e.g. New player data
# Will be of form {ADDRESS: [R1, R2, etc.],}
# Where R1, R2 are Awaited_Response objectsself.
# Responses are addressed by unique ID
awaited_responses = {}
next_awaited_ID = 0

def add_awaited_response(address, target):
    ID = next_awaited_ID
    next_awaited_ID += 1
    awaited_response = Awaited_Response(address, target, ID)
    if address in awaited_responses:
        awaited_responses[address].append(awaited_response)
    else:
        awaited_responses[address] = [awaited_response]
    print("Awaiting new response from {} for function {}...".format(
        address, target.__name__
    ))

def handle_awaited_response(address, DP):
    if address not in awaited_responses:
        print("Response from address that does not exist!")
        return
    if len(awaited_responses[address]) == 0:
        print("Response from address with no outstanding responses!")
        return
    for AR in awaited_responses[address]:
        if AR.ID == DP.data[1]:
            AR.target(*DP.data[0])
            return
    print("Response did not match any outstanding response IDs!")

def add_new_player(address, PDATA):
    game_data.client_chars[address] = PDATA

# Set up socket to listen for connections
server_sock = socket.socket()
server_sock.bind((HOST, PORT))
server_sock.listen(5) # Set max buffered connections to 5

while True:

    print("Listening...")
    client_sock, address = server_sock.accept()
    address = address[0] # Not sure what the second part is used for
    print("\nConnection established from {}.\nAwaiting message...".format(address))
    message_length_bytes = client_sock.recv(4096)
    message_length = int.from_bytes(message_length_bytes, 'big')
    print("Message length header received: '{}'".format(message_length))

    send_ack(client_sock, basic=True) # Send basic ack to client

    data_bytes = b''
    while len(data_bytes) < message_length:
        data_frame = client_sock.recv(4096) # Buffer size
        data_bytes += data_frame
        print("Received {} bytes in this data frame.".format(len(data_frame)))

    print("Data transmission received successfully.")

    send_ack(client_sock, "ACK_KEEP_ALIVE")
    print("Keep alive acknowledgement sent to client.")

    try:
        datapacket = pickle.loads(zlib.decompress(data_bytes))
        print("Data unpacked successfully.")
    except:
        print("ERROR UNPACKING DATA")
        continue

    data_type = datapacket.type
    print("\nReceived {} packet from {}.".format(data_type, address))

    if data_type == "PDATA":
        print("Player Data:")
        player_data = datapacket
        print("Name: {}, STR/ACC/AGI/HP: {}/{}/{}/{}".format(name, str, acc, agi, hp))
        print("Location: {}, Item: {}, Gold: {}, Cheater: {}".format(location, item, gold, cheater))
    elif data_type == "HAND":
        if address in game_data.client_chars:
            player_name = game_data.client_chars[address].name
            response = DataPacket(
                "MESSAGE","Welcome back {}!".format(player_name))
            sendDataPacket(client_sock, response)
            # Ask the player if they want to continue with their existing character
        else:
            response = DataPacket(
                "NEED_INPUT",
                    ["New player! Would you like to make a new character?",
                    3, # Max input length for client
                    next_awaited_ID]) # For keeping track of what this input is for
            print("Asking client for new player response.")
            sendDataPacket(client_sock, response)
            add_awaited_response(address, add_new_player)

    elif data_type == "RESPONSE":
        handle_awaited_response(address, datapacket)

    else:
        print("UNKNOWN PACKET TYPE")

    client_connections.append((address))
    time.sleep(0.1)
