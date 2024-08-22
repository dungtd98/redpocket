# import secrets
# import base64
# from cryptography.hazmat.primitives.asymmetric import rsa
# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.backends import default_backend

# # Step 1: Generate a nonce
# nonce = secrets.token_urlsafe(16)

# # Step 2: Generate RSA key pair
# private_key = rsa.generate_private_key(
#     public_exponent=65537,
#     key_size=2048,
#     backend=default_backend()
# )
# public_key = private_key.public_key()

# # Step 3: Convert the public key to PEM format and encode in URL-safe base64
# public_key_pem = b"""-----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAk/vfs0ytA8P+ubKxUPW1
# w9qthOuOUH2QtIhmyA+9/qbIKHlf1bR+BcwpXU+8TLglAREs+qm9MeaIrhKH6ITI
# 4nauIxsyorEMklo4xZlDw+uGekmBOZbZ2mbKCJNiHVFuP/sg86A02aUvn6udrxjQ
# kakZTm81713b1sFq4qwy2a+Ee0rSq2dywxFWObAdWDzwqQx2d/XNGWkvzct9REE6
# XPQNjTLvPOVpcfkkpLscAH5HZpJ7JMi3Tj6vN2TzhWjyESj5ptkFZGphOo8PqrQA
# HlH2xErX2K68kJ/b36Dn8PC4rAZAzmiG0DNRtkKrPUolWQyi9Qbl7oVJBO55AiZK
# WQIDAQAB
# -----END PUBLIC KEY-----"""
# public_key_b64 = base64.urlsafe_b64encode(public_key_pem).decode('utf-8')

# # Step 4: Construct the OAuth URL
# bot_id = '5899297704'
# scope = 'identity'

# telegram_oauth_url = f"https://oauth.telegram.org/auth?bot_id={bot_id}&scope={scope}&public_key={public_key_b64}&nonce={nonce}"

# print("Telegram OAuth URL:", telegram_oauth_url)

import base64
import urllib.parse

# Assuming you have your public key in PEM format in `public_key_pem`:
public_key_pem = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAk/vfs0ytA8P+ubKxUPW1
w9qthOuOUH2QtIhmyA+9/qbIKHlf1bR+BcwpXU+8TLglAREs+qm9MeaIrhKH6ITI
4nauIxsyorEMklo4xZlDw+uGekmBOZbZ2mbKCJNiHVFuP/sg86A02aUvn6udrxjQ
kakZTm81713b1sFq4qwy2a+Ee0rSq2dywxFWObAdWDzwqQx2d/XNGWkvzct9REE6
XPQNjTLvPOVpcfkkpLscAH5HZpJ7JMi3Tj6vN2TzhWjyESj5ptkFZGphOo8PqrQA
HlH2xErX2K68kJ/b36Dn8PC4rAZAzmiG0DNRtkKrPUolWQyi9Qbl7oVJBO55AiZK
WQIDAQAB
-----END PUBLIC KEY-----"""

# Base64 URL-safe encode
public_key_b64 = base64.urlsafe_b64encode(public_key_pem).decode('utf-8')

# URL-encode the base64 string
public_key_urlencoded = urllib.parse.quote(public_key_b64)

telegram_oauth_url = f"https://oauth.telegram.org/auth?bot_id=5899297704&scope=identity&public_key={public_key_urlencoded}&nonce=9WN7ZMBHfle_Vi7IAcQAuQ"

print("Telegram OAuth URL:", telegram_oauth_url)
