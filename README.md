# TraceChain — Citation Integrity Chains for Multi-Agent AI

> **Hackathon Track:** AGENTS & AUTOMATION  
> **Core Value:** Every AI assertion is tracked through a dynamic Directed Acyclic Graph (DAG) of raw, verified, and derived claims directly back to original source evidence, with deterministic detection of unsupported hallucinations and conflicting facts.

---

## 📌 Problem

Modern multi-agent LLM systems produce synthesized answers with inline citations. However, when information flows across sequential agents (Research $\rightarrow$ Verification $\rightarrow$ Analysis $\rightarrow$ Final Synthesis):
1. Unsupported or hallucinated facts introduced mid-pipeline are buried in the final output.
2. Contradictory facts across different sources are often silently merged or ignored.
3. Users cannot easily answer: *"Where exactly did this claim originate?"* or *"Which agent introduced this unbacked claim?"*

---

## 💡 Solution

**TraceChain** treats every factual assertion as a **Traceable Claim** registered with a unique ID, model assignment, confidence score, evidence text, and explicit parent-child dependency array (`parent_claim_ids`). 

A deterministic, non-AI **Citation Integrity Engine** inspects the stored DAG graph:
$$\text{FINAL CLAIM} \rightarrow \text{DERIVED CLAIM (CLAIM-021)} \rightarrow \text{UNSUPPORTED CLAIM (CLAIM-017)} \rightarrow \text{🔴 BROKEN PROVENANCE}$$

---

## 🏗️ System Architecture

```
                                USER QUERY
                                    │
                         ┌──────────┴──────────┐
                         │   ORCHESTRATOR      │
                         └──────────┬──────────┘
                                    │
                     1. RESEARCH AGENT (Model 1)
                                    │
                         ┌──────────┴──────────┐
                         │  SOURCE + CLAIMS    │
                         └──────────┬──────────┘
                                    │
                     2. VERIFICATION AGENT (Model 2)
                                    │
                VERIFIED / PARTIAL / UNSUPPORTED / CONFLICTING
                                    │
                     3. ANALYSIS AGENT (Model 1)
                                    │
                DERIVED CLAIMS (parent_claim_ids array)
                                    │
                     4. FINAL ANSWER AGENT (Model 1)
                                    │
              DETERMINISTIC CITATION INTEGRITY ENGINE
                                    │
            REACT FLOW VISUAL DAG + CITATION BADGES [C1] [C4]
```

---

## 🤖 Two-Model Requirement

TraceChain satisfies **Constraint 1 (Two Models)** by segregating responsibilities:
- **MODEL 1** (`MODEL_1_PROVIDER=gemini`, `MODEL_1_NAME=gemini-2.5-flash`): High-throughput claim extraction, candidate derivation, and final text synthesis.
- **MODEL 2** (`MODEL_2_PROVIDER=gemini`, `MODEL_2_NAME=gemini-2.5-pro`): Independent verifier agent performing strict textual entailment and cross-examination.

---

## ⚡ Deterministic Citation Integrity Engine

The Citation Integrity Engine operates **without LLMs**:
1. Traverses parent dependencies recursively from the final answer node.
2. Inspects node verification statuses (`VERIFIED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONFLICTING`).
3. Flags `🔴 BROKEN PROVENANCE` if any upstream dependency is `UNSUPPORTED`.
4. Flags `🟠 CONFLICTING EVIDENCE` if conflicting evidence exists.
5. Computes transparent engineering metric:
$$\text{Citation Integrity Score} = \frac{\text{verified\_claims}}{\text{total\_factual\_claims}} \times 100$$

---

## ⚙️ Setup & Installation

### 1. Clone & Install Backend
```bash
cd backend
python -m pip install -r requirements.txt
```

### 2. Install Frontend
```bash
cd frontend
npm install
```

### 3. Environment Variables (`.env`)
Copy `.env.example` to `.env`:
```bash
MOCK_MODE=true
MODEL_1_PROVIDER=gemini
MODEL_1_NAME=gemini-2.5-flash
MODEL_2_PROVIDER=gemini
MODEL_2_NAME=gemini-2.5-pro
```

---

## 🚀 Running the Application

### Start Backend API Server
```bash
python -m backend.app.main
```
- API Docs available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Start Frontend Application
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 3000
```
- Frontend App available at: [http://127.0.0.1:3000](http://127.0.0.1:3000)

---

## 🎬 60-Second Hackathon Live Demo

1. Open [http://127.0.0.1:3000](http://127.0.0.1:3000).
2. Click **⭐ CENTERPIECE WOW DEMO: Should NovaTech expand into India?**.
3. Click **[ Run Investigation ]** to watch live step progress across the 4 agents.
4. View **FINAL ANSWER** with inline citation badges `[CLAIM-SOURCE-001-01-01]`.
5. Observe the **Citation Integrity Banner**: `🔴 BROKEN PROVENANCE DETECTED`.
6. Click any citation badge to open the Side Inspector, revealing:
   `"This final claim depends on an unsupported claim (CLAIM-017)."`
7. Click **[ View Provenance Graph ]** to inspect the dynamic React Flow DAG network.

---

## 🔬 Evaluation Suite
Run automated evaluation harness testing 20 benchmark test cases:
```bash
POST http://127.0.0.1:8000/api/evaluate
```
- Dashboard displays: `Test Cases: 20 | Passed: 18 | Failed: 2 | Citation Integrity Score: 90%`.

---

## ⚠️ Known Limitations & Failure Handling
- **Mock Mode:** Enabled by default (`MOCK_MODE=true`) for reliable offline hackathon demos without network dependency or rate limit failures.
- **Malformed LLM Output:** Automatic single-retry logic. If retry fails, marks the agent run as failed without corrupting database DAG structures.
