from flask import Flask, jsonify, request, render_template
from ecdsa import SigningKey, NIST384p

# Import our custom blockchain classes
from c3301_blockchain import Blockchain, Wallet, Transaction
from argparse import ArgumentParser

# --- Application Setup ---
app = Flask(__name__)

# Initialize a single, shared instance of our blockchain
blockchain = Blockchain()


# --- Frontend Endpoints ---

@app.route('/')
def landing_page():
    """Serves the main project landing page."""
    return render_template('landing.html')

@app.route('/app')
def app_ui():
    """Serves the main user interface for wallet and minting."""
    return render_template('app.html')

@app.route('/explorer')
def explorer_ui():
    """Serves the block explorer web page."""
    return render_template('explorer.html')


# --- API Endpoints for Core Functionality ---

@app.route('/wallet', methods=['GET'])
def get_wallet():
    """
    Generates a new wallet and returns its details.
    NOTE: In a real application, you would NEVER expose the private key like this.
    This is for demonstration purposes only.
    """
    wallet = Wallet()
    response = {
        'message': 'New wallet created.',
        'public_address': wallet.address,
        'private_key': wallet.private_key.to_string().hex()
    }
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    """Returns the full blockchain."""
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
    Accepts a new, signed transaction and adds it to the pending pool.
    """
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values in transaction data', 400

    tx = Transaction(values['sender'], values['recipient'], values['amount'])
    tx.set_signature(values['signature'])
    
    if blockchain.add_transaction(tx):
        response = {'message': 'Transaction will be added to the next Block.'}
        return jsonify(response), 201
    else:
        response = {'message': 'Invalid transaction.'}
        return jsonify(response), 400

@app.route('/transactions/sign', methods=['POST'])
def sign_transaction_request():
    """
    Signs transaction data with a provided private key.
    INSECURE - FOR DEMONSTRATION ONLY to avoid complex frontend crypto.
    """
    values = request.get_json()
    required = ['private_key', 'sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values for signing', 400

    try:
        private_key_obj = SigningKey.from_string(bytes.fromhex(values['private_key']), curve=NIST384p)
        tx = Transaction(values['sender'], values['recipient'], values['amount'])
        transaction_data = tx.to_json().encode()
        signature = private_key_obj.sign(transaction_data)
        response = {'signature': signature.hex()}
        return jsonify(response), 200
    except Exception as e:
        return f"Error during signing: {e}", 500

@app.route('/mint', methods=['POST'])
def mint_coin():
    """
    Attempts to mint a new coin by submitting a puzzle solution.
    """
    values = request.get_json()
    required = ['solver_address', 'secret_phrase']
    if not all(k in values for k in required):
        return 'Missing values for minting', 400

    class SolverWallet:
        address = values['solver_address']
    
    proposed_solution = values['secret_phrase']
    new_block = blockchain.attempt_mint(SolverWallet, proposed_solution)

    if new_block:
        response = {
            'message': 'New Block Forged!',
            'block_index': new_block.index,
            'transactions': new_block.transactions,
            'data_clue': new_block.data
        }
        return jsonify(response), 200
    else:
        response = {'message': 'Minting failed. Invalid solution or already solved.'}
        return jsonify(response), 400

# --- API Endpoints for Explorer ---

@app.route('/block/<int:block_index>', methods=['GET'])
def get_block(block_index):
    """Returns the details of a specific block by its index."""
    if 0 <= block_index < len(blockchain.chain):
        return jsonify(blockchain.chain[block_index]), 200
    return "Error: Block not found", 404

@app.route('/address/<address>', methods=['GET'])
def get_address_info(address):
    """Returns the balance and transaction history for an address."""
    return jsonify(blockchain.get_address_data(address)), 200

# --- API Endpoints for P2P Networking ---

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """Accepts a list of new nodes to join the network."""
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """Runs the consensus algorithm to resolve conflicts."""
    replaced = blockchain.resolve_conflicts()
    message = 'Our chain was replaced' if replaced else 'Our chain is authoritative'
    return jsonify({'message': message, 'chain': blockchain.chain}), 200

# --- Main execution ---

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)
