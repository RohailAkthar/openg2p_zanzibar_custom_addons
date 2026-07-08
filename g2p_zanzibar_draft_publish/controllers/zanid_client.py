import base64
import json
import logging
from typing import Optional, Dict, Any

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.exceptions import InvalidSignature

_logger = logging.getLogger(__name__)


class ZanidSignatureError(Exception):
    """Raised when signing or verification fails."""
    pass


class ZanidClient:
    def __init__(
        self,
        base_url: str,
        private_key_path: str,
        private_key_password: str,
        api_key: str,
        x_road_client: Optional[str] = None,
        private_key_alias: Optional[str] = None,
        zcsra_public_cert_path: Optional[str] = None,
        zcsra_public_cert_password: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """
        base_url:               Base SG URL, e.g. ".../ZANID/zanid"
        private_key_path:       Path to your institution's private .pfx / .p12 keystore
        private_key_password:   Password for the keystore
        api_key:                Your institution's API key issued by ZCSRA
        x_road_client:          Value for the X-Road-Client header
        private_key_alias:      Alias to select inside the keystore, if it contains multiple entries
        zcsra_public_cert_path: Optional path to ZCSRA's public cert to verify response signatures
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.x_road_client = x_road_client
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self._private_key = self._load_private_key(
            private_key_path, private_key_password, private_key_alias
        )
        self._zcsra_public_key = None
        if zcsra_public_cert_path:
            self._zcsra_public_key = self._load_public_key(
                zcsra_public_cert_path, zcsra_public_cert_password
            )

    # ------------------------------------------------------------------ #
    # Key loading
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_private_key(path: str, password: str, alias: Optional[str] = None):
        with open(path, "rb") as f:
            pfx_data = f.read()

        password_bytes = password.encode() if password else None

        if path.lower().endswith((".pfx", ".p12")):
            private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data, password_bytes
            )
            if private_key is None:
                raise ZanidSignatureError(
                    f"No private key found in keystore '{path}'. "
                    "Check the file actually contains a private key entry."
                )
            return private_key
        else:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            return load_pem_private_key(pfx_data, password=password_bytes)

    @staticmethod
    def _load_public_key(path: str, password: Optional[str] = None):
        with open(path, "rb") as f:
            data = f.read()

        if path.lower().endswith((".pfx", ".p12")):
            from cryptography.hazmat.primitives.serialization import pkcs12 as pkcs12_mod
            password_bytes = password.encode() if password else None
            try:
                _, cert, additional = pkcs12_mod.load_key_and_certificates(data, password_bytes)
            except ValueError:
                certs = pkcs12_mod.load_pkcs12(data, password_bytes)
                cert = certs.cert.certificate if certs.cert else None
                if cert is None and certs.additional_certs:
                    cert = certs.additional_certs[0].certificate
                additional = []
            if cert is None and additional:
                cert = additional[0]
            if cert is None:
                raise ZanidSignatureError(f"No certificate found in '{path}'")
            return cert.public_key()
        else:
            from cryptography import x509
            try:
                cert = x509.load_pem_x509_certificate(data)
            except ValueError:
                cert = x509.load_der_x509_certificate(data)
            return cert.public_key()

    # ------------------------------------------------------------------ #
    # Core signing / verification (SHA1withRSA per ZANID SG spec)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _canonical_json(payload: Dict[str, Any]) -> bytes:
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def sign_payload(self, payload: Dict[str, Any]) -> str:
        message = self._canonical_json(payload)
        signature = self._private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
        return base64.b64encode(signature).decode("ascii")

    def verify_response_signature(self, payload: Dict[str, Any], signature_b64: str) -> bool:
        if self._zcsra_public_key is None:
            raise ZanidSignatureError(
                "No ZCSRA public certificate loaded."
            )
        message = self._canonical_json(payload)
        signature = base64.b64decode(signature_b64)
        try:
            self._zcsra_public_key.verify(
                signature,
                message,
                padding.PKCS1v15(),
                hashes.SHA1(),
            )
            return True
        except InvalidSignature:
            return False

    # ------------------------------------------------------------------ #
    # Request building / sending
    # ------------------------------------------------------------------ #

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.x_road_client:
            headers["X-Road-Client"] = self.x_road_client
        return headers

    def _send(self, endpoint_suffix: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        signature = self.sign_payload(payload)
        body = {"payload": payload, "signature": signature}

        url = f"{self.base_url}/{endpoint_suffix.lstrip('/')}"
        _logger.info("Sending request to ZANID SG URL: %s", url)
        response = requests.post(
            url,
            headers=self._headers(),
            json=body,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------ #
    # Public API — demographic request
    # ------------------------------------------------------------------ #

    def query_demographic(self, zanid: str, endpoint_suffix: str = "request") -> Dict[str, Any]:
        payload = {"apiKey": self.api_key, "zanid": str(zanid)}
        return self._send(endpoint_suffix, payload)


# ---------------------------------------------------------------------- #
# ZANID SG response codes (for quick reference / error handling)
# ---------------------------------------------------------------------- #

RESPONSE_CODES = {
    9000: "Success",
    9001: "Invalid Signature",
    9002: "Invalid API Key",
    9003: "ZanID Not Found",
    9004: "Operation Failed",
    9005: "Invalid Payload",
    9006: "Invalid IP Address",
    9007: "Query Method Not Permitted",
}

