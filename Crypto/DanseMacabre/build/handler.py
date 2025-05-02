import socketserver
import threading
import subprocess

HOST = "0.0.0.0"
PORT = 6666

class ChallengeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        process = subprocess.Popen(
            ["python3", "server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        def read_from_process():
            while True:
                # Je lis 1 caractère à la fois pour flush les input
                # Y'a probablement plus opti, mais ça marche
                output = process.stdout.read(1)
                if output:
                    self.request.sendall(output.encode())
                else:
                    break

        threading.Thread(target=read_from_process, daemon=True).start()

        while True:
            data = self.request.recv(1024)
            if not data:
                break
            process.stdin.write(data.decode())
            process.stdin.flush()

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ThreadedServer((HOST, PORT), ChallengeHandler) as server:
        print(f"Server started on {HOST}:{PORT}")
        server.serve_forever()
