#nonce = bytes.fromhex('a29f62a4c6cdaae5')
public_key_bytes = bytes.fromhex('b24f6d4e5f8147af1d1cd8c26e1a510b7a0f7f0a7bcc60688955d327b99c6475')
public_key_controller = bytes.fromhex('4bef5ae83d1461ca715cd643c607e9371cec17c27d27b6d3ccc5ace843549026')
private_key_verifier = bytes.fromhex('8ed2d03fa136f5232f957e41d368940153d580e6b5ea57b68aa8836ff9539010')
public_key_verifier = bytes.fromhex('2463f9d5e61b84689b3b19ae10a3d6b5bfd1e69a643d7061aca4d04f7fd98db9')

basedir = r"C:\Users\yusong\OneDrive - INRIA\Documents\implementation\DotBot-firmware-token\projects\03app_dotbot\Output\nrf5340dk-app\Debug\Exe"
accepted_type_evidence = [60, 61, 258] #cbor /cwt /swid+cbor
approved_hash_dotbot = [
    ("a9bd6a4436951ae4cf1b7b9a8d6696321fe10b981916e1dc9e4a3bb8067a9a79"),
    ("9db1221d2ff7e268b38f3d321b0a42591ffdd7ed2028a5ee678f342329e3722a"),
]
approved_hash_controller = [
    ("h'A33F72164816796AD0A91D8546667B8EC144F4FD4BFE0C93EEBD346C385B3F0B")
]