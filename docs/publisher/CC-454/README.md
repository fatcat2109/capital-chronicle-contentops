# CC-454 — restore company LinkedIn and YouTube article routes

Jim's decision 121 reopens these two Neo article routes. Eight derivatives are required again; company LinkedIn keeps the existing reviewed member copy. Member LinkedIn and Instagram keep their official APIs.

The branch starts at operating HEAD `dddf45f2411f4c69960ec9d416da3e91de4c5b9e`, because remote master predates the applied Publisher work. Existing lane and operating-root changes are recorded by hash in `pre-existing-work.json` and stay outside these commits. The observed launch configuration is `gpt-6.1-sol/max`, with runtime model telemetry `CONFIGURED_NOT_OBSERVED`.

First route sub-step: `route-tests.xml` records 32 passes. Controlled coordinator transports cover all eight destinations, restored company selection, preserved identities, readback of uncertainty, no backfill of closed policy no-writes, API routes and unchanged status/card destinations. These checks do not claim public publication.

Live page access was inspected through BrowserOS Neo: company 143198922 has Start a post; @CapitalChronicleYouTube has its Posts tab and composer. Neither page showed an account restriction. The remaining implementation extends the existing CC-436 transport; no schedule changes or extra status/card routes are part of this item.
