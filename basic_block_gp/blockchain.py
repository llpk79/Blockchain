import json
from hashlib import blake2b
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request

SECRET_KEY = b'super secret key'
AUTH_SIZE = 32


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        A block should have:
        * Index
        * Timestamp
        * List of current transactions
        * The proof used to mine this block
        * The hash of the previous block

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        if not self.chain or self.valid_proof(json.dumps(self.last_block), proof):
            block = {
                'index': len(self.chain),
                'prev_hash': previous_hash,
                'proof': proof,
                'timestamp': time(),
                'transactions': self.current_transactions,
            }

            # Reset the current list of transactions
            self.current_transactions = []
            # Append the chain to the block
            self.chain.append(block)
            # Return the new block
            return block
        print('Invalid proof.')

    def hash(self, block_string):
        """
        Creates a SHA-256 hash of a Block

        :param block_string": <dict> json string of Block
        "return": <str>
        """
        hasher = blake2b(key=SECRET_KEY, digest_size=AUTH_SIZE)
        hasher.update(block_string.encode('utf8'))
        hash = hasher.hexdigest()
        return hash

    @property
    def last_block(self):
        return self.chain[-1]

    def valid_proof(self, block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 3
        leading zeroes?  Return true if the proof is valid.

        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        proof_string = block_string + str(proof)
        n = 5
        if self.hash(proof_string)[:n] == '0' * n:
            return True
        return False

    def new_transaction(self, sender, recipient, amount):
        """Create a new transaction to add to the next block.

        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the `block` that will hold this transaction
        """
        transaction = {
            'amount': amount,
            'recipient': recipient,
            'sender': sender,
        }
        self.current_transactions.append(transaction)
        return len(self.chain)


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()
print(blockchain.last_block)


@app.route('/mine', methods=['POST'])
def mine():
    """Validate proof sent by client."""
    data = request.get_json()
    if 'proof' in data:
        proposed_proof = data['proof']
    else:
        response = {
            'message:': "Must submit proof."
        }
        return jsonify(response), 400

    if 'id' in data:
        user_id = data['id']
    else:
        response = {
            'message:': "Must submit user_id"
        }
        return jsonify(response), 400

    block = blockchain.last_block
    block_string = json.dumps(block)

    if blockchain.valid_proof(block_string, proposed_proof):
        blockchain.new_transaction(0, user_id, 1)
        blockchain.new_block(proof=proposed_proof, previous_hash=blockchain.hash(block_string))
        response = {
            'message': "New Block Forged"
        }
    else:
        response = {
            'message': "Sorry, your proof is not valid."
        }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    """Return the chain and its current length"""
    response = {
        'chain_length': len(blockchain.chain),
        'chain': {f"block_{x}": block for x, block in enumerate(blockchain.chain)}
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    if 'amount' in data:
        amount = data['amount']
    else:
        response = {
            'message': 'Include ammount'
        }
        return jsonify(response)
    if 'recipient' in data:
        recipient = data['recipient']
    else:
        response = {
            'message': 'Include recipient id.'
        }
        return jsonify(response)
    if 'sender' in data:
        sender = data['sender']
    else:
        response = {
            'message': "Include sender id."
        }
        return jsonify(response)

    blockchain.new_transaction(amount=amount, sender=sender, recipient=recipient)
    response = {
        'message': f'Index of transaction: {len(blockchain.chain)}'
    }
    return jsonify(response)


@app.route('/last_block', methods=['GET'])
def last_block():
    """Return the last block of the blockchain."""
    response = {
        'last_block': blockchain.last_block
    }
    return jsonify(response), 200


# Run the program on port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
