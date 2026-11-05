The composed X and YouTube returns captured public objects and text while explicitly marking binary media comparison pending. The ten-minute successful-readback cache reused those partial returns after comparison finished, preventing their completed media evidence from reaching reconciliation in the same bucket.

The native readback owner now issues a read-only successor bound to the immutable partial return's hash. A completed exact observation still uses the normal cache, identity, object, content, media and freshness checks. No write or retry is added.

Validation: python -m pytest -q tests/test_native_neo_executor_v1.py -k 'pending_media_readback or successful_exact_readback_survives_bucket_change' --tb=short: 9 passed, 66 deselected in 6.62s. One targeted pytest process, no parallel workers.
