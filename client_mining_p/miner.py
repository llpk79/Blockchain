from hashlib import blake2b
import requests
from uuid import uuid4
from timeit import default_timer
import random
import sys
import json


SECRET_KEY = b'super secret key'
AUTH_SIZE = 32


def proof_of_work(block):
    """
    Simple Proof of Work Algorithm
    Stringify the block and look for a proof.
    Loop through possibilities, checking each one against `valid_proof`
    in an effort to find a number that is a valid proof
    :return: A valid proof for the provided block
    """
    x = 0
    block_string = json.dumps(block)
    status = ''
    dash = True
    while True:
        if valid_proof(block_string, x):
            return x
        x += 1
        if x % 100000 == 0:
            if dash:
                status += '-'
                dash = False
                # Test transaction endpoint.
                do_a_transaction()
            else:
                status += '*'
                dash = True
            print(status, end="\r")
        if x % 10000000 == 0:
            status = ''
            print(status)


def valid_proof(block_string, proof):
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
    hasher = blake2b(key=SECRET_KEY, digest_size=AUTH_SIZE)
    hasher.update(proof_string.encode('utf8'))
    hash = hasher.hexdigest()
    n = 5
    if hash[:n] == '0' * n:
        return True
    return False


def do_a_transaction():
    post_data = {'amount': random.randint(0, 100),
                 'recipient': random.randint(0, 100),
                 'sender': random.randint(0, 100)}
    requests.post(url='http://localhost:5000' + '/transactions/new', json=post_data)


if __name__ == '__main__':
    # What is the server address? IE `python3 miner.py https://server.com/api/`
    if len(sys.argv) > 1:
        node = sys.argv[1]
    else:
        node = "http://localhost:5000"

    # Load ID
    try:
        f = open("my_id.txt", "r")
        id = f.read()
        print("ID is", id)
        f.close()
    except FileNotFoundError:
        id = str(uuid4()).replace('-', '')
        print("ID is", id)
        f = open("my_id.txt", "w")
        f.write(id)
        f.close()

    coins_mined = 0

    # Run forever until interrupted
    while True:
        then = default_timer()
        print('Mining...')
        r = requests.get(url=node + "/last_block")
        # Handle non-json response
        try:
            data = r.json()
        except ValueError:
            print("Error:  Non-json response")
            print("Response returned:")
            print(r)
            break

        # Get the block from `data` and use it to look for a new proof
        block = data['last_block']
        new_proof = proof_of_work(block)

        # When found, POST it to the server {"proof": new_proof, "id": id}
        post_data = {"proof": new_proof, "id": id}

        r = requests.post(url=node + "/mine", json=post_data)
        data = r.json()

        # If the server responds with a 'message' 'New Block Forged'
        # add 1 to the number of coins mined and print it.  Otherwise,
        # print the message from the server.
        message = data['message']
        if message == 'New Block Forged':
            coins_mined += 1
            print('\n', message)
            print(f"Total coins mined this session: {coins_mined}")
            now = default_timer()
            print(f"Time to mine last coin: {now - then:.2f} seconds.")
            if coins_mined == 20:
                r = requests.get(url=node + "/chain")
                print(r.json())
                break
        else:
            print(message)
