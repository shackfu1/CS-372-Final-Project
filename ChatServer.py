import sys
import socket
import select
import json

def usage():
    print("usage: ChatServer.py port", file=sys.stderr)

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

def run_server(port):
    buffers = {}
    nicks = {}
    listener = socket.socket()
    connection = ('', port)
    listener.bind(connection)
    listener.listen()
    sock_set = {listener}
    while True:
        ready_to_read, _, _ = select.select(sock_set, {}, {})
        for sock in ready_to_read:
            if sock == listener:
                new_conn, addr = listener.accept()
                addr, port = new_conn.getpeername()
                print("('" + str(addr) + "', " + str(port) + "): connected")
                sock_set.add(new_conn)
                buffers[new_conn] = b''
                nicks[new_conn] = None
            else:
                message = None
                raw_message = None
                escape = False
                while escape == False:
                    if len(buffers[sock]) > 2 and buffers[sock][0] == 0 and len(buffers[sock]) >= buffers[sock][1] + 2:
                        message_length = buffers[sock][1] + 2
                        raw_message = buffers[sock][:message_length]
                        buffers[sock] = buffers[sock][message_length:]
                    if raw_message == None:
                        data = sock.recv(40)
                    addr, port = sock.getpeername()
                    if raw_message:
                        message = json.loads(raw_message[2:].decode())
                        if message["type"] == "hello":
                            nicks[sock] = message["nick"]
                        if message["type"] == "chat" and message["message"][0] == "/":
                            if message["message"][1:] == "q": ##send a "quit" packet if the mesage is /q
                                for s in sock_set:
                                    if s != listener:
                                        SendPacket(message["nick"], s, "quit", None)
                            sock_set.remove(sock)
                            sock.close()
                        else: ##if message is not a command, send the raw packet back
                            for s in sock_set:
                                if s != listener:
                                    s.sendall(raw_message)
                        escape = True
                    else:
                        buffers[sock] += data
def main(argv):
    try:
        port = int(argv[1])
    except:
        usage()
        return 1

    run_server(port)

if __name__ == "__main__":
    sys.exit(main(sys.argv))