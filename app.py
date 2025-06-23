from flask import Flask, jsonify, request, render_template
from ecdsa import SigningKey, NIST384p
from c3301_blockchain import Blockchain, Wallet, Transaction
from argparse import ArgumentParser

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explorer')
def explorer_ui():
    return render_template('explorer.html')

@app.route('/wallet', methods=['GET'])
def get_wallet():
    wallet = Wallet()
    return jsonify({
        'message': 'New wallet created.',
        'public_address': wallet.address,
        'private_key': wallet.private_key.to_string().hex()
    }), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required): return 'Missing values', 400
    tx = Transaction(values['sender'], values['recipient'], values['amount'])
    tx.set_signature(values['signature'])
    if blockchain.add_transaction(tx):
        return jsonify({'message': 'Transaction will be added to the next Block.'}), 201
    return jsonify({'message': 'Invalid transaction.'}), 400

@app.route('/transactions/sign', methods=['POST'])
def sign_transaction_request():
    values = request.get_json()
    required = ['private_key', 'sender', 'recipient', 'amount']
    if not all(k in values for k in required): return 'Missing values', 400
    try:
        pk_obj = SigningKey.from_string(bytes.fromhex(values['private_key']), curve=NIST384p)
        tx = Transaction(values['sender'], values['recipient'], values['amount'])
        signature = pk_obj.sign(tx.to_json().encode())
        return jsonify({'signature': signature.hex()}), 200
    except Exception as e: return f"Error: {e}", 500

@app.route('/mint', methods=['POST'])
def mint_coin():
    values = request.get_json()
    required = ['solver_address', 'secret_phrase']
    if not all(k in values for k in required): return 'Missing values', 400
    class SolverWallet: address = values['solver_address']
    new_block = blockchain.attempt_mint(SolverWallet, values['secret_phrase'])
    if new_block:
        return jsonify({
            'message': 'New Block Forged!',
            'block_index': new_block.index,
            'transactions': new_block.transactions,
            'data_clue': new_block.data
        }), 200
    return jsonify({'message': 'Minting failed. Invalid solution or already solved.'}), 400

@app.route('/block/<int:block_index>', methods=['GET'])
def get_block(block_index):
    if 0 <= block_index < len(blockchain.chain):
        return jsonify(blockchain.chain[block_index]), 200
    return "Error: Block not found", 404

@app.route('/address/<address>', methods=['GET'])
def get_address_info(address):
    return jsonify(blockchain.get_address_data(address)), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    nodes = request.get_json().get('nodes')
    if nodes is None: return "Error: Please supply a valid list of nodes", 400
    for node in nodes: blockchain.register_node(node)
    return jsonify({'message': 'New nodes have been added', 'total_nodes': list(blockchain.nodes)}), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    message = 'Our chain was replaced' if replaced else 'Our chain is authoritative'
    return jsonify({'message': message, 'chain': blockchain.chain}), 200

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)
