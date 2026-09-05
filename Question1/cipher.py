from __future__ import annotations


# moves a character forward or backward within its own alphabet, wrapping around
def _shift_char(ch: str, amount: int, base: int, size: int) -> str:
    return chr((ord(ch) - base + amount) % size + base)


# figures out which category a character belongs to and shifts it accordingly
def _transform_char(ch: str, shift1: int, shift2: int, direction: int) -> str:
    if "a" <= ch <= "n":
        amount = (shift1 * shift2) * direction
        return _shift_char(ch, amount, ord("a"), 14)
    if "o" <= ch <= "z":
        amount = -(shift1 + shift2) * direction
        return _shift_char(ch, amount, ord("o"), 12)
    if "A" <= ch <= "M":
        amount = -shift1 * direction
        return _shift_char(ch, amount, ord("A"), 13)
    if "N" <= ch <= "Z":
        amount = (shift2 ** 2) * direction
        return _shift_char(ch, amount, ord("N"), 13)
    if ch.isdigit():
        amount = (shift1 - shift2) * direction
        return _shift_char(ch, amount, ord("0"), 10)
    return ch


# applies the shift to every character in a block of text
def _transform_text(text: str, shift1: int, shift2: int, direction: int) -> str:
    return "".join(_transform_char(c, shift1, shift2, direction) for c in text)


# reads a text file, encrypts its contents, and writes the result to a new file
def encrypt_file(shift1: int, shift2: int, input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    encrypted = _transform_text(content, shift1, shift2, direction=1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(encrypted)


# keeps asking the user for input until they give a valid non-negative whole number
def _read_shift(prompt: str) -> int:
    while True:
        value = input(prompt).strip()
        try:
            number = int(value)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if number < 0:
            print("Please enter a non-negative integer.")
            continue
        return number


# runs the program: gets the shift values from the user and encrypts the file
def main() -> None:
    raw_path = "raw_text.txt"
    encrypted_path = "encrypted_text.txt"
    decrypted_path = "decrypted_text.txt"

    shift1 = _read_shift("Enter shift1 (non-negative integer): ")
    shift2 = _read_shift("Enter shift2 (non-negative integer): ")

    encrypt_file(shift1, shift2, raw_path, encrypted_path)
    print(f"Encrypted '{raw_path}' -> '{encrypted_path}'")


if __name__ == "__main__":
    main()
