This self-signed localhost certificate and its public test private key exist
only for isolated loopback tests. They are not installed in any trust store.
`test-http.py` checks that the default TLS trust policy rejects the certificate.
Never use this key for an actual service.
