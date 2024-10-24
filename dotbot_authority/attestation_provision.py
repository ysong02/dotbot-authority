#nonce = bytes.fromhex('a29f62a4c6cdaae5')
public_key_bytes = bytes.fromhex('b24f6d4e5f8147af1d1cd8c26e1a510b7a0f7f0a7bcc60688955d327b99c6475')
#basedir = r"C:\Users\yusong\OneDrive - INRIA\Documents\implementation\DotBot-firmware\projects\01drv_attestation\Output\nrf52840dk\Debug\Exe" 
basedir = r"C:\Users\yusong\OneDrive - INRIA\Documents\implementation\DotBot-firmware-token\projects\03app_dotbot\Output\nrf5340dk-app\Debug\Exe"
accepted_type_evidence = [60, 61, 258] #cbor /cwt /swid+cbor
approved_hash_evidence = [
    ("5e0b9ca06bd0fe8af89142525d50d6b197393d3102d7a4b08c52e8f786fc67e4", "DotBot"),
    ("666b9ca06bd0fe8af86666666650d6b197393d3102d7a4b08c52e8f786666666", "CoffeeBot firmware"),

]
