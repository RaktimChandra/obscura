"""Central configuration for OBSCURA.

Every tunable lives here so the demo can be reasoned about in one place.
Read this first when you want to understand the privacy/security posture.
"""

# ---- Differential privacy ----
# Epsilon is the privacy budget. Smaller = more private = more noise.
EPSILON_DEFAULT = 1.0
# Total epsilon a single zone may spend per rolling window before we refuse
# to answer any more queries about it. This is the "we refuse to over-query
# our own citizens" guarantee.
ZONE_EPSILON_BUDGET = 10.0
# Sensitivity of a counting query: one person can change a count by at most 1.
COUNT_SENSITIVITY = 1.0
# k-anonymity: never release a statistic about a group smaller than this.
K_ANON_THRESHOLD = 5

# ---- Threshold cryptography (Shamir t-of-n) ----
# n key holders, t required to reconstruct. 2-of-3: police + oversight + judiciary.
SHAMIR_N = 3
SHAMIR_T = 2
KEY_HOLDERS = ["police", "oversight_officer", "judiciary"]
# 13th Mersenne prime (2**521 - 1). Larger than any 256-bit AES key, so a key
# always fits inside the finite field used for secret sharing.
SHAMIR_PRIME = 2 ** 521 - 1

# ---- Demo / runtime ----
FEATURE_BUFFER_SIZE = 600          # ~ last N feature frames kept in memory
SYNTHETIC_FEED_HZ = 2              # frames per second for the synthetic feed
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
DB_PATH = "obscura.db"
