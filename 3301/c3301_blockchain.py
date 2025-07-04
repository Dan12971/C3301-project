import hashlib
import time
import json
import os
from ecdsa import SigningKey, VerifyingKey, NIST384p

class PuzzleMaster:
    # ... (The PuzzleMaster class is correct and does not need changes)
    def _generate_word_from_seed(self, seed_int, length=7):
        word = ""; temp_seed = seed_int
        for _ in range(length): word += chr((temp_seed % 26) + ord('A')); temp_seed >>= 5
        return word
    def _create_caesar_cipher_puzzle(self, seed):
        seed_int = int(seed, 16); solution_word = self._generate_word_from_seed(seed_int); solution_number = (seed_int >> 64) % 1000; solution = f"{solution_word}{solution_number}"; shift_key = (seed_int >> 32) % 22 + 3; encrypted_text = ""
        for char in solution:
            if 'A' <= char <= 'Z': shifted = ord(char) + shift_key; encrypted_text += chr(shifted - 26 if shifted > ord('Z') else shifted)
            else: encrypted_text += char
        puzzle = f"Decrypt the following text: '{encrypted_text}'"; clue = f"Caesar cipher, shift key = {shift_key}"; solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return { "puzzle_type": "HashCommitment", "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }
    def _create_vigenere_puzzle(self, seed):
        seed_int = int(seed, 16); solution_word = self._generate_word_from_seed(seed_int, length=8); keyword = self._generate_word_from_seed(seed_int >> 64, length=5); solution_number = (seed_int >> 128) % 1000; solution = f"{solution_word}{solution_number}"; encrypted_text = ""
        for i, char in enumerate(solution):
            if 'A' <= char <= 'Z': shift = ord(keyword[i % len(keyword)]) - ord('A'); shifted = ord(char) + shift; encrypted_text += chr(shifted - 26 if shifted > ord('Z') else shifted)
            else: encrypted_text += char
        puzzle = f"Decrypt the text using the keyword: '{encrypted_text}'"; clue = f"Vigenère cipher, keyword = '{keyword}'"; solution_hash = hashlib.sha256(solution.encode()).hexdigest()
        return { "puzzle_type": "HashCommitment", "puzzle": puzzle, "clue": clue, "solution_hash": solution_hash }
    def _create_hashing_challenge_puzzle(self, seed, difficulty_level):
        seed_int = int(seed, 16); num_zeros = 3 + (difficulty_level // 500); salt = seed_int % 1000000; puzzle_string = f"C3301-Block-{difficulty_level}-{salt}-"; puzzle = f"Find a number (nonce) such that the SHA-256 hash of '{puzzle_string}{{nonce}}' starts with {num_zeros} zeros."; clue = "This requires a brute-force script to solve. The solution is the nonce itself."
        return { "puzzle_type": "HashingChallenge", "puzzle": puzzle, "clue": clue, "puzzle_data": { "prefix": puzzle_string, "zeros": num_zeros } }
    def create_new_puzzle(self, difficulty_level, seed):
        seed_int = int(seed, 16);
        if difficulty_level <= 1500: return self._create_caesar_cipher_puzzle(seed) if seed_int % 2 == 0 else self._create_vigenere_puzzle(seed)
        elif difficulty_level <= 3301: return self._create_hashing_challenge_puzzle(seed, difficulty_level)
        else: return {"puzzle": "All tokens have been discovered.", "clue": "The hunt is complete."}

class Wallet:
    def __init__(self): self.private_key = SigningKey.generate(curve=NIST384p); self.public_key = self.private_key.verifying_key; self.address = self.public_key.to_string().hex()

class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None, data=None): self.sender, self.recipient, self.amount, self.timestamp, self.signature, self.data = sender, recipient, amount, timestamp or time.time(), None, data or {}
    def to_json(self): return json.dumps({"sender": self.sender, "recipient": self.recipient, "amount": self.amount, "timestamp": self.timestamp, "data": self.data}, sort_keys=True)
    def set_signature(self, signature): self.signature = signature
    @staticmethod
    def is_valid(transaction):
        if transaction.sender in ["MINT_REWARD", "NETWORK_FEES"]: return True
        if not transaction.signature: return False
        try:
            pk_bytes = bytes.fromhex(transaction.sender); verifying_key = VerifyingKey.from_string(pk_bytes, curve=NIST384p); sig_bytes = bytes.fromhex(transaction.signature)
            return verifying_key.verify(sig_bytes, transaction.to_json().encode())
        except Exception as e: print(f"Transaction validation failed: {e}"); return False

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, data=None, nonce=0): self.index, self.transactions, self.timestamp, self.previous_hash, self.data, self.nonce, self.hash = index, transactions, timestamp, previous_hash, data, nonce, self.calculate_hash()
    def calculate_hash(self): return hashlib.sha256((str(self.index) + json.dumps(self.transactions, sort_keys=True) + str(self.timestamp) + str(self.previous_hash) + json.dumps(self.data, sort_keys=True) + str(self.nonce)).encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []; self.pending_transactions = []; self.nodes = set(); self.chain_file = "blockchain_data.json"; self.puzzle_master = PuzzleMaster(); self.transaction_fee = 0.001; self.load_chain_from_disk()
    def save_chain_to_disk(self):
        try:
            chain_data = [vars(block) for block in self.chain]
            with open(self.chain_file, 'w') as f: json.dump(chain_data, f, indent=4)
        except Exception as e: print(f"Error saving chain to disk: {e}")
    def load_chain_from_disk(self):
        if not os.path.exists(self.chain_file): self.create_genesis_block(); self.save_chain_to_disk(); return
        try:
            with open(self.chain_file, 'r') as f: self.chain = [Block(**block_data) for block_data in json.load(f)]
        except Exception: self.create_genesis_block(); self.save_chain_to_disk()
    def create_genesis_block(self):
        genesis_seed = hashlib.sha256("The Hunt Begins 2025-06-24".encode()).hexdigest()
        first_puzzle = self.puzzle_master.create_new_puzzle(difficulty_level=1, seed=genesis_seed)
        self.chain = [Block(index=0, transactions=[], timestamp=time.time(), previous_hash="0", data=first_puzzle)]
    @property
    def latest_block(self): return self.chain[-1]
    
    # --- NEW HELPER METHOD ---
    def get_balance(self, address):
        """Calculates the balance of an address by iterating through all confirmed blocks."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.get('sender') == address:
                    balance -= tx.get('amount', 0)
                    balance -= self.transaction_fee # Also deduct the fee
                if tx.get('recipient') == address:
                    balance += tx.get('amount', 0)
        return balance

    # UPDATED to perform validation, INCLUDING BALANCE CHECK
    def add_transaction(self, transaction):
        if not Transaction.is_valid(transaction):
            print("Transaction validation failed: Invalid signature.")
            return False
        
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance < (transaction.amount + self.transaction_fee):
            print(f"Transaction validation failed: Insufficient funds for sender {transaction.sender[:10]}...")
            print(f"  Required: {transaction.amount + self.transaction_fee}, Available: {sender_balance}")
            return False
            
        self.pending_transactions.append(transaction)
        return True

    def forge_transaction_block(self, forger_address):
        if not self.pending_transactions: print("No pending transactions to forge."); return None
        print(f"Forger {forger_address[:10]}... is forging a new transaction block.")
        total_fees = len(self.pending_transactions) * self.transaction_fee
        fee_tx = Transaction(sender="NETWORK_FEES", recipient=forger_address, amount=total_fees)
        all_transactions = [fee_tx] + self.pending_transactions # Now a list of objects
        new_block = Block(index=len(self.chain), transactions=[vars(tx) for tx in all_transactions], timestamp=time.time(), previous_hash=self.latest_block.hash, data={"type": "TRANSACTION_BLOCK", "forged_by": forger_address})
        self.chain.append(new_block); self.pending_transactions = []; self.save_chain_to_disk(); print(f"Success! Transaction Block #{new_block.index} forged."); return new_block

    def attempt_mint(self, solver_wallet, proposed_solution):
        # ... (This logic is correct and remains the same)
        latest_block_data = self.latest_block.data; puzzle_type = latest_block_data.get('puzzle_type')
        if latest_block_data.get('type') == 'TRANSACTION_BLOCK': print("Minting Error: Must solve puzzle from the last Artifact Block."); return None
        is_solution_correct = False
        if puzzle_type == "HashCommitment":
            commitment = latest_block_data.get('solution_hash')
            if commitment and hashlib.sha256(proposed_solution.encode()).hexdigest() == commitment: is_solution_correct = True
        elif puzzle_type == "HashingChallenge":
            try:
                nonce = int(proposed_solution); puzzle_data = latest_block_data.get('puzzle_data', {}); prefix, zeros = puzzle_data.get('prefix', ''), puzzle_data.get('zeros', 0)
                if hashlib.sha256(f"{prefix}{nonce}".encode()).hexdigest().startswith("0" * zeros): is_solution_correct = True
            except (ValueError, TypeError): return None
        if not is_solution_correct: print("Failed Mint Attempt: Incorrect solution."); return None
        print("Solution Correct! Forging new ARTIFACT block...")
        artifact_block_count = sum(1 for b in self.chain if b.data.get('puzzle_type')); next_difficulty_level = artifact_block_count + 1
        previous_block_hash_as_seed = self.latest_block.hash; next_puzzle_package = self.puzzle_master.create_new_puzzle(difficulty_level=next_difficulty_level, seed=previous_block_hash_as_seed)
        total_reward = 1 + (len(self.pending_transactions) * self.transaction_fee)
        all_transactions = [Transaction(sender="MINT_REWARD", recipient=solver_wallet.address, amount=total_reward)] + self.pending_transactions
        new_block = Block(index=len(self.chain), transactions=[vars(tx) for tx in all_transactions], timestamp=time.time(), previous_hash=self.latest_block.hash, data=next_puzzle_package)
        self.chain.append(new_block); self.pending_transactions = []; self.save_chain_to_disk(); print(f"Success! Artifact Block #{new_block.index} created."); return new_block

    def get_address_data(self, address):
        txs, balance = [], 0.0
        for block in self.chain:
            for tx_data in block.transactions:
                if tx_data.get('sender') == address: balance -= tx_data.get('amount', 0); txs.append(tx_data)
                if tx_data.get('recipient') == address: balance += tx_data.get('amount', 0); txs.append(tx_data)
        return {'address': address, 'balance': balance, 'transactions': txs, 'transaction_count': len(txs)}

