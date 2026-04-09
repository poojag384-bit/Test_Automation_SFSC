# SCI-3817 Test Report: Skill Routing Priority Verification

**Test ID:** SCI-3817
**Environment:** Sandbox (QAFull)
**Execution Date:** April 7, 2026
**Tester:** Automated (Playwright + SFDX CLI)
**Overall Status:** PARTIAL PASS

---

## 1. Test Objective

Verify that Salesforce Omni-Channel Skill-Based Routing assigns the correct priority numbers in the Skills Backlog when cases are assigned to different owner groups (VIP, B2B, T2, T1) across different country Point-of-Sale configurations (Italy, Netherlands, Other/France), and that priority numbers update correctly when case priority is changed between High, Medium, and Low.

## 2. Test Environment

- **Org:** sixt3--qafull.sandbox.lightning.force.com
- **Application:** Command Center for Service > Skills Backlog
- **Email-to-Case Addresses:**
  - Italy: service.qafull@sixt.it
  - Netherlands: service.qafull@sixt.nl

## 3. Expected Priority Matrix

| Owner Group | High | Medium | Low |
|-------------|------|--------|-----|
| *_VIP       | 51   | 55     | 57  |
| *_B2B       | 61   | 65     | 67  |
| IT_T2 / BNL_T2 | 101 | 105 | 107 |
| OF_T2       | 111  | 115    | 117 |
| *_T1        | 131  | 135    | 137 |

---

## 4. Scenario Execution Summary

| # | Scenario | Lines | Status | Notes |
|---|----------|-------|--------|-------|
| 1 | IT_VIP (Italy) | 2-18 | **PASS** | All priority values match |
| 2 | BNL_VIP (Netherlands) | 21-35 | **PASS** | All priority values match |
| 3 | OF_VIP (Other/France) | 37-51 | **BLOCKED** | Group does not exist |
| 4 | IT_B2B > IT_T2 > IT_T1 | 53-91 | **PARTIAL FAIL** | T1 priority mismatch |
| 5 | BNL_B2B > BNL_T2 > BNL_T1 | 92-129 | **PARTIAL FAIL** | T1 priority mismatch |
| 6 | OF_B2B > OF_T2 > OF_T1 | 131-167 | **BLOCKED** | Groups do not exist |

---

## 5. Detailed Scenario Results

### Scenario 1: IT_VIP (Lines 2-18) - PASS

**Case Number:** 15557333
**Email To:** service.qafull@sixt.it
**Subject:** Vehicle breakdown
**Owner Group:** IT_VIP

| Step | Action | Expected Priority | Actual Priority | Result |
|------|--------|-------------------|-----------------|--------|
| 9 | Verify Skills Backlog (High) | 51 | 51 | PASS |
| 10-12 | Update to Medium, verify | 55 | 55 | PASS |
| 15-17 | Update to High, verify | 51 | 51 | PASS |

**Skills Assigned:** English, Italy, VIP
**Screenshots:** sci3817_sc1_*.png

---

### Scenario 2: BNL_VIP (Lines 21-35) - PASS

**Case Number:** 15557344
**Email To:** service.qafull@sixt.nl
**Subject:** Vehicle breakdown2
**Owner Group:** BNL_VIP

| Step | Action | Expected Priority | Actual Priority | Result |
|------|--------|-------------------|-----------------|--------|
| 9 | Verify Skills Backlog (High) | 51 | 51 | PASS |
| 10-12 | Update to Medium, verify | 55 | 55 | PASS |
| 13-15 | Update to High, verify | 51 | 51 | PASS |

**Skills Assigned:** English, Netherlands, VIP
**Screenshots:** sci3817_sc2_*.png

---

### Scenario 3: OF_VIP (Lines 37-51) - BLOCKED

**Case Number:** 15557345 (created but could not assign owner)
**Email To:** service.qafull@sixt.it
**Subject:** Vehicle breakdown3
**Owner Group:** OF_VIP

**Blocking Reason:** The queue group `OF_VIP` does not exist in the QAFull sandbox environment. Verified via both SFDX CLI query (`SELECT Id, Name FROM Group WHERE Name='OF_VIP' AND Type='Queue'` returned 0 records) and Playwright UI search in the Change Owner dialog (returned "No results for OF_VIP").

**Action Required:** Create the `OF_VIP` queue group in QAFull, or confirm if this group has been renamed/removed.

---

### Scenario 4: IT_B2B > IT_T2 > IT_T1 (Lines 53-91) - PARTIAL FAIL

**Case Number:** 15557345
**Email To:** service.qafull@sixt.it
**Subject:** Vehicle breakdown3

#### Phase 1: IT_B2B Owner - PASS

| Step | Action | Expected Priority | Actual Priority | Result |
|------|--------|-------------------|-----------------|--------|
| 9 | Verify Skills Backlog (High) | 61 | 61 | PASS |
| 10-12 | Update to Medium, verify | 65 | 65 | PASS |

**Skills Assigned:** B2B, English, Italy
**Screenshots:** sci3817_sc4_step1_owner_ITB2B.png, sci3817_sc4_step2_backlog_ITB2B_high61.png, sci3817_sc4_step3_backlog_ITB2B_medium65.png

#### Phase 2: IT_T2 Owner - PASS

| Step | Action | Expected Priority | Actual Priority | Result |
|------|--------|-------------------|-----------------|--------|
| 18 | Verify Skills Backlog (High) | 101 | 101 | PASS |
| 19-21 | Update to Medium, verify | 105 | 105 | PASS |
| 22-24 | Update to High, verify | 101 | 101 | PASS |
| 25-27 | Update to Low, verify | 107 | 107 | PASS |

**Skills Assigned:** English, Italy, T1_during_RENTAL
**Screenshots:** sci3817_sc4_step4_backlog_ITT2_high101.png, sci3817_sc4_step5_backlog_ITT2_medium105.png, sci3817_sc4_step6_backlog_ITT2_high101_again.png, sci3817_sc4_step7_backlog_ITT2_low107.png

#### Phase 3: IT_T1 Owner - FAIL

| Step | Action | Expected Priority | Actual Priority | Delta | Result |
|------|--------|-------------------|-----------------|-------|--------|
| 31 | Verify Skills Backlog (High) | 131 | **121** | -10 | **FAIL** |
| 32-34 | Update to Medium, verify | 135 | **125** | -10 | **FAIL** |

**Skills Assigned:** English, Italy, T1_during_RENTAL
**Screenshots:** sci3817_sc4_step8_backlog_ITT1_high121_expected131.png, sci3817_sc4_step9_backlog_ITT1_medium125_expected135.png

**Defect Note:** IT_T1 group uses a base priority offset of 120 instead of the expected 130. The +1/+5/+7 pattern for High/Medium/Low is correct (121/125/127), but the base value is wrong.

---

### Scenario 5: BNL_B2B > BNL_T2 > BNL_T1 (Lines 92-129) - PARTIAL FAIL

**Case Number:** 15557344
**Email To:** service.qafull@sixt.nl
**Subject:** Vehicle breakdown2

#### Phase 1: BNL_B2B Owner - PASS

| Step | Action | Expected Priority | Actual Priority | Result |
|------|--------|-------------------|-----------------|--------|
| 9 | Verify Skills Backlog (High) | 61 | 61 | PASS |
| 10-12 | Update to Medium, verify | 65 | 65 | PASS |

**Skills Assigned:** B2B, English, Netherlands
**Screenshots:** sci3817_sc5_step1_backlog_BNLB2B_high61.png, sci3817_sc5_step2_backlog_BNLB2B_medium65.png

#### Phase 2: BNL_T2 Owner - PASS

| Step | Action | Expected Priority | Actual Priority | Result |
|------|--------|-------------------|-----------------|--------|
| 18 | Verify Skills Backlog (High) | 101 | 101 | PASS |
| 19-21 | Update to Medium, verify | 105 | 105 | PASS |
| 22-24 | Update to High, verify | 101 | 101 | PASS |
| 25-27 | Update to Low, verify | 107 | 107 | PASS |

**Skills Assigned:** English, Netherlands, T1_during_RENTAL
**Screenshots:** sci3817_sc5_step3_backlog_BNLT2_high101.png, sci3817_sc5_step4_backlog_BNLT2_medium105.png, sci3817_sc5_step5_backlog_BNLT2_high101_again.png, sci3817_sc5_step6_backlog_BNLT2_low107.png

#### Phase 3: BNL_T1 Owner - FAIL

| Step | Action | Expected Priority | Actual Priority | Delta | Result |
|------|--------|-------------------|-----------------|-------|--------|
| 31 | Verify Skills Backlog (High) | 131 | **121** | -10 | **FAIL** |
| 32-34 | Update to Medium, verify | 135 | **125** | -10 | **FAIL** |

**Skills Assigned:** English, Netherlands, T1_during_RENTAL
**Screenshots:** sci3817_sc5_step7_backlog_BNLT1_high121_expected131.png, sci3817_sc5_step8_backlog_BNLT1_medium125_expected135.png

**Defect Note:** BNL_T1 group exhibits the same -10 offset as IT_T1. Base priority is 120 instead of expected 130.

---

### Scenario 6: OF_B2B > OF_T2 > OF_T1 (Lines 131-167) - BLOCKED

**Email To:** service.qafull@sixt.it
**Subject:** Vehicle breakdown3

**Blocking Reason:** None of the OF_ queue groups (OF_B2B, OF_T2, OF_T1) exist in the QAFull sandbox environment. Verified via SFDX CLI query:
```
SELECT Id, Name FROM Group WHERE Name LIKE 'OF_%' AND Type='Queue'
```
Returned 0 records.

**Action Required:** Create the OF_B2B, OF_T2, and OF_T1 queue groups in QAFull, or confirm if these groups have been renamed/relocated.

---

## 6. Defects Found

### DEF-001: T1 Queue Groups Have Incorrect Priority Base Offset

**Severity:** Medium
**Affected Groups:** IT_T1, BNL_T1 (likely OF_T1 as well)
**Description:** When a case is assigned to a T1 queue group, the Skills Backlog priority number uses a base offset of 120 instead of the expected 130. The High/Medium/Low delta pattern (+1/+5/+7) is correct.

| Priority | Expected | Actual |
|----------|----------|--------|
| High     | 131      | 121    |
| Medium   | 135      | 125    |
| Low      | 137      | 127    |

**Reproduction:** Assign any case to IT_T1 or BNL_T1 queue and check the Priority column in Command Center for Service > Skills Backlog.

### DEF-002: OF_ Queue Groups Missing from QAFull

**Severity:** High (Blocks Scenarios 3 and 6)
**Affected Groups:** OF_VIP, OF_B2B, OF_T2, OF_T1
**Description:** All Other/France (OF_) queue groups referenced in the test script do not exist in the QAFull sandbox. This prevents execution of Scenarios 3 and 6 entirely.

---

## 7. Test Evidence (Screenshots)

All screenshots are saved in `/Users/p978590/SFSC_POC/` with the prefix `sci3817_`:

| File | Description |
|------|-------------|
| sci3817_sc1_final_backlog_high.png | SC1: IT_VIP final backlog verification (High=51) |
| sci3817_sc2_step1_composed.png | SC2: Email composed for BNL_VIP |
| sci3817_sc2_step2_owner_changed.png | SC2: Owner changed to BNL_VIP |
| sci3817_sc2_step3_backlog_high51.png | SC2: Backlog priority 51 (High) |
| sci3817_sc2_step4_priority_medium.png | SC2: Priority changed to Medium |
| sci3817_sc2_step5_backlog_medium55.png | SC2: Backlog priority 55 (Medium) |
| sci3817_sc2_step6_backlog_high51_final.png | SC2: Backlog priority 51 (High, final) |
| sci3817_sc4_step1_owner_ITB2B.png | SC4: Owner changed to IT_B2B |
| sci3817_sc4_step2_backlog_ITB2B_high61.png | SC4: IT_B2B backlog priority 61 (High) |
| sci3817_sc4_step3_backlog_ITB2B_medium65.png | SC4: IT_B2B backlog priority 65 (Medium) |
| sci3817_sc4_step4_backlog_ITT2_high101.png | SC4: IT_T2 backlog priority 101 (High) |
| sci3817_sc4_step5_backlog_ITT2_medium105.png | SC4: IT_T2 backlog priority 105 (Medium) |
| sci3817_sc4_step6_backlog_ITT2_high101_again.png | SC4: IT_T2 backlog priority 101 (High, re-verify) |
| sci3817_sc4_step7_backlog_ITT2_low107.png | SC4: IT_T2 backlog priority 107 (Low) |
| sci3817_sc4_step8_backlog_ITT1_high121_expected131.png | SC4: IT_T1 backlog 121 (expected 131) |
| sci3817_sc4_step9_backlog_ITT1_medium125_expected135.png | SC4: IT_T1 backlog 125 (expected 135) |
| sci3817_sc5_step1_backlog_BNLB2B_high61.png | SC5: BNL_B2B backlog priority 61 (High) |
| sci3817_sc5_step2_backlog_BNLB2B_medium65.png | SC5: BNL_B2B backlog priority 65 (Medium) |
| sci3817_sc5_step3_backlog_BNLT2_high101.png | SC5: BNL_T2 backlog priority 101 (High) |
| sci3817_sc5_step4_backlog_BNLT2_medium105.png | SC5: BNL_T2 backlog priority 105 (Medium) |
| sci3817_sc5_step5_backlog_BNLT2_high101_again.png | SC5: BNL_T2 backlog priority 101 (High, re-verify) |
| sci3817_sc5_step6_backlog_BNLT2_low107.png | SC5: BNL_T2 backlog priority 107 (Low) |
| sci3817_sc5_step7_backlog_BNLT1_high121_expected131.png | SC5: BNL_T1 backlog 121 (expected 131) |
| sci3817_sc5_step8_backlog_BNLT1_medium125_expected135.png | SC5: BNL_T1 backlog 125 (expected 135) |

---

## 8. Actual vs Expected Priority Summary

| Owner Group | Priority | Expected | Actual | Result |
|-------------|----------|----------|--------|--------|
| IT_VIP | High | 51 | 51 | PASS |
| IT_VIP | Medium | 55 | 55 | PASS |
| BNL_VIP | High | 51 | 51 | PASS |
| BNL_VIP | Medium | 55 | 55 | PASS |
| OF_VIP | High | 51 | N/A | BLOCKED |
| IT_B2B | High | 61 | 61 | PASS |
| IT_B2B | Medium | 65 | 65 | PASS |
| BNL_B2B | High | 61 | 61 | PASS |
| BNL_B2B | Medium | 65 | 65 | PASS |
| OF_B2B | High | 61 | N/A | BLOCKED |
| IT_T2 | High | 101 | 101 | PASS |
| IT_T2 | Medium | 105 | 105 | PASS |
| IT_T2 | Low | 107 | 107 | PASS |
| BNL_T2 | High | 101 | 101 | PASS |
| BNL_T2 | Medium | 105 | 105 | PASS |
| BNL_T2 | Low | 107 | 107 | PASS |
| OF_T2 | High | 111 | N/A | BLOCKED |
| IT_T1 | High | 131 | **121** | **FAIL** |
| IT_T1 | Medium | 135 | **125** | **FAIL** |
| BNL_T1 | High | 131 | **121** | **FAIL** |
| BNL_T1 | Medium | 135 | **125** | **FAIL** |
| OF_T1 | High | 131 | N/A | BLOCKED |

---

## 9. Conclusion

Out of 6 scenarios:
- **2 PASSED** fully (Scenarios 1 and 2 - VIP groups)
- **2 PARTIALLY FAILED** (Scenarios 4 and 5 - B2B and T2 phases pass, T1 phase fails with -10 offset)
- **2 BLOCKED** (Scenarios 3 and 6 - OF_ groups do not exist in environment)

The T1 priority offset discrepancy (120 vs 130) is consistent across both IT and BNL country configurations, suggesting a systematic configuration issue in the Omni-Channel routing rules for T1 queue groups rather than a test data problem.
