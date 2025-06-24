from flask import Flask, jsonify, request, render_template
from c3301_blockchain import Blockchain, Wallet
from argparse import ArgumentParser

app = Flask(__name__)
blockchain = Blockchain()

# --- Frontend Routes ---
@app.route('/')
def landing_page(): return render_template('landing.html')
@app.route('/app')
def app_ui(): return render_template('app.html')
@app.route('/explorer')
def explorer_ui(): return render_template('explorer.html')

# --- NEW Endpoint for Transaction Layer ---
@app.route('/forge', methods=['POST'])
def forge_block():
    """
    Creates a new block to confirm pending transactions,
    rewarding the forger with the transaction fees.
    """
    values = request.get_json()
    forger_address = values.get('forger_address')
    if not forger_address:
        return jsonify({'message': 'Error: Forger address is required.'}), 400

    new_block = blockchain.forge_transaction_block(forger_address)

    if new_block:
        response = {
            'message': 'Transaction Block Forged!',
            'block_index': new_block.index,
            'transactions': new_block.transactions
        }
        return jsonify(response), 200
    else:
        response = {'message': 'Forging failed. No pending transactions.'}
        return jsonify(response), 400

# --- Existing API Endpoints ---
# (The rest of the file is the same, included for completeness)
@app.route('/wallet', methods=['GET'])
def get_wallet():
    wallet = Wallet()
    return jsonify({ 'public_address': wallet.address, 'private_key': wallet.private_key.to_string().hex() }), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # ... (this endpoint remains the same)
    # NOTE: In a real PoS system, transaction validation would be more complex.
    # For our prototype, adding it to the pending pool is sufficient.
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required): return 'Missing values', 400
    
    # In a full implementation, the transaction signature would be verified here
    # before adding to the pool. We are simplifying for the prototype.
    blockchain.add_transaction(values)
    return jsonify({'message': 'Transaction added to pending pool.'}), 201

@app.route('/mint', methods=['POST'])
def mint_coin():
    # ... (this endpoint remains the same)
    values = request.get_json()
    required = ['solver_address', 'secret_phrase']
    if not all(k in values for k in required): return 'Missing values', 400
    class SolverWallet: address = values['solver_address']
    new_block = blockchain.attempt_mint(SolverWallet, values['secret_phrase'])
    if new_block:
        return jsonify({ 'message': 'New Artifact Block Forged!', 'block': new_block.__dict__ }), 200
    else:
        return jsonify({'message': 'Minting failed. Invalid solution or already solved.'}), 400

