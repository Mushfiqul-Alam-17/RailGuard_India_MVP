import logging
import hashlib
import os
import json
import binascii
import time
from datetime import datetime
from eth_hash.auto import keccak

# Configure logging
logger = logging.getLogger(__name__)

class BlockchainVerifier:
    """Simple blockchain for Trust ID verification"""

    def __init__(self):
        # Set up storage
        self.blockchain_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blockchain')
        if not os.path.exists(self.blockchain_dir):
            os.makedirs(self.blockchain_dir)

        self.blockchain_file = os.path.join(self.blockchain_dir, 'blockchain.json')

        # Initialize blockchain if it doesn't exist
        if not os.path.exists(self.blockchain_file):
            self._initialize_blockchain()
        else:
            # Load existing blockchain
            with open(self.blockchain_file, 'r') as f:
                self.chain = json.load(f)

        logger.info(f"Blockchain initialized with genesis block: {self.chain[0]['hash'][:8]}...")

    def _initialize_blockchain(self):
        """Create genesis block"""
        genesis_block = {
            'index': 0,
            'timestamp': datetime.now().isoformat(),
            'data': 'Genesis Block - RailGuard India Trust ID System',
            'previous_hash': '0' * 64,
            'nonce': 0
        }

        # Add hash to genesis block
        genesis_block['hash'] = self._hash_block(genesis_block)

        # Initialize chain with genesis block
        self.chain = [genesis_block]

        # Save blockchain
        self._save_blockchain()

    def _hash_block(self, block):
        """Create SHA-256 hash of a block"""
        # Convert block to a consistent string format
        block_string = json.dumps(
            {key: block[key] for key in sorted(block.keys()) if key != 'hash'}, 
            sort_keys=True
        )

        # Return the hash as a hexadecimal string
        return hashlib.sha256(block_string.encode()).hexdigest()

    def _save_blockchain(self):
        """Save blockchain to file"""
        with open(self.blockchain_file, 'w') as f:
            json.dump(self.chain, f, indent=2)

    def _get_last_block(self):
        """Get the last block in the chain"""
        return self.chain[-1]

    def _create_block(self, data):
        """Create a new block with the given data"""
        last_block = self._get_last_block()

        new_block = {
            'index': last_block['index'] + 1,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'previous_hash': last_block['hash'],
            'nonce': 0
        }

        # Simple proof of work (find a hash with 3 leading zeros)
        while True:
            new_block['hash'] = self._hash_block(new_block)
            if new_block['hash'].startswith('000'):
                break
            new_block['nonce'] += 1

        return new_block

    def add_transaction(self, data):
        """Add a new transaction to the blockchain"""
        new_block = self._create_block(data)
        self.chain.append(new_block)
        self._save_blockchain()
        return new_block

    def verify_chain(self):
        """Verify the integrity of the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # Check hash of current block
            if current_block['hash'] != self._hash_block(current_block):
                return False

            # Check if previous hash matches
            if current_block['previous_hash'] != previous_block['hash']:
                return False

        return True

def create_trust_id(phone, aadhaar=""):
    """Create a new Trust ID in the blockchain"""
    try:
        # Initialize blockchain
        blockchain = BlockchainVerifier()

        # Create unique data for this trust ID
        timestamp = int(time.time())
        random_salt = binascii.hexlify(os.urandom(8)).decode()

        # Create trust ID data
        trust_id_data = {
            'phone': phone,
            'aadhaar_hash': hashlib.sha256(aadhaar.encode()).hexdigest() if aadhaar else "",
            'timestamp': timestamp,
            'salt': random_salt
        }

        # Add to blockchain
        block = blockchain.add_transaction(trust_id_data)

        # Create TID hash (simplified)
        tid_hash = keccak(
            f"{phone}:{timestamp}:{random_salt}".encode()
        ).hex()

        # In a real implementation, this would be stored on IPFS
        # For demo, we'll return the block hash as the IPFS CID
        ipfs_cid = block['hash'][:16]

        return tid_hash, ipfs_cid
    except Exception as e:
        logger.error(f"Error creating trust ID: {str(e)}")
        return hashlib.sha256(phone.encode()).hexdigest(), "error"

def verify_trust_id(tid_hash):
    """Verify a Trust ID exists in the blockchain"""
    try:
        # Initialize blockchain
        blockchain = BlockchainVerifier()

        # Verify blockchain integrity
        if not blockchain.verify_chain():
            logger.error("Blockchain verification failed")
            return False

        # Search for the TID hash in the blockchain
        for block in blockchain.chain:
            if block['index'] == 0:  # Skip genesis block
                continue

            # Extract data from block
            data = block['data']

            # Check if this block contains the TID
            if isinstance(data, dict) and 'phone' in data:
                # Recreate the TID hash
                phone = data['phone']
                timestamp = data['timestamp']
                salt = data['salt']

                calculated_hash = keccak(
                    f"{phone}:{timestamp}:{salt}".encode()
                ).hex()

                if calculated_hash == tid_hash:
                    return True

        return False
    except Exception as e:
        logger.error(f"Error verifying trust ID: {str(e)}")
        return False