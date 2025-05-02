#!/usr/bin/env python3
from flag import FLAG
import json
import secrets

n = 512
q = 0x10001
g = secrets.randbits(64)
MAX_REQUESTS = 512


def product(A, B):
    """
    Computes the product of:
    - Matrix x Matrix
    - Matrix x Vector
    - Vector x Vector (dot product)

    :param A: List of lists (matrix) or a simple list (vector)
    :param B: List of lists (matrix) or a simple list (vector)
    :return: The product result as a list or a scalar
    """

    # Case 1: Vector × Vector -> Dot product
    if isinstance(A[0], (int, float)) and isinstance(B[0], (int, float)):
        if len(A) != len(B):
            raise ValueError("Both vectors must have the same size")
        return sum(a * b for a, b in zip(A, B))

    # Case 2: Matrix × Vector
    if isinstance(A[0], list) and isinstance(B[0], (int, float)):
        if len(A[0]) != len(B):
            raise ValueError("The number of columns in A must match the size of B")
        return [sum(A[i][j] * B[j] for j in range(len(B))) for i in range(len(A))]

    # Case 3: Matrix × Matrix
    if isinstance(A[0], list) and isinstance(B[0], list):
        if len(A[0]) != len(B):
            raise ValueError(
                "The number of columns in A must match the number of rows in B"
            )

        m, n = len(A), len(A[0])
        p = len(B[0])

        result = [[0] * p for _ in range(m)]
        for i in range(m):
            for j in range(p):
                for k in range(n):
                    result[i][j] += A[i][k] * B[k][j]
        return result

    raise ValueError("Invalid inputs, A and B must be lists or lists of lists")


class LearningWeirdStreamCipherLikeWithErrors_____WhatTheFuckThisClassNameIsWayyyyyyTooLongLolz:
    def __init__(self, challenge, flag):
        self.S = [secrets.randbelow(q) for _ in range(n)]
        self.challenge = challenge
        self.FLAG = flag
        stream = []
        while len(stream) < n:
            k = secrets.randbits(2 * n)
            stream = [g << i for i in range(len(bin(k)[2:]))]
            k_binary = bin(k)[2:]
            deleted = 0
            for i in range(1, len(k_binary)):
                k_i = k_binary[i]
                if not int(k_i):
                    del stream[i - deleted]
                    deleted += 1
        self.stream = stream
        self.leaks = 0

    def get_leak(self, index, e=secrets.randbelow(q)):
        if index < 0 or index >= len(self.stream):
            return {"error": "Invalid index"}
        if not self.leaks < MAX_REQUESTS:
            return {"error": "Too much requests"}

        A = [secrets.randbelow(q) for _ in range(n)]
        B = product(A, self.S) + (self.stream[index] + e) * q
        self.leaks += 1
        return {"A": A, "B": str(B)}

    def get_encrypted_challenge(self):
        binary_challenge = list(
            map(
                int,
                " ".join(
                    bin(int.from_bytes(self.challenge, byteorder="big"))[2:]
                ).split(" "),
            )
        )
        encrypted_challenge = product(
            binary_challenge, self.stream[: len(binary_challenge)]
        )
        return {"value": hex(encrypted_challenge)[2:]}

    def get_flag(self, challenge_guess):
        if challenge_guess == self.challenge:
            return {"success": self.FLAG}
        return {"fail": "hmmmmm"}


def main():
    challenge = secrets.token_bytes(64)
    challenge_instance = LearningWeirdStreamCipherLikeWithErrors_____WhatTheFuckThisClassNameIsWayyyyyyTooLongLolz(
        challenge, FLAG
    )
    print("Welcome to the LWSCLWE Challenge!")

    while True:
        try:
            command = json.loads(input("Enter your command in JSON format: "))
            if "action" not in command:
                print(json.dumps({"error": "Invalid command format."}))
                continue

            action = command["action"]

            if action == "get_leak":
                if "index" not in command:
                    print(json.dumps({"error": "Missing index"}))
                else:
                    print(
                        json.dumps(challenge_instance.get_leak(int(command["index"])))
                    )

            elif action == "get_encrypted_challenge":
                print(json.dumps(challenge_instance.get_encrypted_challenge()))

            elif action == "get_flag":
                if "challenge_guess" not in command:
                    print(json.dumps({"error": "Invalid command format."}))
                else:
                    challenge_guess = bytes.fromhex(command["challenge_guess"])
                    print(json.dumps(challenge_instance.get_flag(challenge_guess)))

            elif action == "exit":
                print(json.dumps({"status": "Goodbye!"}))
                break

            else:
                print(json.dumps({"error": "Unknown action."}))
        except Exception as e:
            print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
