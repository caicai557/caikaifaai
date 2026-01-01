# 代码地图 - council

> 生成时间: 2026-01-01 12:27

## 概览

- 文件总数: 122
- 代码行数: 25177

## 文件结构

### `dev_orchestrator.py`
- 类: DevStatus, SubTask, DevResult
- 函数: 无

### `__init__.py`
- 类: 无
- 函数: 无

### `cli.py`
- 类: 无
- 函数: classify_command, route_command, status_command

### `exceptions.py`
- 类: CouncilError, AgentError, AgentNotFoundError
- 函数: 无

### `simple_agent.py`
- 类: Task, AgentState, SimpleAgent
- 函数: 无

### `mcp/protocol.py`
- 类: MCPProtocolHandler
- 函数: handle_request

### `mcp/__init__.py`
- 类: 无
- 函数: 无

### `mcp/monitor.py`
- 类: MetricPoint, SemanticEntropyMonitor
- 函数: log_response, get_stats, clear

### `mcp/simulate.py`
- 类: 无
- 函数: extract_target, is_delete_operation, find_dependents

### `mcp/a2a_bridge.py`
- 类: AgentCapability, AgentCapabilityDescriptor, A2AMessage
- 函数: generate_message_id, to_dict, from_dict

### `mcp/tool_search.py`
- 类: ToolCategory, ToolDefinition, ToolRegistry
- 函数: create_default_registry, matches, register

### `mcp/ai_council_server.py`
- 类: ModelProvider, ModelConfig, ModelResponse
- 函数: get_enabled_models, evaluate_votes, get_status

### `utils/__init__.py`
- 类: 无
- 函数: 无

### `utils/yasl.py`
- 类: YASLSerializer
- 函数: dump, load

### `utils/retry.py`
- 类: RetryConfig, RetryStats, RetryManager
- 函数: calculate_delay, retry, async_retry

### `orchestration/collaboration.py`
- 类: CollaborationMode, CollaborationResult, Vote
- 函数: to_dict, get_session, get_all_sessions

### `orchestration/events.py`
- 类: EventType, Event
- 函数: to_dict, create

### `orchestration/handoff.py`
- 类: HandoffPriority, HandoffStatus, ContextSnapshot
- 函数: add_decision, add_fact, to_prompt

### `orchestration/graph.py`
- 类: NodeType, Checkpoint, State
- 函数: to_dict, from_dict, to_dict

### `orchestration/hub.py`
- 类: Hub
- 函数: ledger, ledger, subscribe

### `orchestration/__init__.py`
- 类: 无
- 函数: 无

### `orchestration/delegation.py`
- 类: DelegationStatus, DelegationRequest, DelegationResult
- 函数: delegate, get_current_chain, get_history

### `orchestration/model_router.py`
- 类: ModelConfig, RoutingResult, ModelPerformanceStats
- 函数: success_rate, avg_latency_ms, recent_avg_latency_ms

### `orchestration/blast_radius.py`
- 类: ImpactLevel, BlastRadiusResult, BlastRadiusAnalyzer
- 函数: build_graph, analyze, analyze_multiple

### `orchestration/task_classifier.py`
- 类: TaskType, RecommendedModel, ModelSpec
- 函数: classify, recommend_model, get_model_spec

### `orchestration/tripartite.py`
- 类: TripartiteRole, TaskLedger, AuditReport
- 函数: run

### `orchestration/health_check.py`
- 类: HealthStatus, HealthCheckResult, ModelHealth
- 函数: update, register, unregister

### `orchestration/adaptive_router.py`
- 类: RiskLevel, ResponseMode, RoutingDecision
- 函数: assess_risk, route, explain_decision

### `orchestration/ledger.py`
- 类: IterationStatus, TaskLedger, IterationRecord
- 函数: add_fact, add_query, resolve_query

### `orchestration/multi_model_executor.py`
- 类: ModelRole, ModelTask, ModelResult
- 函数: create_planner_task, create_executor_task, create_reviewer_task

### `orchestration/agent_registry.py`
- 类: AgentCapability, RegisteredAgent, AgentRegistry
- 函数: register, unregister, get

### `tests/test_protocol_schema.py`
- 类: TestVoteEnum, TestMinimalVote, TestMinimalThinkResult
- 函数: test_vote_values, test_to_legacy, test_valid_vote

### `tests/test_wald_consensus.py`
- 类: TestWaldConsensusAutoCommit, TestWaldConsensusReject, TestWaldConsensusHoldForHuman
- 函数: test_unanimous_high_confidence_approval, test_approve_with_changes_counts_as_approve, test_unanimous_high_confidence_rejection

### `tests/test_shadow_facilitator.py`
- 类: TestShadowFacilitator, TestShadowResult
- 函数: test_unanimous_approve_resolves_in_shadow, test_unanimous_reject_resolves_in_shadow, test_disagreement_triggers_escalation

### `tests/test_governance_hardening.py`
- 类: TestGovernanceHardening
- 函数: test_scan_content_dangerous_rm_rf, test_scan_content_suspicious_eval, test_requires_approval_with_content

### `tests/test_server_consensus.py`
- 类: TestServerConsensus
- 函数: test_parse_vote_approve, test_parse_vote_reject, test_evaluate_votes_autocommit

### `tests/test_rbac.py`
- 类: TestSensitivePathBlocking, TestRolePermissionMatrix, TestPathBasedPermissions
- 函数: test_ssh_directory_is_sensitive, test_env_files_are_sensitive, test_secrets_directory_is_sensitive

### `tests/test_real_agents.py`
- 类: TestRealAgents
- 函数: test_architect_think, test_coder_vote, test_security_auditor_scan_behavior

### `tests/test_ai_council_server.py`
- 类: TestModelConfiguration, TestAPIKeyValidation, TestServerStatus
- 函数: test_default_models_exist, test_model_config_creation, test_models_disabled_without_api_key

### `tests/__init__.py`
- 类: 无
- 函数: 无

### `tests/test_patch_generator.py`
- 类: TestPatchGenerator
- 函数: setUp, test_extract_code_block, test_construct_prompt

### `tests/test_server_governance.py`
- 类: TestServerGovernance
- 函数: 无

### `tests/test_self_healing.py`
- 类: TestTestResult, TestDiagnosis, TestPatch
- 函数: test_create_passing_result, test_create_failing_result, test_create_diagnosis

### `tests/test_governance_gateway.py`
- 类: TestRequiresApprovalHighRisk, TestProtectedPathDetection, TestApprovalWorkflow
- 函数: test_deploy_requires_approval, test_database_requires_approval, test_security_requires_approval

### `skills/coding_skill.py`
- 类: CodingInput, CodingOutput, CodingSkill
- 函数: 无

### `skills/data_analysis_skill.py`
- 类: AnalysisInput, AnalysisOutput, DataAnalysisSkill
- 函数: 无

### `skills/base_skill.py`
- 类: BaseSkill
- 函数: 无

### `skills/research_skill.py`
- 类: ResearchInput, ResearchOutput, ResearchSkill
- 函数: 无

### `skills/security_audit_skill.py`
- 类: AuditInput, SecurityFinding, AuditOutput
- 函数: 无

### `skills/__init__.py`
- 类: 无
- 函数: 无
