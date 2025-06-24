import hashlib
import time
import json
import requests
import os
import random
from ecdsa import SigningKey, VerifyingKey, NIST384p

class PuzzleMaster:
    """
    The Amnesiac Oracle for generating and managing puzzles.
    It randomly selects from multiple puzzle types.
    """
    def __init__(self):
        # A simple word list to generate our puzzle text from
        self.word_list = [
            "ETERNAL", "VIGILANCE", "CIPHER", "ORACLE", "SECRET", "ALGORITHM",
            "DISCOVERY", "GENESIS", "PROTOCOL", "ANONYMOUS", "CICADA", "PRIME"
        ]

    def _create_caesar_cipher_puzzle(self):
        """Generates a puzzle package for a Caesar cipher challenge."""
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
        return { "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }

    def _create_anagram_puzzle(self):
        """Generates a puzzle package for an anagram challenge."""
        solution = random.choice(self.word_list) + str(random.randint(100, 999))
        
        l = list(solution)
        random.shuffle(l)
        scrambled_word = "".join(l)

        puzzle = f"Unscramble the following letters to find the secret phrase: '{scrambled_word}'"
        clue = "The solution is a single word followed by a three-digit number."
        solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return { "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }

    def _create_vigenere_puzzle(self):
        """Generates a puzzle package for a Vigenère cipher challenge."""
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

        puzzle = f"Decrypt the following text using the provided keyword: '{encrypted_text}'"
        clue = f"Vigenère cipher, keyword = '{keyword}'"
        solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return { "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }

    def create_new_puzzle(self, difficulty=1):
        """Generates a new puzzle package by RANDOMLY choosing a puzzle type."""
        puzzle_generators = [
            self._create_caesar_cipher_puzzle,
            self._create_anagram_puzzle,
            self._create_vigenere_puzzle
        ]
        chosen_generator = random.choice(puzzle_generators)
        return chosen_generator()

class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=NIST384p)
        self.public_key = self.private_key.verifying_key
        self.address = self.public_key.to_string().hex()

class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = time.time()
        self.signature = None

    def to_json(self):
        return json.dumps({"sender": self.sender, "recipient": self.recipient, "amount": self.amount, "timestamp": self.timestamp}, sort_keys=True)

    def set_signature(self, signature):
        self.signature = signature

    @staticmethod
    def is_valid(transaction):
        if transaction.sender == "MINT_REWARD": return True
        if not transaction.signature: return False
        try:
            pk_bytes = bytes.fromhex(transaction.sender)
            public_key = VerifyingKey.from_string(pk_bytes, curve=NIST384p)
            sig_bytes = bytes.fromhex(transaction.signature)
            return public_key.verify(sig_bytes, transaction.to_json().encode())
        except: return False

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, data=None, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.data = data
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = str(self.index) + json.dumps(self.transactions, sort_keys=True) + str(self.timestamp) + str(self.previous_hash) + json.dumps(self.data, sort_keys=True) + str(self.nonce)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.nodes = set()
        self.chain_file = "blockchain_data.json"
        self.puzzle_master = PuzzleMaster()
        self.transaction_fee = 0.001
        self.load_chain_from_disk()

    def save_chain_to_disk(self):
        try:
            with open(self.chain_file, 'w') as f: json.dump(self.chain, f, indent=4)
        except Exception as e: print(f"Error saving chain to disk: {e}")

    def load_chain_from_disk(self):
        if not os.path.exists(self.chain_file):
            print("No saved blockchain found. Creating a new one.")
            self.create_genesis_block()
            self.save_chain_to_disk()
            return
        try:
            with open(self.chain_file, 'r') as f: self.chain = json.load(f)
            print(f"Blockchain loaded from disk. Found {len(self.chain)} blocks.")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading chain from disk: {e}. Starting fresh.")
            self.create_genesis_block()
            self.save_chain_to_disk()

    def create_genesis_block(self):
        first_puzzle = self.puzzle_master.create_new_puzzle()
        genesis_block = Block(index=0, transactions=[], timestamp=time.time(), previous_hash="0", data=first_puzzle)
        self.chain.append(genesis_block.__dict__)

    @property
    def latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if not Transaction.is_valid(transaction): return False
        self.pending_transactions.append(transaction)
        return True

    def attempt_mint(self, solver_wallet, proposed_solution):
        latest_block_data = self.latest_block['data']
        solution_hash_commitment = latest_block_data.get('solution_hash')
        if not solution_hash_commitment: return None
        proposed_solution_hash = hashlib.sha256(proposed_solution.encode()).hexdigest()
        if proposed_solution_hash != solution_hash_commitment:
            print("Failed Mint Attempt: Incorrect solution.")
            return None
        for block in self.chain:
            if block['index'] != self.latest_block['index'] and block['data'].get('solution_hash') == solution_hash_commitment:
                print("Failed Mint Attempt: This puzzle has already been solved.")
                return None
        total_fees = len(self.pending_transactions) * self.transaction_fee
        total_reward = 1 + total_fees
        mint_tx = Transaction(sender="MINT_REWARD", recipient=solver_wallet.address, amount=total_reward)
        all_tx = [mint_tx] + self.pending_transactions
        next_puzzle = self.puzzle_master.create_new_puzzle()
        new_block = Block(index=len(self.chain), transactions=[tx.__dict__ for tx in all_tx], timestamp=time.time(), previous_hash=self.latest_block['hash'], data=next_puzzle)
        self.chain.append(new_block.__dict__)
        self.pending_transactions = []
        self.save_chain_to_disk()
        print(f"Success! Block #{new_block.index} created.")
        return new_block

    def get_address_data(self, address):
        txs, balance = [], 0.0
        for block in self.chain:
            for tx in block['transactions']:
                if tx['recipient'] == address:
                    balance += tx['amount']
                    txs.append(tx)
                if tx['sender'] == address:
                    balance -= tx['amount']
                    txs.append(tx)
        return {'address': address, 'balance': balance, 'transactions': txs, 'transaction_count': len(txs)}

    def register_node(self, address):
        self.nodes.add(address)

    def resolve_conflicts(self):
        neighbours, new_chain, max_length = self.nodes, None, len(self.chain)
        for node in neighbours:
            try:
                response = requests.get(f'{node}/chain')
                if response.status_code == 200:
                    length, chain_data = response.json()['length'], response.json()['chain']
                    if length > max_length: max_length, new_chain = length, chain_data
            except requests.exceptions.ConnectionError: print(f"Could not connect to node {node}.")
        if new_chain:
            self.chain = new_chain
            self.save_chain_to_disk()
            return True
        return False
        
