Create a method in the `Blockchain` class called `new_transaction` 
that adds a new transaction to the list of transactions:

    :param sender: <str> Address of the Sender
    :param recipient: <str> Address of the Recipient
    :param amount: <int> Amount
    :return: <int> The index of the `block` that will hold this transaction

Modify the `mine` endpoint to create a reward via a `new_transaction`
for mining a block:

   - [x] The sender is "0" to signify that this node created a new coin
   - [x] The recipient is the id of the miner
   - [x] The amount is 1 coin as a reward for mining the next block

Create an endpoint at `/transactions/new` that accepts a json `POST`:

   - [x] use `request.get_json()` to pull the data out of the POST
   - [x] check that 'sender', 'recipient', and 'amount' are present
       - [x] return a 400 error using `jsonify(response)` with a 'message'
   - [x] upon success, return a 'message' indicating index of the block
      containing the transaction

