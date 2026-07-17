# Encrypt retrievable Invitation Links separately from lookup hashes

Invitation Link lookup continues to use a one-way SHA-256 token hash. While an
Invitation remains usable, the same token is also stored as authenticated ciphertext
using an operator-supplied 256-bit key so an authenticated Tutor can redisplay the
link during a personal email conversation.

The ciphertext is never a lookup key and never appears in ordinary Invitation
responses or logs. Claim, revocation, lazy expiration, and regeneration erase the
stored ciphertext; regeneration also replaces the prior lookup hash atomically. The
encryption key is typed secret configuration and is mandatory outside development,
so production cannot silently use a repository-known fallback.
