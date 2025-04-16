import os
import web3
from web3 import Web3
from eth_account import Account
import json



class TokenProcessor:
    def __init__(self):
        self.private_key = os.getenv('PRIVATE_KEY')
        self.infura_url = os.getenv('INFURA_URL')
        self.usdc_contract_address = os.getenv('ARBITRUM_USDC_CONTRACT_ADDRESS')


    def send_usdc(self, recipient_address: str, amount: float=0.01):
        # Connect to Ethereum network (using Infura as provider)
        w3 = Web3(Web3.HTTPProvider(self.infura_url))
        print(w3.is_connected())
        
        # USDC has 6 decimal places
        amount_in_units = int(amount * 10**6)
        
        # ABI for USDC transfer function
        ABI = [
            {
                "constant": False,
                "inputs": [
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        try:
            # Create contract instance
            contract = w3.eth.contract(address=self.usdc_contract_address, abi=ABI)
            
            # Get nonce
            account = Account.from_key(self.private_key)
            nonce = w3.eth.get_transaction_count(account.address)
            
            # Build transaction
            gas_price = w3.eth.gas_price
            gas_price_with_buffer = int(gas_price * 1.2)  # Add 20% buffer
            
            transaction = contract.functions.transfer(
                recipient_address,
                amount_in_units
            ).build_transaction({
                'chainId': 42161,  # Arbitrum One
                'gas': 500000,     # Increased from 100000 to 500000
                'gasPrice': gas_price_with_buffer,  # Use gasPrice instead of maxFeePerGas
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction successful! Transaction hash: {tx_hash.hex()}")
        
        except Exception as e:
            return print(f"Error: {str(e)}")


if __name__ == '__main__':
    # Example: Send 0.01 USDC
    tp = TokenProcessor(PRIVATE_KEY, INFURA_URL, USDC_CONTRACT_ADDRESS)
    tp.send_usdc(METAMASK_ACCOUNT, 0.01)