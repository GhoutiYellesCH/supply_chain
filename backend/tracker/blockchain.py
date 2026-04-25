"""Hashing + on-chain anchoring helpers."""
import hashlib
import json
import logging
from typing import Optional, Tuple

from django.conf import settings

log = logging.getLogger(__name__)

# Minimal ABI matching contracts/contracts/AdhahiSupplyChain.sol
CONTRACT_ABI = [
    {"inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
     "name": "registerSheep", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
     "name": "addEvent", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
     "name": "verifyEvent",
     "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
     "name": "getRecord",
     "outputs": [
         {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
         {"internalType": "address", "name": "sender", "type": "address"},
         {"internalType": "bool", "name": "exists", "type": "bool"}],
     "stateMutability": "view", "type": "function"},
]


def compute_hash(payload: dict) -> str:
    """Deterministic SHA-256 hash of a JSON-serialisable payload, returned as 0x… hex."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return "0x" + digest


class BlockchainService:
    """Thin wrapper over web3.py. Falls back to no-op if BLOCKCHAIN_DISABLED."""

    def __init__(self):
        self.disabled = settings.BLOCKCHAIN_DISABLED or not settings.WEB3_RPC_URL
        self._w3 = None
        self._contract = None
        self._account = None
        self._next_nonce = None  # locally tracked to avoid RPC pending-nonce lag
        if not self.disabled:
            try:
                from web3 import Web3
                self._w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
                self._account = self._w3.eth.account.from_key(settings.WEB3_PRIVATE_KEY)
                self._contract = self._w3.eth.contract(
                    address=Web3.to_checksum_address(settings.CONTRACT_ADDRESS),
                    abi=CONTRACT_ABI,
                )
            except Exception as e:
                log.warning("Blockchain init failed, disabling: %s", e)
                self.disabled = True

    # ------------------------------------------------------------------ helpers
    def _hex_to_bytes32(self, hex_hash: str) -> bytes:
        h = hex_hash[2:] if hex_hash.startswith("0x") else hex_hash
        return bytes.fromhex(h)

    def _get_nonce(self) -> int:
        """Return the next nonce, tracked locally to handle rapid sequential txs.

        We seed from the chain's pending nonce on first use, then increment
        after each successful send. If we ever drift below the chain state
        (e.g. another process sent a tx), we resync.
        """
        chain_nonce = self._w3.eth.get_transaction_count(self._account.address, "pending")
        if self._next_nonce is None or self._next_nonce < chain_nonce:
            self._next_nonce = chain_nonce
        return self._next_nonce

    def _send(self, fn, wait_receipt: bool = True) -> str:
        nonce = self._get_nonce()
        # Bump suggested gas price by 50% so the tx isn't stuck behind cheaper ones
        gas_price = int(self._w3.eth.gas_price * 1.5)
        tx = fn.build_transaction({
            "from": self._account.address,
            "nonce": nonce,
            "gas": 200_000,
            "gasPrice": gas_price,
            "chainId": self._w3.eth.chain_id,
        })
        signed = self._account.sign_transaction(tx)
        # web3.py renamed rawTransaction → raw_transaction; support both
        raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")
        tx_hash = self._w3.eth.send_raw_transaction(raw)
        # Successfully accepted → reserve this nonce, advance our counter
        self._next_nonce = nonce + 1
        hex_hash = tx_hash.hex()
        if not hex_hash.startswith("0x"):
            hex_hash = "0x" + hex_hash
        log.info("tx submitted: %s (nonce %d, gasPrice %d)", hex_hash, nonce, gas_price)
        if wait_receipt:
            try:
                receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                if receipt.status != 1:
                    raise RuntimeError(f"Transaction reverted: {hex_hash}")
                log.info("tx mined: %s (block %s, gas %s)", hex_hash, receipt.blockNumber, receipt.gasUsed)
            except Exception as e:
                # Don't fail the API call — the tx is in the mempool, will mine eventually.
                # The verify endpoint will pick it up once it lands.
                log.warning("tx %s submitted but not yet mined: %s", hex_hash, e)
        return hex_hash

    # -------------------------------------------------------------- public API
    def register_sheep(self, hex_hash: str, wait_receipt: bool = True) -> Optional[str]:
        if self.disabled:
            return None
        try:
            return self._send(
                self._contract.functions.registerSheep(self._hex_to_bytes32(hex_hash)),
                wait_receipt=wait_receipt,
            )
        except Exception as e:
            log.exception("registerSheep failed: %s", e)
            return None

    def add_event(self, hex_hash: str, wait_receipt: bool = True) -> Optional[str]:
        if self.disabled:
            return None
        try:
            return self._send(
                self._contract.functions.addEvent(self._hex_to_bytes32(hex_hash)),
                wait_receipt=wait_receipt,
            )
        except Exception as e:
            log.exception("addEvent failed: %s", e)
            return None

    def verify(self, hex_hash: str) -> Tuple[bool, Optional[dict]]:
        if self.disabled:
            return False, None
        try:
            b = self._hex_to_bytes32(hex_hash)
            exists = self._contract.functions.verifyEvent(b).call()
            if not exists:
                return False, None
            ts, sender, _ = self._contract.functions.getRecord(b).call()
            return True, {"timestamp": ts, "sender": sender}
        except Exception as e:
            log.exception("verify failed: %s", e)
            return False, None


# Singleton
blockchain = BlockchainService()
