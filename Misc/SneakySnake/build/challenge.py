
def ask_and_validate(prompt, correct_answer,show_flag=False):
    answer = input(prompt).strip()
    if answer.lower() != correct_answer.lower():
        print("Incorrect answer. Access denied.")
        exit(1)
    else:
        print("Good answer")
        if show_flag:
            print(f"\nWell done! This is the flag you can submit for the challenge: {correct_answer}")

def main():
    print("\n🐍🐍🐍 Sneaky Snake 🐍🐍🐍 \n")

    ask_and_validate("1. What is the path of the file used for initial access?\nFlag format: C:\\Users\\xxxxx\\xxxxx\n> ", "C:\\Users\\raiden\\Desktop\\ImportantAPI\\.git\\config")
    ask_and_validate("2. What is the attacker's server IP address?\n> ", "192.168.56.1")
    print("\n========\nFollow this link to download the second part of the challenge")
    print("Link: https://drive.proton.me/urls/6GV7CRNPYW#f2KaFtX6qRNm \nPassword: PWNME_5n34ky_5n4k3\n========\n")
    ask_and_validate("3. What C2 framework did the attacker use?\n> ", "Havoc")
    ask_and_validate("4. Describe the attacker's actions that led to finding the flag:\n> ", "PWNME{D0n7_U53_D3f4ul7_C0nf_F0r_Y0ur_C2}",True)

    print("\nAll answers are correct.")

if __name__ == "__main__":
    main()
