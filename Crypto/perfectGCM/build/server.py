#!/usr/bin/env python3
from challenge import challenge
import json
import sys

def main():
    print("Welcome to the perfect encryption service!")
    print("You can get the encrypted flag, but you will never decrypt it!")
    print("Good luck using the decrypt function without the key!")
    sys.stdout.flush() 
    try:
        while True:
            input_json = sys.stdin.readline()
            if not input_json:
                break
            json_received = json.loads(input_json)
            result = challenge(json_received)
            output_json = json.dumps(result)
            print(output_json)
            sys.stdout.flush()  
    except Exception as e:
        error_message = {"error": str(e)}
        print(json.dumps(error_message))


if __name__ == "__main__":
    main()
