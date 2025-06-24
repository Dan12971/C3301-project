import hashlib
import time
import json
import requests
import os
import random
from ecdsa import SigningKey, VerifyingKey, NIST384p

class PuzzleMaster:
    """
    The Amnesiac Oracle that generates puzzles with progressively increasing difficulty.
    """
    def __init__(self):
        self.word_list = [
            "ETERNAL", "VIGILANCE", "CIPHER", "ORACLE", "SECRET", "ALGORITHM",
            "DISCOVERY", "GENESIS", "PROTOCOL", "ANONYMOUS", "CICADA", "PRIME"
        ]

    def _create_caesar_cipher_puzzle(self):
        # (Logic for this puzzle remains the same)
        solution = random.choice(self.word_list) + str(random.randint(100, 999))
        shift_key = random.randint(3, 24)
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

    def _create_anagram_puzzle(self):
        # (Logic for this puzzle remains the same)
        solution = random.choice(self.word_list) + str(random.randint(100, 999))
        l = list(solution)
        random.shuffle(l)
        scrambled_word = "".join(l)
        puzzle = f"Unscramble the following letters: '{scrambled_word}'"
        clue = "The solution is a single word followed by a three-digit number."
        solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return { "puzzle_type": "HashCommitment", "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }

    def _create_vigenere_puzzle(self):
        # (Logic for this puzzle remains the same)
        solution = random.choice(self.word_list) + str(random.randint(100, 999))
        keyword = random.choice(self.word_list)
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
    
    def _create_hashing_challenge_puzzle(self, difficulty_level):
        """Creates a Proof-of-Work style hashing puzzle."""
        # Difficulty scales: starts at 3 zeros, adds a zero every 500 blocks.
        num_zeros = 3 + (difficulty_level // 500)
        puzzle_string = f"C3301-Block-{difficulty_level}-"
        puzzle = f"Find a number (a nonce) such that the SHA-256 hash of the string '{puzzle_string}{{nonce}}' starts with {num_zeros} leading zeros."
        clue = "This requires a brute-force script to solve. The solution is the nonce itself."
        # For this puzzle type, there's no pre-computed solution hash. Verification happens live.
        return {
            "puzzle_type": "HashingChallenge",
            "puzzle": puzzle,
            "clue": clue,
            "puzzle_data": {
                "prefix": puzzle_string,
                "zeros": num_zeros
            }
        }

    def create_new_puzzle(self, difficulty_level):
        """Generates a puzzle based on the current difficulty level."""
        if difficulty_level <= 500:
            # Easy Tier
            return random.choice([self._create_caesar_cipher_puzzle, self._create_anagram_puzzle])()
        elif difficulty_level <= 1500:
            # Medium Tier
            return random.choice([self._create_anagram_puzzle, self._create_vigenere_puzzle])()
        elif difficulty_level <= 3301:
            # Hard Tier
            return self._create_hashing_challenge_puzzle(difficulty_level)
        else:
            # Final puzzle after all tokens are minted
            return {"puzzle": "All tokens have been discovered.", "clue": "The hunt is complete."}

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

    # ... save_chain_to_disk, load_chain_from_disk, create_genesis_block, etc. remain the same ...
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
        print("Creating a new blockchain...")
        first_puzzle = self.puzzle_master.create_new_puzzle(difficulty_level=1)
        genesis_block = Block(index=0, transactions=[], timestamp=time.time(), previous_hash="0", data=first_puzzle)
        self.chain = [genesis_block.__dict__]

    @property
    def latest_block(self): return self.chain[-1]

    def add_transaction(self, transaction): self.pending_transactions.append(transaction); return True

    def attempt_mint(self, solver_wallet, proposed_solution):
        """UPDATED: Verifies a solution based on the puzzle type."""
        latest_block_data = self.latest_block['data']
        puzzle_type = latest_block_data.get('puzzle_type')
        is_solution_correct = False

        if puzzle_type == "HashCommitment":
            solution_hash_commitment = latest_block_data.get('solution_hash')
            proposed_solution_hash = hashlib.sha256(proposed_solution.encode()).hexdigest()
            if proposed_solution_hash == solution_hash_commitment:
                is_solution_correct = True
        
        elif puzzle_type == "HashingChallenge":
            try:
                nonce = int(proposed_solution)
                puzzle_data = latest_block_data.get('puzzle_data', {})
                prefix = puzzle_data.get('prefix', '')
                zeros = puzzle_data.get('zeros', 0)
                
                # Verify the nonce
                test_string = f"{prefix}{nonce}"
                test_hash = hashlib.sha256(test_string.encode()).hexdigest()
                
                if test_hash.startswith("0" * zeros):
                    is_solution_correct = True
            except (ValueError, TypeError):
                print("Invalid nonce format. Must be a number.")
                return None

        if not is_solution_correct:
            print("Failed Mint Attempt: Incorrect solution.")
            return None

        print("Solution Correct! Forging new block...")
        
        # --- Create Block ---
        next_block_index = len(self.chain)
        next_puzzle_package = self.puzzle_master.create_new_puzzle(difficulty_level=next_block_index)
        
        total_fees = len(self.pending_transactions) * self.transaction_fee
        total_reward = 1 + total_fees
        mint_tx = Transaction(sender="MINT_REWARD", recipient=solver_wallet.address, amount=total_reward)
        all_transactions = [mint_tx] + self.pending_transactions

        new_block = Block(
            index=next_block_index,
            transactions=[tx.__dict__ for tx in all_transactions],
            timestamp=time.time(),
            previous_hash=self.latest_block['hash'],
            data=next_puzzle_package
        )

        self.chain.append(new_block.__dict__)
        self.pending_transactions = []
        self.save_chain_to_disk()
        print(f"Success! Block #{new_block.index} created.")
        return new_block
    
    # ... get_address_data, register_node, resolve_conflicts methods remain the same ...
    def get_address_data(self, address): txs, balance = [], 0.0; [((balance := balance + tx['amount'], txs.append(tx)) if tx['recipient'] == address else (balance := balance - tx['amount'], txs.append(tx))) for block in self.chain for tx in block['transactions']]; return {'address': address, 'balance': balance, 'transactions': txs, 'transaction_count': len(txs)}
        
