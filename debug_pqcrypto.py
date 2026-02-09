import pqcrypto.kem.ml_kem_512 as kem
import sys

print(f"Testing {kem.__name__}")
try:
    pk, sk = kem.generate_keypair()
    print(f"PK type: {type(pk)}, length: {len(pk)}")
    print(f"SK type: {type(sk)}, length: {len(sk)}")
    
    expected_sk_len = 1632
    if len(sk) != expected_sk_len:
        print(f"ERROR: SK length {len(sk)} != {expected_sk_len}")
    else:
        print("SK length matches expectation.")

    ct, ss = kem.encrypt(pk)
    print(f"CT type: {type(ct)}, length: {len(ct)}")
    print(f"SS type: {type(ss)}, length: {len(ss)}")

    ss2 = kem.decrypt(ct, sk)
    print(f"Decrypted SS type: {type(ss2)}, length: {len(ss2)}")
    
    if ss == ss2:
        print("Shared secrets match!")
    else:
        print("Shared secrets DO NOT match!")

except Exception as e:
    print(f"Exception occurred: {e}")
    import traceback
    traceback.print_exc()
