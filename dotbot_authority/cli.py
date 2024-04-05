#!/usr/bin/python3

"""
dotbot-authority-cli new --basedir ~/.dotbots-deployment1 --label dotbot1
dotbot-authority-cli new --basedir ~/.dotbots-deployment1 --label dotbot2
dotbot-authority-cli new --basedir ~/.dotbots-deployment1 --label dotbot3
dotbot-authority-cli new --basedir ~/.dotbots-deployment1 --label dotbot4
dotbot-authority-cli new --basedir ~/.dotbots-deployment1 --label gateway6
dotbot-authority-cli new --basedir ~/.dotbots-deployment1 --label server9
"""

import uuid, cbor2, click, os, re, rich, glob
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta


def gen_id(label, basedir):
    id = uuid.uuid4()
    priv = ec.generate_private_key(ec.SECP256R1(), default_backend())

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Inria"),
            x509.NameAttribute(NameOID.COMMON_NAME, id.urn),
            x509.NameAttribute(NameOID.PSEUDONYM, label),
        ]
    )
    cred_cert_self_signed = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(priv.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .sign(priv, hashes.SHA256(), default_backend())
    )

    cred_rpk_ccs = {
        2: id.bytes,
        8: {
            1: {
                1: 2,
                2: int(label[-1]).to_bytes(1, "big"),
                -1: 1,
                -2: priv.public_key().public_numbers().x.to_bytes(32, "big"),
                -3: priv.public_key().public_numbers().y.to_bytes(32, "big"),
            }
        },
    }

    def write_to_file(filename, content):
        print(f"Writing {len(content)} bytes to {filename}")
        with open(filename, "wb") as f:
            f.write(content)

    write_to_file(
        f"{basedir}/{label}-cert-p256.pem",
        cred_cert_self_signed.public_bytes(serialization.Encoding.PEM),
    )
    write_to_file(
        f"{basedir}/{label}-priv-p256.pem",
        priv.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ),
    )

    write_to_file(
        f"{basedir}/{label}-priv-bytes",
        priv.private_numbers().private_value.to_bytes(32, "big"),
    )
    write_to_file(f"{basedir}/{label}-cred-rpk.cbor", cbor2.dumps(cred_rpk_ccs))


@click.group()
def main():
    pass


@main.command("new")
@click.option(
    "--basedir", required=True, help="Directory where identity info will be saved"
)
@click.option("--label", required=True, help="Label for the new dotbot identity")
def new(basedir, label):
    print(f"Generating new identity.")
    if not os.path.exists(basedir):
        os.mkdir(basedir)
    gen_id(label, basedir)


@main.command("list")
@click.option(
    "--basedir", required=True, help="Directory where identity info is stored"
)
def list(basedir):
    print(f"Listing identities.")
    if not os.path.exists(basedir):
        raise Exception(f"Directory {basedir} does not exist.")
    labels = set(
        [re.match(r"^[a-z0-9]+", filename).group(0) for filename in os.listdir(basedir)]
    )
    labels = {
        label: [os.path.basename(e) for e in glob.glob(f"{basedir}/{label}*")]
        for label in labels
    }
    rich.print(labels)


if __name__ == "__main__":
    main()
