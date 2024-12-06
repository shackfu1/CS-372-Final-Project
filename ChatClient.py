import json
import socket
import sys
import threading

from chatuicurses import init_windows, read_command, print_message, end_windows

def usage():
    print("usage: ChatClient.py nickname server port", file=sys.stderr)

def SendPacket(nick, s, type, message):
    packet = b''
    payload = {"type": type}
    if message:
        payload["message"] = message
    if nick:
        payload["nick"] = nick
    payload = json.dumps(payload).encode()
    length = len(payload).to_bytes(2, "big")
    packet += length + payload
    s.sendall(packet)
    if message == "/q":
        return True
    return False

def ReceivePackets(s):
    packet_buffer = b''
    raw_message = None
    while True:
        if len(packet_buffer) > 2 and packet_buffer[0] == 0 and len(packet_buffer) >= packet_buffer[1] + 2:
            message_length = packet_buffer[1] + 2
            raw_message = packet_buffer[:message_length]
            packet_buffer = packet_buffer[message_length:]

        if raw_message == None:
            data = s.recv(40)

        if raw_message != None:
            message = json.loads(raw_message[2:].decode())
            if message["type"] == "chat":
                print_message(f"{message['nick']}: {message['message']}")
            elif message["type"] == "hello":
                print_message(f"*** {message['nick']} has joined the chat")
            elif message["type"] == "quit":
                print_message(f"*** {message['nick']} has left the chat")
            raw_message = None
            packet_buffer = b''
        else:
            packet_buffer += data


def main(argv):
    init_windows()
    try:
        host = argv[2]
        port = int(argv[3])
        nick = argv[1]
    except:
        usage()
        return 1

    s = socket.socket()
    s.connect((host, port))

    receive_thread = threading.Thread(target=ReceivePackets, args={s})
    receive_thread.start()

    SendPacket(nick, s, "hello", None)

    stopped = False
    while stopped == False:
        try:
            command = read_command("Enter a thing> ")
        except:
            break
        stopped = SendPacket(nick, s, "chat", command)

    end_windows()

if __name__ == "__main__":
    sys.exit(main(sys.argv))