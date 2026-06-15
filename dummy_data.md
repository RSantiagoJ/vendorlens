# Dummy Data

## Instructions for Claude Code

These three vendor proposals are **fictional** responses to a generic
2025-2026 Enterprise Learning Management System (LMS) RFP
(issued November 2025, proposals due December 1, 2025).
The RFP details are distilled in backend/data/context_bundle/rfp_criteria_lms.txt.

Vendor names are real LMS companies. All pricing, contract specifics,
and individual proposal details are entirely fictional and invented for
demo purposes. They do not represent actual bids, terms, or statements
made by these companies.

Save vendor files to: backend/data/vendor_proposals/<bundle>/

Expected pipeline outcome:

- Vendor B (Canvas by Instructure) scores highest â€” recommended
- Vendor A (Blackboard / Anthology) has the most HIGH severity risk flags
- Vendor C (D2L Brightspace) falls in the middle

---

## backend/data/dummy_docs/vendor_a_blackboard.txt

VENDOR PROPOSAL â€” Blackboard Learn Ultra (Anthology Inc.)
Submitted to: University Procurement Office
In Response to: Enterprise Learning Management System RFP
Date: November 28, 2025

COMPANY OVERVIEW
Blackboard, now operating as part of Anthology Inc. following its merger with
Instructure's former parent, is one of the longest-established LMS providers in
higher education. Anthology serves over 3,000 institutions in 80 countries.
Headquarters: Boca Raton, FL (US operations). Parent: Anthology Inc., Raleigh, NC.
Employees: 4,000+.

PRICING
Base platform fee: $44 per enrolled FTE student per year
Estimated total Year 1 (60,000 FTE): $2,640,000
Year 2 escalation: 6% applied automatically ($2,798,400)
Year 3 escalation: 6% applied automatically ($2,966,304)
Per-campus onboarding and configuration: $18,000 per campus (first two included)
Implementation and migration: Professional services required, estimated $95,000
(billed separately, not included in base price)
Add-on modules (priced separately, annual):

- Anthology Intelligence (AI-assisted grading and early alerts): $8/FTE/year
- Advanced Analytics and Outcomes Mapping: $5/FTE/year
- Anthology Ally (accessibility auto-remediation): $3/FTE/year
- Proctoring integration (ProctorU): $12/FTE/year
  Payment terms: Net 30, invoiced annually in advance, non-refundable

CONTRACT TERMS
Contract length: 3 years, non-negotiable
Auto-renewal: Automatically renews for successive 1-year terms
Opt-out notice required: 30 days prior to renewal date
Termination for convenience: 180 days written notice required plus
payment of 40% of remaining contract value as termination fee
Termination for cause: 90 days to cure, no refund of prepaid fees
Governing law: State of North Carolina

LIABILITY
Maximum liability: $50,000 (fixed cap regardless of contract value)
Excludes all data loss, consequential damages, and FERPA-related claims
Data breach liability: capped at $25,000 per incident

CORE LMS FUNCTIONALITY
Blackboard Learn Ultra is a modern, rebuilt LMS interface on the Blackboard platform.

Course management:

- Course creation, copying, and archiving for all modalities
- Course templates and cross-listing support
- Batch course creation via CSV import

Assignment and assessment:

- Assignment submission with inline grading
- Rubric-based assessment tools
- Gradebook with calculated columns and weighted grades
- Grade passback to SIS: supported for Banner and Workday; Ellucian and PeopleSoft
  require professional services integration (additional cost, timeline 8-12 weeks)

Collaboration:

- Discussion boards with threading
- Group projects and peer review (limited peer review tooling â€” full review requires
  third-party LTI integration)
- Announcements and messaging with email notifications

Content standards:

- SCORM 1.2 and 2004 supported
- xAPI (Tin Can): supported via third-party LRS integration only
- LTI 1.1 certified; LTI 1.3 in active development, expected GA Q2 2026

Video:

- Kaltura integration available (additional cost, $6/FTE/year)
- Built-in video recording via Blackboard Collaborate (included)
- Automated captioning: available via Kaltura only; not native

Mobile application:

- iOS app: full feature parity on core functions
- Android app: available, some advanced grading features web-only
- Offline access: course content download for offline reading (iOS only)

Learning analytics:

- Instructor-level engagement dashboards included
- At-risk student flagging: available in Anthology Intelligence add-on only
- System-wide analytics: available in Advanced Analytics add-on only

Plagiarism detection:

- Turnitin integration available (Turnitin licensing billed separately)
- SafeAssign (Blackboard native): included in base price

ACCESSIBILITY
VPAT: Available upon request. Last third-party audit: April 2024.
WCAG 2.1 AA: Claimed for core platform. Known gaps: advanced math equation
editor, certain content editor components. Remediation timeline not disclosed.
Section 508: Conformance documentation available upon request.
Caption support: Automated captions available via Kaltura integration only.
Manual caption upload: .srt files supported.
Screen reader testing: JAWS and NVDA tested internally; VoiceOver not documented.
Anthology Ally (auto-remediation for uploaded documents): available as add-on.

SECURITY AND COMPLIANCE
Security certifications: SOC 2 Type I (SOC 2 Type II audit in progress, expected Q3 2026)
ISO 27001: Not currently certified
Data Processing Agreement: Available upon request, not provided as standard
DPA covers: FERPA. Does not explicitly address Massachusetts Ch. 93H or Ch. 66A.
Incident Response plan: Available upon request.
Disaster Recovery: Documentation available after NDA execution.
University data: Anthology uses anonymized usage and engagement data for
product improvement, benchmarking studies, and AI model training. Opt-out
requires written request and is evaluated case-by-case.
Data ownership: University owns raw course content and student records.
Anthology retains rights to aggregated analytics and usage metadata.
Data portability: Course and grade export available in IMS Common Cartridge
and CSV. Export window: 60 days post-termination. Bulk data export via
professional services at additional cost.
Encryption: TLS 1.2 in transit, AES-128 at rest
Penetration testing: Annual, results not shared with customers.

INTELLECTUAL PROPERTY
Platform configurations, course templates, and workflow customizations created
during implementation are considered Anthology proprietary work product.
University retains ownership of raw course content and student data only.

INTEGRATIONS
SSO: SAML 2.0 supported, tested with Shibboleth and Azure AD
SIS: Banner (native), Workday (native), PeopleSoft and Ellucian via middleware
Microsoft Teams: Integration available, requires separate Microsoft licensing
Zoom: Integration available, included in base price
Open API: REST API available; read-only for most endpoints. Write access
requires Anthology partner agreement (additional cost).
LTI 1.3: In development, not yet production-ready (expected Q2 2026)

SERVICE LEVEL AGREEMENT
Uptime target: 99% (allows approximately 87 hours downtime per year)
Scheduled maintenance: Up to 8 hours per month, not counted against uptime
Support response: Best effort. No contractually defined response time SLAs.
No financial penalties for SLA breach.

SUPPORT AND TRAINING
Support hours: Monday-Friday 8am-8pm ET
Contact methods: Support portal and email. Phone support: Premier tier only.
Dedicated customer success manager: Not included; available at $18,000/year
Onboarding: Two recorded webinars and access to Anthology Academy portal included.
Live training: Not included in base price. On-site workshops $4,000/day plus travel.
Faculty training resources: Self-paced video library and knowledge base included.

MIGRATION SERVICES
Migration from existing LMS: Professional services required ($95,000 estimated).
Timeline: 16-20 weeks from contract signing.
Data migrated: Course shells, uploaded content, and gradebook records.
Student activity history and discussion threads: Not migrated.

CUSTOMER REFERENCES
Seven references provided. Five from higher education, two from multi-campus
public university systems. Contact information available upon request.

SANDBOX ENVIRONMENT
Demo environment available for 21 days during procurement only.
Full sandbox for testing post-signing: Not included in standard contract.

SUPPLIER DIVERSITY
Anthology Inc. does not hold supplier diversity certifications.

ADDITIONAL TERMS
Anthology reserves the right to modify platform features, deprecate legacy
tools, and adjust pricing for add-on modules with 60 days written notice.
University agrees not to publicly benchmark pricing against competitors.

---

## backend/data/dummy_docs/vendor_b_canvas.txt

VENDOR PROPOSAL â€” Canvas LMS by Instructure
Submitted to: University Procurement Office
In Response to: Enterprise Learning Management System RFP
Date: November 25, 2025

COMPANY OVERVIEW
Instructure is the developer of Canvas, the most widely adopted cloud-native
LMS in higher education. Instructure serves over 8,000 institutions and
40 million learners worldwide, including more than 1,000 public college and
university systems.
Headquarters: Salt Lake City, UT. Incorporated in the State of Delaware.
Employees: 1,100+.

PRICING
Base platform fee: $38 per enrolled FTE student per year â€” fixed for full contract term
Estimated total (60,000 FTE): $2,280,000 per year, no escalation for 3 years
All campuses and administrative offices included in base price
All core modules included: Canvas LMS, Canvas Studio (video), Canvas Analytics,
Gauge (assessment), New Quizzes, SpeedGrader, Peer Review, ePortfolio
Implementation and migration: Included â€” Instructure Professional Services
Migration: Course content, gradebook history, and discussion archives migrated
No per-campus onboarding fees. No per-user overage fees up to 75,000 active users.
Payment terms: Net 45, invoiced annually. 2% early payment discount available.
Billing by individual campus or unit available at no additional cost.
Optional add-ons (priced separately):

- Proctoring (Proctorio partnership): $6/FTE/year
- Advanced AI Insights (beta): $4/FTE/year

CONTRACT TERMS
Contract length: 3 years with optional 2-year extension at university discretion
Auto-renewal: Does not auto-renew. Requires affirmative renewal by both parties.
Termination for convenience: 60 days written notice, no financial penalty
Termination for cause: Immediate, full pro-rata refund of prepaid fees
Governing law: Commonwealth of Massachusetts

LIABILITY
Maximum liability: $5,000,000 or total fees paid in prior 12 months, whichever
is greater. Covers data loss, service interruption, FERPA violations, direct
damages, and accessibility compliance failures.

CORE LMS FUNCTIONALITY
Canvas is a purpose-built cloud-native LMS designed for higher education.

Course management:

- Course creation, copying, and archiving across all modalities
- Blueprint Courses for system-wide templates and locked content synchronization
- Cross-listing, course merge, and concluded course access
- Bulk course creation and enrollment via SIS integration

Assignment and assessment:

- SpeedGrader with inline annotation and audio/video feedback
- Rubric-based assessment across all assignment types
- New Quizzes: full-featured assessment engine with item banks
- Gradebook: traditional and mastery-based options
- Grade passback to Banner, Workday, PeopleSoft, and Ellucian â€” all certified
  native integrations included, no professional services required

Collaboration:

- Discussion boards with threaded replies, media embedding
- Group projects, collaborative documents, peer review included
- Announcements with email and push notification delivery
- Canvas Inbox: full-featured messaging system
- Real-time collaboration via Microsoft Teams or Zoom (both included)

Content standards:

- SCORM 1.2 and 2004 supported natively
- xAPI (Tin Can) supported natively with internal LRS
- LTI 1.3 certified â€” full certification documentation provided with proposal
- LTI 2.0 supported for legacy tools

Video:

- Canvas Studio: integrated video recording, editing, and in-video quizzing
  Automated captioning included â€” CART-quality captions, no extra charge
- Lecture capture via Kaltura, Panopto, or Echo360 (all LTI 1.3 native)

Mobile application:

- Canvas Student app: iOS and Android, full feature parity
- Canvas Teacher app: iOS and Android, full grading and course management
- Offline access: course content and submissions available offline, syncs on reconnect

Learning analytics:

- Canvas Analytics: course-level engagement, access frequency, grade correlation
- At-risk flagging: Early Alert tool included, configurable thresholds per campus
- System-wide analytics via Impact (formerly Instructure Analytics): included
- SCORM and xAPI learning object completion tracked natively

Plagiarism detection:

- Turnitin integration: LTI 1.3, included setup support, Turnitin license separate
- Unicheck integration: available

ACCESSIBILITY
VPAT: Provided in HTML format with proposal. Third-party audit completed October 2025.
WCAG 2.1 AA: Fully documented. Third-party audit by Deque Systems, October 2025.
Section 508: Full conformance, documentation provided with proposal.
Caption support: Automated captions on all Canvas Studio video â€” included.
.srt file upload: Supported for all video content.
Screen reader testing: NVDA, JAWS, and VoiceOver â€” all tested, results in VPAT.
Known gaps: One LTI third-party tool (advanced equation editor) has a known
keyboard navigation issue. Remediation committed by Q1 2026. Disclosed proactively.
Accessibility roadmap: Provided with proposal. Committed to WCAG 2.2 by Q2 2026.

SECURITY AND COMPLIANCE
SOC 2 Type II: Current certificate provided with proposal (audit completed August 2025)
ISO 27001: Current certificate provided with proposal
FedRAMP Moderate: In process, expected authorization Q4 2026
Data Processing Agreement: Provided as standard with all contracts.
DPA covers: FERPA, GLBA, COPPA, Massachusetts Ch. 93H, Ch. 66A, and GDPR.
Incident Response plan: Full plan provided with proposal. Annual tabletop exercises.
Disaster Recovery: Full documentation provided. RTO 2 hours, RPO 30 minutes.
University retains full and exclusive ownership of all institutional data at all times.
University data is never used for benchmarking, product improvement, AI model
training, or any purpose beyond direct service delivery.
Data encrypted at rest (AES-256) and in transit (TLS 1.3).
Annual third-party penetration testing â€” summary provided with proposal.
Data portability: Full export in IMS Common Cartridge, CSV, and JSON within
5 business days of termination at no charge.

INTELLECTUAL PROPERTY
University retains full ownership of all data, course content, configurations,
workflows, rubrics, and customizations. No rights transfer to Instructure.
Instructure retains no license to university-created content post-termination.

INTEGRATIONS
SSO: SAML 2.0 certified, tested with Shibboleth, Azure AD, Okta, and Google
SIS: Banner, Workday, PeopleSoft, and Ellucian â€” all certified native integrations
Microsoft Teams: Native integration, Teams meetings embeddable in Canvas courses
Zoom: Native integration included in base price
Open API: Full REST API with read/write access, OAuth 2.0, published documentation,
sandbox API environment available, no partner agreement required
LTI 1.3 tool catalog: 200+ pre-certified LTI tools documented in proposal appendix
Plagiarism: Turnitin and Unicheck (LTI 1.3)
ePortfolio: Canvas ePortfolio included natively

SERVICE LEVEL AGREEMENT
Uptime guarantee: 99.95%
Critical issue response: 30 minutes
High priority response: 2 hours
Standard response: 8 business hours
SLA penalty: 10% monthly fee credit per 0.1% below guaranteed uptime.
Incident history: Last 24 months provided with proposal.

SUPPORT AND TRAINING
Support hours: 24/7 for critical issues; business hours for standard
Contact methods: Phone, live chat, email, dedicated Slack channel for admins
Dedicated Customer Success Manager: Assigned at contract signing, no cost
Escalation path: CSM â†’ Senior Support â†’ VP Customer Success â†’ CEO
Faculty onboarding: Live virtual training for up to 400 faculty included
(on-site option available, travel costs only)
Admin training: Dedicated admin certification course for system and campus admins
Training resources: Canvas Community (forums, guides, videos), weekly live Q&A,
Canvas Certified Educator program â€” all included

MIGRATION SERVICES
Migration from existing LMS: Included in base contract.
Timeline: 12-14 weeks for full system migration, phased campus rollout available.
Data migrated: Course shells, content, gradebook, discussion archives, enrollments.
Student activity history: Best-effort export from outgoing LMS included.
Dedicated migration engineer assigned at no additional cost.

CUSTOMER REFERENCES
Ten references provided. Eight from higher education, four from public
university systems with multiple campuses. Contact information included.

SANDBOX ENVIRONMENT
Full-featured sandbox provided immediately upon contract signing, maintained
throughout the contract term at no cost.
Accessibility testers and faculty pilots may access sandbox prior to signing.

SUPPLIER DIVERSITY
Instructure is exploring supplier diversity partnerships and will engage
MWBE-certified implementation partners for all on-site services.

ADDITIONAL TERMS
Instructure may not modify pricing or core functionality unilaterally.
Any platform changes that remove RFP-required functionality require 180 days
notice and university consent.

---

## backend/data/dummy_docs/vendor_c_brightspace.txt

VENDOR PROPOSAL â€” D2L Brightspace
Submitted to: University Procurement Office
In Response to: Enterprise Learning Management System RFP
Date: November 30, 2025

COMPANY OVERVIEW
D2L (Desire2Learn) is a global EdTech company and the developer of Brightspace,
an LMS serving over 15 million learners at more than 1,000 institutions globally.
D2L has significant presence in public university systems in North America.
Headquarters: Kitchener, Ontario, Canada.
US corporate entity: D2L Ltd., incorporated in Delaware.
Employees: 950+.

PRICING
Base platform fee: $36 per enrolled FTE student per year
Estimated total Year 1 (60,000 FTE): $2,160,000
Year 2: $2,246,400 (4% escalation)
Year 3: $2,336,256 (4% escalation)
Per-campus onboarding fee: $8,000 per campus (first three included)
Migration: Professional services, estimated $55,000 (not included in base price)
Add-on modules (annual):

- Brightspace AI (AI-assisted grading, intelligent agents): $6/FTE/year
- Advanced Analytics (Brightspace Insights): $4/FTE/year
- ePortfolio Premium: $2/FTE/year
- Proctoring (Honorlock): $9/FTE/year
  Payment terms: Net 30, invoiced quarterly in advance

CONTRACT TERMS
Contract length: 3 years
Auto-renewal: Automatically renews for successive 2-year terms
Opt-out notice required: 45 days prior to renewal date
Termination for convenience: 90 days written notice plus 15% early
termination fee on remaining contract value
Governing law: Province of Ontario, Canada; or State of Delaware for
US-entity disputes â€” university's choice at time of signing

LIABILITY
Maximum liability: $500,000 or total fees paid in prior 6 months, whichever
is greater. FERPA-related claims capped separately at $100,000.

CORE LMS FUNCTIONALITY
Brightspace is a modern, cloud-native LMS with a strong track record in higher education.

Course management:

- Course creation, copying, archiving, and cross-listing for all modalities
- Course templates with locked and unlocked content controls
- Bulk course creation via CSV or SIS integration

Assignment and assessment:

- Assignment submission with inline annotation and rubric grading
- Competency-based education (CBE) framework built-in
- Gradebook with weighted and calculated grades
- Grade passback to SIS: Banner native; Workday native; PeopleSoft requires
  middleware (D2L-supported connector, no additional cost)
- Ellucian: timeline and complexity to be scoped in discovery

Collaboration:

- Discussion boards with threading and media embedding
- Group projects and peer review tools included
- Announcements with email and push delivery
- Virtual Classroom (D2L-native): included; Zoom and Teams also supported

Content standards:

- SCORM 1.2 and 2004 natively supported
- xAPI: supported via LRS integration; D2L partners with Watershed
- LTI 1.3: certified (certification documentation provided with proposal)

Video:

- Integration with Panopto and Kaltura (LTI 1.3); lecture capture setup
  included in implementation
- Automated captioning: available via Panopto or Kaltura only (not native)
- Manual caption upload: .srt and .vtt supported for all video

Mobile application:

- Brightspace Pulse: iOS app â€” full content access, notifications, due dates
- Android app: available; some advanced grading features web-only on Android
- Offline access: content download available on iOS; Android offline in roadmap Q3 2026

Learning analytics:

- Brightspace Insights: system-wide analytics dashboard (requires add-on)
- Instructor dashboard: engagement, access frequency â€” included in base
- At-risk flagging: Intelligent Agents tool â€” configurable automated alerts included
- Predictive analytics: available in Brightspace Insights add-on only

Plagiarism detection:

- Turnitin integration: LTI 1.3, setup included; Turnitin licensing separate
- iThenticate: available

ACCESSIBILITY
VPAT: Available upon request. Last third-party audit: September 2024.
WCAG 2.1 AA: Claimed for core platform. Full third-party audit documentation
not included with proposal; available under NDA.
Section 508: Conformance documented, available upon request.
Caption support: .srt and .vtt upload supported. Automated captioning requires
Panopto or Kaltura; not native to the platform.
Screen reader testing: JAWS and NVDA tested. VoiceOver: partial testing documented.
Known gaps: Mobile app (Android) has documented screen reader limitations.
Accessibility roadmap: Available on request.

SECURITY AND COMPLIANCE
Security certifications: SOC 2 Type II â€” certificate available upon request
ISO 27001: Certified â€” certificate available upon request
Data Processing Agreement: Available upon request, not provided as standard.
DPA covers: FERPA, PIPEDA (Canada), GDPR. Massachusetts Ch. 93H and Ch. 66A
can be added as an addendum upon request.
Incident Response: Summary plan provided with proposal; full plan requires NDA.
Disaster Recovery: RTO 4 hours, RPO 1 hour. Summary provided; full doc requires NDA.
University data: D2L uses anonymized and aggregated usage data for platform
benchmarking and product improvement. Individual institution data is not shared.
Opt-out of benchmarking: Available upon written request.
Data ownership: University retains ownership of all course content and student records.
D2L retains analytics metadata derived from usage patterns.
Data portability: Full export in IMS Common Cartridge and CSV within 30 days
of termination at no charge.
Encryption: TLS 1.3 in transit, AES-256 at rest.
Penetration testing: Annual third-party test; summary available upon request.

INTELLECTUAL PROPERTY
University retains ownership of all course content, student data, and custom
configurations. Jointly developed workflows are owned by the university.
D2L retains IP in any proprietary tools or services provided under the agreement.

INTEGRATIONS
SSO: SAML 2.0 supported; tested with Shibboleth and Azure AD
SIS: Banner and Workday (native); PeopleSoft (supported connector, included);
Ellucian: requires scoping â€” compatibility to be confirmed in discovery phase
Microsoft Teams: Integration available; meeting scheduling embedded in courses
Zoom: Integration available; included in base price
Open API: REST API available with read/write access; documentation published;
partner registration required for write access (complimentary for university customers)
LTI 1.3: Certified; documentation provided with proposal
ePortfolio: Brightspace ePortfolio included natively (premium version add-on)

SERVICE LEVEL AGREEMENT
Uptime target: 99.9%
Critical issue response: 1 hour
High priority response: 4 hours
Standard response: 1 business day
SLA penalty: Credits available up to 5% of monthly fee; financial penalties
capped at 5% of monthly fee per incident.

SUPPORT AND TRAINING
Support hours: 24/7 for critical issues; business hours for standard
Contact methods: Phone, email, and ticketing system
Dedicated D2L Success Manager: Assigned for first year at no cost; renewal optional
Onboarding: Four live virtual training sessions included (additional sessions $1,800 each)
Faculty training: Self-paced LMS included; on-site workshops $2,500/day plus travel
Training portal: D2L Community with guides, videos, and user forums â€” included

MIGRATION SERVICES
Migration from existing LMS: Professional services required, $55,000 estimated.
Timeline: 14-18 weeks for full migration.
Data migrated: Course content, gradebook, and enrollment records.
Discussion archives and media: Best-effort, may require additional scoping.

CUSTOMER REFERENCES
Six references provided. Four from higher education, two from multi-campus
public university systems.

SANDBOX ENVIRONMENT
Available for 30 days prior to contract signing.
Post-signing sandbox: Available for first 90 days at no charge; thereafter
$5,000/year or included in premium support tier.

SUPPLIER DIVERSITY
D2L does not hold US supplier diversity certifications. D2L commits to
MWBE-certified subcontractors for on-site implementation services.

ADDITIONAL TERMS
D2L may deprecate features with 90 days notice. Pricing escalation is capped
at 4% per year as stated; no unilateral adjustments outside this cap.
