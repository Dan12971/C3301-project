def solve_caesar_cipher(encrypted_text, shift_key):
    """
    Decrypts a Caesar cipher by shifting letters backward.
    """
    decrypted_text = ""
    
    # We only want to shift letters, not numbers
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for char in encrypted_text:
        if char in alphabet:
            # Find the position of the character in the alphabet (0-25)
            position = alphabet.find(char)
            
            # Shift the position backward, and wrap around if we go past 'A'
            new_position = (position - shift_key) % 26
            
            # Find the new character
            decrypted_text += alphabet[new_position]
        else:
            # If it's a number or other character, just add it as is
            decrypted_text += char
            
    return decrypted_text

# --- Main part of the script ---

# 1. Get these values from the block explorer
encrypted_text_from_explorer = "HUVUFTVBZ100"
shift_key_from_explorer =  7

# 2. Run the solver function
solution = solve_caesar_cipher(encrypted_text_from_explorer, shift_key_from_explorer)

# 3. Print the result
print(f"Encrypted Text: {encrypted_text_from_explorer}")
print(f"Shift Key: {shift_key_from_explorer}")
print("---------------------------------")
print(f"Decrypted Solution: {solution}")

