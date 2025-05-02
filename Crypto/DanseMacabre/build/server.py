from mac import tag

ATTEMPT_LIMIT = 10000


print("Welcome to the Danse MACabre beta-testing.")
print("Find a collision and win a flag!")

for _ in range(ATTEMPT_LIMIT):
    try:
        input1 = input("Message 1 (in hex): ")
        message1 = bytes.fromhex(input1)
        tag1 = tag(message1)
        print("Tag:", tag1.hex())

        input2 = input("Message 2 (in hex): ")
        message2 = bytes.fromhex(input2)
        tag2 = tag(message2)
        print("Tag:", tag2.hex())

        if message1 == message2:
            print("You cheated!")
            exit(1)

    except ValueError:
        print("Invalid message format. Try again next time!")
        exit(1)

    if tag1 == tag2:
        print("You found a collision! Well done!")
        with open("flag.txt", "r") as flag:
            print(flag.read())
        break

    else:
        print("No collision this time. Try again!")

else:
    print("You used all your attempts for now. Try again next time!")
    exit(1)
