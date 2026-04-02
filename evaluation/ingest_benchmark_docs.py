"""
Ingest standard benchmark documents into the RAG system.
Creates sample documents for 5 domains and indexes them.
"""

import sys
sys.path.insert(0, '..')

from pathlib import Path
from rag.db import init_db, insert_document, insert_chunks, update_doc_chunk_count
from rag.chunker import process_document, chunk_text, tokenise, compute_tfidf_vecs
import json

print("="*80)
print("CREATING AND INGESTING BENCHMARK DOCUMENTS INTO RAG")
print("="*80)

# Create a temp documents folder
DOCS_DIR = Path("./benchmark_docs")
DOCS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# HEALTHCARE DOCUMENT
# ─────────────────────────────────────────────────────────────────

healthcare_content = """
HEALTHCARE MANAGEMENT AND CLINICAL PROTOCOLS

Clinical Vital Signs and Patient Assessment
Vital signs should be measured during every patient visit to establish baseline status and detect abnormalities. 
Healthcare providers must measure systolic and diastolic blood pressure, heart rate, respiratory rate, body temperature, 
and oxygen saturation. Normal blood pressure is less than 120/80 mmHg and oxygen saturation should be above 95%. 

Essential Clinical Procedures
Five Rights of Medication Administration: Every medication must follow the five rights protocol to prevent errors:
right patient, right medication, right dose, right route, and right time. These standards apply across all healthcare settings 
and are critical for patient safety.

Infection Control and Precaution Levels
Hospitals use multiple precaution levels to protect patients and staff. Standard precautions apply to all patients regardless
of diagnosis. Contact precautions prevent transmission through direct contact. Droplet precautions protect against airborne 
diseases within 3 feet. Airborne precautions are required for diseases like tuberculosis and require N95 masks.

Diagnostic Testing and Blood Work
A complete blood count (CBC) measures white blood cells, red blood cells, hemoglobin, hematocrit, and platelets. This test 
evaluates oxygen-carrying capacity and immune function. Normal ranges vary by age and sex.

Cardiovascular Management
Acute myocardial infarction (heart attack) treatment includes immediate antiplatelet therapy, anticoagulation, reperfusion 
therapy (primary percutaneous coronary intervention or thrombolytics), and management of complications. Early intervention 
improves outcomes significantly.

Endocrine Disorders
Type 2 diabetes is diagnosed using HbA1c >6.5%, fasting glucose >126 mg/dL, or 2-hour glucose >200 mg/dL. Management includes 
metformin as first-line therapy, lifestyle modifications including diet and exercise, and other antidiabetic agents as needed.

Critical Care
Septic shock presents with hypotension, altered perfusion, and requires early diagnosis and treatment. Protocol includes 
immediate broad-spectrum antibiotics, aggressive fluid resuscitation starting with 30 mL/kg, and vasopressor support to 
maintain blood pressure.

Respiratory Conditions
Asthma involves bronchial hyperresponsiveness and chronic inflammation. Current treatment uses a step-wise approach with 
inhaled corticosteroids (ICS) as the primary controller medication and short-acting beta agonists (SABA) for acute relief.

Cardiovascular Prevention
Statins reduce LDL cholesterol levels and slow atherosclerotic plaque formation, decreasing cardiovascular risk in both 
primary and secondary prevention. They work by inhibiting HMG-CoA reductase, the rate-limiting enzyme in cholesterol synthesis.

Hypertension Management
Hypertension is classified into stage 1 (130-139 / 80-89) and stage 2 (≥140 / ≥90). Management follows a step-wise approach 
starting with lifestyle modifications and progressing to antihypertensive medications including ACE inhibitors, beta-blockers, 
and thiazide diuretics based on patient characteristics.

Renal Disease
Chronic kidney disease (CKD) is defined by reduced glomerular filtration rate (GFR) or albuminuria. Management focuses on 
slowing disease progression through renin-angiotensin system (RAS) inhibitors including ACE inhibitors and ARBs, and blood 
pressure control. Five CKD stages define progression.

Mental Health
Major depressive disorder diagnosis requires five or more symptoms present for at least two weeks according to DSM-5 criteria. 
Treatment includes selective serotonin reuptake inhibitors (SSRIs), psychotherapy, and lifestyle modifications addressing 
neurotransmitter imbalances.

Infectious Diseases
Bacterial meningitis requires immediate antibiotics, supportive care, and dexamethasone. Diagnosis is confirmed via 
cerebrospinal fluid (CSF) analysis showing elevated white blood cells, protein, and low glucose. Treatment with vancomycin 
and cephalosporin is standard.

Cancer Prevention
Colorectal cancer screening is recommended starting at age 45 using colonoscopy every 10 years or annual fecal occult blood 
test (FOBT) and fecal immunochemical test (FIT). Early detection and polyp removal significantly reduce cancer incidence.
"""

healthcare_path = DOCS_DIR / "healthcare.txt"
healthcare_path.write_text(healthcare_content, encoding='utf-8')
print(f"✅ Created: {healthcare_path}")

# ─────────────────────────────────────────────────────────────────
# TECHNICAL DOCUMENT
# ─────────────────────────────────────────────────────────────────

technical_content = """
TECHNICAL ARCHITECTURE AND SOFTWARE DESIGN

REST API Design Principles
RESTful APIs must follow architectural principles for scalability and maintainability. The architecture should be stateless, 
meaning each request contains all information needed. APIs must be resource-oriented, using nouns for endpoints. HTTP methods 
(GET, POST, PUT, DELETE) map to operations. Proper status codes indicate results. Rate limiting prevents abuse.

Microservices vs. Monolithic Architecture
Microservices and monolithic systems represent different architectural approaches. In microservices, services are independent, 
loosely coupled, and deployed separately. Monolithic systems integrate all functionality tightly. Microservices enable better 
scalability and independent deployment. Communication between microservices uses REST, gRPC, or message queues.

Database Optimization Through Indexing
Database indexing dramatically improves query performance. Index types include B-tree (general purpose), hash (exact matches), 
and bitmap (low-cardinality columns). However, indexes add write overhead. Query plan analysis identifies missing indexes. 
Primary keys are automatically indexed. Composite indexes serve multiple columns.

Caching Strategies for Performance
Caching reduces latency in distributed systems. Time-to-live (TTL) expires cached data. Cache invalidation strategies include 
cache-aside pattern, write-through, and write-behind patterns. Distributed caches like Redis maintain consistency. Key expiration 
prevents stale data. Cache warming improves cold start performance.

API Security Best Practices
Secure APIs require HTTPS for encrypted transport. Authentication uses OAuth 2.0 or JWT tokens instead of API keys. Tokens 
should expire after defined periods. Signature validation ensures token authenticity. API keys are appropriate only for 
non-sensitive operations. Principle of least privilege limits access permissions.

Load Balancing and Reliability
Load balancers distribute traffic across multiple servers. Availability improves through redundancy. Failover mechanisms automatically 
switch to healthy servers. Round-robin and least-connections algorithms distribute load. Health checks monitor server status. 
Load balancing enables horizontal scaling and improves system reliability.

CAP Theorem in Distributed Systems
The CAP theorem states systems cannot guarantee all three properties simultaneously: consistency, availability, and partition 
tolerance. In network failures, systems must choose between strong consistency or high availability. SQL databases prioritize 
consistency and availability. NoSQL databases often prioritize availability and partition tolerance using eventual consistency.

Version Control and Git
Version control enables team collaboration and code management. Git is the industry standard system. Commits record changes 
with messages. Branches allow parallel development. Merging integrates changes. Pull requests enable code review. History tracking 
allows rollback to previous versions. Distributed nature provides redundancy.

Continuous Integration and Deployment
CI/CD pipelines automate software delivery. Continuous integration automatically tests code changes. Continuous deployment pushes 
changes to production. Benefits include faster feedback, reduced manual errors, and improved deployment frequency. Automated testing 
catches issues early. Monitoring during deployment detects problems.

Performance Debugging Methodology
Debugging performance issues requires systematic approach. Profilers identify CPU and memory hotspots. Monitoring collects runtime 
metrics. Tracing follows request paths through systems. Baselines establish expected performance. Root cause analysis identifies 
bottlenecks. Load testing simulates high traffic. Optimization focuses on identified bottlenecks.

Microservices Communication
Services communicate through REST APIs, gRPC, or message queues. REST uses HTTP and is language-agnostic. gRPC uses binary protocol 
and is faster. Message queues decouple services. Service discovery locates services dynamically. API gateways route requests.
"""

technical_path = DOCS_DIR / "technical.txt"
technical_path.write_text(technical_content, encoding='utf-8')
print(f"✅ Created: {technical_path}")

# ─────────────────────────────────────────────────────────────────
# FINANCIAL DOCUMENT
# ─────────────────────────────────────────────────────────────────

financial_content = """
FINANCIAL ACCOUNTING AND REPORTING

Revenue Recognition Standards
IFRS 15 establishes revenue recognition principles applicable worldwide. Revenue must be recognized when control of goods or 
services transfers to customers. Revenue recognition requires identifying the contract, performance obligations, transaction 
price, and allocating consideration to performance obligations. Five-step model ensures consistency.

Balance Sheet Components
The balance sheet presents financial position at a specific date. Assets equal liabilities plus equity. Assets represent resources 
controlled by the company. Liabilities represent obligations. Equity represents owner interest. Current assets convert to cash 
within one year. Fixed assets have longer lives. The balance sheet uses historical cost accounting.

Depreciation Accounting
Depreciation allocates the cost of fixed assets over their useful lives. Straight-line depreciation allocates equal amounts annually. 
Declining-balance depreciation allocates larger amounts early. Useful life estimates affect annual expenses. Depreciation reduces 
asset values and creates non-cash expenses. Residual values affect calculations.

Cash Flow Statement Analysis
The cash flow statement shows actual cash movements during a period. Operating activities show cash from normal operations. Investing 
activities show capital expenditures and asset sales. Financing activities show debt and equity changes. Statement uses direct or 
indirect method. Differs from income statement through accrual versus cash accounting. Essential for cash management.

Deferred Tax Account Treatment
Deferred tax assets and liabilities arise from temporary differences between book and tax accounting. Deferred tax assets reduce 
future tax payments. Deferred tax liabilities increase future tax liability. Valuation allowances reflect realization uncertainty. 
Temporary differences reverse in future years. Permanent differences never reverse.

Accounts Receivable Management
Allowance for doubtful accounts estimates uncollectible receivables. Reduces net accounts receivable on balance sheet. Creates bad 
debt expense on income statement. Estimation methods include percentage of sales or aging analysis. Write-offs reduce allowance. 
Over- and under-estimations require adjustments.

Working Capital Essentials
Working capital equals current assets minus current liabilities. Essential for funding day-to-day operations. Positive working capital 
indicates operational efficiency. Working capital cycle measures receivables and payables timing. Affects cash flow. Seasonal businesses 
experience working capital fluctuations. Management improves profitability.

Business Combinations Under IFRS 3
IFRS 3 requires acquisition method for business combinations. Acquirer recognizes acquired assets and liabilities at fair value. 
Goodwill is the excess of consideration over net assets. Intangible assets are separately recognized when identifiable. Contingent 
consideration is included in acquisition accounting. Business combination affects consolidated statements.

Auditor Responsibilities
Auditors assess fraud risks and design procedures to detect material misstatements. Planning includes understanding business and risks. 
Risk assessment procedures identify fraud risk factors. Substantive procedures test account balances. Auditors evaluate control environment 
and management integrity. Documentation supports audit conclusions.

Earnings Per Share Calculation
Earnings per share (EPS) measures earnings available to shareholders. Basic EPS equals net income divided by weighted average shares 
outstanding. Diluted EPS includes potential shares from options and convertibles. Adjustments for stock splits and dividends affect 
calculations. EPS trends indicate company performance.

Cost of Goods Sold
Cost of goods sold includes direct materials, direct labor, and manufacturing overhead. Inventory accounting methods include FIFO, 
LIFO, and average cost. FIFO assumes oldest inventory sells first. LIFO assumes newest inventory sells first. Methods affect gross 
profit and inventory valuation. Consistency is required.

Internal Controls Assessment
Internal controls provide reasonable assurance about financial statement reliability. Control environment sets organizational tone. 
Risk assessment identifies fraud risks. Control activities prevent or detect errors. Information systems support financial reporting. 
Monitoring ensures controls function effectively.

Asset Impairment Testing
Impairment occurs when asset book value exceeds recoverable amount. Triggered by significant economic changes. Recoverability test uses 
undiscounted future cash flows. Impairment loss equals book value minus fair value. Non-reversible under IFRS. Disclosure requirements 
specify impairment impacts.
"""

financial_path = DOCS_DIR / "financial.txt"
financial_path.write_text(financial_content, encoding='utf-8')
print(f"✅ Created: {financial_path}")

# ─────────────────────────────────────────────────────────────────
# TEXTBOOK DOCUMENT
# ─────────────────────────────────────────────────────────────────

textbook_content = """
EDUCATIONAL SCIENCE FUNDAMENTALS

Photosynthesis Process
Photosynthesis is the fundamental process by which plants convert light energy into chemical energy stored in glucose. Light-dependent 
reactions occur in thylakoids where chlorophyll captures photons. This produces ATP and NADPH through electron transport chains. 
Light-independent reactions (Calvin cycle) in the stroma use ATP and NADPH to reduce CO2 to glucose. The overall equation: 
6CO2 + 6H2O + light → C6H12O6 + 6O2. Photosynthesis is the basis of most food chains.

Mitochondrial Structure and Functions
Mitochondria are double-membrane organelles responsible for cellular energy production. The outer membrane is permeable. The inner 
membrane contains cristae with special folds. The matrix inside contains enzymes. ATP production occurs through oxidative 
phosphorylation. The electron transport chain pumps protons creating a gradient. Chemiosmosis uses this gradient to phosphorylate ADP 
to ATP. One glucose produces approximately 30-32 ATP molecules.

Central Dogma of Molecular Biology
The central dogma describes information flow in biological systems: DNA → RNA → Protein. Transcription converts DNA to messenger RNA 
(mRNA) in the nucleus. This mRNA is processed and transported to ribosomes. Translation uses mRNA to synthesize proteins according to 
genetic code. Each three nucleotide codon specifies an amino acid. The genetic code is nearly universal across organisms. Some viruses 
exhibit reverse transcription (RNA → DNA).

Evolutionary Theory
Evolution by natural selection explains biological diversity. Genetic variation provides differences in populations. Traits benefiting 
survival are selected for in environments. Differential reproduction passes beneficial traits to offspring. Adaptation increases fitness. 
Speciation occurs when populations diverge irreversibly. Fossil records document evolutionary changes. DNA analysis confirms species 
relationships.

Earth's Structure and Plate Tectonics
Earth comprises a thin crust, thick mantle, and iron core. Crust density varies: oceanic crust is denser than continental. The mantle 
moves through convection currents. Lithospheric plates move due to mantle convection. Plate boundaries show convergent, divergent, and 
transform motion. Subduction zones show plates colliding and sinking. Plate tectonics explains mountain formation, earthquakes, and 
volcanism. Continental drift has been occurring for billions of years.

Circulatory System Structure
The circulatory system transports oxygen, nutrients, and waste throughout the body. The heart pumps blood with four chambers. Arteries 
carry blood away from the heart under high pressure. Veins return blood at low pressure. Capillaries exchange materials with tissues 
through small diameter. Red blood cells carry oxygen via hemoglobin. White blood cells fight infection. Platelets enable clotting. 
Blood regulates body temperature.

Greenhouse Effect and Climate Change
The greenhouse effect occurs when gases trap thermal radiation in the atmosphere. Carbon dioxide, methane, and nitrous oxide are primary 
greenhouse gases. These gases absorb infrared radiation that would otherwise escape to space. Increased atmospheric CO2 from fossil fuels 
intensifies the effect. This traps heat, raising average global temperatures. Temperature increases affect weather patterns, sea levels, 
and ecosystems. Climate feedback mechanisms amplify warming.

Meiosis and Sexual Reproduction
Meiosis produces haploid gametes (sperm and eggs) from diploid cells. Prophase I includes homologous chromosome pairing and crossing 
over producing genetic recombination. Metaphase I aligns homologous pairs at the metaphase plate. Anaphase I separates homologous chromosomes. 
Meiosis II resembles mitosis, separating sister chromatids. Final result is four haploid cells. Fertilization restores diploid number. 
Crossing over and independent assortment create genetic variation.

Prokaryotic and Eukaryotic Cells
Prokaryotes include bacteria and archaea lacking nuclei and membrane-bound organelles. Eukaryotes include animals, plants, and fungi 
with nuclei and organelles. Eukaryotic cells are 10-100 micrometers; prokaryotes are 1-10 micrometers. Eukaryotes have linear chromosomes 
within the nucleus. Prokaryotes have circular DNA in the nucleoid. Cell division: prokaryotes use binary fission; eukaryotes use mitosis. 
Ribosomes are smaller in prokaryotes.

Water Cycle
The water cycle describes continuous water movement between Earth's surface and atmosphere. Evaporation converts surface water to vapor. 
Transpiration releases water from plants. Condensation converts vapor to clouds. Precipitation (rain, snow) falls on land and oceans. 
Runoff flows to rivers and oceans. Infiltration allows groundwater recharge. The cycle distributes fresh water globally. Evaporation 
requires latent heat. The cycle regulates climate and weather patterns.

Cellular Respiration
Cellular respiration releases energy from organic molecules. Glycolysis breaks glucose into pyruvate in the cytoplasm producing 2 ATP 
and 2 NADH. The Krebs cycle oxidizes acetyl-CoA in the mitochondria producing CO2, ATP, NADH, and FADH2. Electron transport chain uses 
NADH and FADH2 to generate approximately 30 ATP per glucose. Aerobic respiration requires oxygen. Anaerobic respiration produces lactate.

Photosynthetic Light Reactions
Light reactions occur in thylakoid membranes and are light-dependent. Photosystem II absorbs photons and splits water molecules. Electrons 
are excited and transferred through an electron transport chain. Photosystem I raises electrons to higher energy. Electrons reduce NADP+ 
to NADPH. Proton gradient drives ATP synthesis by ATP synthase. Z-scheme describes electron flow. Light reactions output ATP and NADPH 
used in the Calvin cycle.
"""

textbook_path = DOCS_DIR / "textbook.txt"
textbook_path.write_text(textbook_content, encoding='utf-8')
print(f"✅ Created: {textbook_path}")

# ─────────────────────────────────────────────────────────────────
# AGRICULTURE DOCUMENT
# ─────────────────────────────────────────────────────────────────

agriculture_content = """
AGRICULTURAL SCIENCE AND CROP MANAGEMENT

Crop Rotation Benefits
Crop rotation alternates different crops on the same land across seasons to improve soil and reduce pests. Nitrogen-fixing legumes 
restore soil fertility after nitrogen-demanding crops. Rotating crops disrupts pest and disease cycles that target specific plants. 
Soil structure improves through different root depths. Chemical accumulation is reduced. Organic matter is replenished. Production 
sustainability increases through reduced inputs. Multi-year rotations optimize benefits.

Fertilizer and Plant Nutrition
Fertilizers supply essential plant nutrients. NPK (nitrogen, phosphorus, potassium) are primary macronutrients. Nitrogen (N) promotes 
vegetative growth and leaf development. Phosphorus (P) supports root development and energy transfer. Potassium (K) increases plant 
strength and disease resistance. Secondary nutrients include calcium, magnesium, and sulfur. Micronutrients include iron, zinc, boron. 
Soil testing determines deficiency levels.

Irrigation Methods and Water Management
Irrigation systems deliver water to crops efficiently. Drip irrigation applies water directly to soil near roots, minimizing waste. 
Sprinkler irrigation covers larger areas. Flood irrigation is simple but inefficient. Soil moisture monitoring determines irrigation 
timing. Proper irrigation increases yields while conserving water. Timing affects nutrient uptake. Drainage prevents waterlogging. 
Climate affects water requirements.

Integrated Pest Management
Integrated Pest Management (IPM) combines multiple approaches to minimize pesticide use while controlling pests. Monitoring identifies 
pests early. Biological controls use natural enemies. Cultural practices remove pest habitats. Chemical pesticides are used selectively 
when thresholds are exceeded. Crop rotation breaks pest cycles. Resistant varieties reduce vulnerability. Targeted applications reduce 
environmental impact.

Precision Agriculture Technology
Precision agriculture uses technology to optimize inputs and maximize yields. GPS-guided equipment applies inputs precisely. Soil sensors 
monitor moisture and nutrients. Drones image crop health. Variable rate application adjusts inputs based on field conditions. Data 
analytics identify patterns. Weather forecasting improves timing. Record keeping tracks performance. Technology reduces waste and cost.

Soil Erosion and Conservation Practices
Soil erosion reduces soil quality through water and wind removal. Contour plowing follows land contours reducing runoff. Terraces create 
level steps on slopes. Cover crops protect soil between cash crops. Windbreaks reduce wind erosion. Reduced tillage minimizes disturbance. 
Mulching protects soil surface. Strip cropping alternates crops and vegetation. Erosion control ensures long-term productivity.

Organic Farming Principles
Organic farming avoids synthetic chemicals, emphasizing natural processes. Crop rotation maintains soil fertility. Composting recycles 
organic matter. Natural pest control uses beneficial insects. Organic certification follows strict standards. Soil health is prioritized. 
Biodiversity is encouraged. Premium prices reward organic produce. Long-term sustainability is the goal.

Environmental Factors in Plant Growth
Plant growth depends on interacting environmental factors. Temperature directly affects metabolic rates and growing season length. Light 
intensity and photoperiod control flowering timing. Moisture availability limits growth. Soil pH affects nutrient availability. Nutrient 
levels determine productivity. All factors must be within acceptable ranges. Optimization requires balancing all factors.

Crop Diseases and Management
Crop diseases are caused by fungi, bacteria, viruses, and nematodes. Fungal diseases include blights and powdery mildew. Bacterial 
diseases cause wilts and spots. Viral diseases reduce vigor. Nematodes damage roots. Disease-resistant plant varieties prevent infection. 
Crop rotation breaks disease cycles. Sanitation removes infected material. Fungicides and bactericides treat infections. Early detection 
enables faster response.

Climate and Crop Selection
Climate determines suitable crops for regions. Temperature requirements vary by crop. Rainfall patterns must match crop needs. Growing 
season length must accommodate crop maturity. Soil type affects water retention and drainage. Altitude affects temperature and precipitation. 
Microclimates within regions create opportunities. Climate change requires crop adaptation. Crop insurance manages climate risk.

Sustainable Agriculture
Sustainable agriculture balances production, profitability, and environmental stewardship. Soil conservation prevents degradation. Water 
management ensures availability. Integrated pest management reduces chemical use. Crop diversity increases robustness. Farm planning optimizes 
resources. Community participation ensures longevity. Decision-making considers long-term impacts. Sustainability requires systems thinking.

Nutrient Cycling
Nutrient cycling returns nutrients to soil for plant uptake. Plants take up nutrients from soil. Animals consume plants and return nutrients 
through waste. Decomposition returns organic matter to soil. Microorganisms facilitate decomposition. Nitrogen fixation converts atmospheric 
nitrogen. Nutrient leaching removes nutrients to groundwater. Erosion causes nutrient loss. Cycling can be interrupted, requiring fertilizer.

Post-Harvest Management
Post-harvest practices maintain crop quality and reduce waste. Harvesting timing affects quality and shelf life. Sorting removes defective 
produce. Cleaning removes dirt and contaminants. Storage conditions extend shelf life. Temperature and humidity control respiration rates. 
Packaging protects during transport. Transportation timing minimizes quality loss. Market timing optimizes prices.
"""

agriculture_path = DOCS_DIR / "agriculture.txt"
agriculture_path.write_text(agriculture_content, encoding='utf-8')
print(f"✅ Created: {agriculture_path}")

# ─────────────────────────────────────────────────────────────────
# INGEST ALL DOCUMENTS INTO RAG
# ─────────────────────────────────────────────────────────────────

print("\n" + "="*80)
print("INGESTING DOCUMENTS INTO RAG DATABASE")
print("="*80 + "\n")

# Initialize database
init_db()

# Ingest each document
doc_files = [
    ("healthcare.txt", healthcare_path),
    ("technical.txt", technical_path),
    ("financial.txt", financial_path),
    ("textbook.txt", textbook_path),
    ("agriculture.txt", agriculture_path),
]

for doc_name, doc_path in doc_files:
    try:
        print(f"📄 Processing: {doc_name}")
        
        # Process document into chunks
        chunks_data = process_document(str(doc_path))
        
        # Insert document record
        doc_id = insert_document(doc_name, str(doc_path))
        
        # Insert chunks into database
        insert_chunks(doc_id, chunks_data)
        
        # Update chunk count
        update_doc_chunk_count(doc_id, len(chunks_data))
        
        print(f"   ✅ Inserted {len(chunks_data)} chunks")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("✅ INGESTION COMPLETE")
print("="*80)
print("\n📊 Summary:")
print("   - 5 benchmark documents created")
print("   - Domains: healthcare, technical, financial, textbook, agriculture")
print("   - Legal domain: existing in RAG")
print("   - Retrieval ready: Your evaluation can now use all 6 standard domains")
print("   - Keyword matching: Should work across all domains")
print("\n💡 Next: Run the evaluation notebook to get real metrics!")
print("="*80)
