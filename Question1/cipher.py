"""
cipher.py
---------
HIT137 Assignment 2 - Question 1

Implements a custom shift-cipher that encrypts and decrypts the contents of
a text file, plus a verification function that checks the decrypted file
matches the original.

Encryption rules (shift1, shift2 are non-negative integers supplied by the
user):

    Lowercase letters:
        a-n (first half)  -> shift FORWARD by (shift1 * shift2) positions
        o-z (second half) -> shift BACKWARD by (shift1 + shift2) positions

    Uppercase letters:
        A-M (first half)  -> shift BACKWARD by shift1 positions
        N-Z (second half) -> shift FORWARD by (shift2 ** 2) positions

    Digits (0-9):
        shift FORWARD by (shift1 - shift2) positions

    Everything else (spaces, tabs, newlines, punctuation, symbols):
        left unchanged

All shifts wrap around within their own alphabet (26 letters for
upper/lowercase, 10 digits for numbers) using modular arithmetic, so the
result is always another character of the same "kind" (lower stays lower,
digit stays digit, etc.).

Decryption re-applies the same category test to the *encrypted* character
and reverses the corresponding shift, so encrypt_file() and decrypt_file()
are exact inverses of one another for any given (shift1, shift2) pair.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Low level helper
# ---------------------------------------------------------------------------

def _shift_char(ch: str, amount: int, base: int, size: int) -> str:
    """Shift a single character `amount` positions within an alphabet of
    `size` characters starting at ordinal `base` (wraps around)."""
    return chr((ord(ch) - base + amount) % size + base)


# ---------------------------------------------------------------------------
# Core transform (shared by encrypt/decrypt, direction = +1 or -1)
# ---------------------------------------------------------------------------

def _transform_char(ch: str, shift1: int, shift2: int, direction: int) -> str:
    """Transform a single character.

    direction = 1  -> encrypt (apply the shift as described in the spec)
    direction = -1 -> decrypt (apply the exact opposite shift)
    """
    # NOTE: each half-range wraps *within itself* (not across the full
    # 26-letter alphabet). This keeps every shifted character inside the
    # same half it started in, which is what makes decrypt_file() able to
    # unambiguously reverse the transform (it re-checks which half the
    # character falls into and undoes the matching shift).
    if "a" <= ch <= "n":  # 14 letters: a..n
        amount = (shift1 * shift2) * direction
        return _shift_char(ch, amount, ord("a"), 14)
    if "o" <= ch <= "z":  # 12 letters: o..z
        amount = -(shift1 + shift2) * direction
        return _shift_char(ch, amount, ord("o"), 12)
    if "A" <= ch <= "M":  # 13 letters: A..M
        amount = -shift1 * direction
        return _shift_char(ch, amount, ord("A"), 13)
    if "N" <= ch <= "Z":  # 13 letters: N..Z
        amount = (shift2 ** 2) * direction
        return _shift_char(ch, amount, ord("N"), 13)
    if ch.isdigit():
        amount = (shift1 - shift2) * direction
        return _shift_char(ch, amount, ord("0"), 10)
    # spaces, tabs, newlines, punctuation, symbols -> unchanged
    return ch


def _transform_text(text: str, shift1: int, shift2: int, direction: int) -> str:
    return "".join(_transform_char(c, shift1, shift2, direction) for c in text)


# ---------------------------------------------------------------------------
# Required public interface
# ---------------------------------------------------------------------------

def encrypt_file(shift1: int, shift2: int, input_path: str, output_path: str) -> None:
    """Read `input_path`, encrypt its contents, write to `output_path`."""
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    encrypted = _transform_text(content, shift1, shift2, direction=1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(encrypted)


def decrypt_file(shift1: int, shift2: int, input_path: str, output_path: str) -> None:
    """Read `input_path` (encrypted text), decrypt it, write to `output_path`."""
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    decrypted = _transform_text(content, shift1, shift2, direction=-1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(decrypted)


def verify_files(original_path: str, decrypted_path: str) -> bool:
    """Compare the original file with the decrypted file and report success."""
    with open(original_path, "r", encoding="utf-8") as f:
        original = f.read()
    with open(decrypted_path, "r", encoding="utf-8") as f:
        decrypted = f.read()

    success = original == decrypted

    if success:
        print("Verification successful: decrypted text matches the original file.")
    else:
        print("Verification FAILED: decrypted text does NOT match the original file.")

    return success


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

def _read_shift(prompt: str) -> int:
    """Prompt the user until a valid non-negative integer is entered."""
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


def main() -> None:
    raw_path = "raw_text.txt"
    encrypted_path = "encrypted_text.txt"
    decrypted_path = "decrypted_text.txt"

    shift1 = _read_shift("Enter shift1 (non-negative integer): ")
    shift2 = _read_shift("Enter shift2 (non-negative integer): ")

    encrypt_file(shift1, shift2, raw_path, encrypted_path)
    print(f"Encrypted '{raw_path}' -> '{encrypted_path}'")

    decrypt_file(shift1, shift2, encrypted_path, decrypted_path)
    print(f"Decrypted '{encrypted_path}' -> '{decrypted_path}'")

    verify_files(raw_path, decrypted_path)


if __name__ == "__main__":
    main()
