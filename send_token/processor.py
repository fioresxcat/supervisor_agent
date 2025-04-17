import os
import web3
from web3 import Web3
from eth_account import Account
import json
from dotenv import load_dotenv

load_dotenv()


class TokenProcessor:
    def __init__(self):
        self.private_key = os.getenv('PRIVATE_KEY')
        self.infura_url = os.getenv('INFURA_URL')
        self.usdc_contract_address = Web3.to_checksum_address(os.getenv('ARBITRUM_USDC_CONTRACT_ADDRESS'))
        self.w3 = Web3(Web3.HTTPProvider(self.infura_url))


    def send_usdc(self, recipient_address: str, amount: float=0.01) -> bool:
        """
        Sends a specified amount of USDC to a recipient address on the Arbitrum network.

        Args:
            recipient_address: The Ethereum address of the recipient.
            amount: The amount of USDC to send (e.g., 0.01).

        Returns:
            True if the transaction was successful, False otherwise.
        """
        if not self.w3.is_connected():
            print("Error: Not connected to Ethereum network.")
            return False

        if not Web3.is_address(recipient_address):
            print(f"Error: Invalid recipient address: {recipient_address}")
            return False

        if amount <= 0:
            print(f"Error: Amount must be positive: {amount}")
            return False

        try:
            # Ensure recipient address is checksummed
            checksum_recipient_address = Web3.to_checksum_address(recipient_address)

            # USDC has 6 decimal places
            amount_in_units = int(amount * 10**6)

            # ABI for USDC transfer function (simplified)
            transfer_abi = [{
                "constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"
            }]

            # Create contract instance
            contract = self.w3.eth.contract(address=self.usdc_contract_address, abi=transfer_abi)

            # Get sender account and nonce
            account = Account.from_key(self.private_key)
            sender_address = account.address
            nonce = self.w3.eth.get_transaction_count(sender_address)

            # Estimate Gas Limit
            gas_estimate = contract.functions.transfer(
                checksum_recipient_address,
                amount_in_units
            ).estimate_gas({'from': sender_address})
            # Add a buffer (e.g., 20%) to the estimate for safety
            gas_limit = int(gas_estimate * 1.2)

            # Get current gas price and add buffer
            gas_price = self.w3.eth.gas_price
            gas_price_with_buffer = int(gas_price * 1.2) # 20% buffer

            # Build transaction
            transaction = contract.functions.transfer(
                checksum_recipient_address,
                amount_in_units
            ).build_transaction({
                'chainId': 42161,  # Arbitrum One
                'gas': gas_limit,
                'gasPrice': gas_price_with_buffer,
                'nonce': nonce,
                'from': sender_address # Optional but good practice
            })

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            print(f"Transaction submitted. Waiting for confirmation... TX Hash: {tx_hash.hex()}")

            # Wait for transaction receipt with a timeout
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120) # Wait up to 120 seconds

            # Check transaction status from receipt
            if receipt['status'] == 1:
                gas_used = receipt['gasUsed']
                effective_gas_price = receipt.get('effectiveGasPrice', gas_price_with_buffer) # Use effective if available (EIP-1559), else fallback
                gas_cost_eth = Web3.from_wei(gas_used * effective_gas_price, 'ether')

                print("\n--- Transaction Successful! ---")
                print(f"  Recipient: {checksum_recipient_address}")
                print(f"  Amount Sent: {amount} USDC")
                print(f"  Transaction Hash: {receipt['transactionHash'].hex()}")
                print(f"  Block Number: {receipt['blockNumber']}")
                print(f"  Gas Used: {gas_used}")
                print(f"  Effective Gas Price: {Web3.from_wei(effective_gas_price, 'gwei')} Gwei")
                print(f"  Transaction Fee: {gas_cost_eth:.8f} ETH")
                print("-----------------------------\n")
                return True
            else:
                print("\n--- Transaction Failed! ---")
                print(f"  Transaction Hash: {receipt['transactionHash'].hex()}")
                print(f"  Status Code: {receipt['status']}")
                print(f"  Block Number: {receipt['blockNumber']}")
                print("  Reason: Transaction reverted by EVM.") # More specific reasons often require decoding revert messages
                print("---------------------------\n")
                return False

        except Exception as e:
            print(f"\n--- An Error Occurred ---")
            print(f"  Error Type: {type(e).__name__}")
            print(f"  Error Message: {str(e)}")
            # Specific checks for common issues
            if "replacement transaction underpriced" in str(e):
                 print("  Possible Cause: Nonce conflict or insufficient gas price increase for replacement.")
            elif "insufficient funds" in str(e):
                 print("  Possible Cause: Not enough ETH in the sender account to cover gas fees + transaction value (if sending ETH).")
            elif "nonce too low" in str(e):
                 print("  Possible Cause: Trying to reuse a nonce that has already been confirmed.")
            print("---------------------------\n")
            return False


if __name__ == '__main__':
    # Example: Send 0.01 USDC
    tp = TokenProcessor()
    tp.send_usdc('0xceeBf125c0FdB7Efd975Adf289E02dAfc2CAE39F', 0.01)