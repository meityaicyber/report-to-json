# Document Transcript: 1-report.pdf

*Extracted Pages: 18 | Detected Tables: 16 | Total Chars: 17989*

<!-- PAGE_START: 1 -->
## Page 1

### Table 1.1
| Report Release Date | 16.02.2026 |
| --- | --- |
| Type of Audit | API Assessment Final Report |
| Type of Audit Report | Follow Up Report |
| Period | 29.07.2025 to 15.02.2026 |

### Table 1.2
|  |  |  | Document Preparation |
| --- | --- | --- | --- |
| Document Title | Document Title |  | API Assessment Report |
| Document ID |  |  | NA |
| Document Version |  |  | 1.1 |
| Prepared by |  |  | Dev Rana |
| Reviewed by |  |  | Anubhav |
| Approved by |  |  | Ummed |

### Page Text Content
PTDA Business and Technology Services 
Limited  
  
ICCW API Assessment Report  
    
Report Release Date  
16.02.2026  
Type of Audit  
API Assessment Final Report  
Type of Audit Report  
Follow Up Report  
Period  
29.07.2025 to 15.02.2026  
Document Control  
 
Document Preparation   
Document Title    
API Assessment Report  
Document ID    
NA  
Document Version    
1.1  
Prepared by    
Dev Rana  
Reviewed by    
Anubhav  
Approved by    
Ummed

<!-- PAGE_END: 1 -->
---

<!-- PAGE_START: 2 -->
## Page 2

### Table 2.1
| Released by | Dev |
| --- | --- |
| Release date | 16th February 2026 |

### Table 2.2
|  |  |  | Document Change History |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| Version | Version |  | Date | Remarks / Reason of change | Remarks / Reason of change |  |
| 1.0 |  |  | 05th September 2025 | First Audit Report |  |  |
| 1.1 |  |  | 16th February 2026 | Follow Up Report |  |  |

### Table 2.3
|  |  |  | Document Distribution List |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Name | Name |  | Organization | Designation | Email Id | Email Id |  |
| Amrinder |  |  | PTDA Business and Technology Services Limited | Principal Security Engineer | amrinder@PTDA.com |  |  |

### Page Text Content
Released by    
Dev  
Release date    
16th February 2026  
   
 
Document Change History   
 
Version  
Date  
Remarks / Reason of change  
1.0  
05th September 2025  
First Audit Report  
1.1  
16th February 2026  
Follow Up Report  
  
 
Document Distribution List   
 
Name    
Organization    
Designation    
Email Id    
Amrinder  
PTDA Business and Technology 
Services Limited  
Principal Security Engineer  
amrinder@PTDA.com  
    
  
Contents   
Introduction 
3 
Engagement Scope 
3 
Details of Auditing Team 
4 
Audit Activities and Timelines 
5 
Audit Methodology and Criteria/Standard Referred 
5 
Tools/Software Used 
7 
Executive Summary 
8 
Detailed Observations 
8 
Appendices 
16

<!-- PAGE_END: 2 -->
---

<!-- PAGE_START: 3 -->
## Page 3

<!-- PAGE_END: 3 -->
---

<!-- PAGE_START: 4 -->
## Page 4

### Page Text Content
Introduction  
Project Background:   
VERAS was engaged to perform API Assessment for PTDA Business and Technology Services Limited. This assessment utilized tools and 
techniques analogous to those employed by malicious attackers, focusing on evaluating the security of PTDA Business and Technology Services 
Limited’s API infrastructure in terms of confidentiality, integrity, and availability. The primary objective was to uncover both technical and logical 
vulnerabilities within APIs and to provide strategic recommendations for mitigating risks that could arise from these vulnerabilities.  
Objective:  
Conduct comprehensive API assessment to identify and assess vulnerabilities in API’s, thereby enhancing PTDA Business and Technology Services 
Limited security posture and effectively protecting against external threats.  
Assumptions:   
Based on the scope, only the specified APIs were tested. This report has been produced based on the test that was conducted on a particular date 
tested. Vulnerability details provided in this report are based on the API’s provided for assessment considering test was performed on a production 
or identical to production environment.  
It is recommended that prior to acting on the recommendations, following actions are assumed to be taken by PTDA Business and Technology 
Services Limited:  
• 
Any vulnerabilities identified after the GT assessment date may also not form part of this report.  
• 
GT provided the reference link in the detailed vulnerability section for PTDA Business and Technology Services Limited reference only.   
• 
Any fix to application/system should be tested on UAT or non-production environment prior to any patch deployment on production 
environment.   
• 
Appropriate backup and rollback plan are made prior to implementing the recommendation on the system.  
• 
This report is intended solely for the information and internal use of PTDA Business and Technology Services Limited.  
• 
PTDA Business and Technology Services Limited team is responsible for applying security fixes and maintaining effective security 
controls on application, network, and system.  
Engagement Scope  
Below details of assets covered in the scope are included in this section along with other relevant details.

<!-- PAGE_END: 4 -->
---

<!-- PAGE_START: 5 -->
## Page 5

### Table 5.1
| 1 | ICCW | NA | NA | https://varvta- helmino.fc.in/rest/upi/v2/p2p/pay?fcAppType=andr oid&fcChannel=3& | NA | NA | NA | NA | NA |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | ICCW | NA | NA | https://varvta- helmino.fc.in/rest/upi/v3/mandates/create?fcAppT ype=ios&fcChannel=5& | NA | NA | NA | NA | NA |  |

### Table 5.2
| Sr. No. | Name | Designation | Email Id | Professional Qualifications /Certifications |  | Whether the resource |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  | has been listed in the |
|  |  |  |  |  |  | Snapshot information |
|  |  |  |  |  |  | published on CERT-In’s |
|  |  |  |  |  |  | website (Yes/No) |
| 1 | Ummed | Director | Ummed.Meel@ptda.com | CISA, CEH, CHFI, CSRT, DCL | Yes |  |

### Table 5.3
| Professional |
| --- |
| Qualifications |
| /Certifications |

### Table 5.4
| Sr. |
| --- |
| No. |

### Page Text Content
1  
ICCW  
NA  
NA  
https://varvta- 
helmino.fc.in/rest/upi/v2/p2p/pay?fcAppType=andr 
oid&fcChannel=3&  
NA  
NA  
NA  
NA  
NA  
2  
ICCW  
NA  
NA  
https://varvta- 
helmino.fc.in/rest/upi/v3/mandates/create?fcAppT 
ype=ios&fcChannel=5&  
NA  
NA  
NA  
NA  
NA  
  
Date up to which the list has been updated: 20.08.2025 
Details of Auditing Team  
Sr. 
No.  
Name  
Designation  
Email Id  
Professional  
Qualifications  
/Certifications   
Whether the resource 
has been listed in the  
Snapshot information 
published on CERT-In’s 
website (Yes/No)   
1  
Ummed  
Director  
Ummed.Meel@ptda.com 
CISA, 
CEH, 
CHFI, 
CSRT, DCL   
Yes

<!-- PAGE_END: 5 -->
---

<!-- PAGE_START: 6 -->
## Page 6

### Table 6.1
| 2 | Anubhav | Manager | Anubhav@ptda.com | CEH, eJPT | Yes |
| --- | --- | --- | --- | --- | --- |
| 3 | Dev Rana | Senior Associate | Devvrath@ptda.com | - | No |

### Table 6.2
| Assessment Start Date | Assessment End Date |
| --- | --- |

### Page Text Content
2  
Anubhav  
Manager  
Anubhav@ptda.com 
CEH, eJPT  
Yes  
3  
Dev Rana  
Senior Associate  
Devvrath@ptda.com 
-   
No   
  
  
Audit Activities and Timelines  
Security Assessment timeline as follows:  
Assessment Start Date  
Assessment End Date  
29th July 2025  
16th February 2026  
   
  
  
Audit Methodology and Criteria/Standard Referred  
The API security assessment was conducted as an exercise. This was done to simulate as closely as possible the viewpoint of a completely external 
attacker. The following approach is followed performing the assessment on the API provided for testing.

<!-- PAGE_END: 6 -->
---

<!-- PAGE_START: 7 -->
## Page 7

### Embedded Visual Elements
[IMAGE_PAGE_7_FIG_1] *(Figure 1: page_7_fig_1.jpeg, 1600x900px)*

<!-- PAGE_END: 7 -->
---

<!-- PAGE_START: 8 -->
## Page 8

### Table 8.1
| S. No | Name of Tool/Software used | Version of the Tool/Software used | Open Source/Licensed |
| --- | --- | --- | --- |
| 1 | Postman | 11.80.1 | Licensed |
| 2 | Burp Suite Pro | 2026.1 | Licensed |

### Page Text Content
Tools/Software Used  
S. No  
Name of Tool/Software used  
Version of the Tool/Software used  
Open Source/Licensed  
1  
Postman  
11.80.1  
Licensed  
2  
Burp Suite Pro  
  2026.1  
Licensed

<!-- PAGE_END: 8 -->
---

<!-- PAGE_START: 9 -->
## Page 9

### Table 9.1
| 1 | P2P - https://variin/rest/upi/v2/p2p/p ay?fcAppType=android&fcChan nel=3&fcversion=543 Create & Mandate - https://varvta- qain/rest/upi/v3/mand ates/create?fcAppType=ios&fcC hannel=5&fcversion=134139 | Broken Security Control |  | CWE-284: Improper Access Control CWE-693: Protection Mechanism Failure | High | It is recommended to enforce server-side encryption validation on sensitive fields like encryptBase64String, reject empty or invalid values, and allow only strong algorithms such as AES-256 and RSA across all financial APIs. | NA | Repeat | Closed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | P2P - https://fc/rest/upi/v2/p2p/p ay?fcAppType=android&fcChan nel=3&fcversion=543 | Business logic failure |  | CWE-840: Business Logic Errors | High | It is recommended to implement strict server-side validation to reject negative or invalid transaction amounts, and ensure appropriate error codes (e.g., 400 Bad Request) are returned for malformed inputs. | NA | Repeat | Closed |

### Page Text Content
Executive Summary  
A high-level overview of the key audit findings and vulnerabilities. This section is for senior management to understand business risks.   
 
 
 
 
 
 
 
 
 
1  
P2P - 
https://variin/rest/upi/v2/p2p/p 
ay?fcAppType=android&fcChan 
nel=3&fcversion=543  
Create & Mandate -  
https://varvta- 
qain/rest/upi/v3/mand 
ates/create?fcAppType=ios&fcC 
hannel=5&fcversion=134139  
Broken  
Security  
Control  
CWE-284:  
Improper  
Access  
Control  
CWE-693:  
Protection  
Mechanism  
Failure  
  
High  
It is recommended to enforce 
server-side encryption 
validation on sensitive fields 
like encryptBase64String, 
reject empty or invalid values, 
and allow only strong 
algorithms such as AES-256 
and RSA across all financial 
APIs.  
NA  
Repeat  
Closed  
2  
P2P - https://fc/rest/upi/v2/p2p/p 
ay?fcAppType=android&fcChan 
nel=3&fcversion=543  
Business logic 
failure  
CWE-840:  
Business  
Logic  
Errors  
High  
It is recommended to 
implement strict server-side 
validation to reject negative or 
invalid transaction amounts, 
and ensure appropriate error 
codes (e.g., 400 Bad Request) 
are returned for malformed 
inputs.  
NA  
Repeat  
Closed  
  
  
Detailed Observations   
The details of identified vulnerabilities, impact, severity, and recommendations for the same are explained below.

<!-- PAGE_END: 9 -->
---

<!-- PAGE_START: 10 -->
## Page 10

### Page Text Content
1. Broken Authentication  
Status: Closed  
Severity: High  
Detailed Observation:   
It was observed that APIs accept requests with an empty encryptedBase64String, indicating that encryption validation on sensitive fields is not 
enforced.  
Impact:  
An attacker can exploit this weakness to bypass mandatory encryption requirements and transmit sensitive information such as financial 
mandates, transaction details, and payment data without protection. This not only exposes the application to potential data interception and 
tampering but also significantly increases the risk of fraudulent transactions, account compromise, and regulatory non-compliance (e.g., PCI 
DSS, RBI guidelines).  
CVE/CWE:  
• 
CWE-284: Improper Access Control •  CWE-693: Protection Mechanism Failure  
Affected Asset:   
• 
P2P - https://varvta-helmino.vari.in/rest/upi/v2/p2p/pay?fcAppType=android&fcChannel=3&fcversion=543  
• 
Create 
& 
Mandate 
- 
https://varvta-helmino.vari.in/rest/upi/v3/mandates/create?fcAppType=ios&fcChannel=5&fcversion=134139 
Recommendation:   
It is recommended to enforce server-side encryption validation on sensitive fields like encryptBase64String, reject empty or invalid values, and 
allow only strong algorithms such as AES-256 and RSA across all financial APIs.  
  
  
Reference:   
NA  
New or Repeat observation:   
Repeat

<!-- PAGE_END: 10 -->
---

<!-- PAGE_START: 11 -->
## Page 11

### Embedded Visual Elements
[IMAGE_PAGE_11_FIG_1] *(Figure 1: page_11_fig_1.jpeg, 1041x550px)*

### Page Text Content
Proof of Concept:

<!-- PAGE_END: 11 -->
---

<!-- PAGE_START: 12 -->
## Page 12

### Embedded Visual Elements
[IMAGE_PAGE_12_FIG_1] *(Figure 1: page_12_fig_1.jpeg, 1271x595px)*

<!-- PAGE_END: 12 -->
---

<!-- PAGE_START: 13 -->
## Page 13

### Embedded Visual Elements
[IMAGE_PAGE_13_FIG_1] *(Figure 1: page_13_fig_1.jpeg, 1271x595px)*

### Page Text Content
Revalidation Proof of Concept:

<!-- PAGE_END: 13 -->
---

<!-- PAGE_START: 14 -->
## Page 14

### Embedded Visual Elements
[IMAGE_PAGE_14_FIG_1] *(Figure 1: page_14_fig_1.jpeg, 1702x1131px)*

### Page Text Content
•   
P2P

<!-- PAGE_END: 14 -->
---

<!-- PAGE_START: 15 -->
## Page 15

### Page Text Content
2. Business logic failure  
Status: Closed  
Severity: High  
Detailed Observation:   
It was observed that the API endpoint accepts negative transaction amounts (e.g., -5000) and still returns a 200 OK response with a success 
message, indicating lack of input validation.  
Impact:  
An attacker can exploit this flaw to manipulate transaction logic, potentially leading to financial inconsistencies, bypassing business rules, or 
triggering unintended backend behavior.  
CVE/CWE:  
• 
CWE-840: Business Logic Errors  
Affected Asset:   
• 
P2P - https://varvta-helmino.vari.in/rest/upi/v3/mandates/create?fcAppType=ios&fcChannel=5&fcversion=134139  
Recommendation:   
It is recommended to implement strict server-side validation to reject negative or invalid transaction amounts, and ensure appropriate error 
codes (e.g., 400 Bad Request) are returned for malformed inputs.  
  
Reference:   
NA  
New or Repeat observation:   
Repeat  
  
  
Proof of Concept:

<!-- PAGE_END: 15 -->
---

<!-- PAGE_START: 16 -->
## Page 16

### Embedded Visual Elements
[IMAGE_PAGE_16_FIG_1] *(Figure 1: page_16_fig_1.jpeg, 1273x624px)*

### Page Text Content
Revalidation Proof of Concept:

<!-- PAGE_END: 16 -->
---

<!-- PAGE_START: 17 -->
## Page 17

### Embedded Visual Elements
[IMAGE_PAGE_17_FIG_1] *(Figure 1: page_17_fig_1.jpeg, 1656x766px)*

### Page Text Content
Appendices  
   
Risk Rating Criteria   
  
The risk rating is used to signify the level of risk due to gaps noted during the audit and is based on a qualitative criterion defined as follows:

<!-- PAGE_END: 17 -->
---

<!-- PAGE_START: 18 -->
## Page 18

### Table 18.1
| Severity Rating |  |
| --- | --- |
| Critical | Critical risk vulnerability has a high potential of impacting business operations leading to downtime or disruption and provides an attacker with privileged access, resulting in significant outage. If exploited, it has a direct impact on confidentiality, integrity or availability of organizational information. |
| High | High risk vulnerability indicates that successful exploitation of the vulnerability may result in a significant impact to the confidentiality, integrity, or availability of the information accessible through the application/system or even the backend resources like databases, operating systems, etc. |
| Medium | Medium risk vulnerability reveals information about the application and its underlying infrastructure that can be used by an attacker in conjunction with another vulnerability to gain privileged control of the application or its underlying operating system. |
| Low | Low risk vulnerability that has the potential of revealing the information about the system and may lead to unauthorized access to a system, leading to compromise. Higher work factors would be involved for exploiting this type of vulnerability. |

### Table 18.2
| Risk Assessment Matrix |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Risk Assessment Matrix |  |  |  |  |  |  |  |
| Impact of Vulnerability - Consequence | Major |  | High | Critical |  | Critical |  |
| Risk Severity = Impact x Probability |  |  | Hard | Moderate |  | Easy |  |
|  |  |  | Probability of Risk occurrence |  |  |  |  |

### Table 18.3
| Moderate | Medium | Medium | High |
| --- | --- | --- | --- |
| Minor | Low | Medium | Medium |

### Page Text Content
Severity Rating   
 
Critical   
Critical risk vulnerability has a high potential of impacting business operations leading to downtime or disruption and 
provides an attacker with privileged access, resulting in significant outage. If exploited, it has a direct impact on 
confidentiality, integrity or availability of organizational information.   
High   
High risk vulnerability indicates that successful exploitation of the vulnerability may result in a significant impact to the 
confidentiality, integrity, or availability of the information accessible through the application/system or even the backend 
resources like databases, operating systems, etc.    
Medium   
Medium risk vulnerability reveals information about the application and its underlying infrastructure that can be used by 
an attacker in conjunction with another vulnerability to gain privileged control of the application or its underlying operating 
system.   
Low   
Low risk vulnerability that has the potential of revealing the information about the system and may lead to unauthorized 
access to a system, leading to compromise. Higher work factors would be involved for exploiting this type of vulnerability. 
   
   
To capture the risk rating, the following risk assessment matrix is used considering Impact and probability of risk in terms of ease of exploitation.    
Risk Assessment Matrix    
Impact of Vulnerability - Consequence   
Major   
High   
Critical   
Critical   
Moderate   
Medium   
Medium   
High   
Minor   
Low   
Medium   
Medium   
Risk Severity = Impact x Probability   
Hard   
Moderate   
Easy   
Probability of Risk occurrence    
Please note: Risk rating will also depend on the business criticality of the asset.   
   
   
END OF DOCUMENT

<!-- PAGE_END: 18 -->
---