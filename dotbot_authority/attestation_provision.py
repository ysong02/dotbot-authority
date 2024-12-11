#nonce = bytes.fromhex('a29f62a4c6cdaae5')
public_key_bytes = bytes.fromhex('b24f6d4e5f8147af1d1cd8c26e1a510b7a0f7f0a7bcc60688955d327b99c6475')
#basedir = r"C:\Users\yusong\OneDrive - INRIA\Documents\implementation\DotBot-firmware\projects\01drv_attestation\Output\nrf52840dk\Debug\Exe" 
basedir = r"C:\Users\yusong\OneDrive - INRIA\Documents\implementation\DotBot-firmware-token\projects\03app_dotbot\Output\nrf5340dk-app\Debug\Exe"
accepted_type_evidence = [60, 61, 258] #cbor /cwt /swid+cbor
approved_hash_evidence = [
    ("9db1221d2ff7e268b38f3d321b0a42591ffdd7ed2028a5ee678f342329e3722a"),
]
list_hash_versions = [
    ("a9bd6a4436951ae4cf1b7b9a8d6696321fe10b981916e1dc9e4a3bb8067a9a79"),
    ("9db1221d2ff7e268b38f3d321b0a42591ffdd7ed2028a5ee678f342329e3722a"),
]