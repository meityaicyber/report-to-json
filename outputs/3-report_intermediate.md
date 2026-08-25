# Document Transcript: 3-report.pdf

*Extracted Pages: 27 | Detected Tables: 69 | Total Chars: 79417*

<!-- PAGE_START: 1 -->
## Page 1

### Embedded Visual Elements
[IMAGE_PAGE_1_FIG_1] *(Figure 1: page_1_fig_1.png, 1600x900px)*

[IMAGE_PAGE_1_FIG_2] *(Figure 2: page_1_fig_2.png, 1600x900px)*

[IMAGE_PAGE_1_FIG_3] *(Figure 3: page_1_fig_3.png, 1600x900px)*

[IMAGE_PAGE_1_FIG_4] *(Figure 4: page_1_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_1_FIG_5] *(Figure 5: page_1_fig_5.png, 1600x900px)*

[IMAGE_PAGE_1_FIG_6] *(Figure 6: page_1_fig_6.png, 1600x900px)*

[IMAGE_PAGE_1_FIG_7] *(Figure 7: page_1_fig_7.png, 1600x900px)*

[IMAGE_PAGE_1_FIG_8] *(Figure 8: page_1_fig_8.png, 1600x720px)*

[IMAGE_PAGE_1_FIG_9] *(Figure 9: page_1_fig_9.png, 1500x850px)*

[IMAGE_PAGE_1_FIG_10] *(Figure 10: page_1_fig_10.png, 1600x900px)*

[IMAGE_PAGE_1_FIG_11] *(Figure 11: page_1_fig_11.png, 1600x900px)*

### Table 1.1
|  | Prepared by CipherOak Security LLP Application Security Assessment Team |
| --- | --- |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 1
Prepared by
CipherOak Security LLP
Application Security Assessment Team

<!-- PAGE_END: 1 -->
---

<!-- PAGE_START: 2 -->
## Page 2

### Embedded Visual Elements
[IMAGE_PAGE_2_FIG_1] *(Figure 1: page_2_fig_1.png, 1600x900px)*

[IMAGE_PAGE_2_FIG_2] *(Figure 2: page_2_fig_2.png, 1600x900px)*

[IMAGE_PAGE_2_FIG_3] *(Figure 3: page_2_fig_3.png, 1600x900px)*

[IMAGE_PAGE_2_FIG_4] *(Figure 4: page_2_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_2_FIG_5] *(Figure 5: page_2_fig_5.png, 1600x900px)*

[IMAGE_PAGE_2_FIG_6] *(Figure 6: page_2_fig_6.png, 1600x900px)*

[IMAGE_PAGE_2_FIG_7] *(Figure 7: page_2_fig_7.png, 1600x900px)*

[IMAGE_PAGE_2_FIG_8] *(Figure 8: page_2_fig_8.png, 1600x720px)*

[IMAGE_PAGE_2_FIG_9] *(Figure 9: page_2_fig_9.png, 1500x850px)*

[IMAGE_PAGE_2_FIG_10] *(Figure 10: page_2_fig_10.png, 1600x900px)*

[IMAGE_PAGE_2_FIG_11] *(Figure 11: page_2_fig_11.png, 1600x900px)*

### Table 2.1
|  | Document Control & Distribution |
| --- | --- |

### Table 2.2
| Client | Nexora Retail Services Pvt. Ltd. |
| --- | --- |
| Assessed Application | CommerceHub Merchant Portal and supporting API services |
| Assessment Type | Grey-box Web Application Vulnerability Assessment and Penetration Testing |
| Environment | Staging environment with production-equivalent configuration and test data |
| Testing Window | 20-May-2026 to 27-May-2026 |
| Report Date | 05-Jun-2026 |
| Report Classification | Confidential - restricted to Nexora Retail Services and authorized service providers |
| Report ID | COS-NEX-WEB-2026-062 |

### Table 2.3
| Version | Date | Author / Reviewer | Change Summary |
| --- | --- | --- | --- |
| 1.0 | 31-May-2026 | Rohan Shah, Lead Consultant | Initial technical observations consolidated |
| 1.1 | 03-Jun-2026 | Meera Iyer, QA Reviewer | Evidence review and CVSS validation |
| 1.2 | 05-Jun-2026 | CipherOak Security LLP | Final management-ready report issued |
| Distribution note: This document contains sensitive security information. Evidence snippets are redacted where needed and should not be shared outside approved distribution channels. |  |  |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 2
Document Control & Distribution
Client
Nexora Retail Services Pvt. Ltd.
Assessed Application
CommerceHub Merchant Portal and supporting API services
Assessment Type
Grey-box Web Application Vulnerability Assessment and 
Penetration Testing
Environment
Staging environment with production-equivalent configuration and 
test data
Testing Window
20-May-2026 to 27-May-2026
Report Date
05-Jun-2026
Report Classification
Confidential - restricted to Nexora Retail Services and authorized 
service providers
Report ID
COS-NEX-WEB-2026-062
Version
Date
Author / Reviewer
Change Summary
1.0
31-May-2026
Rohan Shah, Lead Consultant
Initial technical observations 
consolidated
1.1
03-Jun-2026
Meera Iyer, QA Reviewer
Evidence review and CVSS 
validation
1.2
05-Jun-2026
CipherOak Security LLP
Final management-ready report 
issued
Distribution note: This document contains sensitive security information. Evidence snippets are redacted where needed and should 
not be shared outside approved distribution channels.

<!-- PAGE_END: 2 -->
---

<!-- PAGE_START: 3 -->
## Page 3

### Embedded Visual Elements
[IMAGE_PAGE_3_FIG_1] *(Figure 1: page_3_fig_1.png, 1600x900px)*

[IMAGE_PAGE_3_FIG_2] *(Figure 2: page_3_fig_2.png, 1600x900px)*

[IMAGE_PAGE_3_FIG_3] *(Figure 3: page_3_fig_3.png, 1600x900px)*

[IMAGE_PAGE_3_FIG_4] *(Figure 4: page_3_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_3_FIG_5] *(Figure 5: page_3_fig_5.png, 1600x900px)*

[IMAGE_PAGE_3_FIG_6] *(Figure 6: page_3_fig_6.png, 1600x900px)*

[IMAGE_PAGE_3_FIG_7] *(Figure 7: page_3_fig_7.png, 1600x900px)*

[IMAGE_PAGE_3_FIG_8] *(Figure 8: page_3_fig_8.png, 1600x720px)*

[IMAGE_PAGE_3_FIG_9] *(Figure 9: page_3_fig_9.png, 1500x850px)*

[IMAGE_PAGE_3_FIG_10] *(Figure 10: page_3_fig_10.png, 1600x900px)*

[IMAGE_PAGE_3_FIG_11] *(Figure 11: page_3_fig_11.png, 1600x900px)*

### Table 3.1
|  | Report Navigator |
| --- | --- |

### Table 3.2
| 1 | Executive Summary and Risk Dashboard |
| --- | --- |
| 2 | Introduction, Objectives, Assumptions and Limitations |
| 3 | Engagement Scope, Testing Credentials and Exclusions |
| 4 | Sampling Criteria, Audit Team and Timeline |
| 5 | Audit Methodology, Criteria and Tools Used |
| 6 | Summary of Detailed Observations |
| 7 | Detailed Vulnerability Observations and Proofs of Concept |
| 8 | Remediation Roadmap and References |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 3
Report Navigator
1
Executive Summary and Risk Dashboard
2
Introduction, Objectives, Assumptions and Limitations
3
Engagement Scope, Testing Credentials and Exclusions
4
Sampling Criteria, Audit Team and Timeline
5
Audit Methodology, Criteria and Tools Used
6
Summary of Detailed Observations
7
Detailed Vulnerability Observations and Proofs of 
Concept
8
Remediation Roadmap and References
The report layout uses dashboard-style summaries for management readers and observation cards for remediation teams. Each finding 
contains preconditions, reproducible evidence, business impact, root cause, remediation guidance and validation checks.

<!-- PAGE_END: 3 -->
---

<!-- PAGE_START: 4 -->
## Page 4

### Embedded Visual Elements
[IMAGE_PAGE_4_FIG_1] *(Figure 1: page_4_fig_1.png, 1600x900px)*

[IMAGE_PAGE_4_FIG_2] *(Figure 2: page_4_fig_2.png, 1600x900px)*

[IMAGE_PAGE_4_FIG_3] *(Figure 3: page_4_fig_3.png, 1600x900px)*

[IMAGE_PAGE_4_FIG_4] *(Figure 4: page_4_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_4_FIG_5] *(Figure 5: page_4_fig_5.png, 1600x900px)*

[IMAGE_PAGE_4_FIG_6] *(Figure 6: page_4_fig_6.png, 1600x900px)*

[IMAGE_PAGE_4_FIG_7] *(Figure 7: page_4_fig_7.png, 1600x900px)*

[IMAGE_PAGE_4_FIG_8] *(Figure 8: page_4_fig_8.png, 1600x720px)*

[IMAGE_PAGE_4_FIG_9] *(Figure 9: page_4_fig_9.png, 1500x850px)*

[IMAGE_PAGE_4_FIG_10] *(Figure 10: page_4_fig_10.png, 1600x900px)*

[IMAGE_PAGE_4_FIG_11] *(Figure 11: page_4_fig_11.png, 1600x900px)*

### Table 4.1
|  | 1. Executive Summary |
| --- | --- |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 4
1. Executive Summary
CipherOak Security LLP performed a grey-box VAPT of Nexora Retail Services' CommerceHub Merchant Portal, covering the staging 
web application, API layer and related file delivery paths. The assessment identified 8 validated vulnerabilities, including 2 Critical and 5 
High severity issues that should be remediated before the next production promotion.
The highest-risk findings are a time-based SQL injection in the order search API and unrestricted OTP attempts in the password reset 
workflow. Both issues present realistic paths to unauthorized data access or account takeover in the tested environment. Several 
browser-side and configuration weaknesses can also be chained with authenticated sessions, especially the CORS origin reflection and 
stored cross-site scripting findings.
Management conclusion: CommerceHub demonstrates functional security controls in several areas, including TLS enforcement at 
the edge and role-based UI restrictions. However, server-side authorization, input handling and account recovery controls require 
immediate hardening. Remediation should prioritize Critical findings within 7 calendar days and High findings within 15 calendar days.

<!-- PAGE_END: 4 -->
---

<!-- PAGE_START: 5 -->
## Page 5

### Embedded Visual Elements
[IMAGE_PAGE_5_FIG_1] *(Figure 1: page_5_fig_1.png, 1600x900px)*

[IMAGE_PAGE_5_FIG_2] *(Figure 2: page_5_fig_2.png, 1600x900px)*

[IMAGE_PAGE_5_FIG_3] *(Figure 3: page_5_fig_3.png, 1600x900px)*

[IMAGE_PAGE_5_FIG_4] *(Figure 4: page_5_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_5_FIG_5] *(Figure 5: page_5_fig_5.png, 1600x900px)*

[IMAGE_PAGE_5_FIG_6] *(Figure 6: page_5_fig_6.png, 1600x900px)*

[IMAGE_PAGE_5_FIG_7] *(Figure 7: page_5_fig_7.png, 1600x900px)*

[IMAGE_PAGE_5_FIG_8] *(Figure 8: page_5_fig_8.png, 1600x720px)*

[IMAGE_PAGE_5_FIG_9] *(Figure 9: page_5_fig_9.png, 1500x850px)*

[IMAGE_PAGE_5_FIG_10] *(Figure 10: page_5_fig_10.png, 1600x900px)*

[IMAGE_PAGE_5_FIG_11] *(Figure 11: page_5_fig_11.png, 1600x900px)*

### Table 5.1
|  | 2. Introduction, Objective, Limitations and Assumptions |
| --- | --- |

### Table 5.2
| Assumption / Constraint | Description |
| --- | --- |
| Time-boxed testing | The assessment was conducted within an agreed testing window; results represent security posture during that period. |
| Staging equivalence | Nexora confirmed that staging uses production-equivalent code paths, middleware and security controls, with test data. |
| Data handling | Evidence was captured using dedicated test tenants and redacted where sensitive identifiers or secrets appeared. |
| Control validation | Findings were validated manually; automated scanner output was not accepted as evidence without manual confirmation. |
| No service disruption | Denial-of-service, destructive database writes and resource-exhaustion techniques were not performed. |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 5
2. Introduction, Objective, Limitations and Assumptions
Introduction
CommerceHub Merchant Portal is a web-based portal used by merchant partners to manage orders, invoices, refunds, profile settings, 
documents and support requests. The assessment focused on validating whether the application and supporting APIs resist common 
web application attack paths under authenticated and unauthenticated test conditions.
Objective
The objective was to identify exploitable vulnerabilities, validate business impact using controlled proof-of-concept activity, map findings 
to recognized web security standards, and provide remediation guidance that can be verified during retesting.
Limitations / Assumptions
Assumption / Constraint
Description
Time-boxed testing
The assessment was conducted within an agreed testing window; results 
represent security posture during that period.
Staging equivalence
Nexora confirmed that staging uses production-equivalent code paths, 
middleware and security controls, with test data.
Data handling
Evidence was captured using dedicated test tenants and redacted where 
sensitive identifiers or secrets appeared.
Control validation
Findings were validated manually; automated scanner output was not 
accepted as evidence without manual confirmation.
No service disruption
Denial-of-service, destructive database writes and resource-exhaustion 
techniques were not performed.

<!-- PAGE_END: 5 -->
---

<!-- PAGE_START: 6 -->
## Page 6

### Embedded Visual Elements
[IMAGE_PAGE_6_FIG_1] *(Figure 1: page_6_fig_1.png, 1600x900px)*

[IMAGE_PAGE_6_FIG_2] *(Figure 2: page_6_fig_2.png, 1600x900px)*

[IMAGE_PAGE_6_FIG_3] *(Figure 3: page_6_fig_3.png, 1600x900px)*

[IMAGE_PAGE_6_FIG_4] *(Figure 4: page_6_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_6_FIG_5] *(Figure 5: page_6_fig_5.png, 1600x900px)*

[IMAGE_PAGE_6_FIG_6] *(Figure 6: page_6_fig_6.png, 1600x900px)*

[IMAGE_PAGE_6_FIG_7] *(Figure 7: page_6_fig_7.png, 1600x900px)*

[IMAGE_PAGE_6_FIG_8] *(Figure 8: page_6_fig_8.png, 1600x720px)*

[IMAGE_PAGE_6_FIG_9] *(Figure 9: page_6_fig_9.png, 1500x850px)*

[IMAGE_PAGE_6_FIG_10] *(Figure 10: page_6_fig_10.png, 1600x900px)*

[IMAGE_PAGE_6_FIG_11] *(Figure 11: page_6_fig_11.png, 1600x900px)*

### Table 6.1
|  | 3. Engagement Scope, Testing Credentials and Deviations |
| --- | --- |

### Table 6.2
| Asset | URL / Identifier | In-Scope Functions |
| --- | --- | --- |
| Web Portal | https://merchant-stage.nexora-retail.example | Merchant dashboard, order search, invoices, refunds, support ticketing, document upload |
| API Gateway | https://api-stage.nexora-retail.example | REST APIs used by portal, mobile browser flows and support console |
| Asset Delivery | https://assets-stage.nexora-retail.example | Uploaded merchant documents and static content delivery |
| Identity Provider | https://auth-stage.nexora-retail.example | Login, MFA, password reset and token issuance flows |

### Table 6.3
| Role | Username | Authentication | Purpose |
| --- | --- | --- | --- |
| Merchant Admin | qa.merchant.admin@nexora.local | MFA enabled | Orders, refunds, document upload, profile management |
| Merchant Operator | qa.merchant.operator@nexora.local | MFA enabled | Orders, invoices and support tickets |
| Vendor Viewer | qa.vendor.viewer@nexora.local | MFA enabled | Read-only merchant records for tenant NTX-MER-021 |
| Support Agent | qa.support.agent@nexora.local | MFA enabled | Back-office support ticket review |
| Credential handling: Passwords, recovery seeds and MFA backup codes were provided through Nexora's approved secure channel and are not stored in this report. |  |  |  |

### Table 6.4
| Category | Details |
| --- | --- |
| Excluded | Production environment, payment gateway settlement rails, third-party logistics APIs, mobile native applications and social engineering. |
| Added | CORS behavior, asset domain content handling and password reset OTP behavior were added after initial reconnaissance indicated elevated risk. |
| Deviation | Automated request-rate testing was capped to agreed thresholds and executed only against designated test accounts. |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 6
3. Engagement Scope, Testing Credentials and Deviations
Engagement Scope
Asset
URL / Identifier
In-Scope Functions
Web Portal
https://merchant-stage.nexora-retail.example
Merchant dashboard, order search, invoices, 
refunds, support ticketing, document upload
API Gateway
https://api-stage.nexora-retail.example
REST APIs used by portal, mobile browser flows 
and support console
Asset Delivery
https://assets-stage.nexora-retail.example
Uploaded merchant documents and static 
content delivery
Identity Provider
https://auth-stage.nexora-retail.example
Login, MFA, password reset and token issuance 
flows
Testing Credentials
Role
Username
Authentication
Purpose
Merchant Admin
qa.merchant.admin@nexora.local
MFA enabled
Orders, refunds, document upload, 
profile management
Merchant Operator
qa.merchant.operator@nexora.local
MFA enabled
Orders, invoices and support tickets
Vendor Viewer
qa.vendor.viewer@nexora.local
MFA enabled
Read-only merchant records for 
tenant NTX-MER-021
Support Agent
qa.support.agent@nexora.local
MFA enabled
Back-office support ticket review
Credential handling: Passwords, recovery seeds and MFA backup codes were provided through Nexora's approved secure channel 
and are not stored in this report.
Exclusions / Additions / Deviations
Category
Details
Excluded
Production environment, payment gateway settlement rails, third-party 
logistics APIs, mobile native applications and social engineering.
Added
CORS behavior, asset domain content handling and password reset OTP 
behavior were added after initial reconnaissance indicated elevated risk.
Deviation
Automated request-rate testing was capped to agreed thresholds and 
executed only against designated test accounts.

<!-- PAGE_END: 6 -->
---

<!-- PAGE_START: 7 -->
## Page 7

### Embedded Visual Elements
[IMAGE_PAGE_7_FIG_1] *(Figure 1: page_7_fig_1.png, 1600x900px)*

[IMAGE_PAGE_7_FIG_2] *(Figure 2: page_7_fig_2.png, 1600x900px)*

[IMAGE_PAGE_7_FIG_3] *(Figure 3: page_7_fig_3.png, 1600x900px)*

[IMAGE_PAGE_7_FIG_4] *(Figure 4: page_7_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_7_FIG_5] *(Figure 5: page_7_fig_5.png, 1600x900px)*

[IMAGE_PAGE_7_FIG_6] *(Figure 6: page_7_fig_6.png, 1600x900px)*

[IMAGE_PAGE_7_FIG_7] *(Figure 7: page_7_fig_7.png, 1600x900px)*

[IMAGE_PAGE_7_FIG_8] *(Figure 8: page_7_fig_8.png, 1600x720px)*

[IMAGE_PAGE_7_FIG_9] *(Figure 9: page_7_fig_9.png, 1500x850px)*

[IMAGE_PAGE_7_FIG_10] *(Figure 10: page_7_fig_10.png, 1600x900px)*

[IMAGE_PAGE_7_FIG_11] *(Figure 11: page_7_fig_11.png, 1600x900px)*

### Table 7.1
|  | 4. Sampling Criteria, Audit Team and Timelines |
| --- | --- |

### Table 7.2
| Sample Area | Selection Rationale |
| --- | --- |
| Authorization | Tenant ID, invoice ID, refund ID, support ticket ID and admin function access checks across four roles. |
| Input handling | Search, filters, ticket comments, upload metadata, JSON bodies and query parameters. |
| Authentication | Login, MFA, password reset, session termination and token validation paths. |
| Data exposure | Profile, invoice, order, debug, document and support APIs. |
| Browser security | CORS, CSP, active content handling, cookie attributes and cross-origin behavior. |

### Table 7.3
| Name | Role | Responsibilities |
| --- | --- | --- |
| Rohan Shah | Lead Security Consultant | Engagement lead, authorization testing, reporting |
| Meera Iyer | Senior Application Security Analyst | API testing, injection validation, retest criteria |
| Nikhil Rao | Security Engineer | Authentication, session management and tooling |
| Priya S. Menon | Quality Reviewer | Evidence review, CVSS validation and report quality control |

### Table 7.4
| Date / Window | Activity | Outcome |
| --- | --- | --- |
| 20-May-2026 | Kick-off and access validation | Scope, credentials and rules of engagement confirmed |
| 21-May-2026 to 22-May-2026 | Reconnaissance and mapping | Application flows, API inventory, role matrix and test data mapped |
| 23-May-2026 to 26-May-2026 | Manual exploitation and validation | Business logic, auth, injection, browser security and upload controls tested |
| 27-May-2026 | Evidence review | Screenshots, HTTP traces and technical impact confirmed |
| 31-May-2026 to 05-Jun-2026 | Reporting | Risk rating, remediation plan and management summary finalized |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 7
4. Sampling Criteria, Audit Team and Timelines
Sampling Criteria
Test cases were selected using a risk-weighted sampling model. Priority was given to functions processing personal data, financial 
instructions, tenant-separated data, role transitions, file ingestion, state-changing actions, account recovery and unauthenticated 
endpoints exposed at the application edge.
Sample Area
Selection Rationale
Authorization
Tenant ID, invoice ID, refund ID, support ticket ID and admin function 
access checks across four roles.
Input handling
Search, filters, ticket comments, upload metadata, JSON bodies and query 
parameters.
Authentication
Login, MFA, password reset, session termination and token validation 
paths.
Data exposure
Profile, invoice, order, debug, document and support APIs.
Browser security
CORS, CSP, active content handling, cookie attributes and cross-origin 
behavior.
Details of Auditing Team
Name
Role
Responsibilities
Rohan Shah
Lead Security Consultant
Engagement lead, authorization testing, reporting
Meera Iyer
Senior Application Security Analyst
API testing, injection validation, retest criteria
Nikhil Rao
Security Engineer
Authentication, session management and tooling
Priya S. Menon
Quality Reviewer
Evidence review, CVSS validation and report 
quality control
Audit Activities and Timelines
Date / Window
Activity
Outcome
20-May-2026
Kick-off and access validation
Scope, credentials and rules of engagement 
confirmed
21-May-2026 to 22-May-2026
Reconnaissance and mapping
Application flows, API inventory, role matrix and 
test data mapped
23-May-2026 to 26-May-2026
Manual exploitation and validation
Business logic, auth, injection, browser security 
and upload controls tested
27-May-2026
Evidence review
Screenshots, HTTP traces and technical impact 
confirmed
31-May-2026 to 05-Jun-2026
Reporting
Risk rating, remediation plan and management 
summary finalized

<!-- PAGE_END: 7 -->
---

<!-- PAGE_START: 8 -->
## Page 8

### Embedded Visual Elements
[IMAGE_PAGE_8_FIG_1] *(Figure 1: page_8_fig_1.png, 1600x900px)*

[IMAGE_PAGE_8_FIG_2] *(Figure 2: page_8_fig_2.png, 1600x900px)*

[IMAGE_PAGE_8_FIG_3] *(Figure 3: page_8_fig_3.png, 1600x900px)*

[IMAGE_PAGE_8_FIG_4] *(Figure 4: page_8_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_8_FIG_5] *(Figure 5: page_8_fig_5.png, 1600x900px)*

[IMAGE_PAGE_8_FIG_6] *(Figure 6: page_8_fig_6.png, 1600x900px)*

[IMAGE_PAGE_8_FIG_7] *(Figure 7: page_8_fig_7.png, 1600x900px)*

[IMAGE_PAGE_8_FIG_8] *(Figure 8: page_8_fig_8.png, 1600x720px)*

[IMAGE_PAGE_8_FIG_9] *(Figure 9: page_8_fig_9.png, 1500x850px)*

[IMAGE_PAGE_8_FIG_10] *(Figure 10: page_8_fig_10.png, 1600x900px)*

[IMAGE_PAGE_8_FIG_11] *(Figure 11: page_8_fig_11.png, 1600x900px)*

### Table 8.1
|  | 5. Audit Methodology, Criteria and Tools Used |
| --- | --- |

### Table 8.2
| Reference | How it was applied |
| --- | --- |
| OWASP Top 10 2025 | Used for web application risk categorization and management-level mapping. |
| OWASP Web Security Testing Guide | Used as the primary manual testing guide for authentication, authorization, input validation, session management and configuration checks. |
| OWASP ASVS 5.0.0 | Used as the control reference for application security verification and remediation expectations. |
| FIRST CVSS v3.1 | Used for technical severity scoring. Each finding includes a CVSS vector string. |
| Nexora Rules of Engagement | Used to define test accounts, rate limits, prohibited actions and communication process. |

### Table 8.3
| Phase | Activities |
| --- | --- |
| 1. Planning | Scope validation, rules of engagement, credential onboarding, stakeholder contacts and evidence handling process. |
| 2. Discovery | Crawl portal, proxy traffic, enumerate API routes, identify role-specific workflows and capture baseline behavior. |
| 3. Vulnerability Identification | Manual testing supported by targeted scanners, payload variation, authorization matrix testing and workflow abuse testing. |
| 4. Exploit Validation | Controlled PoC execution using test data only, with response evidence, screenshots and business impact analysis. |
| 5. Risk Rating | CVSS v3.1 base score combined with business impact, data sensitivity and exploit preconditions. |
| 6. Reporting | Root cause, remediation guidance, retest criteria, target owners and prioritization. |

### Table 8.4
| Assessment Type | Grey-box web application VAPT with authenticated role-based testing and limited unauthenticated testing. |
| --- | --- |
| Testing Environment | Staging environment, production-equivalent application build, production-equivalent infrastructure policies and synthetic test data. |
| Connectivity | Auditor IP ranges allowlisted by Nexora for staging access. Browser and proxy traffic routed through CipherOak test workstation. |
| Evidence Handling | Screenshots, HTTP requests and response snippets sanitized for secrets, personal data and tenant identifiers. |

### Table 8.5
| Tool | Purpose |
| --- | --- |
| Burp Suite Professional | Proxying, manual request replay, Intruder rate-limit validation and evidence capture |
| OWASP ZAP | Supplementary passive scanning and header review |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 8
5. Audit Methodology, Criteria and Tools Used
Audit Methodology and Criteria / Standards Referred
Reference
How it was applied
OWASP Top 10 2025
Used for web application risk categorization and management-level 
mapping.
OWASP Web Security Testing Guide
Used as the primary manual testing guide for authentication, authorization, 
input validation, session management and configuration checks.
OWASP ASVS 5.0.0
Used as the control reference for application security verification and 
remediation expectations.
FIRST CVSS v3.1
Used for technical severity scoring. Each finding includes a CVSS vector 
string.
Nexora Rules of Engagement
Used to define test accounts, rate limits, prohibited actions and 
communication process.
Approach and Methodology
Phase
Activities
1. Planning
Scope validation, rules of engagement, credential onboarding, stakeholder 
contacts and evidence handling process.
2. Discovery
Crawl portal, proxy traffic, enumerate API routes, identify role-specific 
workflows and capture baseline behavior.
3. Vulnerability Identification
Manual testing supported by targeted scanners, payload variation, 
authorization matrix testing and workflow abuse testing.
4. Exploit Validation
Controlled PoC execution using test data only, with response evidence, 
screenshots and business impact analysis.
5. Risk Rating
CVSS v3.1 base score combined with business impact, data sensitivity and 
exploit preconditions.
6. Reporting
Root cause, remediation guidance, retest criteria, target owners and 
prioritization.
Type of Assessment and Testing Environment
Assessment Type
Grey-box web application VAPT with authenticated role-based 
testing and limited unauthenticated testing.
Testing Environment
Staging environment, production-equivalent application build, 
production-equivalent infrastructure policies and synthetic test 
data.
Connectivity
Auditor IP ranges allowlisted by Nexora for staging access. 
Browser and proxy traffic routed through CipherOak test 
workstation.
Evidence Handling
Screenshots, HTTP requests and response snippets sanitized for 
secrets, personal data and tenant identifiers.
Tools / Software Used
Tool
Purpose
Burp Suite Professional
Proxying, manual request replay, Intruder rate-limit validation and evidence 
capture
OWASP ZAP
Supplementary passive scanning and header review

<!-- PAGE_END: 8 -->
---

<!-- PAGE_START: 9 -->
## Page 9

### Embedded Visual Elements
[IMAGE_PAGE_9_FIG_1] *(Figure 1: page_9_fig_1.png, 1600x900px)*

[IMAGE_PAGE_9_FIG_2] *(Figure 2: page_9_fig_2.png, 1600x900px)*

[IMAGE_PAGE_9_FIG_3] *(Figure 3: page_9_fig_3.png, 1600x900px)*

[IMAGE_PAGE_9_FIG_4] *(Figure 4: page_9_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_9_FIG_5] *(Figure 5: page_9_fig_5.png, 1600x900px)*

[IMAGE_PAGE_9_FIG_6] *(Figure 6: page_9_fig_6.png, 1600x900px)*

[IMAGE_PAGE_9_FIG_7] *(Figure 7: page_9_fig_7.png, 1600x900px)*

[IMAGE_PAGE_9_FIG_8] *(Figure 8: page_9_fig_8.png, 1600x720px)*

[IMAGE_PAGE_9_FIG_9] *(Figure 9: page_9_fig_9.png, 1500x850px)*

[IMAGE_PAGE_9_FIG_10] *(Figure 10: page_9_fig_10.png, 1600x900px)*

[IMAGE_PAGE_9_FIG_11] *(Figure 11: page_9_fig_11.png, 1600x900px)*

### Table 9.1
| Tool | Purpose |
| --- | --- |
| Postman / curl | API request reproduction and authorization matrix checks |
| Browser DevTools | DOM inspection, storage review, CORS verification and console validation |
| Nuclei and custom scripts | Targeted template checks and repeatability validation |
| JWT tooling | Token header/payload inspection and validation checks |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 9
Tool
Purpose
Postman / curl
API request reproduction and authorization matrix checks
Browser DevTools
DOM inspection, storage review, CORS verification and console validation
Nuclei and custom scripts
Targeted template checks and repeatability validation
JWT tooling
Token header/payload inspection and validation checks

<!-- PAGE_END: 9 -->
---

<!-- PAGE_START: 10 -->
## Page 10

### Embedded Visual Elements
[IMAGE_PAGE_10_FIG_1] *(Figure 1: page_10_fig_1.png, 1600x900px)*

[IMAGE_PAGE_10_FIG_2] *(Figure 2: page_10_fig_2.png, 1600x900px)*

[IMAGE_PAGE_10_FIG_3] *(Figure 3: page_10_fig_3.png, 1600x900px)*

[IMAGE_PAGE_10_FIG_4] *(Figure 4: page_10_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_10_FIG_5] *(Figure 5: page_10_fig_5.png, 1600x900px)*

[IMAGE_PAGE_10_FIG_6] *(Figure 6: page_10_fig_6.png, 1600x900px)*

[IMAGE_PAGE_10_FIG_7] *(Figure 7: page_10_fig_7.png, 1600x900px)*

[IMAGE_PAGE_10_FIG_8] *(Figure 8: page_10_fig_8.png, 1600x720px)*

[IMAGE_PAGE_10_FIG_9] *(Figure 9: page_10_fig_9.png, 1500x850px)*

[IMAGE_PAGE_10_FIG_10] *(Figure 10: page_10_fig_10.png, 1600x900px)*

[IMAGE_PAGE_10_FIG_11] *(Figure 11: page_10_fig_11.png, 1600x900px)*

### Table 10.1
|  | 6. Summary of Detailed Observations |
| --- | --- |

### Table 10.2
| ID | Observation | Severity | CVSS | OWASP Mapping | Status |
| --- | --- | --- | --- | --- | --- |
| F-01 | Broken Object Level Authorization in Invoice Retrieval | High | 8.1 | A01: Broken Access Control | Open |
| F-02 | Time-Based SQL Injection in Orders Search API | Critical | 9.9 | A05: Injection | Open |
| F-03 | Password Reset OTP Endpoint Missing Rate Limiting | Critical | 9.1 | A07: Authentication Failures | Open |
| F-04 | Stored Cross-Site Scripting in Support Ticket Comments | High | 8.7 | A05: Injection | Open |
| F-05 | JWT Issuer/Audience Validation Gap Enables Role Confusion | High | 8.1 | A07: Authentication Failures | Open |
| F-06 | CORS Origin Reflection with Credentialed API Access | High | 8.2 | A02: Security Misconfiguration | Open |
| F-07 | Unauthenticated Debug Configuration Endpoint Exposure | High | 7.5 | A02: Security Misconfiguration | Open |
| F-08 | Active Content Upload Served from Trusted Asset Domain | Medium | 6.1 | A08: Software/Data Integrity Failures | Open |

### Table 10.3
| Rating | Remediation Priority |
| --- | --- |
| Critical | Immediate exploitation likely or severe business impact; target remediation within 7 calendar days. |
| High | High likelihood or material impact; target remediation within 15 calendar days. |
| Medium | Moderate exploitability or impact; target remediation within 30 calendar days. |
| Low | Limited impact or requiring unusual preconditions; target remediation in planned hardening cycles. |
| Chaining risk: Stored XSS, permissive CORS and weak authorization controls can amplify each other. Remediation should consider attack chains rather than treating each item as an isolated defect. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 10
6. Summary of Detailed Observations
ID
Observation
Severity
CVSS
OWASP Mapping
Status
F-01
Broken Object Level 
Authorization in Invoice 
Retrieval
High
8.1
A01: Broken Access 
Control
Open
F-02
Time-Based SQL 
Injection in Orders 
Search API
Critical
9.9
A05: Injection
Open
F-03
Password Reset OTP 
Endpoint Missing Rate 
Limiting
Critical
9.1
A07: Authentication 
Failures
Open
F-04
Stored Cross-Site 
Scripting in Support 
Ticket Comments
High
8.7
A05: Injection
Open
F-05
JWT Issuer/Audience 
Validation Gap 
Enables Role 
Confusion
High
8.1
A07: Authentication 
Failures
Open
F-06
CORS Origin 
Reflection with 
Credentialed API 
Access
High
8.2
A02: Security 
Misconfiguration
Open
F-07
Unauthenticated 
Debug Configuration 
Endpoint Exposure
High
7.5
A02: Security 
Misconfiguration
Open
F-08
Active Content Upload 
Served from Trusted 
Asset Domain
Medium
6.1
A08: Software/Data 
Integrity Failures
Open
Risk Rating Key
Rating
Remediation Priority
Critical
Immediate exploitation likely or severe business impact; target remediation 
within 7 calendar days.
High
High likelihood or material impact; target remediation within 15 calendar 
days.
Medium
Moderate exploitability or impact; target remediation within 30 calendar 
days.
Low
Limited impact or requiring unusual preconditions; target remediation in 
planned hardening cycles.
Chaining risk: Stored XSS, permissive CORS and weak authorization controls can amplify each other. Remediation should consider 
attack chains rather than treating each item as an isolated defect.

<!-- PAGE_END: 10 -->
---

<!-- PAGE_START: 11 -->
## Page 11

### Embedded Visual Elements
[IMAGE_PAGE_11_FIG_1] *(Figure 1: page_11_fig_1.png, 1600x900px)*

[IMAGE_PAGE_11_FIG_2] *(Figure 2: page_11_fig_2.png, 1600x900px)*

[IMAGE_PAGE_11_FIG_3] *(Figure 3: page_11_fig_3.png, 1600x900px)*

[IMAGE_PAGE_11_FIG_4] *(Figure 4: page_11_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_11_FIG_5] *(Figure 5: page_11_fig_5.png, 1600x900px)*

[IMAGE_PAGE_11_FIG_6] *(Figure 6: page_11_fig_6.png, 1600x900px)*

[IMAGE_PAGE_11_FIG_7] *(Figure 7: page_11_fig_7.png, 1600x900px)*

[IMAGE_PAGE_11_FIG_8] *(Figure 8: page_11_fig_8.png, 1600x720px)*

[IMAGE_PAGE_11_FIG_9] *(Figure 9: page_11_fig_9.png, 1500x850px)*

[IMAGE_PAGE_11_FIG_10] *(Figure 10: page_11_fig_10.png, 1600x900px)*

[IMAGE_PAGE_11_FIG_11] *(Figure 11: page_11_fig_11.png, 1600x900px)*

### Table 11.1
|  | 7. Detailed Vulnerability Observations and Proofs of Concept |
| --- | --- |

### Table 11.2
| Evidence standard: Each proof of concept was executed against agreed in-scope staging assets using approved test accounts. Request and response excerpts are sanitized but preserve the technical behavior necessary for remediation. |  |  |  |
| --- | --- | --- | --- |
| F-01 | High | CVSS 8.1 | Open |

### Table 11.3
| Affected Component | GET /api/v2/tenants/{tenantId}/invoices/{invoiceId} |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A01 - Broken Access Control |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N |

### Table 11.4
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Authenticate as Vendor Viewer for tenant NTX-MER-021. |
| 2 | Send a legitimate invoice request and capture the request in the proxy. |
| 3 | Replace only the invoiceId value with INV-2026-004918, belonging to NTX- MER-044. |
| 4 | Observe HTTP 200 response containing another tenant's invoice metadata and payout account suffix. |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 11
7. Detailed Vulnerability Observations and Proofs of Concept
Evidence standard: Each proof of concept was executed against agreed in-scope staging assets using approved test accounts. 
Request and response excerpts are sanitized but preserve the technical behavior necessary for remediation.
F-01
High
CVSS 8.1
Open
Broken Object Level Authorization in Invoice Retrieval
Affected Component
GET /api/v2/tenants/{tenantId}/invoices/{invoiceId}
OWASP Mapping
OWASP Top 10 2025 A01 - Broken Access Control
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N
Observation Summary
The invoice retrieval API accepted a valid invoice identifier from a different merchant tenant and returned invoice details even though the 
authenticated user belonged to another tenant. The UI restricted access, but the API did not perform equivalent object-level 
authorization.
Preconditions
Authenticated as qa.vendor.viewer@nexora.local with read-only access to tenant NTX-MER-021. Auditor used invoice identifiers 
discovered through predictable numbering during authorized testing.
Step
Proof-of-Concept Activity
1
Authenticate as Vendor Viewer for tenant NTX-MER-021.
2
Send a legitimate invoice request and capture the request in the proxy.
3
Replace only the invoiceId value with INV-2026-004918, belonging to NTX-
MER-044.
4
Observe HTTP 200 response containing another tenant's invoice metadata 
and payout account suffix.
Evidence F-01 - Sanitized proof-of-concept capture
Business Impact
An attacker with any low-privilege merchant account could enumerate or access invoice records belonging to other merchants, exposing 
payment metadata, invoice totals and customer identifiers. Integrity impact exists where adjacent invoice actions reuse the same 
authorization pattern.

<!-- PAGE_END: 11 -->
---

<!-- PAGE_START: 12 -->
## Page 12

### Embedded Visual Elements
[IMAGE_PAGE_12_FIG_1] *(Figure 1: page_12_fig_1.png, 1600x900px)*

[IMAGE_PAGE_12_FIG_2] *(Figure 2: page_12_fig_2.png, 1600x900px)*

[IMAGE_PAGE_12_FIG_3] *(Figure 3: page_12_fig_3.png, 1600x900px)*

[IMAGE_PAGE_12_FIG_4] *(Figure 4: page_12_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_12_FIG_5] *(Figure 5: page_12_fig_5.png, 1600x900px)*

[IMAGE_PAGE_12_FIG_6] *(Figure 6: page_12_fig_6.png, 1600x900px)*

[IMAGE_PAGE_12_FIG_7] *(Figure 7: page_12_fig_7.png, 1600x900px)*

[IMAGE_PAGE_12_FIG_8] *(Figure 8: page_12_fig_8.png, 1600x720px)*

[IMAGE_PAGE_12_FIG_9] *(Figure 9: page_12_fig_9.png, 1500x850px)*

[IMAGE_PAGE_12_FIG_10] *(Figure 10: page_12_fig_10.png, 1600x900px)*

[IMAGE_PAGE_12_FIG_11] *(Figure 11: page_12_fig_11.png, 1600x900px)*

### Table 12.1
| # | Action |
| --- | --- |
| 1 | Enforce object-level authorization in the service layer for every tenant- scoped resource. |
| 2 | Resolve the authenticated tenant from server-side claims and ignore client- supplied tenant identifiers for authorization decisions. |
| 3 | Use non-sequential object identifiers or add enumeration detection for sensitive resources. |
| 4 | Add negative authorization tests for cross-tenant object access to CI/CD. |
| Retest / Validation Criteria: Retest by replaying cross-tenant invoice IDs under all non-owner roles and verify HTTP 403/404 with no object metadata leakage. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 12
Likely Root Cause
Authorization logic trusts route parameters and UI restrictions instead of validating that the requested object belongs to the authenticated 
user's tenant on every API call.
Recommended Remediation
#
Action
1
Enforce object-level authorization in the service layer for every tenant-
scoped resource.
2
Resolve the authenticated tenant from server-side claims and ignore client-
supplied tenant identifiers for authorization decisions.
3
Use non-sequential object identifiers or add enumeration detection for 
sensitive resources.
4
Add negative authorization tests for cross-tenant object access to CI/CD.
Retest / Validation Criteria: Retest by replaying cross-tenant invoice IDs under all non-owner roles and verify HTTP 403/404 with no 
object metadata leakage.

<!-- PAGE_END: 12 -->
---

<!-- PAGE_START: 13 -->
## Page 13

### Embedded Visual Elements
[IMAGE_PAGE_13_FIG_1] *(Figure 1: page_13_fig_1.png, 1600x900px)*

[IMAGE_PAGE_13_FIG_2] *(Figure 2: page_13_fig_2.png, 1600x900px)*

[IMAGE_PAGE_13_FIG_3] *(Figure 3: page_13_fig_3.png, 1600x900px)*

[IMAGE_PAGE_13_FIG_4] *(Figure 4: page_13_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_13_FIG_5] *(Figure 5: page_13_fig_5.png, 1600x900px)*

[IMAGE_PAGE_13_FIG_6] *(Figure 6: page_13_fig_6.png, 1600x900px)*

[IMAGE_PAGE_13_FIG_7] *(Figure 7: page_13_fig_7.png, 1600x900px)*

[IMAGE_PAGE_13_FIG_8] *(Figure 8: page_13_fig_8.png, 1600x720px)*

[IMAGE_PAGE_13_FIG_9] *(Figure 9: page_13_fig_9.png, 1500x850px)*

[IMAGE_PAGE_13_FIG_10] *(Figure 10: page_13_fig_10.png, 1600x900px)*

[IMAGE_PAGE_13_FIG_11] *(Figure 11: page_13_fig_11.png, 1600x900px)*

### Table 13.1
| F-02 | Critical | CVSS 9.9 | Open |
| --- | --- | --- | --- |

### Table 13.2
| Affected Component | POST /api/v2/orders/search |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A05 - Injection |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H |

### Table 13.3
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Capture a normal order search request and record baseline response time. |
| 2 | Submit a controlled database time-delay payload in the query value. |
| 3 | Repeat the request five times across the testing window to rule out network variance. |
| 4 | Confirm the median delay increased from approximately 312 ms to approximately 5.86 seconds. |

### Table 13.4
| # | Action |
| --- | --- |
| 1 | Replace dynamic SQL concatenation with parameterized statements or vetted ORM query builders. |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 13
F-02
Critical
CVSS 9.9
Open
Time-Based SQL Injection in Orders Search API
Affected Component
POST /api/v2/orders/search
OWASP Mapping
OWASP Top 10 2025 A05 - Injection
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H
Observation Summary
The order search API appears to concatenate the query field into a database statement. Controlled time-delay testing produced 
consistent database-side response delays, confirming injection without needing destructive or data-exfiltration payloads.
Preconditions
Authenticated merchant operator role. No elevated privileges were required beyond normal order search access.
Step
Proof-of-Concept Activity
1
Capture a normal order search request and record baseline response time.
2
Submit a controlled database time-delay payload in the query value.
3
Repeat the request five times across the testing window to rule out network 
variance.
4
Confirm the median delay increased from approximately 312 ms to 
approximately 5.86 seconds.
Evidence F-02 - Sanitized proof-of-concept capture
Business Impact
Successful exploitation could allow attackers to read or alter order data, bypass merchant-level filters, execute expensive database 
operations or pivot into application data stores depending on database permissions.
Likely Root Cause
Dynamic SQL construction is likely used for flexible search filters without parameterized queries or safe query builders.
Recommended Remediation
#
Action
1
Replace dynamic SQL concatenation with parameterized statements or 
vetted ORM query builders.

<!-- PAGE_END: 13 -->
---

<!-- PAGE_START: 14 -->
## Page 14

### Embedded Visual Elements
[IMAGE_PAGE_14_FIG_1] *(Figure 1: page_14_fig_1.png, 1600x900px)*

[IMAGE_PAGE_14_FIG_2] *(Figure 2: page_14_fig_2.png, 1600x900px)*

[IMAGE_PAGE_14_FIG_3] *(Figure 3: page_14_fig_3.png, 1600x900px)*

[IMAGE_PAGE_14_FIG_4] *(Figure 4: page_14_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_14_FIG_5] *(Figure 5: page_14_fig_5.png, 1600x900px)*

[IMAGE_PAGE_14_FIG_6] *(Figure 6: page_14_fig_6.png, 1600x900px)*

[IMAGE_PAGE_14_FIG_7] *(Figure 7: page_14_fig_7.png, 1600x900px)*

[IMAGE_PAGE_14_FIG_8] *(Figure 8: page_14_fig_8.png, 1600x720px)*

[IMAGE_PAGE_14_FIG_9] *(Figure 9: page_14_fig_9.png, 1500x850px)*

[IMAGE_PAGE_14_FIG_10] *(Figure 10: page_14_fig_10.png, 1600x900px)*

[IMAGE_PAGE_14_FIG_11] *(Figure 11: page_14_fig_11.png, 1600x900px)*

### Table 14.1
| # | Action |
| --- | --- |
| 2 | Implement allowlisted search fields and server-side query parsing. |
| 3 | Run database accounts with least privilege and separate read/write permissions. |
| 4 | Add SQL injection unit tests and SAST rules for query construction paths. |
| Retest / Validation Criteria: Confirm time-delay payloads no longer alter response time beyond normal variance and that database logs show prepared statement use for search queries. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 14
#
Action
2
Implement allowlisted search fields and server-side query parsing.
3
Run database accounts with least privilege and separate read/write 
permissions.
4
Add SQL injection unit tests and SAST rules for query construction paths.
Retest / Validation Criteria: Confirm time-delay payloads no longer alter response time beyond normal variance and that database 
logs show prepared statement use for search queries.

<!-- PAGE_END: 14 -->
---

<!-- PAGE_START: 15 -->
## Page 15

### Embedded Visual Elements
[IMAGE_PAGE_15_FIG_1] *(Figure 1: page_15_fig_1.png, 1600x900px)*

[IMAGE_PAGE_15_FIG_2] *(Figure 2: page_15_fig_2.png, 1600x900px)*

[IMAGE_PAGE_15_FIG_3] *(Figure 3: page_15_fig_3.png, 1600x900px)*

[IMAGE_PAGE_15_FIG_4] *(Figure 4: page_15_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_15_FIG_5] *(Figure 5: page_15_fig_5.png, 1600x900px)*

[IMAGE_PAGE_15_FIG_6] *(Figure 6: page_15_fig_6.png, 1600x900px)*

[IMAGE_PAGE_15_FIG_7] *(Figure 7: page_15_fig_7.png, 1600x900px)*

[IMAGE_PAGE_15_FIG_8] *(Figure 8: page_15_fig_8.png, 1600x720px)*

[IMAGE_PAGE_15_FIG_9] *(Figure 9: page_15_fig_9.png, 1500x850px)*

[IMAGE_PAGE_15_FIG_10] *(Figure 10: page_15_fig_10.png, 1600x900px)*

[IMAGE_PAGE_15_FIG_11] *(Figure 11: page_15_fig_11.png, 1600x900px)*

### Table 15.1
| F-03 | Critical | CVSS 9.1 | Open |
| --- | --- | --- | --- |

### Table 15.2
| Affected Component | POST /auth/v1/password-reset/verify-otp |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A07 - Authentication Failures |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N |

### Table 15.3
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Initiate password reset for qa.vendor.operator@nexora.local. |
| 2 | Capture the OTP verification request in the proxy. |
| 3 | Send sequential OTP values under the agreed rate cap using the designated test account. |
| 4 | Observe no account lockout or rate-limit headers and a successful reset_token_issued response for the valid OTP. |

### Table 15.4
| # | Action |
| --- | --- |
| 1 | Add strict per-account and per-IP attempt limits with exponential backoff. |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 15
F-03
Critical
CVSS 9.1
Open
Password Reset OTP Endpoint Missing Rate Limiting
Affected Component
POST /auth/v1/password-reset/verify-otp
OWASP Mapping
OWASP Top 10 2025 A07 - Authentication Failures
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N
Observation Summary
The password reset OTP verification endpoint accepted thousands of consecutive attempts for the authorized test account without 
lockout, throttling, step-up verification or risk challenge. A valid reset token was issued when the correct OTP was reached.
Preconditions
Knowledge of a registered user email and ability to trigger the password reset workflow. No authenticated session was required.
Step
Proof-of-Concept Activity
1
Initiate password reset for qa.vendor.operator@nexora.local.
2
Capture the OTP verification request in the proxy.
3
Send sequential OTP values under the agreed rate cap using the 
designated test account.
4
Observe no account lockout or rate-limit headers and a successful 
reset_token_issued response for the valid OTP.
Evidence F-03 - Sanitized proof-of-concept capture
Business Impact
An attacker could brute force OTPs for targeted accounts, obtain a password reset token and take over merchant or support accounts, 
depending on target role and monitoring effectiveness.
Likely Root Cause
OTP verification lacks per-account, per-IP and per-device attempt tracking. OTP entropy and validity window are not compensated by 
enforcement controls.
Recommended Remediation
#
Action
1
Add strict per-account and per-IP attempt limits with exponential backoff.

<!-- PAGE_END: 15 -->
---

<!-- PAGE_START: 16 -->
## Page 16

### Embedded Visual Elements
[IMAGE_PAGE_16_FIG_1] *(Figure 1: page_16_fig_1.png, 1600x900px)*

[IMAGE_PAGE_16_FIG_2] *(Figure 2: page_16_fig_2.png, 1600x900px)*

[IMAGE_PAGE_16_FIG_3] *(Figure 3: page_16_fig_3.png, 1600x900px)*

[IMAGE_PAGE_16_FIG_4] *(Figure 4: page_16_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_16_FIG_5] *(Figure 5: page_16_fig_5.png, 1600x900px)*

[IMAGE_PAGE_16_FIG_6] *(Figure 6: page_16_fig_6.png, 1600x900px)*

[IMAGE_PAGE_16_FIG_7] *(Figure 7: page_16_fig_7.png, 1600x900px)*

[IMAGE_PAGE_16_FIG_8] *(Figure 8: page_16_fig_8.png, 1600x720px)*

[IMAGE_PAGE_16_FIG_9] *(Figure 9: page_16_fig_9.png, 1500x850px)*

[IMAGE_PAGE_16_FIG_10] *(Figure 10: page_16_fig_10.png, 1600x900px)*

[IMAGE_PAGE_16_FIG_11] *(Figure 11: page_16_fig_11.png, 1600x900px)*

### Table 16.1
| # | Action |
| --- | --- |
| 2 | Invalidate OTP after a small number of failed attempts and require restart of recovery flow. |
| 3 | Add risk-based step-up controls and alerting for repeated recovery attempts. |
| 4 | Log and monitor reset attempt patterns, including distributed attempts across IPs. |
| Retest / Validation Criteria: Retest sequential and distributed OTP attempts and verify lockout, telemetry and alert generation before reset token issuance. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 16
#
Action
2
Invalidate OTP after a small number of failed attempts and require restart 
of recovery flow.
3
Add risk-based step-up controls and alerting for repeated recovery 
attempts.
4
Log and monitor reset attempt patterns, including distributed attempts 
across IPs.
Retest / Validation Criteria: Retest sequential and distributed OTP attempts and verify lockout, telemetry and alert generation before 
reset token issuance.

<!-- PAGE_END: 16 -->
---

<!-- PAGE_START: 17 -->
## Page 17

### Embedded Visual Elements
[IMAGE_PAGE_17_FIG_1] *(Figure 1: page_17_fig_1.png, 1600x900px)*

[IMAGE_PAGE_17_FIG_2] *(Figure 2: page_17_fig_2.png, 1600x900px)*

[IMAGE_PAGE_17_FIG_3] *(Figure 3: page_17_fig_3.png, 1600x900px)*

[IMAGE_PAGE_17_FIG_4] *(Figure 4: page_17_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_17_FIG_5] *(Figure 5: page_17_fig_5.png, 1600x900px)*

[IMAGE_PAGE_17_FIG_6] *(Figure 6: page_17_fig_6.png, 1600x900px)*

[IMAGE_PAGE_17_FIG_7] *(Figure 7: page_17_fig_7.png, 1600x900px)*

[IMAGE_PAGE_17_FIG_8] *(Figure 8: page_17_fig_8.png, 1600x720px)*

[IMAGE_PAGE_17_FIG_9] *(Figure 9: page_17_fig_9.png, 1500x850px)*

[IMAGE_PAGE_17_FIG_10] *(Figure 10: page_17_fig_10.png, 1600x900px)*

[IMAGE_PAGE_17_FIG_11] *(Figure 11: page_17_fig_11.png, 1600x900px)*

### Table 17.1
| F-04 | High | CVSS 8.7 | Open |
| --- | --- | --- | --- |

### Table 17.2
| Affected Component | POST /api/v2/support/tickets/{ticketId}/comments |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A05 - Injection |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:N |

### Table 17.3
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Create a support ticket as Merchant Operator. |
| 2 | Submit a comment containing a benign JavaScript alert payload. |
| 3 | Log in as Support Agent and open the ticket in the back-office portal. |
| 4 | Observe JavaScript execution in the support user's browser context. |

### Table 17.4
| # | Action |
| --- | --- |
| 1 | Apply contextual output encoding for all user-controlled fields. |
| 2 | Sanitize rich-text input with a mature allowlist sanitizer if rich text is |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 17
F-04
High
CVSS 8.7
Open
Stored Cross-Site Scripting in Support Ticket Comments
Affected Component
POST /api/v2/support/tickets/{ticketId}/comments
OWASP Mapping
OWASP Top 10 2025 A05 - Injection
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:N
Observation Summary
HTML submitted by a merchant user in a support ticket comment was stored and later executed in the support agent portal when the 
ticket was opened. The issue affects a privileged back-office workflow.
Preconditions
Authenticated merchant user with permission to create or update support ticket comments. Victim support user must open the affected 
ticket.
Step
Proof-of-Concept Activity
1
Create a support ticket as Merchant Operator.
2
Submit a comment containing a benign JavaScript alert payload.
3
Log in as Support Agent and open the ticket in the back-office portal.
4
Observe JavaScript execution in the support user's browser context.
Evidence F-04 - Sanitized proof-of-concept capture
Business Impact
An attacker could execute arbitrary JavaScript in a support user's session, read sensitive ticket data, perform unauthorized actions 
through the victim's privileges or chain with weak CORS/session controls.
Likely Root Cause
User-generated comment content is rendered as HTML in the support console without contextual output encoding or sanitization. No 
effective Content Security Policy was present in the tested view.
Recommended Remediation
#
Action
1
Apply contextual output encoding for all user-controlled fields.
2
Sanitize rich-text input with a mature allowlist sanitizer if rich text is

<!-- PAGE_END: 17 -->
---

<!-- PAGE_START: 18 -->
## Page 18

### Embedded Visual Elements
[IMAGE_PAGE_18_FIG_1] *(Figure 1: page_18_fig_1.png, 1600x900px)*

[IMAGE_PAGE_18_FIG_2] *(Figure 2: page_18_fig_2.png, 1600x900px)*

[IMAGE_PAGE_18_FIG_3] *(Figure 3: page_18_fig_3.png, 1600x900px)*

[IMAGE_PAGE_18_FIG_4] *(Figure 4: page_18_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_18_FIG_5] *(Figure 5: page_18_fig_5.png, 1600x900px)*

[IMAGE_PAGE_18_FIG_6] *(Figure 6: page_18_fig_6.png, 1600x900px)*

[IMAGE_PAGE_18_FIG_7] *(Figure 7: page_18_fig_7.png, 1600x900px)*

[IMAGE_PAGE_18_FIG_8] *(Figure 8: page_18_fig_8.png, 1600x720px)*

[IMAGE_PAGE_18_FIG_9] *(Figure 9: page_18_fig_9.png, 1500x850px)*

[IMAGE_PAGE_18_FIG_10] *(Figure 10: page_18_fig_10.png, 1600x900px)*

[IMAGE_PAGE_18_FIG_11] *(Figure 11: page_18_fig_11.png, 1600x900px)*

### Table 18.1
| # | Action |
| --- | --- |
|  | required. |
| 3 | Deploy a restrictive Content Security Policy that blocks inline script execution. |
| 4 | Add regression tests for stored XSS in merchant-to-support workflows. |
| Retest / Validation Criteria: Verify stored payloads render as inert text and browser console shows CSP enforcement for inline script attempts. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 18
#
Action
required.
3
Deploy a restrictive Content Security Policy that blocks inline script 
execution.
4
Add regression tests for stored XSS in merchant-to-support workflows.
Retest / Validation Criteria: Verify stored payloads render as inert text and browser console shows CSP enforcement for inline script 
attempts.

<!-- PAGE_END: 18 -->
---

<!-- PAGE_START: 19 -->
## Page 19

### Embedded Visual Elements
[IMAGE_PAGE_19_FIG_1] *(Figure 1: page_19_fig_1.png, 1600x900px)*

[IMAGE_PAGE_19_FIG_2] *(Figure 2: page_19_fig_2.png, 1600x900px)*

[IMAGE_PAGE_19_FIG_3] *(Figure 3: page_19_fig_3.png, 1600x900px)*

[IMAGE_PAGE_19_FIG_4] *(Figure 4: page_19_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_19_FIG_5] *(Figure 5: page_19_fig_5.png, 1600x900px)*

[IMAGE_PAGE_19_FIG_6] *(Figure 6: page_19_fig_6.png, 1600x900px)*

[IMAGE_PAGE_19_FIG_7] *(Figure 7: page_19_fig_7.png, 1600x900px)*

[IMAGE_PAGE_19_FIG_8] *(Figure 8: page_19_fig_8.png, 1600x720px)*

[IMAGE_PAGE_19_FIG_9] *(Figure 9: page_19_fig_9.png, 1500x850px)*

[IMAGE_PAGE_19_FIG_10] *(Figure 10: page_19_fig_10.png, 1600x900px)*

[IMAGE_PAGE_19_FIG_11] *(Figure 11: page_19_fig_11.png, 1600x900px)*

### Table 19.1
| F-05 | High | CVSS 8.1 | Open |
| --- | --- | --- | --- |

### Table 19.2
| Affected Component | API Gateway JWT validation middleware |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A07 - Authentication Failures |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N |

### Table 19.3
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Decode a valid token issued by the staging identity provider for the support audience. |
| 2 | Replay the token against an API endpoint expecting CommerceHub portal audience. |
| 3 | Observe the API accepts the token and evaluates the role claim. |
| 4 | Confirm administrative user metadata is returned for the requested tenant. |

### Table 19.4
| # | Action |
| --- | --- |
| 1 | Enforce exact issuer and audience validation per API service and route |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 19
F-05
High
CVSS 8.1
Open
JWT Issuer/Audience Validation Gap Enables Role Confusion
Affected Component
API Gateway JWT validation middleware
OWASP Mapping
OWASP Top 10 2025 A07 - Authentication Failures
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N
Observation Summary
The API gateway accepted a token issued for a staging support audience when accessing an administrative user endpoint. Authorization 
decisions used role claims without enforcing expected issuer and audience binding for the target API.
Preconditions
Possession of a valid token from another trusted Nexora audience or environment. The test used a sanctioned staging token with 
redacted values.
Step
Proof-of-Concept Activity
1
Decode a valid token issued by the staging identity provider for the support 
audience.
2
Replay the token against an API endpoint expecting CommerceHub portal 
audience.
3
Observe the API accepts the token and evaluates the role claim.
4
Confirm administrative user metadata is returned for the requested tenant.
Evidence F-05 - Sanitized proof-of-concept capture
Business Impact
Role confusion can allow access across applications or environments where tokens share signing trust but differ in intended audience. 
Attackers could bypass intended separation between support, merchant and staging contexts.
Likely Root Cause
JWT validation checks token signature and expiry but does not strictly validate issuer, audience, authorized party and environment-
specific trust boundaries before authorization.
Recommended Remediation
#
Action
1
Enforce exact issuer and audience validation per API service and route

<!-- PAGE_END: 19 -->
---

<!-- PAGE_START: 20 -->
## Page 20

### Embedded Visual Elements
[IMAGE_PAGE_20_FIG_1] *(Figure 1: page_20_fig_1.png, 1600x900px)*

[IMAGE_PAGE_20_FIG_2] *(Figure 2: page_20_fig_2.png, 1600x900px)*

[IMAGE_PAGE_20_FIG_3] *(Figure 3: page_20_fig_3.png, 1600x900px)*

[IMAGE_PAGE_20_FIG_4] *(Figure 4: page_20_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_20_FIG_5] *(Figure 5: page_20_fig_5.png, 1600x900px)*

[IMAGE_PAGE_20_FIG_6] *(Figure 6: page_20_fig_6.png, 1600x900px)*

[IMAGE_PAGE_20_FIG_7] *(Figure 7: page_20_fig_7.png, 1600x900px)*

[IMAGE_PAGE_20_FIG_8] *(Figure 8: page_20_fig_8.png, 1600x720px)*

[IMAGE_PAGE_20_FIG_9] *(Figure 9: page_20_fig_9.png, 1500x850px)*

[IMAGE_PAGE_20_FIG_10] *(Figure 10: page_20_fig_10.png, 1600x900px)*

[IMAGE_PAGE_20_FIG_11] *(Figure 11: page_20_fig_11.png, 1600x900px)*

### Table 20.1
| # | Action |
| --- | --- |
|  | group. |
| 2 | Use separate signing keys or key identifiers per environment and application audience. |
| 3 | Reject tokens containing roles not issued for the target resource server. |
| 4 | Add automated token validation tests for wrong issuer, wrong audience and environment-crossing tokens. |
| Retest / Validation Criteria: Replay tokens from non-target audiences and verify consistent HTTP 401/403 responses before business logic executes. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 20
#
Action
group.
2
Use separate signing keys or key identifiers per environment and 
application audience.
3
Reject tokens containing roles not issued for the target resource server.
4
Add automated token validation tests for wrong issuer, wrong audience 
and environment-crossing tokens.
Retest / Validation Criteria: Replay tokens from non-target audiences and verify consistent HTTP 401/403 responses before 
business logic executes.

<!-- PAGE_END: 20 -->
---

<!-- PAGE_START: 21 -->
## Page 21

### Embedded Visual Elements
[IMAGE_PAGE_21_FIG_1] *(Figure 1: page_21_fig_1.png, 1600x900px)*

[IMAGE_PAGE_21_FIG_2] *(Figure 2: page_21_fig_2.png, 1600x900px)*

[IMAGE_PAGE_21_FIG_3] *(Figure 3: page_21_fig_3.png, 1600x900px)*

[IMAGE_PAGE_21_FIG_4] *(Figure 4: page_21_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_21_FIG_5] *(Figure 5: page_21_fig_5.png, 1600x900px)*

[IMAGE_PAGE_21_FIG_6] *(Figure 6: page_21_fig_6.png, 1600x900px)*

[IMAGE_PAGE_21_FIG_7] *(Figure 7: page_21_fig_7.png, 1600x900px)*

[IMAGE_PAGE_21_FIG_8] *(Figure 8: page_21_fig_8.png, 1600x720px)*

[IMAGE_PAGE_21_FIG_9] *(Figure 9: page_21_fig_9.png, 1500x850px)*

[IMAGE_PAGE_21_FIG_10] *(Figure 10: page_21_fig_10.png, 1600x900px)*

[IMAGE_PAGE_21_FIG_11] *(Figure 11: page_21_fig_11.png, 1600x900px)*

### Table 21.1
| F-06 | High | CVSS 8.2 | Open |
| --- | --- | --- | --- |

### Table 21.2
| Affected Component | API gateway CORS policy |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A02 - Security Misconfiguration |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:L/A:N |

### Table 21.3
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Send an authenticated API request with an untrusted Origin header. |
| 2 | Observe the API reflects the untrusted origin in Access-Control-Allow- Origin. |
| 3 | Confirm Access-Control-Allow-Credentials: true is present. |
| 4 | Validate JSON profile data is returned in the response body. |

### Table 21.4
| # | Action |
| --- | --- |
| 1 | Replace origin reflection with an explicit allowlist of trusted HTTPS origins. |
| 2 | Disable credentialed CORS unless required for a specific trusted web |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 21
F-06
High
CVSS 8.2
Open
CORS Origin Reflection with Credentialed API Access
Affected Component
API gateway CORS policy
OWASP Mapping
OWASP Top 10 2025 A02 - Security Misconfiguration
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:L/A:N
Observation Summary
The API reflected arbitrary Origin values and set Access-Control-Allow-Credentials: true for authenticated endpoints. This permits 
malicious origins to read responses from victims with active sessions under browser enforcement rules.
Preconditions
Victim is authenticated to CommerceHub in the same browser. Attacker controls a website that can induce the victim to visit it.
Step
Proof-of-Concept Activity
1
Send an authenticated API request with an untrusted Origin header.
2
Observe the API reflects the untrusted origin in Access-Control-Allow-
Origin.
3
Confirm Access-Control-Allow-Credentials: true is present.
4
Validate JSON profile data is returned in the response body.
Evidence F-06 - Sanitized proof-of-concept capture
Business Impact
An attacker-controlled website could read sensitive JSON responses from authenticated users, including profile metadata, permissions 
and potentially order or refund information depending on endpoint exposure.
Likely Root Cause
CORS middleware dynamically reflects Origin headers and enables credentialed access without allowlisting trusted origins per 
environment and route.
Recommended Remediation
#
Action
1
Replace origin reflection with an explicit allowlist of trusted HTTPS origins.
2
Disable credentialed CORS unless required for a specific trusted web

<!-- PAGE_END: 21 -->
---

<!-- PAGE_START: 22 -->
## Page 22

### Embedded Visual Elements
[IMAGE_PAGE_22_FIG_1] *(Figure 1: page_22_fig_1.png, 1600x900px)*

[IMAGE_PAGE_22_FIG_2] *(Figure 2: page_22_fig_2.png, 1600x900px)*

[IMAGE_PAGE_22_FIG_3] *(Figure 3: page_22_fig_3.png, 1600x900px)*

[IMAGE_PAGE_22_FIG_4] *(Figure 4: page_22_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_22_FIG_5] *(Figure 5: page_22_fig_5.png, 1600x900px)*

[IMAGE_PAGE_22_FIG_6] *(Figure 6: page_22_fig_6.png, 1600x900px)*

[IMAGE_PAGE_22_FIG_7] *(Figure 7: page_22_fig_7.png, 1600x900px)*

[IMAGE_PAGE_22_FIG_8] *(Figure 8: page_22_fig_8.png, 1600x720px)*

[IMAGE_PAGE_22_FIG_9] *(Figure 9: page_22_fig_9.png, 1500x850px)*

[IMAGE_PAGE_22_FIG_10] *(Figure 10: page_22_fig_10.png, 1600x900px)*

[IMAGE_PAGE_22_FIG_11] *(Figure 11: page_22_fig_11.png, 1600x900px)*

### Table 22.1
| # | Action |
| --- | --- |
|  | client. |
| 3 | Apply route-specific CORS policies and deny CORS by default for sensitive APIs. |
| 4 | Add negative CORS tests for untrusted origins to deployment gates. |
| Retest / Validation Criteria: Requests from untrusted origins should omit Access-Control-Allow-Origin and Access-Control-Allow- Credentials; browser fetch attempts should fail CORS checks. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 22
#
Action
client.
3
Apply route-specific CORS policies and deny CORS by default for sensitive 
APIs.
4
Add negative CORS tests for untrusted origins to deployment gates.
Retest / Validation Criteria: Requests from untrusted origins should omit Access-Control-Allow-Origin and Access-Control-Allow-
Credentials; browser fetch attempts should fail CORS checks.

<!-- PAGE_END: 22 -->
---

<!-- PAGE_START: 23 -->
## Page 23

### Embedded Visual Elements
[IMAGE_PAGE_23_FIG_1] *(Figure 1: page_23_fig_1.png, 1600x900px)*

[IMAGE_PAGE_23_FIG_2] *(Figure 2: page_23_fig_2.png, 1600x900px)*

[IMAGE_PAGE_23_FIG_3] *(Figure 3: page_23_fig_3.png, 1600x900px)*

[IMAGE_PAGE_23_FIG_4] *(Figure 4: page_23_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_23_FIG_5] *(Figure 5: page_23_fig_5.png, 1600x900px)*

[IMAGE_PAGE_23_FIG_6] *(Figure 6: page_23_fig_6.png, 1600x900px)*

[IMAGE_PAGE_23_FIG_7] *(Figure 7: page_23_fig_7.png, 1600x900px)*

[IMAGE_PAGE_23_FIG_8] *(Figure 8: page_23_fig_8.png, 1600x720px)*

[IMAGE_PAGE_23_FIG_9] *(Figure 9: page_23_fig_9.png, 1500x850px)*

[IMAGE_PAGE_23_FIG_10] *(Figure 10: page_23_fig_10.png, 1600x900px)*

[IMAGE_PAGE_23_FIG_11] *(Figure 11: page_23_fig_11.png, 1600x900px)*

### Table 23.1
| F-07 | High | CVSS 7.5 | Open |
| --- | --- | --- | --- |

### Table 23.2
| Affected Component | GET /__debug/config |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A02 - Security Misconfiguration |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N |

### Table 23.3
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Browse directly to /__debug/config on the staging portal host. |
| 2 | Observe HTTP 200 response with JSON configuration values. |
| 3 | Validate that returned values include internal database hostnames and credential-like secrets. |
| 4 | Capture sanitized evidence and cease further access to secret material. |

### Table 23.4
| # | Action |
| --- | --- |
| 1 | Disable debug routes outside local development environments. |
| 2 | Restrict operational endpoints to authenticated administrative networks |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 23
F-07
High
CVSS 7.5
Open
Unauthenticated Debug Configuration Endpoint Exposure
Affected Component
GET /__debug/config
OWASP Mapping
OWASP Top 10 2025 A02 - Security Misconfiguration
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
Observation Summary
A debug configuration endpoint was exposed without authentication and returned application configuration, internal hostnames, feature 
flags and secret material. Sensitive values were redacted in the evidence after validation.
Preconditions
Network access to the staging portal. No authenticated session was required.
Step
Proof-of-Concept Activity
1
Browse directly to /__debug/config on the staging portal host.
2
Observe HTTP 200 response with JSON configuration values.
3
Validate that returned values include internal database hostnames and 
credential-like secrets.
4
Capture sanitized evidence and cease further access to secret material.
Evidence F-07 - Sanitized proof-of-concept capture
Business Impact
Exposed configuration can assist attackers in credential theft, environment mapping, targeted exploitation and lateral movement. If 
secrets are valid in adjacent environments, impact can increase substantially.
Likely Root Cause
Debug endpoints or actuator-style configuration routes are enabled in a web-accessible environment without authentication, network 
restriction or response redaction.
Recommended Remediation
#
Action
1
Disable debug routes outside local development environments.
2
Restrict operational endpoints to authenticated administrative networks

<!-- PAGE_END: 23 -->
---

<!-- PAGE_START: 24 -->
## Page 24

### Embedded Visual Elements
[IMAGE_PAGE_24_FIG_1] *(Figure 1: page_24_fig_1.png, 1600x900px)*

[IMAGE_PAGE_24_FIG_2] *(Figure 2: page_24_fig_2.png, 1600x900px)*

[IMAGE_PAGE_24_FIG_3] *(Figure 3: page_24_fig_3.png, 1600x900px)*

[IMAGE_PAGE_24_FIG_4] *(Figure 4: page_24_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_24_FIG_5] *(Figure 5: page_24_fig_5.png, 1600x900px)*

[IMAGE_PAGE_24_FIG_6] *(Figure 6: page_24_fig_6.png, 1600x900px)*

[IMAGE_PAGE_24_FIG_7] *(Figure 7: page_24_fig_7.png, 1600x900px)*

[IMAGE_PAGE_24_FIG_8] *(Figure 8: page_24_fig_8.png, 1600x720px)*

[IMAGE_PAGE_24_FIG_9] *(Figure 9: page_24_fig_9.png, 1500x850px)*

[IMAGE_PAGE_24_FIG_10] *(Figure 10: page_24_fig_10.png, 1600x900px)*

[IMAGE_PAGE_24_FIG_11] *(Figure 11: page_24_fig_11.png, 1600x900px)*

### Table 24.1
| # | Action |
| --- | --- |
|  | only. |
| 3 | Redact secret values in all diagnostic responses and rotate exposed secrets. |
| 4 | Add deployment checks that fail builds when debug profiles are enabled in shared environments. |
| Retest / Validation Criteria: Confirm /__debug/config returns 404 or 403 externally, secrets are rotated, and debug profile flags are disabled in deployment manifests. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 24
#
Action
only.
3
Redact secret values in all diagnostic responses and rotate exposed 
secrets.
4
Add deployment checks that fail builds when debug profiles are enabled in 
shared environments.
Retest / Validation Criteria: Confirm /__debug/config returns 404 or 403 externally, secrets are rotated, and debug profile flags are 
disabled in deployment manifests.

<!-- PAGE_END: 24 -->
---

<!-- PAGE_START: 25 -->
## Page 25

### Embedded Visual Elements
[IMAGE_PAGE_25_FIG_1] *(Figure 1: page_25_fig_1.png, 1600x900px)*

[IMAGE_PAGE_25_FIG_2] *(Figure 2: page_25_fig_2.png, 1600x900px)*

[IMAGE_PAGE_25_FIG_3] *(Figure 3: page_25_fig_3.png, 1600x900px)*

[IMAGE_PAGE_25_FIG_4] *(Figure 4: page_25_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_25_FIG_5] *(Figure 5: page_25_fig_5.png, 1600x900px)*

[IMAGE_PAGE_25_FIG_6] *(Figure 6: page_25_fig_6.png, 1600x900px)*

[IMAGE_PAGE_25_FIG_7] *(Figure 7: page_25_fig_7.png, 1600x900px)*

[IMAGE_PAGE_25_FIG_8] *(Figure 8: page_25_fig_8.png, 1600x720px)*

[IMAGE_PAGE_25_FIG_9] *(Figure 9: page_25_fig_9.png, 1500x850px)*

[IMAGE_PAGE_25_FIG_10] *(Figure 10: page_25_fig_10.png, 1600x900px)*

[IMAGE_PAGE_25_FIG_11] *(Figure 11: page_25_fig_11.png, 1600x900px)*

### Table 25.1
| F-08 | Medium | CVSS 6.1 | Open |
| --- | --- | --- | --- |

### Table 25.2
| Affected Component | POST /api/v2/documents/upload and assets-stage delivery |
| --- | --- |
| OWASP Mapping | OWASP Top 10 2025 A08 - Software/Data Integrity Failures |
| CVSS Vector | CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N |

### Table 25.3
| Step | Proof-of-Concept Activity |
| --- | --- |
| 1 | Upload a file named invoice-preview.html using the merchant document upload API. |
| 2 | Observe the API returns a public asset URL and preserves contentType text/html. |
| 3 | Request the public URL and confirm Content-Type: text/html is returned. |
| 4 | Confirm X-Content-Type-Options and download disposition protections are not present. |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 25
F-08
Medium
CVSS 6.1
Open
Active Content Upload Served from Trusted Asset Domain
Affected Component
POST /api/v2/documents/upload and assets-stage delivery
OWASP Mapping
OWASP Top 10 2025 A08 - Software/Data Integrity Failures
CVSS Vector
CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N
Observation Summary
The document upload function accepted HTML content and served it from a trusted Nexora asset subdomain as text/html. Users viewing 
the file would execute attacker-supplied script in a domain visually associated with Nexora.
Preconditions
Authenticated merchant user with document upload permissions. Victim must open the public asset URL or receive it through a trusted 
workflow.
Step
Proof-of-Concept Activity
1
Upload a file named invoice-preview.html using the merchant document 
upload API.
2
Observe the API returns a public asset URL and preserves contentType 
text/html.
3
Request the public URL and confirm Content-Type: text/html is returned.
4
Confirm X-Content-Type-Options and download disposition protections are 
not present.
Evidence F-08 - Sanitized proof-of-concept capture
Business Impact
The issue can support phishing, token-adjacent attack chains, browser-based pivoting and brand abuse. If asset domain cookies or 
privileged integrations are later introduced, impact may increase.
Likely Root Cause
Upload validation checks file size and extension inconsistently and the asset delivery layer preserves user-controlled active content 
types.

<!-- PAGE_END: 25 -->
---

<!-- PAGE_START: 26 -->
## Page 26

### Embedded Visual Elements
[IMAGE_PAGE_26_FIG_1] *(Figure 1: page_26_fig_1.png, 1600x900px)*

[IMAGE_PAGE_26_FIG_2] *(Figure 2: page_26_fig_2.png, 1600x900px)*

[IMAGE_PAGE_26_FIG_3] *(Figure 3: page_26_fig_3.png, 1600x900px)*

[IMAGE_PAGE_26_FIG_4] *(Figure 4: page_26_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_26_FIG_5] *(Figure 5: page_26_fig_5.png, 1600x900px)*

[IMAGE_PAGE_26_FIG_6] *(Figure 6: page_26_fig_6.png, 1600x900px)*

[IMAGE_PAGE_26_FIG_7] *(Figure 7: page_26_fig_7.png, 1600x900px)*

[IMAGE_PAGE_26_FIG_8] *(Figure 8: page_26_fig_8.png, 1600x720px)*

[IMAGE_PAGE_26_FIG_9] *(Figure 9: page_26_fig_9.png, 1500x850px)*

[IMAGE_PAGE_26_FIG_10] *(Figure 10: page_26_fig_10.png, 1600x900px)*

[IMAGE_PAGE_26_FIG_11] *(Figure 11: page_26_fig_11.png, 1600x900px)*

### Table 26.1
| # | Action |
| --- | --- |
| 1 | Block active content types such as HTML, SVG with script, JavaScript and XML unless explicitly required. |
| 2 | Serve untrusted uploads from a segregated domain with no application cookies or trust relationship. |
| 3 | Force Content-Disposition: attachment and X-Content-Type-Options: nosniff for untrusted files. |
| 4 | Perform server-side MIME validation and normalize file extensions. |
| Retest / Validation Criteria: Attempt to upload HTML/SVG/JS files and verify rejection or forced safe download from an isolated domain. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 26
Recommended Remediation
#
Action
1
Block active content types such as HTML, SVG with script, JavaScript and 
XML unless explicitly required.
2
Serve untrusted uploads from a segregated domain with no application 
cookies or trust relationship.
3
Force Content-Disposition: attachment and X-Content-Type-Options: 
nosniff for untrusted files.
4
Perform server-side MIME validation and normalize file extensions.
Retest / Validation Criteria: Attempt to upload HTML/SVG/JS files and verify rejection or forced safe download from an isolated 
domain.

<!-- PAGE_END: 26 -->
---

<!-- PAGE_START: 27 -->
## Page 27

### Embedded Visual Elements
[IMAGE_PAGE_27_FIG_1] *(Figure 1: page_27_fig_1.png, 1600x900px)*

[IMAGE_PAGE_27_FIG_2] *(Figure 2: page_27_fig_2.png, 1600x900px)*

[IMAGE_PAGE_27_FIG_3] *(Figure 3: page_27_fig_3.png, 1600x900px)*

[IMAGE_PAGE_27_FIG_4] *(Figure 4: page_27_fig_4.jpeg, 734x196px)*

[IMAGE_PAGE_27_FIG_5] *(Figure 5: page_27_fig_5.png, 1600x900px)*

[IMAGE_PAGE_27_FIG_6] *(Figure 6: page_27_fig_6.png, 1600x900px)*

[IMAGE_PAGE_27_FIG_7] *(Figure 7: page_27_fig_7.png, 1600x900px)*

[IMAGE_PAGE_27_FIG_8] *(Figure 8: page_27_fig_8.png, 1600x720px)*

[IMAGE_PAGE_27_FIG_9] *(Figure 9: page_27_fig_9.png, 1500x850px)*

[IMAGE_PAGE_27_FIG_10] *(Figure 10: page_27_fig_10.png, 1600x900px)*

[IMAGE_PAGE_27_FIG_11] *(Figure 11: page_27_fig_11.png, 1600x900px)*

### Table 27.1
|  | 8. Remediation Roadmap and References |
| --- | --- |

### Table 27.2
| Target Window | Findings | Actions |
| --- | --- | --- |
| 0-7 days | F-02, F-03 | Patch SQL injection path; enforce OTP lockout/rate limits; rotate any secrets exposed through debug endpoint. |
| 8-15 days | F-01, F-04, F-05, F-06, F-07 | Implement server-side authorization checks, output encoding/CSP, strict JWT validation, CORS allowlisting and remove debug endpoints. |
| 16-30 days | F-08 | Harden upload validation and segregate untrusted content delivery. |
| Ongoing | All | Add regression tests, centralized authorization libraries, secure coding gates and security telemetry dashboards. |

### Table 27.3
| Control Area | Retest Expectation |
| --- | --- |
| Authorization | Cross-tenant and cross-role negative tests return 403/404 with no object metadata. |
| Injection | Parameterized queries confirmed; timing and error-based payloads fail safely. |
| Authentication | OTP rate limits, account lockouts and monitoring alerts confirmed under sequential and distributed attempts. |
| Browser security | Stored payloads render inert; CSP blocks inline script; CORS denies untrusted origins. |
| Configuration | Debug endpoints disabled; exposed secrets rotated; deployment checks prevent recurrence. |
| Uploads | Active content rejected or forced as safe download from isolated domain. |

### Table 27.4
| Reference | URL |
| --- | --- |
| OWASP Top Ten Web Application Security Risks | https://owasp.org/www-project-top-ten/ |
| OWASP Web Security Testing Guide | https://owasp.org/www-project-web-security-testing-guide/ |
| OWASP Application Security Verification Standard | https://github.com/OWASP/ASVS |
| FIRST CVSS v3.1 Specification Document | https://www.first.org/cvss/v3.1/specification-document |
| Closure note: Retesting should be performed after code remediation, configuration deployment and secret rotation are complete. Evidence from retesting should be appended to this report or tracked in Nexora's vulnerability management workflow. |  |

### Page Text Content
CONFIDENTIAL | Nexora Retail Services Pvt. Ltd. | Web Application VAPT Report | Page 27
8. Remediation Roadmap and References
Prioritized Remediation Roadmap
Target Window
Findings
Actions
0-7 days
F-02, F-03
Patch SQL injection path; enforce OTP 
lockout/rate limits; rotate any secrets exposed 
through debug endpoint.
8-15 days
F-01, F-04, F-05, F-06, F-07
Implement server-side authorization checks, 
output encoding/CSP, strict JWT validation, 
CORS allowlisting and remove debug endpoints.
16-30 days
F-08
Harden upload validation and segregate 
untrusted content delivery.
Ongoing
All
Add regression tests, centralized authorization 
libraries, secure coding gates and security 
telemetry dashboards.
Retesting Checklist
Control Area
Retest Expectation
Authorization
Cross-tenant and cross-role negative tests return 403/404 with no object 
metadata.
Injection
Parameterized queries confirmed; timing and error-based payloads fail 
safely.
Authentication
OTP rate limits, account lockouts and monitoring alerts confirmed under 
sequential and distributed attempts.
Browser security
Stored payloads render inert; CSP blocks inline script; CORS denies 
untrusted origins.
Configuration
Debug endpoints disabled; exposed secrets rotated; deployment checks 
prevent recurrence.
Uploads
Active content rejected or forced as safe download from isolated domain.
References
Reference
URL
OWASP Top Ten Web Application Security Risks
https://owasp.org/www-project-top-ten/
OWASP Web Security Testing Guide
https://owasp.org/www-project-web-security-testing-guide/
OWASP Application Security Verification Standard
https://github.com/OWASP/ASVS
FIRST CVSS v3.1 Specification Document
https://www.first.org/cvss/v3.1/specification-document
Closure note: Retesting should be performed after code remediation, configuration deployment and secret rotation are complete. 
Evidence from retesting should be appended to this report or tracked in Nexora's vulnerability management workflow.

<!-- PAGE_END: 27 -->
---