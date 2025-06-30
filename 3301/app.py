from flask import Flask, jsonify, request, render_template
from ecdsa import SigningKey, NIST384p
from c3301_blockchain import Blockchain, Wallet, Transaction
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

# --- API Endpoints ---
@app.route('/wallet', methods=['GET'])
def get_wallet():
    wallet = Wallet()
    return jsonify({ 'public_address': wallet.address, 'private_key': wallet.private_key.to_string().hex() }), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = [vars(block) for block in blockchain.chain]
    return jsonify({'chain': chain_data, 'length': len(chain_data)}), 200

# REWRITTEN to correctly create the Transaction object
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature', 'timestamp']
    if not all(k in values for k in required):
        return jsonify({'message': 'Missing values in transaction data'}), 400

    # Create a proper Transaction object from the received data
    tx_object = Transaction(
        sender=values['sender'],
        recipient=values['recipient'],
        amount=values['amount'],
        timestamp=values['timestamp']
    )
    tx_object.set_signature(values['signature'])

    # The add_transaction method now performs full validation
    if blockchain.add_transaction(tx_object):
        response = {'message': 'Transaction is valid and has been added to the pending pool.'}
        return jsonify(response), 201
    else:
        response = {'message': 'Transaction failed validation and was rejected.'}
        return jsonify(response), 400

@app.route('/transactions/sign', methods=['POST'])
def sign_transaction_request():
    values = request.get_json()
    required = ['private_key', 'sender', 'recipient', 'amount', 'timestamp']
    if not all(k in values for k in required): return jsonify({'message': 'Missing values'}), 400
    try:
        pk_obj = SigningKey.from_string(bytes.fromhex(values['private_key']), curve=NIST384p)
        tx = Transaction(values['sender'], values['recipient'], values['amount'], timestamp=values['timestamp'])
        signature = pk_obj.sign(tx.to_json().encode())
        return jsonify({'signature': signature.hex()}), 200
    except Exception as e:
        return jsonify({'message': f"Error during signing: {e}"}), 500

@app.route('/forge', methods=['POST'])
def forge_block():
    values = request.get_json()
    forger_address = values.get('forger_address')
    if not forger_address: return jsonify({'message': 'Error: Forger address is required.'}), 400
    new_block = blockchain.forge_transaction_block(forger_address)
    if new_block:
        return jsonify({'message': 'Transaction Block Forged!', 'block': vars(new_block)}), 200
    else:
        return jsonify({'message': 'Forging failed. No pending transactions.'}), 400

@app.route('/mint', methods=['POST'])
def mint_coin():
    values = request.get_json(); required = ['solver_address', 'secret_phrase']
    if not all(k in values for k in required): return jsonify({'message': 'Missing values'}), 400
    class SolverWallet: address = values['solver_address']
    new_block = blockchain.attempt_mint(SolverWallet, values['secret_phrase'])
    if new_block:
        return jsonify({'message': 'New Artifact Block Forged!', 'block': vars(new_block)}), 200
    return jsonify({'message': 'Minting failed. Invalid solution.'}), 400

@app.route('/address/<address>', methods=['GET'])
def get_address_info(address): return jsonify(blockchain.get_address_data(address)), 200

# --- Main execution ---
if __name__ == '__main__':
    parser = ArgumentParser(); parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on'); args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)

