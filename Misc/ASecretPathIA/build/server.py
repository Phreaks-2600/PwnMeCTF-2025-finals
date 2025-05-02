import socket
import threading
import torch
import ast
import os 
import random
import string

name = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
flag_name = f"{name}.txt"

flag_value = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

with open(flag_name, "w") as f:
    f.write(f"{os.environ['FLAG']}")


def load_model():
    with torch.serialization.safe_globals(['exec']):
        model = torch.load("mlp_backdoor.pth", weights_only=False)
    model.eval()
    return model

model = load_model()

def handle_client(conn, addr):
    try:
        data = conn.recv(4096)
        if not data:
            conn.close()
            return

        input_str = data.decode(errors="ignore").strip()

        try:
            parsed_input = ast.literal_eval(input_str)
            tensor = torch.tensor(parsed_input, dtype=torch.float32)
            if tensor.dim() == 1:
                tensor = tensor.unsqueeze(0)

            with torch.no_grad():
                output = model(tensor)

            result = f"{output.tolist()}\n"
            #print(f"[✓] Pred : {result.strip()}")
            conn.sendall(result.encode())

        except Exception as e:
            print(f"Error : {str(e)}")

    except Exception as e:
        print(f"[!] Except : {str(e)}")
    finally:
        conn.close()

HOST = "0.0.0.0"
PORT = 4444

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
