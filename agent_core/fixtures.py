"""Synthetic persona fixtures. No real people, channels, domains, or secrets."""

from __future__ import annotations

from agent_core.schema import Evidence, GraphEdge, GraphNode, KnowledgeGraph, NodeType


def synthetic_graph(persona_id: str) -> KnowledgeGraph:
    builders = {
        "lena_kraus": _lena_kraus,
        "max_rieder": _max_rieder,
        "sara_neumann": _sara_neumann,
    }
    try:
        return builders[persona_id]()
    except KeyError as exc:
        known = ", ".join(sorted(builders))
        raise ValueError(f"Unknown synthetic persona '{persona_id}'. Known personas: {known}") from exc


def _graph(persona_id: str, nodes: list[GraphNode], edges: list[GraphEdge], evidence: list[Evidence]) -> KnowledgeGraph:
    return KnowledgeGraph(
        persona_id=persona_id,
        nodes={node.id: node for node in nodes},
        edges={edge.id: edge for edge in edges},
        evidence={item.id: item for item in evidence},
    )


def _lena_kraus() -> KnowledgeGraph:
    evidence = [
        Evidence(
            id="ev_lena_role",
            source="synthetic_public_company_page",
            description="Lena Kraus is CFO at Northstar Robotics.",
            confidence=0.95,
            tags=("role", "finance"),
        ),
        Evidence(
            id="ev_lena_audit",
            source="synthetic_public_event_agenda",
            description="Northstar Robotics is preparing for an audit readiness workshop.",
            confidence=0.86,
            tags=("audit", "finance", "vendor_risk"),
        ),
        Evidence(
            id="ev_lena_supplier",
            source="synthetic_public_procurement_panel",
            description="Lena discussed supplier risk and cashflow controls in a public panel.",
            confidence=0.82,
            tags=("supplier_risk", "cashflow", "vendor_risk"),
        ),
        Evidence(
            id="ev_lena_old_job_low_conf",
            source="synthetic_unverified_blog",
            description="Unverified claim about a past employer.",
            confidence=0.31,
            safe_to_use=False,
            tags=("old_job",),
        ),
    ]
    nodes = [
        GraphNode("person_lena", NodeType.PERSON, "Lena Kraus", {"persona": "synthetic"}),
        GraphNode("role_lena_cfo", NodeType.ROLE, "CFO", {"seniority": "executive"}),
        GraphNode("company_northstar", NodeType.COMPANY, "Northstar Robotics", {"domain": "northstar-robotics.test"}),
        GraphNode("interest_audit", NodeType.INTEREST, "audit readiness", {}),
        GraphNode("interest_supplier", NodeType.INTEREST, "supplier risk", {}),
        GraphNode("angle_vendor_review", NodeType.CONTACT_ANGLE, "vendor onboarding review", {}),
    ]
    edges = [
        GraphEdge("edge_lena_role", "person_lena", "role_lena_cfo", "has role", ("ev_lena_role",), 0.95, ("role", "finance")),
        GraphEdge("edge_lena_company", "role_lena_cfo", "company_northstar", "at company", ("ev_lena_role",), 0.95, ("role", "finance")),
        GraphEdge("edge_lena_audit", "company_northstar", "interest_audit", "is preparing", ("ev_lena_audit",), 0.86, ("audit", "vendor_risk")),
        GraphEdge("edge_lena_supplier", "person_lena", "interest_supplier", "publicly discusses", ("ev_lena_supplier",), 0.82, ("supplier_risk", "vendor_risk")),
        GraphEdge("edge_lena_angle", "interest_supplier", "angle_vendor_review", "supports angle", ("ev_lena_supplier",), 0.82, ("vendor_risk", "action")),
        GraphEdge("edge_lena_old_job", "person_lena", "company_northstar", "may have old job", ("ev_lena_old_job_low_conf",), 0.31, ("old_job",), False),
    ]
    return _graph("lena_kraus", nodes, edges, evidence)


def _max_rieder() -> KnowledgeGraph:
    evidence = [
        Evidence("ev_max_role", "synthetic_public_company_page", "Max Rieder is CTO at AtlasDev Tools.", 0.94, tags=("role", "technical")),
        Evidence("ev_max_ci", "synthetic_public_git_talk", "Max talks about CI/CD, security reviews, and developer experience.", 0.84, tags=("ci_cd", "security_review", "developer_experience")),
        Evidence("ev_max_blog", "synthetic_public_blog", "AtlasDev Tools is testing integration beta workflows.", 0.79, tags=("integration_beta", "developer_experience")),
    ]
    nodes = [
        GraphNode("person_max", NodeType.PERSON, "Max Rieder", {"persona": "synthetic"}),
        GraphNode("role_max_cto", NodeType.ROLE, "CTO", {}),
        GraphNode("company_atlas", NodeType.COMPANY, "AtlasDev Tools", {"domain": "atlasdev-tools.test"}),
        GraphNode("interest_ci", NodeType.INTEREST, "CI/CD security reviews", {}),
        GraphNode("angle_security_advisory", NodeType.CONTACT_ANGLE, "security advisory review", {}),
    ]
    edges = [
        GraphEdge("edge_max_role", "person_max", "role_max_cto", "has role", ("ev_max_role",), 0.94, ("role", "technical")),
        GraphEdge("edge_max_company", "role_max_cto", "company_atlas", "at company", ("ev_max_role",), 0.94, ("role", "technical")),
        GraphEdge("edge_max_ci", "person_max", "interest_ci", "publicly discusses", ("ev_max_ci",), 0.84, ("ci_cd", "security_review")),
        GraphEdge("edge_max_angle", "interest_ci", "angle_security_advisory", "supports angle", ("ev_max_blog",), 0.79, ("integration_beta", "action")),
    ]
    return _graph("max_rieder", nodes, edges, evidence)


def _sara_neumann() -> KnowledgeGraph:
    evidence = [
        Evidence("ev_sara_role", "synthetic_public_company_page", "Sara Neumann is Head of People at HelioCare.", 0.93, tags=("role", "people")),
        Evidence("ev_sara_onboarding", "synthetic_public_hr_panel", "Sara discusses onboarding and leadership training.", 0.85, tags=("onboarding", "leadership_training")),
        Evidence("ev_sara_retention", "synthetic_public_webinar", "HelioCare is improving employee retention programs.", 0.8, tags=("retention", "people")),
    ]
    nodes = [
        GraphNode("person_sara", NodeType.PERSON, "Sara Neumann", {"persona": "synthetic"}),
        GraphNode("role_sara_people", NodeType.ROLE, "Head of People", {}),
        GraphNode("company_heliocare", NodeType.COMPANY, "HelioCare", {"domain": "heliocare.test"}),
        GraphNode("interest_onboarding", NodeType.INTEREST, "onboarding", {}),
        GraphNode("angle_workshop", NodeType.CONTACT_ANGLE, "workshop calendar invite", {}),
    ]
    edges = [
        GraphEdge("edge_sara_role", "person_sara", "role_sara_people", "has role", ("ev_sara_role",), 0.93, ("role", "people")),
        GraphEdge("edge_sara_company", "role_sara_people", "company_heliocare", "at company", ("ev_sara_role",), 0.93, ("role", "people")),
        GraphEdge("edge_sara_onboarding", "person_sara", "interest_onboarding", "publicly discusses", ("ev_sara_onboarding",), 0.85, ("onboarding", "people")),
        GraphEdge("edge_sara_angle", "interest_onboarding", "angle_workshop", "supports angle", ("ev_sara_retention",), 0.8, ("leadership_training", "action")),
    ]
    return _graph("sara_neumann", nodes, edges, evidence)
