import json
import os
import random
import requests
import sys
sys.path.append('../')
from settings import settings
from hashlib import blake2b
from multiprocessing import Pool, cpu_count
from timeit import default_timer
from uuid import uuid4

SECRET_KEY = os.getenv('SECRET_KEY').encode()
AUTH_SIZE = int(os.getenv('AUTH_SIZE'))
URL = os.getenv('URL')
NUM_ZEROS = int(os.environ.get('NUM_ZEROS'))
PROCESSES = cpu_count()

print('\ncpu_count:', PROCESSES)
print(f'Hash difficulty: {NUM_ZEROS}')


def _hash(proof_string):
    hasher = blake2b(key=SECRET_KEY, digest_size=AUTH_SIZE)
    hasher.update(proof_string.encode('utf8'))
    hash_ = hasher.hexdigest()
    return hash_


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
    if _hash(proof_string)[:NUM_ZEROS] == '0' * NUM_ZEROS:
        return True
    return False


def get_data():
    req = requests.get(url=URL + "/last_block")
    try:
        data = req.json()
    except ValueError:
        print("Error:  Non-json response")
        print("Response returned:")
        print(req)
        return
    return data


def do_a_transaction():
    requests.post(url=URL + '/transactions/new', json={'amount': random.randint(0, 100),
                                                       'sender': random.randint(0, 100),
                                                       'recipient': random.randint(0, 100)})


def status_update(x, dash, status):
    if x % 100000 == 0:
        if dash:
            status += '-'
            do_a_transaction()
            dash = False
        else:
            status += '*'
            dash = True
        print(status, end='\r')
    if x % 10000000 == 0:
        status = '$'
        print(status)
    return dash


def final_status(coins_mined, guess_rates, total_time):
    print('\nSession finished.')
    print(f"Total coins mined this session: {coins_mined}")
    print(f'Average guess rate average this session: {sum(guess_rates) / len(guess_rates):.2f}/sec')
    print(f'High average guess rate: {max(guess_rates):.2f}/sec '
          f'Low average guess rate: {min(guess_rates):.2f}/sec')
    print(f'Average time per block: {total_time / coins_mined:.2f} sec')
    print(f'Total time this session: {total_time:.2f} sec')


def get_node():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = URL
    return url


def get_id():
    try:
        f = open("../my_id.txt", "r")
        id_ = f.read()
        print("ID is", id_)
        f.close()

    except FileNotFoundError:
        id_ = str(uuid4()).replace('-', '')
        print("ID is", id_)
        f = open("my_id.txt", "w")
        f.write(id_)
        f.close()
    return id_


def block_update(coins_mined, guess_rate, coin_time):
    print(f'\n** {message} **')
    print(f"Total coins mined this session: {coins_mined}")
    print(f'Guess rate for this block: {guess_rate:.2f}/sec')
    print(f"Time to mine last block: {coin_time:.2f} sec")
    print(f'Average time per block: {total_time / coins_mined:.2f} sec')
    print(f'Total time this session: {total_time:.2f} sec\n')


if __name__ == '__main__':
    # What is the server address? IE `python3 miner.py https://server.com/api/`
    try:
        with Pool() as pool:
            url = get_node()
            id_ = get_id()

            coins_mined, total_time = 0, 0
            guess_rates = []

            # Run forever until interrupted
            while True:
                then = default_timer()
                print('Mining next block...  "-*" = 200,000 guesses')
                data = get_data()

                # Get the block from `data` and use it to look for a new proof
                block = json.dumps(data['last_block'])
                x, guesses = 0, 100000
                status, dash = '$', True
                print(status, end='\r')
                while True:
                    new_proof = pool.starmap(valid_proof, [(block, guess) for guess in range(x, x + guesses)],
                                             chunksize=guesses // PROCESSES)
                    new_proof_ = [x for x, guess in enumerate(new_proof, start=x) if guess]
                    if new_proof_:
                        break
                    x += guesses
                    dash = status_update(x, dash, status)

                # When found, POST it to the server {"proof": new_proof, "id": id}
                post = {"proof": new_proof_[0], "id": id_}
                req = requests.post(url=url + "/mine", json=post)
                data = req.json()

                # If the server responds with a 'message' 'New Block Forged'
                # add 1 to the number of coins mined and print it.  Otherwise,
                # print the message from the server.
                message = data['message']
                if message == 'New Block Forged':
                    coins_mined += 1
                    now = default_timer()
                    coin_time = now - then
                    total_time += coin_time
                    guess_rate = new_proof_[0] / coin_time
                    guess_rates.append(guess_rate)
                    block_update(coins_mined, guess_rate, coin_time)
                else:
                    print(message)
    except KeyboardInterrupt:
        final_status(coins_mined, guess_rates, total_time)
        sys.exit(0)

