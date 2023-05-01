'''
    auth.py
    Authentication functions for dechat
'''

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256

def main():
    '''
        main
        Demonstration of the authentication functions
    '''
    # Make a new key
    key = RSA.generate(2048)

    # This is how you get a printable key
    printable_private_key = key.export_key()

    # This is how you turn a printable key back into a key object
    # The private key should never leave the client
    priv_key = RSA.import_key(printable_private_key)

    # This is the object that should be shared with the server
    pub_key = priv_key.public_key()

    # Generate a challenge, this should be new and random every time
    challenge = generate_challenge()
    print("Generated Challenge: ", challenge)

    # Attempt the challenge
    challenge_solution = solve_challenge(challenge, priv_key)
    print("Completed Challenge: ", challenge_solution)

    # Check the validity
    print("Validity: ", verify_challenge(challenge, challenge_solution, pub_key))


def generate_challenge(challenge_len=256) -> bytes:
    '''
        generate_challenge
        Generates a random challenge
        :: challenge_len :: Number of bytes in the challenge
    '''
    return get_random_bytes(challenge_len)

def solve_challenge(challenge: bytes, priv_key) -> bytes:
    '''
        solve_challenge
        Signs the hash of the challenge with a pubkey
        :: challenge :: Random bytes to hash then sign
        :: priv_key :: Private key to sign
        Returns the signed bytes
    '''
    hash_obj = SHA256.new(data=challenge)
    signed_challenge = pkcs1_15.new(priv_key).sign(hash_obj)
    return signed_challenge

def verify_challenge(challenge : bytes, response : bytes, pub_key) -> bool:
    '''
        verify_challenge
        Verifies the response to a challenge
        :: challenge :: Random bytes to hash then sign
        :: response  :: An attempt at hashing and signing the challenge
        :: pub_key :: Public key to test against
        The pkcs1_15 verification raises a value error on failure
        This function wraps that error and returns a boolean
    '''
    try:
        hash_obj = SHA256.new(data=challenge)
        pkcs1_15.new(pub_key).verify(hash_obj, response)
        return True
    except ValueError:
        return False


# This is an example of using the authentication
if __name__ == '__main__':
    main()
