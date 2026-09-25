from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF

SH = "http://www.w3.org/ns/shacl#"
SH_NodeShape = URIRef(SH + "NodeShape")
SH_SPARQLTarget = URIRef(SH + "SPARQLTarget")
SH_target = URIRef(SH + "target")
SH_targetClass = URIRef(SH + "targetClass")
SH_select = URIRef(SH + "select")
SH_property = URIRef(SH + "property")
SH_path = URIRef(SH + "path")
SH_inversePath = URIRef(SH + "inversePath")
SH_class = URIRef(SH + "class")
SH_datatype = URIRef(SH + "datatype")
SH_node = URIRef(SH + "node")
SH_and = URIRef(SH + "and")
SH_or = URIRef(SH + "or")
SH_xone = URIRef(SH + "xone")
SH_not = URIRef(SH + "not")
SH_minCount = URIRef(SH + "minCount")
SH_maxCount = URIRef(SH + "maxCount")
SH_qualifiedValueShape = URIRef(SH + "qualifiedValueShape")
SH_qualifiedMinCount = URIRef(SH + "qualifiedMinCount")
SH_qualifiedMaxCount = URIRef(SH + "qualifiedMaxCount")
SH_minInclusive = URIRef(SH + "minInclusive")
SH_maxInclusive = URIRef(SH + "maxInclusive")
SH_minExclusive = URIRef(SH + "minExclusive")
SH_maxExclusive = URIRef(SH + "maxExclusive")
SH_hasValue = URIRef(SH + "hasValue")
SH_pattern = URIRef(SH + "pattern")
SH_uniqueLang = URIRef(SH + "uniqueLang")
SH_languageIn = URIRef(SH + "languageIn")
SH_equals = URIRef(SH + "equals")
SH_disjoint = URIRef(SH + "disjoint")
SH_lessThan = URIRef(SH + "lessThan")
SH_lessThanOrEquals = URIRef(SH + "lessThanOrEquals")
SH_nodeKind = URIRef(SH + "nodeKind")
SH_message = URIRef(SH + "message")


@dataclass
class DiagramNode:
    node_id: str
    label: str
    classes: list[str] = field(default_factory=list)
    uri: str | None = None


@dataclass
class DiagramBuilder:
    nodes: list[DiagramNode] = field(default_factory=list)
    edges: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    class_defs: list[str] = field(default_factory=list)

    def add_node(
        self,
        node_id: str,
        label: str,
        *classes: str,
        uri: str | None = None,
    ) -> str:
        self.nodes.append(DiagramNode(node_id, label, list(classes), uri))
        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        label: str | None = None,
        dashed: bool = False,
    ) -> None:
        edge = f"    {source} -.-> {target}" if dashed else f"    {source} --> {target}"
        if label:
            connector = "-.->|" if dashed else "-->|"
            edge = f"    {source} {connector}{self.safe_text(label, 80)}| {target}"
        self.edges.append(edge)

    def add_link(self, node_id: str, uri: str, tooltip: str = "Open ontology term") -> None:
        if uri.startswith(("http://", "https://")):
            safe_uri = uri.replace('"', "%22").replace("\\", "%5C")
            safe_tip = self.safe_text(tooltip, 80)
            # Mermaid click links require an explicitly permissive security level.
            self.links.append(
                f'    click {node_id} href "{safe_uri}" "{safe_tip}" _blank'
            )

    @staticmethod
    def safe_text(value: object, max_len: int = 120) -> str:
        """Sanitise text for Mermaid flowchart labels/edge labels."""
        text = str(value).replace("\r", " ").replace("\n", " ")
        text = html.escape(text, quote=True)
        text = re.sub(r"[|{}\[\]()]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_len]


class SHACLDiagramGenerator:
    """Generate a Mermaid flowchart representing SHACL applicability and logic.

    The renderer treats SHACL constraints as Boolean checks for visualisation purposes:
    - sh:target / sh:SPARQLTarget / sh:targetClass are the antecedent/applicability.
    - sh:property and logical constraints form the consequent/requirements.
    - AND: every child must succeed.
    - OR: one child must succeed; failure continues to the next alternative.
    - NOT: success/failure are inverted.

    The generated diagram is an explanatory view. It is not a replacement for a SHACL
    validator. The original SHACL remains the source of truth.
    """

    def __init__(self) -> None:
        self.counter = 0

    def _id(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}_{self.counter}"

    @staticmethod
    def _local_name(value: str | URIRef | Literal | BNode | None) -> str:
        if value is None or isinstance(value, BNode):
            return ""
        text = str(value)
        if "#" in text:
            text = text.rsplit("#", 1)[-1]
        elif "/" in text:
            text = text.rstrip("/").rsplit("/", 1)[-1]
        elif ":" in text:
            text = text.rsplit(":", 1)[-1]
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        return text.replace("_", " ").replace("-", " ").strip()

    def _display_value(self, graph: Graph, value: object) -> tuple[str, str | None]:
        """Return display text and, where possible, the underlying URI."""
        if isinstance(value, URIRef):
            return self._local_name(value), str(value)
        text = str(value)
        # Try to resolve simple QName values used inside SPARQL.
        if re.fullmatch(r"[A-Za-z_][\w.-]*:[\w.-]+", text):
            prefix, local = text.split(":", 1)
            for ns_prefix, namespace in graph.namespaces():
                if ns_prefix == prefix:
                    uri = str(namespace) + local
                    return local, uri
        return text, None

    def generate(self, shacl_text: str) -> str:
        graph = Graph()
        graph.parse(data=shacl_text, format="turtle")
        return self.generate_from_graph(graph)

    def generate_from_graph(self, graph: Graph) -> str:
        builder = DiagramBuilder()
        builder.class_defs = [
            "classDef antecedent fill:#E1F5FE,stroke:#1976D2,stroke-width:2px,color:#0D47A1;",
            "classDef consequent fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#7C2D00;",
            "classDef logic fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C;",
            "classDef check fill:#FFF8E1,stroke:#F9A825,stroke-width:1.5px,color:#5D4037;",
            "classDef outcome fill:#E8F5E9,stroke:#388E3C,stroke-width:2px,color:#1B5E20;",
            "classDef failure fill:#FFEBEE,stroke:#D32F2F,stroke-width:2px,color:#B71C1C;",
            "classDef scope fill:#ECEFF1,stroke:#607D8B,stroke-width:1.5px,color:#263238;",
            "classDef note fill:#F5F5F5,stroke:#757575,stroke-width:1px,color:#424242;",
        ]

        # SHACL NodeShapes may be named resources or blank nodes. Do not
        # discard blank-node shapes because generated SHACL commonly uses
        # an anonymous NodeShape such as: [] a sh:NodeShape ; ... .
        shapes = list(graph.subjects(RDF.type, SH_NodeShape))
        if not shapes:
            return self._empty_diagram("No sh:NodeShape found")

        for shape_index, shape in enumerate(shapes, start=1):
            self._render_rule(graph, shape, builder, shape_index)

        return self._render_mermaid(builder)

    def _render_rule(
        self,
        graph: Graph,
        shape: BNode | URIRef,
        builder: DiagramBuilder,
        shape_index: int,
    ) -> None:
        title = self._local_name(shape) or f"SHACL Rule {shape_index}"
        start = builder.add_node(
            self._id("rule"),
            title,
            "antecedent",
            uri=str(shape),
        )
        builder.add_link(start, str(shape), "Open SHACL shape")

        out_of_scope = builder.add_node(
            self._id("scope"),
            "Out of scope",
            "scope",
        )
        complies = builder.add_node(
            self._id("complies"),
            "Complies",
            "outcome",
        )
        fails = builder.add_node(
            self._id("fails"),
            "Does not comply",
            "failure",
        )

        requirement_summary = self._describe_requirements(graph, constraints=[])
        requirement_start = builder.add_node(
            self._id("requirements"),
            requirement_summary,
            "consequent",
        )

        antecedent_entry, antecedent_exit = self._render_antecedent(
            graph, shape, start, out_of_scope, builder
        )
        if antecedent_entry:
            builder.add_edge(start, antecedent_entry, "evaluate")
            if antecedent_exit:
                builder.add_edge(antecedent_exit, requirement_start, "YES")
        else:
            builder.add_edge(start, requirement_start, "applies")

        constraints = self._top_level_constraints(graph, shape)
        requirement_summary = self._describe_requirements(graph, constraints)
        # Update the previously-created node now that the actual SHACL constraints are known.
        for node in builder.nodes:
            if node.node_id == requirement_start:
                node.label = requirement_summary
                break

        if constraints:
            if len(constraints) == 1:
                requirement_entry = self._render_constraint(
                    graph,
                    constraints[0],
                    complies,
                    fails,
                    builder,
                )
            else:
                requirement_entry = self._render_and_group(
                    graph,
                    constraints,
                    complies,
                    fails,
                    builder,
                    label="AND",
                )
            builder.add_edge(requirement_start, requirement_entry, "evaluate")
        else:
            builder.add_edge(requirement_start, complies, "YES")
            builder.add_edge(requirement_start, fails, "NO")

    def _render_antecedent(
        self,
        graph: Graph,
        shape: URIRef,
        start: str,
        out_of_scope: str,
        builder: DiagramBuilder,
    ) -> tuple[str | None, str | None]:
        entries: list[tuple[str, str]] = []

        target = graph.value(shape, SH_target)
        if target and (target, RDF.type, SH_SPARQLTarget) in graph:
            query = graph.value(target, SH_select)
            conditions = self._extract_sparql_conditions(str(query or ""))
            if not conditions:
                node = builder.add_node(
                    self._id("sparql"),
                    "SPARQLTarget",
                    "antecedent",
                )
                entries.append((node, node))
            else:
                previous = None
                first = None
                for condition in conditions:
                    condition_label, condition_uri = self._format_sparql_condition(graph, condition)
                    node = builder.add_node(
                        self._id("target"),
                        f"SPARQLTarget\n{condition_label}",
                        "antecedent",
                        uri=condition_uri,
                    )
                    if condition_uri:
                        builder.add_link(node, condition_uri)
                    if first is None:
                        first = node
                    if previous:
                        builder.add_edge(previous, node, "YES")
                    builder.add_edge(node, out_of_scope, "NO")
                    previous = node
                entries.append((first, previous))
        elif target:
            node = builder.add_node(
                self._id("target"),
                "Target",
                "antecedent",
            )
            entries.append((node, node))
            builder.add_edge(node, out_of_scope, "NO")

        target_class = graph.value(shape, SH_targetClass)
        if target_class:
            label, uri = self._display_value(graph, target_class)
            node = builder.add_node(
                self._id("targetclass"),
                f"Target class?\n{label}",
                "antecedent",
                uri=uri,
            )
            if uri:
                builder.add_link(node, uri)
            builder.add_edge(node, out_of_scope, "NO")
            if entries:
                builder.add_edge(entries[-1][1], node, "YES")
                entries[-1] = (entries[-1][0], node)
            else:
                entries.append((node, node))

        if not entries:
            return None, None
        return entries[0][0], entries[-1][1]

    def _describe_requirements(
        self,
        graph: Graph,
        constraints: list[tuple[str, BNode | URIRef]],
    ) -> str:
        """Create a concise human-readable summary of the consequent.

        The summary is derived only from SHACL structure. It intentionally avoids
        presenting an inferred legal interpretation as if it were source text.
        """
        if not constraints:
            return "Requirements"

        descriptions: list[str] = []
        for kind, node in constraints:
            if kind == "property":
                descriptions.append(self._describe_constraint_node(graph, node))
            elif kind in {"and", "or", "xor", "not"}:
                descriptions.append(self._describe_logic_node(graph, kind, node))

        descriptions = [d for d in descriptions if d]
        if not descriptions:
            return "Requirements"

        # Multiple constraints attached directly to a shape are conjunctive in SHACL.
        # Individual logical constraints (e.g. sh:or) are already expanded inside
        # _describe_constraint_node, so they retain their own Boolean operator.
        summary = " AND ".join(descriptions)
        return "Requirement:\n" + summary

    def _describe_logic_node(
        self,
        graph: Graph,
        kind: str,
        node: BNode | URIRef,
    ) -> str:
        predicate = {
            "and": SH_and,
            "or": SH_or,
            "xor": SH_xone,
            "not": SH_not,
        }[kind]
        collection = graph.value(node, predicate)
        if kind == "not":
            child = graph.value(node, predicate)
            child_desc = self._describe_constraint_node(graph, child) if child else "constraint"
            return f"NOT ({child_desc})"
        if not collection:
            return kind.upper()
        children = [self._describe_constraint_node(graph, item) for item in graph.items(collection)]
        children = [item for item in children if item]
        if not children:
            return kind.upper()
        separator = f" {kind.upper()} "
        return separator.join(children)

    def _describe_constraint_node(
        self,
        graph: Graph,
        node: BNode | URIRef | None,
    ) -> str:
        if node is None:
            return "constraint"

        # A nested shape can contain one or more property shapes.
        nested_properties = list(graph.objects(node, SH_property))
        if nested_properties:
            descriptions = [self._describe_constraint_node(graph, item) for item in nested_properties]
            descriptions = [item for item in descriptions if item]
            if descriptions:
                if len(descriptions) == 1:
                    return descriptions[0]
                return " AND ".join(descriptions)

        for kind, predicate in (("or", SH_or), ("and", SH_and), ("xor", SH_xone), ("not", SH_not)):
            if graph.value(node, predicate) is not None:
                return self._describe_logic_node(graph, kind, node)

        path = graph.value(node, SH_path)
        facets = self._constraint_facets(graph, node)

        if path is None:
            cls = graph.value(node, SH_class)
            if cls is not None:
                return f"{self._local_name(cls)}"
            value = graph.value(node, SH_hasValue)
            if value is not None:
                return f"value = {self._display_value(graph, value)[0]}"
            datatype = graph.value(node, SH_datatype)
            if datatype is not None:
                return f"datatype = {self._local_name(datatype)}"
            return "constraint"

        path_label, _ = self._describe_path(graph, path)
        if facets:
            return f"{path_label} ({', '.join(facets[:3])})"
        return path_label

    def _top_level_constraints(self, graph: Graph, shape: URIRef) -> list[tuple[str, BNode | URIRef]]:
        constraints: list[tuple[str, BNode | URIRef]] = []
        for prop in graph.objects(shape, SH_property):
            constraints.append(("property", prop))
        for predicate, label in (
            (SH_and, "AND"),
            (SH_or, "OR"),
            (SH_xone, "XOR"),
            (SH_not, "NOT"),
        ):
            if graph.value(shape, predicate):
                constraints.append((label.lower(), shape))
        return constraints

    def _render_and_group(
        self,
        graph: Graph,
        constraints: list[tuple[str, BNode | URIRef]],
        on_success: str,
        on_failure: str,
        builder: DiagramBuilder,
        label: str = "AND",
    ) -> str:
        # All top-level constraints on a NodeShape are conjunctive.
        gate = builder.add_node(self._id("and"), label, "logic")
        next_entry = on_success
        for constraint in reversed(constraints):
            next_entry = self._render_constraint(
                graph, constraint, next_entry, on_failure, builder
            )
        builder.add_edge(gate, next_entry, "evaluate")
        return gate

    def _render_constraint(
        self,
        graph: Graph,
        constraint: tuple[str, BNode | URIRef],
        on_success: str,
        on_failure: str,
        builder: DiagramBuilder,
    ) -> str:
        kind, node = constraint

        # Nested SHACL node expressions may contain property shapes even though the
        # node itself has no sh:path. This occurs, for example, in sh:or lists such
        # as: [ sh:property [ sh:path ... ; sh:class ... ] ] . Render those
        # properties recursively instead of falling back to a generic "Constraint".
        if kind == "constraint":
            nested_properties = list(graph.objects(node, SH_property))
            if nested_properties:
                nested_constraints = [("property", item) for item in nested_properties]
                if len(nested_constraints) == 1:
                    return self._render_constraint(
                        graph,
                        nested_constraints[0],
                        on_success,
                        on_failure,
                        builder,
                    )
                return self._render_and_group(
                    graph,
                    nested_constraints,
                    on_success,
                    on_failure,
                    builder,
                    label="AND",
                )

            for nested_kind, predicate in (("and", SH_and), ("or", SH_or), ("xor", SH_xone), ("not", SH_not)):
                if graph.value(node, predicate) is not None:
                    return self._render_constraint(
                        graph,
                        (nested_kind, node),
                        on_success,
                        on_failure,
                        builder,
                    )

        if kind in {"property", "and", "or", "xor", "not"}:
            # Logical constraint attached to this node.
            if kind == "property":
                logical_predicates = (SH_and, SH_or, SH_xone, SH_not)
                has_logic = any(graph.value(node, predicate) for predicate in logical_predicates)
                if has_logic:
                    # The property path/cardinality part is the first visual check;
                    # the logical value constraint is then evaluated on the YES path.
                    property_entry, property_outcome = self._render_property_base(
                        graph, node, on_failure, builder
                    )
                    logic_entries: list[str] = []
                    if graph.value(node, SH_and):
                        logic_entries.append(("and", node))
                    if graph.value(node, SH_or):
                        logic_entries.append(("or", node))
                    if graph.value(node, SH_xone):
                        logic_entries.append(("xor", node))
                    if graph.value(node, SH_not):
                        logic_entries.append(("not", node))
                    next_entry = on_success
                    for logic_constraint in reversed(logic_entries):
                        next_entry = self._render_constraint(
                            graph, logic_constraint, next_entry, on_failure, builder
                        )
                    builder.add_edge(property_outcome, next_entry, "YES")
                    return property_entry
            elif kind == "and":
                collection = graph.value(node, SH_and)
                children = [("constraint", item) for item in graph.items(collection)] if collection else []
                return self._render_logic_group(
                    graph, "AND", children, on_success, on_failure, builder
                )
            elif kind == "or":
                collection = graph.value(node, SH_or)
                children = [("constraint", item) for item in graph.items(collection)] if collection else []
                return self._render_logic_group(
                    graph, "OR", children, on_success, on_failure, builder
                )
            elif kind == "xor":
                collection = graph.value(node, SH_xone)
                children = [("constraint", item) for item in graph.items(collection)] if collection else []
                return self._render_logic_group(
                    graph, "XOR", children, on_success, on_failure, builder
                )
            elif kind == "not":
                child = graph.value(node, SH_not)
                gate = builder.add_node(self._id("not"), "NOT", "logic")
                child_entry = self._render_constraint(
                    graph,
                    ("constraint", child),
                    on_failure,
                    on_success,
                    builder,
                ) if child else gate
                builder.add_edge(gate, child_entry, "evaluate")
                return gate

        return self._render_leaf(graph, node, on_success, on_failure, builder)

    def _render_logic_group(
        self,
        graph: Graph,
        logic_label: str,
        children: list[tuple[str, BNode | URIRef]],
        on_success: str,
        on_failure: str,
        builder: DiagramBuilder,
    ) -> str:
        gate = builder.add_node(self._id("logic"), logic_label, "logic")
        if not children:
            builder.add_edge(gate, on_success, "YES")
            return gate

        if logic_label == "AND":
            next_entry = on_success
            for child in reversed(children):
                next_entry = self._render_constraint(
                    graph, child, next_entry, on_failure, builder
                )
            builder.add_edge(gate, next_entry, "evaluate")
            return gate

        if logic_label == "OR":
            next_entry = on_failure
            for child in reversed(children):
                next_entry = self._render_constraint(
                    graph, child, on_success, next_entry, builder
                )
            builder.add_edge(gate, next_entry, "try alternatives")
            return gate

        # XOR is approximated visually as an exclusive choice. The underlying SHACL
        # validator remains authoritative for the exact semantics.
        next_entry = on_failure
        for child in reversed(children):
            next_entry = self._render_constraint(
                graph, child, on_success, next_entry, builder
            )
        builder.add_edge(gate, next_entry, "evaluate")
        return gate

    def _render_property_base(
        self,
        graph: Graph,
        node: BNode | URIRef,
        on_failure: str,
        builder: DiagramBuilder,
    ) -> tuple[str, str]:
        """Render the non-logical part of a property shape.

        Returns the entry node and the node from which a logical value constraint
        can continue.
        """
        path = graph.value(node, SH_path)
        path_label, path_uri = self._describe_path(graph, path)
        facets = self._constraint_facets(graph, node)
        decision_id = builder.add_node(
            self._id("check"),
            path_label + (("\n" + "\n".join(facets[:6])) if facets else ""),
            "check",
            uri=path_uri,
        )
        if path_uri:
            builder.add_link(decision_id, path_uri)
        builder.add_edge(decision_id, on_failure, "NO")
        return decision_id, decision_id

    def _render_leaf(
        self,
        graph: Graph,
        node: BNode | URIRef,
        on_success: str,
        on_failure: str,
        builder: DiagramBuilder,
    ) -> str:
        path = graph.value(node, SH_path)
        path_label, path_uri = self._describe_path(graph, path)
        facets = self._constraint_facets(graph, node)

        # When a blank node only contains a class/hasValue/etc., render it as a direct
        # decision rather than pretending it is a property path.
        if path is None:
            if graph.value(node, SH_class):
                cls = graph.value(node, SH_class)
                label, uri = self._display_value(graph, cls)
                node_label = f"Is a {label}?"
                uri = uri or path_uri
            elif graph.value(node, SH_hasValue) is not None:
                value = graph.value(node, SH_hasValue)
                node_label = f"Value = {value}?"
                uri = None
            elif graph.value(node, SH_datatype):
                value = graph.value(node, SH_datatype)
                label, uri = self._display_value(graph, value)
                node_label = f"Datatype = {label}?"
            else:
                node_label = "Constraint"
                uri = None
        else:
            node_label = path_label
            uri = path_uri

        if facets:
            # Avoid repeating Type when the node itself is already presented as a class.
            if node_label.startswith("Is a "):
                facets = [f for f in facets if not f.startswith("Type:")]
            if facets:
                node_label += "\n" + "\n".join(facets[:6])

        decision_id = builder.add_node(
            self._id("check"),
            node_label,
            "check" if path is not None else "consequent",
            uri=uri,
        )
        if uri:
            builder.add_link(decision_id, uri)

        nested = graph.value(node, SH_node)
        qualified = graph.value(node, SH_qualifiedValueShape)

        if nested:
            nested_entry = self._render_constraint(
                graph,
                ("constraint", nested),
                on_success,
                on_failure,
                builder,
            )
            builder.add_edge(decision_id, nested_entry, "verify")
            return decision_id

        if qualified:
            qualified_entry = self._render_constraint(
                graph,
                ("constraint", qualified),
                on_success,
                on_failure,
                builder,
            )
            builder.add_edge(decision_id, qualified_entry, "verify qualified values")
            return decision_id

        builder.add_edge(decision_id, on_success, "YES")
        builder.add_edge(decision_id, on_failure, "NO")
        return decision_id

    def _constraint_summary(self, graph: Graph, node: BNode | URIRef) -> str:
        """Create a compact semantic summary for a SHACL property/value constraint."""
        path = graph.value(node, SH_path)
        facets = self._constraint_facets(graph, node)

        if path is None:
            cls = graph.value(node, SH_class)
            if cls is not None:
                return self._local_name(cls)
            if (value := graph.value(node, SH_hasValue)) is not None:
                text, _ = self._display_value(graph, value)
                return f"value = {text}"
            if (value := graph.value(node, SH_datatype)) is not None:
                return f"datatype = {self._local_name(value)}"
            return "constraint"

        path_label, _ = self._describe_path(graph, path)
        details = []
        if (value := graph.value(node, SH_class)) is not None:
            details.append(f"Type: {self._local_name(value)}")
        details.extend(f for f in facets if not f.startswith("Type:"))
        if details:
            return f"{path_label} ({', '.join(details[:3])})"
        return path_label

    def _constraint_facets(self, graph: Graph, node: BNode | URIRef) -> list[str]:
        facets: list[str] = []
        if (value := graph.value(node, SH_class)) is not None:
            facets.append(f"Type: {self._local_name(value)}")
        if (value := graph.value(node, SH_datatype)) is not None:
            facets.append(f"Datatype: {self._local_name(value)}")
        for predicate, prefix in (
            (SH_minCount, "Min count"),
            (SH_maxCount, "Max count"),
            (SH_qualifiedMinCount, "Qualified min count"),
            (SH_qualifiedMaxCount, "Qualified max count"),
        ):
            if (value := graph.value(node, predicate)) is not None:
                facets.append(f"{prefix}: {value}")
        for predicate, symbol in (
            (SH_minInclusive, "≥"),
            (SH_maxInclusive, "≤"),
            (SH_minExclusive, ">"),
            (SH_maxExclusive, "<"),
            (SH_equals, "="),
            (SH_disjoint, "≠"),
            (SH_lessThan, "<"),
            (SH_lessThanOrEquals, "≤"),
        ):
            if (value := graph.value(node, predicate)) is not None:
                text, _ = self._display_value(graph, value)
                facets.append(f"{symbol} {text}")
        if (value := graph.value(node, SH_hasValue)) is not None:
            text, _ = self._display_value(graph, value)
            facets.append(f"Value: {text}")
        if (value := graph.value(node, SH_nodeKind)) is not None:
            facets.append(f"Node kind: {self._local_name(value)}")
        if (value := graph.value(node, SH_pattern)) is not None:
            facets.append(f"Pattern: {value}")
        if (value := graph.value(node, SH_uniqueLang)) is not None:
            facets.append(f"Unique language: {value}")
        return facets

    def _describe_path(
        self,
        graph: Graph,
        path: BNode | URIRef | None,
    ) -> tuple[str, str | None]:
        if path is None:
            return "Constraint", None
        inverse = graph.value(path, SH_inversePath)
        if inverse:
            return f"Inverse of {self._local_name(inverse)}", str(inverse)
        if isinstance(path, URIRef):
            return self._local_name(path), str(path)
        return "Complex property path", None

    @staticmethod
    def _extract_sparql_conditions(query: str) -> list[str]:
        """Extract common WHERE/FILTER conditions for visualisation.

        This intentionally supports the common SHACL SPARQL target patterns used by
        the Requirement Generator. It does not attempt to parse arbitrary SPARQL.
        """
        query = re.sub(r"#.*", "", query)
        conditions: list[str] = []

        for match in re.finditer(
            r"\?(?:this|target|x)\s+a\s+([A-Za-z_][\w.-]*:[\w.-]+)",
            query,
            re.IGNORECASE,
        ):
            conditions.append(f"is {match.group(1)}")

        # Simple triple patterns. Remove FILTER EXISTS blocks first so the same
        # triple is not rendered twice.
        query_without_exists = re.sub(
            r"FILTER\s+EXISTS\s*\{.*?\}",
            "",
            query,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in re.finditer(
            r"\?(?:this|target|x)\s+([A-Za-z_][\w.-]*:[\w.-]+)\s+([^.;{}]+?)\s*\.",
            query_without_exists,
        ):
            predicate = match.group(1)
            obj = re.sub(r"\s+", " ", match.group(2).strip())
            if predicate != "a":
                conditions.append(f"{predicate.split(':')[-1]} = {obj}")

        for match in re.finditer(
            r"FILTER\s+EXISTS\s*\{(.*?)\}",
            query,
            re.IGNORECASE | re.DOTALL,
        ):
            expression = re.sub(r"\s+", " ", match.group(1).strip())
            conditions.append(f"exists: {expression}")

        for match in re.finditer(
            r"FILTER\s*\((.*?)\)",
            query,
            re.IGNORECASE | re.DOTALL,
        ):
            expression = re.sub(r"\s+", " ", match.group(1).strip())
            conditions.append(f"filter: {expression}")

        # Deduplicate and cap the visual complexity.
        return list(dict.fromkeys(conditions))[:8]

    def _format_sparql_condition(
        self,
        graph: Graph,
        condition: str,
    ) -> tuple[str, str | None]:
        """Format a target condition and resolve its first ontology QName when possible."""
        qnames = re.findall(r"[A-Za-z_][\w.-]*:[A-Za-z_][\w.-]*", condition)
        uri = None
        for qname in qnames:
            prefix, local = qname.split(":", 1)
            for ns_prefix, namespace in graph.namespaces():
                if ns_prefix == prefix:
                    uri = str(namespace) + local
                    break
            if uri:
                break

        label = condition
        if uri:
            # Replace the QName with a more readable local-name representation.
            for qname in qnames:
                label = label.replace(qname, self._local_name(uri), 1)
                break
        return label, uri

    @staticmethod
    def _empty_diagram(message: str) -> str:
        safe = DiagramBuilder.safe_text(message)
        return (
            "flowchart TD\n"
            f'    A["{safe}"]:::note\n'
            "    classDef note fill:#F5F5F5,stroke:#757575,stroke-width:1px,color:#424242;"
        )

    def _render_mermaid(self, builder: DiagramBuilder) -> str:
        lines = ["flowchart TD", "    %% FireBIM SHACL visualisation"]
        lines += [
            "    LegendAnte[\"Antecedent / applicability\"]:::antecedent",
            "    LegendCons[\"Consequent / requirements\"]:::consequent",
            "    LegendLogic[\"Logical operator\"]:::logic",
            "    LegendResult[\"Compliance outcome\"]:::outcome",
            "    LegendFail[\"Non-compliance outcome\"]:::failure",
        ]

        for node in builder.nodes:
            label = html.escape(node.label, quote=True).replace("\n", "<br/>")
            label = label.replace('"', "&quot;")
            if "logic" in node.classes:
                shape = f'{{"{label}"}}'
            elif node.node_id.startswith("rule_"):
                shape = f'(("{label}"))'
            else:
                shape = f'["{label}"]'
            lines.append(f"    {node.node_id}{shape}")
            for class_name in node.classes:
                lines.append(f"    class {node.node_id} {class_name}")

        lines.extend(builder.edges)
        lines.extend(builder.links)
        lines.extend(builder.class_defs)
        return "\n".join(lines)


def render_mermaid_html(mermaid_code: str, height: int = 760) -> str:
    """Return self-contained HTML used by Streamlit's HTML component renderer.

    Mermaid is loaded as an ES module inside the iframe. The module import,
    Mermaid initialisation, rendering, and SVG insertion are all covered by the
    same error handler so a failed CDN load cannot silently leave an empty div.
    """
    source_json = json.dumps(mermaid_code).replace("</", "<\\/")
    mermaid_version = "11.17.2"
    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background: transparent;
    }}
    body {{
      min-height: {height}px;
      overflow: auto;
      font-family: sans-serif;
    }}
    #firebim-diagram {{
      width: 100%;
      min-height: {max(height - 20, 300)}px;
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }}
    .error {{
      width: 100%;
      box-sizing: border-box;
      white-space: pre-wrap;
      color: #b71c1c;
      background: #ffebee;
      border: 1px solid #ef9a9a;
      border-radius: 4px;
      font-family: monospace;
      padding: 1rem;
    }}
  </style>
</head>
<body>
  <div id="firebim-diagram"></div>
  <script type="module">
    const source = {source_json};
    const target = document.getElementById("firebim-diagram");

    const showError = (error) => {{
      const message = String(error?.stack || error?.message || error);
      target.innerHTML = "<div class='error'>Mermaid rendering error:\\n\\n" +
        message.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") +
        "</div>";
      console.error("FireBIM Mermaid rendering error", error);
    }};

    try {{
      const {{ default: mermaid }} = await import(
        "https://cdn.jsdelivr.net/npm/mermaid@{mermaid_version}/dist/mermaid.esm.min.mjs"
      );

      mermaid.initialize({{
        startOnLoad: false,
        securityLevel: "loose",
        theme: "default",
        htmlLabels: true,
        flowchart: {{
          useMaxWidth: true,
          curve: "basis"
        }}
      }});

      const {{ svg, bindFunctions }} = await mermaid.render(
        "firebimRuleDiagram",
        source
      );

      // Preserve Mermaid's clickable links when the SVG is embedded by Streamlit.
      if (svg.includes("<svg ") && !svg.includes("xmlns:xlink=")) {{
        target.innerHTML = svg.replace(
          "<svg ",
          '<svg xmlns:xlink="http://www.w3.org/1999/xlink" '
        );
      }} else {{
        target.innerHTML = svg;
      }}

      if (bindFunctions) bindFunctions(target);
    }} catch (error) {{
      showError(error);
    }}
  </script>
</body>
</html>
"""
