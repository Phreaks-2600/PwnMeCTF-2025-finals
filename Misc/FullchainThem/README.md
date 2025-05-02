# FullchainThem

## Description
We've heard rumors about an online game that's rigged — players never seem to win.
After digging a little deeper, we uncovered that it's actually a kind of online casino, allegedly being used to launder money for a criminal organization...

We've managed to get our hands on the source code, and it looks like their contracts use the Diamond Proxy pattern in a way that feels... fishy.

If we could somehow seize the funds locked in their Pool, that would be ideal.
I'm counting on you!

## Difficulty
- Insane

## Author
- [Ectario](https://x.com/Ectari0)

## Attachments
- [fullchainthem.zip](attachments/fullchainthem.zip)

## Usage
```sh
cd build/
curl -L https://foundry.paradigm.xyz | bash
foundryup
docker compose up --build -d
```

## Writeups
- N/A