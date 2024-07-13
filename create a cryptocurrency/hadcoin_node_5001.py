#module 2-creating cryptocurrency
import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests#to make decentralization
from uuid import uuid4#to create address for each node
from urllib.parse import urlparse
#part 1 building a blockchain
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1,previous_hash='0')#proof,previous_hash are the arbitary values we can put whatever we want
        self.nodes = set()
    def create_block(self, proof, previous_hash):
        block = {
        'index' : len(self.chain)+1, 
        'timestamp': str(datetime.datetime.now()), 
        'proof' : proof, 
        'previous_hash' : previous_hash,
        'transactions' : self.transactions
                }
        self.transactions = []       
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1#to solve the problem we need to increament this new proof variable by one at each iteration to find the crct proof of targeted hash value
        check_proof = False#new_proof is not solution to the problem
        while check_proof is False:
            #use hash function sha256 combined to hexdigest function to return a string of 64 characters
            #this string will need to start from four leading zeros i.e., the targeted hash vale(smallest)
            #too many leading zeroes makes the miners hard to mine
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()#'-' is bcz to make it non-symmetrical a+b=b+a but,a-b!=b-a
            #**2 is only to increase the complexity to find the targeted hash
            #check four leading zeros 
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()#dumps converts the block data into str
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1 
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block#change the previous_block to current block and current to block to next block
            block_index += 1
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender' : sender,
                                  'receiver' : receiver,
                                  'amount' : amount})
        previous_block = get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f"http://{node}/get_chain")
            if response.status_code == 200:
                length = response.json()['length']#use json method coz,that response is bounded jsonify
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False





#Part 2 - Mining our blockchain
#creating a web app
app = Flask(__name__)

#creating an address for the node on port 5000 here,node means computer or miner
node_address = str(uuid4()).replace('-','')#uuid4 generates unique random address

#creating a blockchain
blockchain = Blockchain()

#mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'hadelin', amount = 1)#amount is the reward offering myself for the mining of the block
    block = blockchain.create_block(proof, previous_hash)
    response = {'message' : "congratulations you have mined a block!",
                 'index' : block['index'],
                 'timestamp' : block['timestamp'],
                 'proof' : block['proof'],
                 'previous_hash' : block['previous_hash'],
                 'transactions' : block['transactions']}
    return jsonify(response), 200

#Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

#checking the blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    check = blockchain.is_chain_valid(blockchain.chain)
    if check:
        response = {'message' : "blockchain is valid", 'chain' : blockchain.chain}
        
    else:
        response = {'message' : "blockchain is not valid", 'chain' : blockchain.chain}
    return jsonify(response), 200

#Adding a new Transaction to the blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    #check all the keys are present in the json file
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return "some elements of the transaction are missing", 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message' : f'this transaction will be added to block {index}'}
    return jsonify(respose), 201



#Part 3 Decentralizing our blockchain

#connecting the nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : 'All the nodes are now connected. The hadcoin blockchain now contains the following nodes',
                'total_nodes' : list(blockchain.nodes)}
    return jsonify(response), 201

#replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['POST'])
def replace_chain():
    is_chain_replace = blockchain.replace_chain()
    if is_chain_replace:
        response = {'message' : "the nodes had different so,the chain was replaced by the longest chain", 'new_chain' : blockchain.chain}
        
    else:
        response = {'message' : "All good.The chain is the largest one", 'actual_chain' : blockchain.chain}
    return jsonify(response), 200
        


#Running the app
app.run(host = '0.0.0.0', port = 5001)



