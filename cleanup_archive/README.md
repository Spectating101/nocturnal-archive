# <NOCTURNAL-ARCHIVE>

## <META>

type:research_paper_analysis_system;architecture:python+rust_hybrid;purpose:multi_llm_academic_research_processing;core_features:paper_analysis,research_synthesis,intelligent_llm_routing,quota_management;user_types:academic_researchers,industry_professionals,graduate_students,technology_scouts

</META>

## <OVERVIEW>

Nocturnal Archive is a modular, production-ready backend for automated academic research, powered by advanced LLMs and robust paper retrieval. It enables interactive research planning, automated literature search, document analysis, and synthesis—all orchestrated through a CLI chatbot and microservice architecture.
</OVERVIEW>

---

## <ARCHITECTURE>

```
CLI_INTERFACE <-> RESEARCH_MANAGEMENT <-> PAPER_COLLECTION
      ^                    ^                     ^
      v                    v                     v
LLM_SERVICE <------> SYNTHESIS_ENGINE <----> SEARCH_SERVICE
      ^                    ^                     ^
      v                    v                     v
CORE_SERVICES[STORAGE, QUEUE_HANDLER, CONFIGURATION]
      ^                    ^                     ^
      v                    v                     v
EXTERNAL[MISTRAL_API, CEREBRAS_API, COHERE_API, OPENALEX, REDIS, MONGODB]
```

</ARCHITECTURE>

---

## <FEATURES>

- **Interactive Chatbot**: Context-aware research planning and Q&A
- **LLM Integration**: Modular support for Cerebras, Mistral, Cohere (easily swappable)
- **Automated Paper Discovery**: OpenAlex, Semantic Scholar, arXiv, Sci-Hub, and more
- **Document Analysis & Synthesis**: LLM-powered extraction of findings, gaps, and connections
- **Session Management**: Persistent research sessions, progress tracking, and synthesis storage
- **Background Processing**: Asynchronous paper search and analysis
- **Robust Storage**: MongoDB and Redis for data and session management
- **Extensible Architecture**: Python microservices, Rust components, and clear separation of concerns
- **News Monitor**: Personalized news tracking based on user profile and research history
  </FEATURES>

---

## <COMPONENTS>

core[rust]:{document_processor.rs:pdf_extraction_chunking,queue_handler.rs:processing_queues_retry_logic,research_manager.rs:session_orchestration}

llm_service:{
llm_manager.py:central_operation_management,
model_dispatcher.py:provider_selection_task_routing,
api_clients:{
mistral_client.py:1B_tokens_month,
cerebras_client.py:1M_tokens_day,
cohere_client.py:1K_requests_month
},
usage_tracker.py:quota_monitoring_fallback_chains,
embeddings.py:vector_generation
}

paper_service:{
paper_manager.py:paper_crud_operations,
metadata.py:extraction_normalization,
openalex.py:academic_api_integration
}

research_service:{
context_manager.py:session_tracking_management,
synthesizer.py:multi_paper_synthesis_generation,
critical_paper_detector.py:importance_ranking,
dispatcher.py:llm_driven_research_engine_selection
}

search_service:{
search_engine.py:unified_search_capabilities,
vector_search.py:similarity_search,
indexer.py:document_indexing
}

news_service:{
news_monitor.py:personalized_news_tracking,
topic_classifier.py:user_interest_identification,
alert_system.py:notification_management
}

storage:{
db/connections.py:database_management,
db/models.py:data_schemas,
db/operations.py:crud_abstraction
}
</COMPONENTS>

---

## <USER_TYPES>

academic_researcher:{goals:[comprehensive_literature_review,research_gap_identification,methodology_assessment,systematic_review],preferences:[deep_analysis,citation_network_exploration,methodology_focus,theoretical_framework_understanding],timeline:extended,output_formats:[academic_paper,citation_manager_export,latex]}
industry_professional:{goals:[market_research,technology_assessment,practical_application_finding,competitive_intelligence],preferences:[medium_depth,recent_developments_focus,rapid_turnaround,commercial_viability_emphasis],timeline:compressed,output_formats:[executive_summary,presentation,decision_framework]}
graduate_student:{goals:[literature_review,concept_understanding,research_direction_identification,methodology_learning],preferences:[balanced_depth,educational_focus,clear_explanations,structured_progression],timeline:academic_semester,output_formats:[thesis_section,study_guide,methodology_review]}
technology_scout:{goals:[emerging_technology_identification,readiness_assessment,patent_landscape_monitoring,cross_domain_innovation],preferences:[broad_coverage,novelty_focus,trend_analysis,technical_feasibility],timeline:continuous,output_formats:[trend_report,technology_radar,alert_system]}
</USER_TYPES>

---

## <INSTALLATION>

dependencies:{python:3.8+,rust_toolchain,redis_server,mongodb,api_accounts:[mistral,cerebras,cohere]}

setup:```bash
git clone <repo-url>
cd Nocturnal-Archive
pip install -r requirements.txt

# Start full stack (API + Redis + MongoDB + Qdrant + Neo4j + Worker)

docker compose up -d --build

# Configure API keys via environment (preferred) or src/config/api_config.json

cp .env.local.example .env.local # then fill in values

# Health check

python system_health_check.py

# Optional: run CLI chatbot locally

python run_chatbot.py

````
</INSTALLATION>

---

## <CONFIG>
database:{mongodb:{url:"mongodb://localhost:27017",database:"nocturnal_archive",collection_prefix:"na_"},redis:{url:"redis://localhost:6379",db:0,key_prefix:"na:"}}
llm_services:{mistral:{api_key:"YOUR_MISTRAL_API_KEY",enabled:true,priority:1,models:{default:"mistral-large-latest",synthesis:"mistral-large-latest"},limits:{daily_tokens:500000,monthly_tokens:1000000000,rate_limit:"500K tokens/min"}},cerebras:{api_key:"YOUR_CEREBRAS_API_KEY",enabled:true,priority:2,models:{default:"cerebras-gpt-1",synthesis:"cerebras-gpt-1"},limits:{daily_tokens:1000000,rate_limit:"30 requests/min"}},cohere:{api_key:"YOUR_COHERE_API_KEY",enabled:true,priority:3,models:{default:"command-light",synthesis:"command"},limits:{monthly_requests:1000,rate_limit:"20 requests/min"}}}
processing:{chunk_size:4000,overlap:200,max_concurrent:5,retry_attempts:3,timeout:300}
</CONFIG>

---

## <WORKFLOWS>
research_session_creation:{entry:research_service/context_manager.py:create_session,user_actions:[define_topic,select_analysis_scope,choose_focus_areas,set_llm_strategy,review_confirm_parameters],system_actions:[create_session_id,initialize_metadata,setup_processing_queues,begin_paper_discovery],parameters:{topic:str,scope:[light|medium|deep],focus_areas:[methods,materials,economics,environmental_impact,applications],llm_strategy:[balanced,speed,depth,token-efficient]},implementation:```
session_id = await research_manager.create_session(
    topic="biodegradable electronics",
    scope="medium",
    focus_areas=["methods", "materials"],
    llm_strategy="balanced"
)
````

}
paper_management:{entry:paper_service/paper_manager.py,sources:[manual_upload,url_import,openalex_integration,citation_network],processing_pipeline:[metadata_extraction,content_analysis,llm_processing],operations:{add_paper:`paper_id = await paper_manager.add_paper(content=pdf_content, filename="research_paper.pdf", content_type="application/pdf")`,search_papers:`papers = await paper_manager.search_papers(query="plastic recycling 3D printing", limit=20)`,get_status:`status = await paper_manager.get_paper_status(paper_id)`}}
llm_provider_management:{providers:{mistral:{tokens_month:1B,tokens_min:500K,priority:1,models:{default:"mistral-large-latest"}},cerebras:{tokens_day:1M,requests_min:30,priority:2,models:{default:"llama-3-8b-instruct"}},cohere:{requests_month:1K,requests_min:20,priority:3,models:{default:"command-light"}}},routing_logic:```
if task_type == "summarization":
if mistral.can_request(tokens):
use_mistral()
elif cerebras.can_request(tokens):
use_cerebras()
else:
queue_for_later()

````,quota_management:[real-time_tracking,rate_limiting,automatic_provider_switching,caching],error_handling:[primary_attempt,secondary_fallback,tertiary_backup,exponential_backoff]}
synthesis_generation:{entry:research_service/synthesizer.py:generate_synthesis,source_options:[research_session,paper_selection,topic_search],synthesis_depth:[executive_summary,detailed_analysis,full_report],output_formats:[markdown,academic_paper,presentation,json],quality_assurance:[citation_verification,contradiction_detection,completeness_assessment],implementation:```
synthesis = await synthesizer.generate_synthesis(
    papers=processed_papers,
    depth="detailed_analysis",
    format="markdown",
    initial_consensus="Research focuses on sustainability"
)
````

}
</WORKFLOWS>

---

## <ERROR_HANDLING>

provider_errors:{rate_limit:[exponential_backoff,automatic_retry],quota_exceeded:[switch_to_next_provider,queue_for_off-peak],content_filter:[log_alert,manual_review]}
system_errors:{database_connection:[retry_with_backoff,local_caching],file_processing:[partial_extraction,error_logging],llm_timeout:[request_chunking,provider_switching]}
health_checks:```python
async def system_health_check():
return {
"database": await check_database_health(),
"redis": await check_redis_health(),
"llm_providers": await check_llm_health(),
"storage": await check_storage_health()
}

````
</ERROR_HANDLING>

---

## <RESEARCH_ENGINE_ARCHITECTURE>

engines:{
  academic_paper:{depth:deepest,trigger:intent["literature_review","systematic_review","peer_reviewed","citations","methodology","gap_analysis"],sources:[openalex,semantic_scholar,arxiv,scihub],citation_tracking:true,escalation:true},
  web_deep:{depth:intermediate,trigger:intent["latest_trends","comprehensive","in-depth","compare","survey"],sources:[web_search,news,blogs],citation_tracking:true,escalation:true},
  web_context:{depth:surface,trigger:intent["quick_fact","definition","recent_news","overview"],sources:[web_search],citation_tracking:true,escalation:false,parallel:true}
}

dispatcher:{
  logic:llm_intent_detection+topic_classification+conversation_state+user_profile,
  escalation:[surface→deep→academic],
  clarification:if_intent=="clarification"→ask_for_more_context,
  user_preference_override:true,
  extensible:true
}

citation_reference_tracking:{
  every_response:{citations:[title,authors,date,url_or_doi],provenance:db_storage,cache:reuse_for_similar_queries},
  auditability:true
}

database_cache_layer:{
  responses:{fields:[query,answer,citations,user_profile,timestamp]},
  storage:[mongodb,redis],
  traceability:true
}

frontend_port:{
  api:structured,context:full,citations:full,provenance:full,plug_and_play:true
}

</RESEARCH_ENGINE_ARCHITECTURE>

## <WHERE_WE_LEFT_OFF>

state:{
  dispatcher:llm_driven,context_aware,escalation_supported,clarification_supported,
  citation_tracking:enabled,db_storage:enabled,
  multi_engine:academic_paper+web_deep+web_context,frontend_port:ready
}

## <NEXT_STEPS>

next_steps:{
  engine_implementation:{academic_paper:connect_to_context_manager_and_synthesizer,web_deep:implement_deep_web_browsing_and_synthesis,web_context:connect_to_search_engine_and_summarizer},
  dispatcher_extension:{hybrid_parallel_support:true,advanced_user_profile_adaptation:true,confidence_based_escalation:true},
  news_monitor:{personalized_tracking:implement,user_profile_integration:enhance,topic_classification:expand,alert_system:develop},
  api_extension:{add_rest_endpoints_for_frontend_integration:true},
  testing:{unit:expand,integrations:expand,edge_cases:cover},
  documentation:{expand_symbolic_docs:true,add_examples:true}
}

---

## <ADVANCED_USAGE>
custom_providers:{steps:[create_client_in_api_clients,implement_interface,add_config,update_dispatcher],example:```
# Create new provider in src/services/llm_service/api_clients/new_provider.py
# Implement required methods: process_document(), generate_synthesis()
# Add to api_config.json and update model_dispatcher.py routing logic
````

}
batch_operations:{example:```python
topics = ["sustainability", "renewable energy", "carbon capture"]
for topic in topics:
session_id = await create_research_session(topic)
await monitor_session_completion(session_id)

````
}
caching_strategies:{approaches:[redis_paper_caching,llm_response_caching,document_compression,cache_warming],benefits:[reduced_api_calls,faster_response_times,quota_conservation]}
concurrent_processing:{approaches:[multiple_workers,connection_pooling,load_balancing],implementation:```python
# Configure concurrent processing in processing section of config
# "processing": {"max_concurrent": 5}
````

}
</ADVANCED_USAGE>

---

## <MENTAL_MODELS>

research_funnel:{progression:[broad_topic→specific_questions→detailed_analysis→actionable_insights],implications:[progressive_focusing,stage-appropriate_synthesis,guidance_on_narrowing_focus]}
knowledge_building:{progression:[individual_papers→themes→patterns→frameworks→theories],implications:[relationship_emphasis,explicit_connections,cumulative_understanding]}
problem_solution:{progression:[problem_definition→solution_exploration→solution_evaluation→implementation_planning],implications:[practical_orientation,comparative_evaluation,decision_focus]}
time_value:{balance:[time_investment↔information_value],implications:[efficiency_emphasis,value_maximization,constraint_acknowledgment]}
</MENTAL_MODELS>

---

## <USAGE_SCENARIOS>

research_proposal:{goal:develop_compelling_research_proposal_with_literature_foundation,approach:[exploratory_research→targeted_investigation],activities:[landscape_mapping,gap_identification,methodology_assessment,proposal_formulation],success_metrics:[clear_gap_articulation,comprehensive_literature_coverage,justified_methodology]}
technology_assessment:{goal:evaluate_emerging_technology_for_business_application,approach:targeted_investigation_with_economics_applications_focus,activities:[technical_maturity_assessment,competitive_analysis,market_evaluation,risk_assessment],success_metrics:[clear_viability_assessment,quantitative_comparison,actionable_recommendations]}
systematic_literature_review:{goal:conduct_authoritative_review_for_policy_publication,approach:systematic_review_with_comprehensive_coverage,activities:[protocol_development,exhaustive_search,systematic_analysis,meta-analysis],success_metrics:[complete_evidence_coverage,rigorous_methodology,publishable_conclusions]}
competitive_intelligence:{goal:monitor_landscape_and_identify_strategic_opportunities_threats,approach:continuous_monitoring_with_regular_analysis,activities:[baseline_assessment,ongoing_surveillance,threat_opportunity_analysis],success_metrics:[comprehensive_landscape_mapping,early_warning_capability,strategic_intelligence]}
</USAGE_SCENARIOS>

---

## <FUTURE_ENHANCEMENTS>

- Cross-document querying: Implement cross-document thematic analysis.
- Enterprise Features: Add user authentication and compliance tools (GDPR, HIPAA).
- API endpoints for web/frontend integration.
- Security hardening and input sanitization.
- Structured logging and observability.
- Expanded unit and integration tests.
- Improved data validation and synthesis quality.
- Comprehensive documentation in `docs/`.
  </FUTURE_ENHANCEMENTS>

---

## <LICENSE>

MIT License
</LICENSE>

## <CONTACT>

For questions, issues, or contributions, open an issue or contact the maintainer.
</CONTACT>
