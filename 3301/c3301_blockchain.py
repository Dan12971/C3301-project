import hashlib
import time
import json
import requests
import os
from ecdsa import SigningKey, VerifyingKey, NIST384p

class PuzzleMaster:
    """
    The Amnesiac Oracle. It algorithmically generates trustless puzzles
    and solutions directly from a seed, without any predefined word lists.
    """
    def _generate_word_from_seed(self, seed_int, length=7):
        """Generates a deterministic, random-looking word from a seed integer."""
        word = ""
        # Use a temporary variable to not alter the main seed_int for other operations
        temp_seed = seed_int
        for _ in range(length):
            # Generate a character code from 0-25
            char_code = temp_seed % 26
            word += chr(char_code + ord('A')) # Convert to an uppercase letter
            # Bit-shift the seed to use a different part for the next character
            temp_seed = temp_seed >> 5
        return word

    def _create_caesar_cipher_puzzle(self, seed):
        seed_int = int(seed, 16)
        
        # CHANGED: Word is now generated algorithmically
        solution_word = self._generate_word_from_seed(seed_int)
        solution_number = (seed_int >> 64) % 1000 # Use different bits
        solution = f"{solution_word}{solution_number}"
        
        shift_key = (seed_int >> 32) % 22 + 3

        encrypted_text = ""
        for char in solution:
            if 'A' <= char <= 'Z':
                shifted = ord(char) + shift_key
                if shifted > ord('Z'): shifted -= 26
                encrypted_text += chr(shifted)
            else: encrypted_text += char
        
        puzzle = f"Decrypt the following text: '{encrypted_text}'"
        clue = f"Caesar cipher, shift key = {shift_key}"
        solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return { "puzzle_type": "HashCommitment", "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }

    def _create_vigenere_puzzle(self, seed):
        seed_int = int(seed, 16)

        # CHANGED: Both solution and keyword are generated from the seed
        solution_word = self._generate_word_from_seed(seed_int, length=8)
        keyword = self._generate_word_from_seed(seed_int >> 64, length=5) # Use different bits for the keyword
        solution_number = (seed_int >> 128) % 1000
        solution = f"{solution_word}{solution_number}"
        
        encrypted_text = ""
        for i, char in enumerate(solution):
            if 'A' <= char <= 'Z':
                shift = ord(keyword[i % len(keyword)]) - ord('A')
                shifted = ord(char) + shift
                if shifted > ord('Z'): shifted -= 26
                encrypted_text += chr(shifted)
            else: encrypted_text += char

        puzzle = f"Decrypt the text using the keyword: '{encrypted_text}'"
        clue = f"Vigenère cipher, keyword = '{keyword}'"
        solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return { "puzzle_type": "HashCommitment", "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }

    def _create_hashing_challenge_puzzle(self, seed, difficulty_level):
        seed_int = int(seed, 16)
        num_zeros = 3 + (difficulty_level // 500)
        salt = seed_int % 1000000
        puzzle_string = f"C3301-Block-{difficulty_level}-{salt}-"
        puzzle = f"Find a number (nonce) such that the SHA-256 hash of '{puzzle_string}{{nonce}}' starts with {num_zeros} zeros."
        clue = "This requires a brute-force script to solve. The solution is the nonce."
        return { "puzzle_type": "HashingChallenge", "puzzle": puzzle, "clue": clue, "puzzle_data": { "prefix": puzzle_string, "zeros": num_zeros } }

    def create_new_puzzle(self, difficulty_level, seed):
        seed_int = int(seed, 16)
        
        if difficulty_level <= 1500:
            if seed_int % 2 == 0:
                return self._create_caesar_cipher_puzzle(seed)
            else:
                return self._create_vigenere_puzzle(seed)
        else:
            return self._create_hashing_challenge_puzzle(seed, difficulty_level)

# --- Wallet, Transaction, and Block classes remain the same ---
class Wallet:
    def __init__(self): self.private_key = SigningKey.generate(curve=NIST384p); self.public_key = self.private_key.verifying_key; self.address = self.public_key.to_string().hex()
class Transaction:
    def __init__(self, sender, recipient, amount, data=None): self.sender, self.recipient, self.amount, self.timestamp, self.signature, self.data = sender, recipient, amount, time.time(), None, data or {}
    def to_json(self): return json.dumps({"sender": self.sender, "recipient": self.recipient, "amount": self.amount, "timestamp": self.timestamp, "data": self.data}, sort_keys=True)
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, data=None, nonce=0): self.index, self.transactions, self.timestamp, self.previous_hash, self.data, self.nonce, self.hash = index, transactions, timestamp, previous_hash, data, nonce, self.calculate_hash()
    def calculate_hash(self): return hashlib.sha256((str(self.index) + json.dumps(self.transactions, sort_keys=True) + str(self.timestamp) + str(self.previous_hash) + json.dumps(self.data, sort_keys=True) + str(self.nonce)).encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []; self.pending_transactions = []; self.nodes = set(); self.chain_file = "blockchain_data.json"; self.puzzle_master = PuzzleMaster(); self.transaction_fee = 0.001
        self.load_chain_from_disk()

    def save_chain_to_disk(self):
        try:
            with open(self.chain_file, 'w') as f: json.dump(self.chain, f, indent=4)
        except Exception as e: print(f"Error saving chain to disk: {e}")

    def load_chain_from_disk(self):
        if not os.path.exists(self.chain_file): self.create_genesis_block(); self.save_chain_to_disk()
        else:
            try:
                with open(self.chain_file, 'r') as f: self.chain = json.load(f)
            except (IOError, json.JSONDecodeError): self.create_genesis_block(); self.save_chain_to_disk()

    def create_genesis_block(self):
        print("Creating a new blockchain with a deterministic Genesis Block...")
        genesis_seed = hashlib.sha256("The Hunt Begins 2025-06-24".encode()).hexdigest()
        first_puzzle = self.puzzle_master.create_new_puzzle(difficulty_level=1, seed=genesis_seed)
        genesis_block = Block(index=0, transactions=[], timestamp=time.time(), previous_hash="0", data=first_puzzle)
        self.chain = [genesis_block.__dict__]

    @property
    def latest_block(self): return self.chain[-1]

    def add_transaction(self, transaction): self.pending_transactions.append(transaction); return True

    def attempt_mint(self, solver_wallet, proposed_solution):
        latest_block_data = self.latest_block['data']
        puzzle_type = latest_block_data.get('puzzle_type')
        is_solution_correct = False

        if puzzle_type == "HashCommitment":
            solution_hash_commitment = latest_block_data.get('solution_hash')
            proposed_solution_hash = hashlib.sha256(proposed_solution.encode()).hexdigest()
            if proposed_solution_hash == solution_hash_commitment: is_solution_correct = True
        
        elif puzzle_type == "HashingChallenge":
            try:
                nonce = int(proposed_solution)
                puzzle_data = latest_block_data.get('puzzle_data', {})
                prefix, zeros = puzzle_data.get('prefix', ''), puzzle_data.get('zeros', 0)
                if hashlib.sha256(f"{prefix}{nonce}".encode()).hexdigest().startswith("0" * zeros): is_solution_correct = True
            except (ValueError, TypeError): return None

        if not is_solution_correct:
            print("Failed Mint Attempt: Incorrect solution.")
            return None

        print("Solution Correct! Forging new block...")
        
        previous_block_hash_as_seed = self.latest_block['hash']
        next_block_index = len(self.chain)
        next_puzzle_package = self.puzzle_master.create_new_puzzle(difficulty_level=next_block_index, seed=previous_block_hash_as_seed)
        
        total_fees = len(self.pending_transactions) * self.transaction_fee
        total_reward = 1 + total_fees
        mint_tx = Transaction(sender="MINT_REWARD", recipient=solver_wallet.address, amount=total_reward)
        all_transactions = [mint_tx] + self.pending_transactions

        new_block = Block(index=next_block_index, transactions=[tx.__dict__ for tx in all_transactions], timestamp=time.time(), previous_hash=self.latest_block['hash'], data=next_puzzle_package)

        self.chain.append(new_block.__dict__)
        self.pending_transactions = []
        self.save_chain_to_disk()
        print(f"Success! Block #{new_block.index} created.")
        return new_block
    
    def get_address_data(self, address): txs, balance = [], 0.0; [((balance := balance + tx['amount'], txs.append(tx)) if tx['recipient'] == address else (balance := balance - tx['amount'], txs.append(tx))) for block in self.chain for tx in block['transactions']]; return {'address': address, 'balance': balance, 'transactions': txs, 'transaction_count': len(txs)}
        
