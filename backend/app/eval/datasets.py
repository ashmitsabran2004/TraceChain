from typing import List
from backend.app.schemas import EvalTestCase, SourceDocument

def generate_20_eval_test_cases() -> List[EvalTestCase]:
    cases = []
    
    # Test Case 1: Flagship WOW Demo Centerpiece
    cases.append(EvalTestCase(
        id="EVAL-001",
        name="⭐ CENTERPIECE WOW DEMO: NovaTech India Expansion Audit",
        description="Evaluates Broken Provenance (CLAIM-017 Unsupported Market Leader Claim -> CLAIM-021 -> Final Answer) & Conflicting Growth Rates (12% vs 7%).",
        query="Should NovaTech expand into India?",
        documents=[
            SourceDocument(
                source_id="SOURCE-001", id="SOURCE-001",
                title="NovaTech Q2 APAC Market Brief (Source A)",
                url="https://novatech.io/reports/apac-q2-2025",
                publisher="NovaTech Corporate Strategy", published_at="2025-07-15",
                content="NovaTech Q2 2025 APAC market growth reached 12% year-over-year. Market competition in local enterprise AI sectors remains moderate. Customer acquisition costs are declining. Initial regulatory compliance costs average $2.5M annually.",
                author="Strategy Office", date="2025-07-15", doc_type="Internal Report",
                source_type="demo"
            ),
            SourceDocument(
                source_id="SOURCE-002", id="SOURCE-002",
                title="Secondary Industry Analyst Review (Source B)",
                url="https://techpulse.com/analysis/novatech-india",
                publisher="Tech Pulse Analytics", published_at="2025-08-01",
                content="Tech Pulse independent audit estimated NovaTech APAC market growth at 7% in Q2 2025. Unbacked assertion: NovaTech is the market leader in India with 90% market share.",
                author="Tech Pulse Team", date="2025-08-01", doc_type="Analyst Review",
                source_type="demo"
            )
        ],
        expected_verified_claims=10, expected_conflicting=1, expected_unsupported=2
    ))

    # Test Case 2: Clinical Trial Contradiction
    cases.append(EvalTestCase(
        id="EVAL-002",
        name="🏥 Clinical Trial TX-409 Contradiction Audit",
        description="Tests detection of factual contradictions between primary trial results and secondary commentary.",
        query="What were the safety and efficacy outcomes of Clinical Trial TX-409?",
        documents=[
            SourceDocument(
                source_id="doc_med_01", id="doc_med_01",
                title="TX-409 Phase II Clinical Efficacy Report",
                content="The TX-409 Phase II trial evaluated 450 patients. Biomarker levels dropped 14.2%. Adverse events occurred in 4.1% of participants. No severe cardiac events were reported.",
                author="Dr. E. Vance", date="2025-11-10", doc_type="Medical Journal",
                source_type="demo"
            ),
            SourceDocument(
                source_id="doc_med_02", id="doc_med_02",
                title="Secondary Commentary",
                content="Trial notes biomarker reduction reached 14.2%. However, secondary blog mistakenly reported severe cardiac events in 25% of patients.",
                author="Review Board", date="2026-01-15", doc_type="Commentary",
                source_type="demo"
            )
        ],
        expected_verified_claims=3, expected_conflicting=1, expected_unsupported=0
    ))

    # Generate test cases 3 to 20 programmatically for complete benchmark coverage
    domains = [
        ("Financial", "Q3 Earnings Revenue Audit", "Analyze NovaCorp Q3 revenue and operating margin metrics.", "NovaCorp reported revenue of $4.2B with 64.2% gross margin. Operating income reached $890M."),
        ("Legal", "Master Service Agreement Audit", "What are the confidentiality and termination notice periods under the MSA?", "Section 8.1 Confidentiality obligations persist for 5 years. Termination requires 60 days written notice."),
        ("Cybersecurity", "Zero-Trust Vulnerability Audit", "What is the severity of CVE-2025-8891 in cloud infrastructure?", "CVE-2025-8891 CVSS score is 9.8 Critical. Remote code execution patch released on August 4."),
        ("SupplyChain", "Semiconductor Lead Time Analysis", "Assess global wafer fabrication lead times for 3nm nodes.", "3nm wafer lead times expanded to 26 weeks. Production capacity utilization reached 98%."),
        ("Energy", "Renewable Grid Storage Efficiency", "What is the round-trip efficiency of grid-scale LFP batteries?", "LFP battery systems demonstrated 88.5% round-trip efficiency over 1,000 cycles."),
        ("Aerospace", "Composite Fuselage Fatigue Testing", "Review structural stress testing for carbon composite airframes.", "Carbon composite panel sustained 150,000 simulated flight hours without micro-cracking."),
        ("E-Commerce", "Holiday Season Fulfillment Logistics", "Evaluate same-day delivery fulfillment rates across North America.", "Same-day delivery fulfillment reached 94.1% across metropolitan distribution centers."),
        ("Automotive", "EV Solid-State Battery Energy Density", "What is the gravimetric energy density of SS-700 battery cells?", "SS-700 solid-state cell achieved 450 Wh/kg energy density during bench testing.")
    ]

    for idx in range(3, 21):
        domain, title, q, body = domains[(idx - 3) % len(domains)]
        is_failing_case = (idx == 7 or idx == 14)
        cases.append(EvalTestCase(
            id=f"EVAL-{String(idx + 1).padStart(3, '0')}" if False else f"EVAL-{idx:03d}",
            name=f"[{domain}] {title} #{idx}",
            description=f"Automated evaluation benchmark test case for {domain.lower()} citation integrity.",
            query=q,
            documents=[
                SourceDocument(
                    source_id=f"DOC-EVAL-{idx:03d}", id=f"DOC-EVAL-{idx:03d}",
                    title=f"{domain} Benchmark Source #{idx}",
                    content=body + (" Unbacked claim asserting 1000% profit." if is_failing_case else ""),
                    publisher=f"{domain} Analytics", published_at="2025-08-01",
                    source_type="demo"
                )
            ],
            expected_verified_claims=3 if not is_failing_case else 1,
            expected_conflicting=0 if not is_failing_case else 1,
            expected_unsupported=0 if not is_failing_case else 2
        ))

    return cases

EVAL_TEST_CASES = generate_20_eval_test_cases()
