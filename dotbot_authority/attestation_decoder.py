import cbor2
from pycose.messages.sign1message import Sign1Message
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature
from logger import LOGGER
import attestation_provision

IANA_CBOR_COSWID_FILE_FS_NAME_KEY = 24
#IANA_CBOR_COSWID_FILE_SIZE_KEY = 20
IANA_CBOR_COSWID_FILE_HASH_IMAGE_KEY = 7
IANA_CBOR_COSWID_FILE_KEY = 17

IANA_CBOR_COSWID_ENTITY_ENTITY_NAME_KEY = 31
IANA_CBOR_COSWID_ENTITY_ROLE = 33

IANA_CBOR_COSWID_TAG_ID_KEY = 0
IANA_CBOR_COSWID_TAG_VERSION_KEY = 12
IANA_CBOR_COSWID_SOFTWARE_NAME_KEY = 1
IANA_CBOR_COSWID_ENTITY_KEY = 2
IANA_CBOR_COSWID_EVIDENCE_KEY = 3

IANA_CBOR_EAT_UEID_KEY = 256
IANA_CBOR_EAT_NONCE_KEY = 10
IANA_CBOR_EAT_MEASUREMENTS_KEY = 273 

IANA_COAP_CONTENT_FORMATS_SWID = 258

IANA_COSE_HEADER_PARAMETERS_ALG = 1

def parse_payload(payload_bytes):
    nonce = payload_bytes.get(IANA_CBOR_EAT_NONCE_KEY).hex()
    ueid = payload_bytes.get(IANA_CBOR_EAT_UEID_KEY)
    measurements = payload_bytes.get(IANA_CBOR_EAT_MEASUREMENTS_KEY)

    decoded_info = {
        "nonce": nonce,
        "ueid": ueid,
        "measurements": [],
    }

    if measurements:
        for measurement in measurements:

            content_format_id = measurement[0]
            coswid = measurement[1]
            #tag_id = coswid.get(IANA_CBOR_COSWID_TAG_ID_KEY)
            #tag_version = coswid.get(IANA_CBOR_COSWID_TAG_VERSION_KEY)
            #software_name = coswid.get(IANA_CBOR_COSWID_SOFTWARE_NAME_KEY)

            # entity = coswid.get(IANA_CBOR_COSWID_ENTITY_KEY)
            # if entity:
            #     entity_name = entity.get(IANA_CBOR_COSWID_ENTITY_ENTITY_NAME_KEY)
            #     entity_role = entity.get(IANA_CBOR_COSWID_ENTITY_ROLE)
    
            evidence = coswid.get(IANA_CBOR_COSWID_EVIDENCE_KEY)
            files_info = []
            if evidence:
                files = evidence.get(IANA_CBOR_COSWID_FILE_KEY)
                    
                if files:
                    for file_data in files:
                        
                        fs_name = file_data.get(IANA_CBOR_COSWID_FILE_FS_NAME_KEY)
                        #size = file_data.get(IANA_CBOR_COSWID_FILE_SIZE_KEY)
                        hash_image = file_data.get(IANA_CBOR_COSWID_FILE_HASH_IMAGE_KEY)

                        if hash_image:
                            hash_alg = hash_image[0]
                            hash_value = hash_image[1].hex()
                        file_info = {
                            "fs_name": fs_name,
                            #"size": size,
                            "hash_alg": hash_alg,
                            "hash_value": hash_value,
                        }
                        files_info.append(file_info)

    decoded_info["measurements"].append({
        "content_format_id": content_format_id,
        #"tag_id": tag_id,
        #"tag_version": tag_version,
        #"software_name": software_name,
        #"entity_name": entity_name,
        #"entity_role": entity_role,
        "files_info": files_info,
    })

    return decoded_info  

def decode_cose_sign1_message(cose_sign1_bytes, public_key_bytes):
    LOGGER.debug(f"start to parse the cose_sign1 message")

    # decode the COSE_Sign1 message
    cose_msg = Sign1Message.decode(cose_sign1_bytes)
    if not isinstance(cose_msg, Sign1Message):
        print("The message is not a COSE_Sign1 message.")
    
    # signature check
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    protected_header = cose_msg.phdr_encoded
    payload = cose_msg.payload
    signature = cose_msg.signature
    external_aad = b''
    sig_structure = cbor2.dumps(["Signature1", protected_header, external_aad, payload])
    #try:
    public_key.verify(signature, sig_structure)
    print("Signature check: SUCCESS\n Signature is: ", signature.hex())
    # except InvalidSignauture as e:
    #     raise MyException ()    
    if isinstance(payload, bytes):
        payload = cbor2.loads(payload)

    decode_info = parse_payload(payload)

    return decode_info

def generate_result_pp(result_int, nonce_reuslt_pp):
    token_payload = {
        256:'controller',
        10: nonce_reuslt_pp,
        274:[["", ["", result_int]]]
    }
    cbor_token_payload = cbor2.dumps(token_payload)
    protected = cbor2.dumps({1:-8})
    
    #prepare the signature of cose_sign1
    sig_structure = [
        "Signature1", protected, b"", cbor_token_payload
    ]
    cbor_sig_structure = cbor2.dumps(sig_structure)
    print(cbor_sig_structure.hex(" "))
    private_key = Ed25519PrivateKey.from_private_bytes(attestation_provision.private_key_verifier)
    signature = private_key.sign(cbor_sig_structure)

    # assemble to be a cose_sign1
    cose_sign1 = [
        protected,
        {},
        cbor_token_payload,
        signature
    ]
    tagged_cose = cbor2.dumps(cbor2.CBORTag(18, cose_sign1))
    return tagged_cose

# for swarm attestation
def mr_swarm_check_signature(signature_attester, asn_dl, version, node_id):
    # prepare sig_structure
    hash_verifier = attestation_provision.swarm_reference_value_list[version]
    key_id_verifier = attestation_provision.node_to_key_id[node_id]
    sig_structure = cbor2.dumps([asn_dl, hash_verifier, key_id_verifier])
    
    public_key_bytes = attestation_provision.swarm_public_key_list[key_id_verifier]
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    try:
        public_key.verify(signature_attester, sig_structure)
        return True
    except InvalidSignature:
        return False

def mr_swarm_generate_verification_response(result, node_id):
    if (result):
        sig_structure_cbor = cbor2.dumps([1, attestation_provision.key_id_v, node_id])
    else:
        sig_structure_cbor = cbor2.dumps([0, attestation_provision.key_id_v, node_id])
    private_key = Ed25519PrivateKey.from_private_bytes(attestation_provision.private_key_verifier)
    result_signed = private_key.sign(sig_structure_cbor)
    # generate verification_response
    verification_response = cbor2.dumps([result_signed, node_id, attestation_provision.key_id_v])
    return verification_response
