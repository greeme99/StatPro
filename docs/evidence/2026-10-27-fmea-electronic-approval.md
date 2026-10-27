# FMEA electronic approval control baseline

## Public regulatory reference

FDA guidance describes Part 11 controls including limiting system access to authorized individuals, authority checks, and accountability policies. The current eCFR requires closed systems to protect authenticity and integrity, signature manifestations to show the signer name, execution date/time, and meaning, electronic signatures to remain linked to their records, and each signature to be unique to one individual.

- https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application
- https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/subpart-B/section-11.10
- https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/subpart-B/section-11.50
- https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/subpart-B/section-11.70
- https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/subpart-C/section-11.100

These references justify individual technical controls. They do **not** establish that StatPro, a deployment, or an operating organization complies with 21 CFR Part 11.

## Minitab 14 boundary

No Minitab 14 FMEA electronic-signature screen, persisted record, session command, or binary behavior has been established. This increment is an independent StatPro quality-workflow feature and makes no Minitab 14 equivalence claim.

## StatPro implementation

- `statpro-approval-user` creates a local identity with a random salt and scrypt verifier; it does not persist the plaintext password.
- The identity file has a versioned format, rejects duplicate user IDs, and is replaced atomically. The default filename is ignored by Git.
- Every approval request requires password reauthentication. The identity must have the `fmea_approver` role.
- The server supplies the execution time and records the signer ID, display name, role, signature meaning, authority, and authentication method.
- The signature stores the digest of the in-review revision. The domain transition rejects a signature for any other revision, and the resulting approved revision retains its signed parent digest.
- All linked SPC/MSA Runs must still exist and match their stored Run ID, ETag, and input digest at approval time.
- The immutable audit event owns the signature record. Review reports manifest the signer name, time, meaning, and signed digest without exposing credentials.
- Legacy self-reported approval events remain readable and are labelled unauthenticated instead of being silently upgraded.

## Verification

- Identity unit tests cover successful reauthentication, invalid passwords, missing approval authority, atomic persistence, duplicate rejection, and absence of the plaintext password.
- Domain tests reject a signature whose digest does not match the current revision.
- API tests cover 401 invalid credentials, 403 authorization behavior, 503 missing configuration, signature fields, server time, report manifestation, and approval blocking when linked evidence cannot be verified.
- UI tests cover the user ID/password approval form and ensure the password is sent only in the approval request.
- Full local regression: Python 171/171 and UI 52/52 passed on 2026-10-27; the UI production build also passed.

## Known limitations

- The API is loopback-only and does not provide TLS or general user-session authentication.
- Identity proofing, credential issuance/revocation procedures, account lockout/expiry, MFA, enterprise identity-provider integration, and separation-of-duty policy administration remain deployment responsibilities or future work.
- Identity-file changes require an API restart.
- Statistical Run identity checks do not establish that an analysis is suitable for a particular Control Plan characteristic.
- Regulatory validation, procedural controls, and legal-equivalence assessment are outside this implementation claim.
