"""Synthetic e-discovery corpus. Every name, number, and matter here is invented.

Designed so each page steers toward a different branch of the review graph.
"""

PROTOCOL = (
    "Matter 24-CV-118 (Hollis v. Arcadia Freight). Produce all documents concerning "
    "Q3 2024 revenue recognition, including revenue timing, cutoff adjustments, and "
    "communications about restating quarterly figures."
)

PAGES = [
    {
        "doc_id": "ARC-000141",
        "expect": "produce",
        "page": (
            "ARCADIA FREIGHT -- Q3 2024 REVENUE SUMMARY (INTERNAL)\n"
            "Recognized revenue for the quarter ended 30 Sep 2024 was $48.2M, up 6% "
            "sequentially. Of this, $3.1M relates to shipments that departed on "
            "1 Oct and was recognized in Q3 under the prior cutoff convention. "
            "Finance is reviewing whether the cutoff should be restated."
        ),
    },
    {
        "doc_id": "ARC-000212",
        "expect": "withhold",
        "page": (
            "ARCADIA FREIGHT -- FACILITIES NOTICE\n"
            "The Dock 4 loading bay will be closed for resurfacing from 11-14 March. "
            "Please route all inbound pallets to Dock 2. Vending machines on the "
            "second floor will be restocked Tuesday."
        ),
    },
    {
        "doc_id": "ARC-000377",
        "expect": "redact",
        "page": (
            "ARCADIA FREIGHT -- Q3 CUTOFF ADJUSTMENT APPROVALS\n"
            "The Q3 revenue cutoff adjustment of $3.1M was approved by the following:\n"
            "  Dana Whitfield, Controller -- dana.whitfield@arcadiafreight.example "
            "-- mobile 555-0148 -- employee ID 44192\n"
            "  Marcus Oyelaran, VP Finance -- payroll account 8841-220-19\n"
            "Supporting workpapers are filed under WP-Q3-CUTOFF-11."
        ),
    },
    {
        "doc_id": "ARC-000401",
        "expect": "attorney_review",
        "page": (
            "PRIVILEGED AND CONFIDENTIAL -- ATTORNEY-CLIENT COMMUNICATION\n"
            "From: Priya Raghunathan, Associate General Counsel\n"
            "To: Marcus Oyelaran, VP Finance\n"
            "Marcus -- my advice is that the Q3 cutoff treatment is defensible but "
            "not free of risk. If we restate, we should expect the plaintiffs to "
            "argue the original recognition was knowing. Do not circulate this note "
            "outside the finance leadership group."
        ),
    },
    {
        "doc_id": "ARC-000455",
        "expect": "attorney_review",
        "page": (
            "ARCADIA FREIGHT -- HANDWRITTEN NOTE (OCR, PARTIAL)\n"
            "[illegible] ...cutoff?? ask P before we book it -- she said last time "
            "we [illegible] exposure. 3.1 or 3.4, check w/ Dana. don't put in deck"
        ),
    },
    {
        "doc_id": "ARC-000508",
        "expect": "produce",
        "page": (
            "ARCADIA FREIGHT -- AUDIT COMMITTEE MINUTES (EXCERPT)\n"
            "The Committee discussed the Q3 revenue cutoff convention and asked "
            "management to prepare a memo quantifying the effect of recognizing the "
            "$3.1M in Q4 instead. No decision was taken. Next review: 14 November."
        ),
    },
]
