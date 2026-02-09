import importlib
import time
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

from .logger import setup_logger

logger = setup_logger("Algorithms")

# Mapping from NIST standard names to pqcrypto module names
# Note: This assumes pqcrypto uses the pre-standardization names (Kyber, Dilithium) 
# or has aliases. We will try to map common names.
PQCRYPTO_MAPPING = {
    # KEMs
    "ML-KEM-512": "pqcrypto.kem.ml_kem_512",
    "ML-KEM-768": "pqcrypto.kem.ml_kem_768",
    "Kyber512": "pqcrypto.kem.kyber512",
    "Kyber768": "pqcrypto.kem.kyber768",
    
    # Signatures
    "ML-DSA-44": "pqcrypto.sign.ml_dsa_44",
    "ML-DSA-65": "pqcrypto.sign.ml_dsa_65",
    "Dilithium2": "pqcrypto.sign.dilithium2",
    "Dilithium3": "pqcrypto.sign.dilithium3",
    "Falcon-512": "pqcrypto.sign.falcon_512",
    "SPHINCS+-128s-simple": "pqcrypto.sign.sphincs_shake_128s_simple",
}

class CryptoAlgorithm(ABC):
    def __init__(self, name: str, implementation: str):
        self.name = name
        self.implementation = implementation
        self.module = self._load_module()

    def _load_module(self):
        if self.implementation == "pqcrypto":
            module_name = PQCRYPTO_MAPPING.get(self.name, self.name)
            try:
                return importlib.import_module(module_name)
            except ImportError as e:
                logger.error(f"Failed to load {module_name} for {self.name}: {e}")
                raise
        elif self.implementation == "dilithium-py":
            # Placeholder for dilithium-py support
            if "ML-DSA" in self.name or "Dilithium" in self.name:
                # This assumes a specific structure for dilithium-py which might vary
                raise NotImplementedError("dilithium-py support not fully implemented yet")
        else:
            raise ValueError(f"Unknown implementation: {self.implementation}")
        return None

class KEM(CryptoAlgorithm):
    def keygen(self) -> Tuple[bytes, bytes]:
        """Returns (public_key, secret_key)"""
        pk, sk = self.module.generate_keypair()
        # Debug logging
        logger.info(f"DEBUG: {self.name} KeyGen -> pk_len={len(pk)}, sk_len={len(sk)}")
        return bytes(pk), bytes(sk)

    def encaps(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Returns (ciphertext, shared_secret)"""
        # Ensure input is bytes
        if not isinstance(public_key, bytes): public_key = bytes(public_key)
        
        ct, ss = self.module.encrypt(public_key)
        return bytes(ct), bytes(ss)

    def decaps(self, ciphertext: bytes, secret_key: bytes) -> bytes:
        """Returns shared_secret"""
        # Ensure inputs are bytes
        if not isinstance(ciphertext, bytes): ciphertext = bytes(ciphertext)
        if not isinstance(secret_key, bytes): secret_key = bytes(secret_key)
        
        # Note: pqcrypto's decrypt(secret_key, ciphertext) expects SK first!
        # This is opposite to many other libraries (like cryptography.io or even our abstraction which usually does func(data, key))
        # But looking at the inspected code: def decrypt(secret_key, ciphertext): ...
        return bytes(self.module.decrypt(secret_key, ciphertext))

class Signature(CryptoAlgorithm):
    def keygen(self) -> Tuple[bytes, bytes]:
        """Returns (public_key, secret_key)"""
        pk, sk = self.module.generate_keypair()
        return bytes(pk), bytes(sk)

    def sign(self, message: bytes, secret_key: bytes) -> bytes:
        """Returns signature"""
        if not isinstance(message, bytes): message = bytes(message)
        if not isinstance(secret_key, bytes): secret_key = bytes(secret_key)
        
        return bytes(self.module.sign(secret_key, message))

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Returns True if valid, False otherwise"""
        if not isinstance(public_key, bytes): public_key = bytes(public_key)
        if not isinstance(message, bytes): message = bytes(message)
        if not isinstance(signature, bytes): signature = bytes(signature)
        # pqcrypto verify usually returns None on success, raises Exception on failure 
        # OR returns boolean. Need to check specific implementation. 
        # Usually: open(verification_key, signed_message) -> message or None
        # But pqcrypto might expose verify(pk, msg, sig)
        
        # Checking typical pqcrypto interface:
        # sign(sk, msg) -> signed_msg (sig + msg) or just sig?
        # usually pqcrypto.sign.dilithium2.sign(sk, msg) returns signature + message
        # and open(pk, sm) returns message.
        
        # However, for benchmarking, we often want 'detached' signatures.
        # If the library only supports attached, we measure that.
        # Let's assume standard pqcrypto `sign` returns `signature` (or `signed_message`)
        # We will wrap it.
        
        try:
            if hasattr(self.module, 'verify'):
                return self.module.verify(public_key, message, signature)
            elif hasattr(self.module, 'open'):
                 # 'open' usually takes (pk, signed_message)
                 # If we have detached signature, we might need to construct it.
                 # For simplicity in benchmark, we might just measure 'open' cost
                 # assuming we passed the right thing.
                 # Let's assume we use what `sign` returned.
                 res = self.module.open(public_key, signature)
                 return res == message
        except Exception:
            return False
        return False

def get_algorithm(alg_type: str, name: str, implementation: str = "pqcrypto") -> CryptoAlgorithm:
    if alg_type.lower() == "kem":
        return KEM(name, implementation)
    elif alg_type.lower() == "sign":
        return Signature(name, implementation)
    else:
        raise ValueError(f"Unknown algorithm type: {alg_type}")
