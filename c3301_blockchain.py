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
    It creates a puzzle and a hash of the solution, then "forgets" the solution.
    """
    def __init__(self):
        self.word_list = [
            "ETERNAL", "VIGILANCE", "CIPHER", "ORACLE", "SECRET", "ALGORITHM",
            "DISCOVERY", "GENESIS", "PROTOCOL", "ANONYMOUS", "CICADA", "PRIME"
        ]

    def _generate_caesar_cipher(self, text, shift):
        encrypted_text = ""
        for char in text:
            if 'A' <= char <= 'Z':
                shifted = ord(char) + shift
                if shifted > ord('Z'):
                    shifted -= 26
                encrypted_text += chr(shifted)
            else:
                encrypted_text += char
        return encrypted_text

    def create_new_puzzle(self, difficulty=1):
        solution = random.choice(self.word_list)
        solution = f"{solution}{random.randint(100, 999)}"
        shift_key = random.randint(3, 24)
        encrypted_text = self._generate_caesar_cipher(solution, shift_key)
        puzzle = f"Decrypt the following text: '{encrypted_text}'"
        clue = f"Caesar cipher, shift key = {shift_key}"
        solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return {
            "puzzle": puzzle,
            "clue": clue,
            "solution_hash": solution_hash
        }

class Wallet:
    """
    Manages a user's key pair (private and public key).
    """
    def __init__(self):
        self.private_key = SigningKey.generate(curve=NIST384p)
        self.public_key = self.private_key.verifying_key
        self.address = self.public_key.to_string().hex()

    def sign_transaction(self, transaction):
        transaction_data = transaction.to_json().encode()
        signature = self.private_key.sign(transaction_data)
        return signature.hex()

class Transaction:
    """
    Represents a transaction, which can be standard or for minting.
    """
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = time.time()
        self.signature = None

    def to_json(self):
        return json.dumps({
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp
        }, sort_keys=True)

    def set_signature(self, signature):
        self.signature = signature

    @staticmethod
    def is_valid(transaction):
        if transaction.sender == "MINT_REWARD":
            return True
        if not transaction.signature:
            return False
        try:
            public_key_bytes = bytes.fromhex(transaction.sender)
            public_key = VerifyingKey.from_string(public_key_bytes, curve=NIST384p)
            signature_bytes = bytes.fromhex(transaction.signature)
            return public_key.verify(signature_bytes, transaction.to_json().encode())
        except:
            return False

    def __repr__(self):
        return (
            f"  Transaction(\n"
            f"    Sender: {self.sender}\n"
            f"    Recipient: {self.recipient}\n"
            f"    Amount: {self.amount}\n"
            f"    Timestamp: {self.timestamp}\n"
            f"    Signature: {self.signature[:10] if self.signature else 'None'}...\n"
            f"  )"
        )

class Block:
    """
    Represents a single block in our C3301 blockchain.
    """
    def __init__(self, index, transactions, timestamp, previous_hash, data=None, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.data = data
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = (
            str(self.index) +
            json.dumps(self.transactions, sort_keys=True) +
            str(self.timestamp) +
            str(self.previous_hash) +
            json.dumps(self.data, sort_keys=True) +
            str(self.nonce)
        )
        return hashlib.sha256(block_string.encode()).hexdigest()

    def __repr__(self):
        transactions_str = json.dumps(self.transactions, indent=4)
        data_str = json.dumps(self.data, indent=4)
        return (
            f"Block(\n"
            f"  Index: {self.index}\n"
            f"  Transactions: {transactions_str}\n"
            f"  Timestamp: {self.timestamp}\n"
            f"  Previous Hash: {self.previous_hash}\n"
            f"  Data: {data_str}\n"
            f"  Hash: {self.hash}\n"
            f"  Nonce: {self.nonce}\n"
            f")"
        )

class Blockchain:
    """
    Manages the chain of blocks, transactions, and puzzle logic.
    """
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.nodes = set()
        self.chain_file = "blockchain_data.json"
        self.puzzle_master = PuzzleMaster()
        self.load_chain_from_disk()

    def save_chain_to_disk(self):
        try:
            with open(self.chain_file, 'w') as f:
                json.dump(self.chain, f, indent=4)
        except Exception as e:
            print(f"Error saving chain to disk: {e}")

    def load_chain_from_disk(self):
        if not os.path.exists(self.chain_file):
            print("No saved blockchain found. Creating a new one.")
            self.create_genesis_block()
            self.save_chain_to_disk()
            return
        try:
            with open(self.chain_file, 'r') as f:
                self.chain = json.load(f)
                print(f"Blockchain loaded from disk. Found {len(self.chain)} blocks.")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading chain from disk: {e}. Starting fresh.")
            self.create_genesis_block()
            self.save_chain_to_disk()

    def create_genesis_block(self):
        first_puzzle_package = self.puzzle_master.create_new_puzzle()
        genesis_block_obj = Block(
            index=0,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0",
            data=first_puzzle_package
        )
        self.chain.append(genesis_block_obj.__dict__)

    @property
    def latest_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if not Transaction.is_valid(transaction):
            print("Failed to add transaction: Invalid transaction.")
            return False
        self.pending_transactions.append(transaction)
        return True

    def attempt_mint(self, solver_wallet, proposed_solution):
        latest_block_data = self.latest_block['data']
        solution_hash_commitment = latest_block_data.get('solution_hash')

        if not solution_hash_commitment:
            print("Minting Error: No solution hash found in the latest block.")
            return None

        proposed_solution_hash = hashlib.sha256(proposed_solution.encode()).hexdigest()
        
        # --- DEBUGGING LINES ADDED HERE ---
        print("---------------------------------")
        print(f"DEBUG: User's proposed hash: {proposed_solution_hash}")
        print(f"DEBUG: Correct solution hash: {solution_hash_commitment}")
        print("---------------------------------")
        # ------------------------------------

        if proposed_solution_hash != solution_hash_commitment:
            print(f"Failed Mint Attempt: Incorrect solution.")
            return None

        for block in self.chain:
            if block['index'] != self.latest_block['index'] and block['data'].get('solution_hash') == solution_hash_commitment:
                print(f"Failed Mint Attempt: This puzzle has already been solved.")
                return None

        print("Solution Correct! Forging new block...")
        mint_transaction = Transaction(sender="MINT_REWARD", recipient=solver_wallet.address, amount=1)
        all_transactions = [mint_transaction] + self.pending_transactions
        next_puzzle_package = self.puzzle_master.create_new_puzzle()
        new_block_obj = Block(
            index=len(self.chain),
            transactions=[tx.__dict__ for tx in all_transactions],
            timestamp=time.time(),
            previous_hash=self.latest_block['hash'],
            data=next_puzzle_package
        )
        self.chain.append(new_block_obj.__dict__)
        self.pending_transactions = []
        self.save_chain_to_disk()
        print(f"Success! Block #{new_block_obj.index} created. {solver_wallet.address[:10]}... minted 1 C3301.")
        return new_block_obj

    def get_address_data(self, address):
        address_transactions = []
        balance = 0.0
        for block in self.chain:
            for tx in block['transactions']:
                if tx['recipient'] == address:
                    balance += tx['amount']
                    address_transactions.append(tx)
                if tx['sender'] == address:
                    balance -= tx['amount']
                    address_transactions.append(tx)
        return {
            'address': address,
            'balance': balance,
            'transactions': transactions,
            'transaction_count': len(transactions)
        }

    def register_node(self, address):
        self.nodes.add(address)

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            try:
                response = requests.get(f'{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain_data = response.json()['chain']
                    if length > max_length:
                        max_length = length
                        new_chain = chain_data
            except requests.exceptions.ConnectionError:
                print(f"Could not connect to node {node}. Skipping.")
        if new_chain:
            self.chain = new_chain
            self.save_chain_to_disk()
            print("Our chain was replaced by a longer one.")
            return True
        print("Our chain is authoritative.")
        return False
