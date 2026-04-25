"""Sanity-check the backend .env values used for blockchain integration.

Usage:
    cd backend
    source .venv/bin/activate
    python check_env.py

Verifies:
  1. Required variables are set and not placeholders.
  2. Private key is exactly 64 hex chars (with optional 0x).
  3. Contract address is a valid checksum-able address.
  4. RPC URL is reachable and returns a Sepolia chain id (11155111).
  5. The signing account has a balance (warns if 0).
  6. The contract address actually has bytecode deployed at it.
  7. A read-only call to verifyEvent() succeeds against the contract.
"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def ok(msg):    print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):  print(f"  {RED}✗{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}!{RESET} {msg}")
def section(t): print(f"\n{BOLD}{t}{RESET}")

errors = 0
warnings = 0

# ---------------------------------------------------------------- 1. variables
section("1. Required variables")

rpc = os.getenv("WEB3_RPC_URL", "").strip()
pk  = os.getenv("WEB3_PRIVATE_KEY", "").strip()
addr= os.getenv("CONTRACT_ADDRESS", "").strip()
disabled = os.getenv("BLOCKCHAIN_DISABLED", "False").strip().lower() == "true"

PLACEHOLDERS = {
    "WEB3_RPC_URL": ["YOUR_KEY", "your_key"],
    "WEB3_PRIVATE_KEY": ["your_test_account_private_key"],
    "CONTRACT_ADDRESS": ["0xDeployedContractAddress"],
}

def is_placeholder(name, val):
    if not val:
        return True
    return any(p in val for p in PLACEHOLDERS[name])

for name, val in [("WEB3_RPC_URL", rpc), ("WEB3_PRIVATE_KEY", pk), ("CONTRACT_ADDRESS", addr)]:
    if is_placeholder(name, val):
        fail(f"{name} is missing or still a placeholder")
        errors += 1
    else:
        masked = val if name == "WEB3_RPC_URL" else val[:6] + "…" + val[-4:]
        ok(f"{name} = {masked}")

if disabled:
    warn("BLOCKCHAIN_DISABLED=True → backend will SKIP on-chain calls.")
    warnings += 1
else:
    ok("BLOCKCHAIN_DISABLED=False → on-chain calls enabled.")

# ---------------------------------------------------------------- 2. format
section("2. Format checks")

clean_pk = pk[2:] if pk.startswith("0x") else pk
if re.fullmatch(r"[0-9a-fA-F]{64}", clean_pk):
    ok("Private key is exactly 64 hex chars.")
else:
    fail(f"Private key length = {len(clean_pk)} chars (need 64 hex). Got: '{clean_pk[:10]}…'")
    errors += 1

if re.fullmatch(r"0x[0-9a-fA-F]{40}", addr):
    ok("Contract address has correct 0x + 40 hex format.")
else:
    fail(f"Contract address invalid format: '{addr}'")
    errors += 1

if not (rpc.startswith("http://") or rpc.startswith("https://")):
    fail(f"RPC URL must start with http(s)://  Got: '{rpc}'")
    errors += 1
else:
    ok("RPC URL scheme looks valid.")

if errors:
    print(f"\n{RED}Format errors found — fix .env first, then re-run.{RESET}")
    sys.exit(1)

# ---------------------------------------------------------------- 3. live checks
section("3. Live blockchain checks")

try:
    from web3 import Web3
except ImportError:
    fail("web3.py not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))

try:
    if not w3.is_connected():
        fail("Cannot connect to RPC URL.")
        errors += 1
        sys.exit(1)
    ok("Connected to RPC.")
except Exception as e:
    fail(f"RPC connection error: {e}")
    sys.exit(1)

try:
    chain_id = w3.eth.chain_id
    if chain_id == 11155111:
        ok(f"Chain id = {chain_id} (Sepolia ✓)")
    else:
        warn(f"Chain id = {chain_id} (Sepolia is 11155111). Make sure this is intentional.")
        warnings += 1
except Exception as e:
    fail(f"Could not read chain id: {e}")
    errors += 1

# Account & balance
try:
    acct = w3.eth.account.from_key("0x" + clean_pk)
    ok(f"Derived account address: {acct.address}")
    bal_wei = w3.eth.get_balance(acct.address)
    bal_eth = w3.from_wei(bal_wei, "ether")
    if bal_wei == 0:
        warn(f"Balance = 0 ETH. Fund this address from a Sepolia faucet before sending txs.")
        warnings += 1
    else:
        ok(f"Balance = {bal_eth} ETH")
except Exception as e:
    fail(f"Account/balance check failed: {e}")
    errors += 1

# Contract code at address
try:
    checksum = Web3.to_checksum_address(addr)
    code = w3.eth.get_code(checksum)
    if code in (b"", b"0x", bytes.fromhex("")):
        fail(f"No contract bytecode at {checksum}. Wrong CONTRACT_ADDRESS or wrong network.")
        errors += 1
    else:
        ok(f"Bytecode found at {checksum} ({len(code)} bytes).")
except Exception as e:
    fail(f"get_code failed: {e}")
    errors += 1

# Try a read-only call (verifyEvent on a dummy hash → should return False, not error)
try:
    VERIFY_ABI = [{
        "inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
        "name": "verifyEvent",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view", "type": "function",
    }]
    contract = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=VERIFY_ABI)
    dummy = b"\x00" * 32
    res = contract.functions.verifyEvent(dummy).call()
    ok(f"verifyEvent() callable on contract (returned {res} for zero hash, expected False).")
except Exception as e:
    fail(f"Contract call failed — ABI may not match deployed contract: {e}")
    errors += 1

# ---------------------------------------------------------------- summary
section("Summary")
if errors == 0 and warnings == 0:
    print(f"{GREEN}{BOLD}All checks passed. .env looks good.{RESET}")
    sys.exit(0)
elif errors == 0:
    print(f"{YELLOW}{BOLD}OK with {warnings} warning(s).{RESET}")
    sys.exit(0)
else:
    print(f"{RED}{BOLD}{errors} error(s), {warnings} warning(s). Fix and re-run.{RESET}")
    sys.exit(1)
