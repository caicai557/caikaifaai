"""
Tests for council/mcp/a2a_bridge.py
"""

from council.mcp.a2a_bridge import (
    A2ABridge,
    A2AMessage,
    AgentCapability,
    AgentCapabilityDescriptor,
    generate_message_id,
)


class TestAgentCapabilityDescriptor:
    """Tests for AgentCapabilityDescriptor"""

    def test_create_descriptor(self):
        """Test creating a capability descriptor"""
        desc = AgentCapabilityDescriptor(
            agent_name="Coder",
            capabilities=[AgentCapability.CODE, AgentCapability.EXECUTE],
            description="A coding agent",
        )
        assert desc.agent_name == "Coder"
        assert AgentCapability.CODE in desc.capabilities

    def test_to_dict(self):
        """Test converting to dict"""
        desc = AgentCapabilityDescriptor(
            agent_name="Architect",
            capabilities=[AgentCapability.THINK, AgentCapability.ARCHITECTURE],
            description="Architecture agent",
        )
        d = desc.to_dict()
        assert d["name"] == "Architect"
        assert "think" in d["capabilities"]
        assert "architecture" in d["capabilities"]

    def test_from_dict(self):
        """Test creating from dict"""
        data = {
            "name": "Auditor",
            "capabilities": ["security_audit", "review"],
            "description": "Security auditor",
        }
        desc = AgentCapabilityDescriptor.from_dict(data)
        assert desc.agent_name == "Auditor"
        assert AgentCapability.SECURITY_AUDIT in desc.capabilities


class TestA2AMessage:
    """Tests for A2AMessage"""

    def test_create_message(self):
        """Test creating a message"""
        msg = A2AMessage(
            message_id="msg_001",
            from_agent="Orchestrator",
            to_agent="Coder",
            action="execute_task",
            payload={"task": "Implement login"},
        )
        assert msg.from_agent == "Orchestrator"
        assert msg.action == "execute_task"

    def test_to_json(self):
        """Test serializing to JSON"""
        msg = A2AMessage(
            message_id="msg_002",
            from_agent="A",
            to_agent="B",
            action="test",
            payload={"key": "value"},
        )
        json_str = msg.to_json()
        assert "msg_002" in json_str
        assert "test" in json_str


class TestA2ABridge:
    """Tests for A2ABridge"""

    def test_register_agent(self):
        """Test registering an agent"""
        bridge = A2ABridge()
        desc = AgentCapabilityDescriptor(
            agent_name="Coder",
            capabilities=[AgentCapability.CODE],
            description="Coder",
        )
        bridge.register_agent(desc)
        assert "Coder" in bridge._agents

    def test_discover_agents_all(self):
        """Test discovering all agents"""
        bridge = A2ABridge()
        bridge.register_agent(
            AgentCapabilityDescriptor("A", [AgentCapability.THINK], "Agent A")
        )
        bridge.register_agent(
            AgentCapabilityDescriptor("B", [AgentCapability.CODE], "Agent B")
        )

        agents = bridge.discover_agents()
        assert len(agents) == 2

    def test_discover_agents_by_capability(self):
        """Test discovering agents by capability"""
        bridge = A2ABridge()
        bridge.register_agent(
            AgentCapabilityDescriptor("Coder", [AgentCapability.CODE], "Coder")
        )
        bridge.register_agent(
            AgentCapabilityDescriptor(
                "Architect", [AgentCapability.ARCHITECTURE], "Architect"
            )
        )

        coders = bridge.discover_agents(AgentCapability.CODE)
        assert len(coders) == 1
        assert coders[0].agent_name == "Coder"

    def test_send_message_with_handler(self):
        """Test sending a message with handler"""
        bridge = A2ABridge()
        received = []

        def handler(msg):
            received.append(msg)
            return A2AMessage(
                message_id="reply_001",
                from_agent=msg.to_agent,
                to_agent=msg.from_agent,
                action="reply",
                payload={"status": "ok"},
            )

        bridge.register_handler("Coder", handler)

        msg = A2AMessage(
            message_id="msg_001",
            from_agent="Orchestrator",
            to_agent="Coder",
            action="execute",
            payload={},
        )
        response = bridge.send_message(msg)

        assert len(received) == 1
        assert response is not None
        assert response.action == "reply"

    def test_send_message_queued(self):
        """Test that messages are queued when no handler"""
        bridge = A2ABridge()
        msg = A2AMessage(
            message_id="msg_001",
            from_agent="A",
            to_agent="UnknownAgent",
            action="test",
            payload={},
        )
        response = bridge.send_message(msg)

        assert response is None
        assert len(bridge._pending_messages) == 1

    def test_route_to_best_agent(self):
        """Test routing to best agent by capability"""
        bridge = A2ABridge()
        bridge.register_agent(
            AgentCapabilityDescriptor(
                "Coder1", [AgentCapability.CODE], "Coder 1", priority=1
            )
        )
        bridge.register_agent(
            AgentCapabilityDescriptor(
                "Coder2", [AgentCapability.CODE], "Coder 2", priority=5
            )
        )

        responses = []

        def handler(msg):
            responses.append(msg.to_agent)
            return None

        bridge.register_handler("Coder2", handler)

        msg = A2AMessage(
            message_id="msg_001",
            from_agent="Orchestrator",
            to_agent="",
            action="code",
            payload={},
        )
        bridge.route_to_best_agent(AgentCapability.CODE, msg)

        # Should route to Coder2 (higher priority)
        assert "Coder2" in responses

    def test_create_mcp_tool_response(self):
        """Test creating MCP tool response format"""
        bridge = A2ABridge()
        response = bridge.create_mcp_tool_response(
            agent_response="Task completed successfully",
            agent_name="Coder",
        )

        assert response["content"][0]["type"] == "text"
        assert "completed" in response["content"][0]["text"]
        assert response["metadata"]["agent"] == "Coder"

    def test_get_message_log(self):
        """Test getting message log"""
        bridge = A2ABridge()
        msg = A2AMessage(
            message_id="msg_001",
            from_agent="A",
            to_agent="B",
            action="test",
            payload={},
        )
        bridge.send_message(msg)

        log = bridge.get_message_log()
        assert len(log) == 1
        assert log[0]["id"] == "msg_001"


class TestGenerateMessageId:
    """Tests for message ID generator"""

    def test_generate_unique_ids(self):
        """Test that IDs are unique"""
        id1 = generate_message_id()
        id2 = generate_message_id()
        assert id1 != id2
        assert id1.startswith("msg_")
