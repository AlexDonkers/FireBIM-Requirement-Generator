from __future__ import annotations

from ..models import OntologyMatch


SHACL_TEMPLATES = r'''
TEMPLATE 1: Applicability-as-Target (SPARQL Target Pattern)
Use this when the rule applies only to a specific subset defined by multiple conditions.
Pattern:
<ShapeName> a sh:NodeShape ;
    sh:target [
        a sh:SPARQLTarget ;
        sh:select \"\"\"
            SELECT ?this WHERE {
                ?this a fbo:Class .
                ?this fbo:hasProperty ?value .
                # The 'left side' of the FOL goes here to filter ?this
            }
        \"\"\" ;
    ] ;
    sh:property [ ... ] . The 'right side' (requirement) goes here.

TEMPLATE 2: Inverse Relationship Pattern
Use this when checking a parent container from the perspective of a child element.
Pattern:
sh:path [ sh:inversePath bot:containsElement ] ;
sh:class fbo:ParentClass ;

TEMPLATE 3: Cardinality & Existence
Use to check if a specific number of relationships exist.
- minCount: at least X
- maxCount: at most X
Pattern:
sh:property [
    sh:path <property_uri> ;
    sh:minCount 1 ;  # Required
    sh:maxCount 1 ;  # Unique
] .

TEMPLATE 4: Topological Containment (BOT)
- Element-to-Zone: Use sh:path bot:hasElement or its inverse sh:path [ sh:inversePath bot:hasElement ] .
- Zone-to-Zone: Use sh:path bot:containsZone or its inverse sh:path [ sh:inversePath bot:containsZone ] .
Pattern:
sh:property [
    sh:path [ sh:inversePath bot:hasElement ] ; # If checking element context
    sh:class bot:Zone ;
] .

TEMPLATE 5: Datatype Property Constraints (Comparative)
Use for numerical ratings (Fire Resistance, Area, Height).
Pattern:
sh:property [
    sh:path fbo:fireResistanceRating ;
    sh:datatype xsd:integer ;
    sh:minInclusive 60 ; # Greater than or equal to
    sh:maxInclusive 120 ; # Less than or equal to
] .

TEMPLATE 6: Object Property Relationships
Use for specific logical links between elements (e.g. 'connected to', 'equipped with').
Pattern:
sh:property [
    sh:path fbo:hasElement ;
    sh:class fbo:FireExtinguisher ;
] .

TEMPLATE 7: Multiple Logical Rules (AND/OR Logic)
Use when the 'Then' side of the FOL has multiple requirements.
Pattern:
sh:and (
    [ sh:property [ ...rule 1... ] ]
    [ sh:property [ ...rule 2... ] ]
) .

TEMPLATE 8: Requirement with Exceptions (OR Pattern)
Use this when a rule has a general obligation but lists specific exclusions.

<ShapeName> a sh:NodeShape ;
    sh:target [
        a sh:SPARQLTarget ;
        sh:select \"\"\"
            SELECT ?this WHERE {
                # [ANTECEDENT LOGIC]
            }
        \"\"\" ;
    ] ;
    sh:or (
        The Requirement
        [
            sh:property [
                sh:path bot:containsZone ; # Example path
                sh:class fbo:FireCompartment ;
            ]
        ]
        The Exceptions
        [
            sh:class fbo:ToiletRoom
        ]
        [
            sh:class fbo:BathRoom
        ]
    ) .

TEMPLATE 9: Property relationship vs Class type
<ShapeName> a sh:NodeShape ;
    sh:target [
        a sh:SPARQLTarget ;
        sh:select \"\"\"
            SELECT ?this WHERE {
                ?this a fbo:SomeClass .
                # Data property check:
                ?this fbo:isEnclosedSpace true .
                # Object property check:
                ?this fbo:hasRelationship ?otherObject .
            }
        \"\"\" ;
    ] .

Template 10: MaxCount
<ShapeName> a sh:NodeShape ;
    sh:targetClass fbo:FireCompartment ;
    1. THE COUNT RULE
    sh:property [
        sh:path bot:containsZone  ;
        sh:qualifiedValueShape [ sh:class fbo:Space ] ;
        sh:qualifiedMaxCount 4 ;
        sh:message "A fire compartment may contain a maximum of 4 Spaces."@en ;
    ] .

Template 11: SumAreas
<ShapeName> a sh:NodeShape ;
    sh:targetClass fbo:FireCompartment ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "The total {?propertyName} is {?totalValue}, which exceeds the limit of <LimitValue>." ;
        sh:select \"\"\"
            SELECT ?this (SUM(?value) AS ?totalValue)
            WHERE {
                ?this <path_to_elements> ?element .
                ?element a <TargetClass> .
                ?element <property_to_sum> ?value .
            }
            GROUP BY ?this
            HAVING (SUM(?value) > <LimitValue>)
        \"\"\" ;
    ] .
'''


def build_prompt(
    statement: str,
    features: list[str],
    matches: list[OntologyMatch],
    topology_terms: str = "",
) -> str:
    ontology_context = "\n".join(
        f"- {m.label} | <{m.uri}> | similarity={m.similarity}"
        for m in matches
    )

    return f"""
You are a specialist in Semantic Web technologies and building regulations.
Generate a machine-interpretable representation of the regulatory statement below.

## REGULATORY TEXT
{statement}

## EXTRACTED FEATURES
{', '.join(features)}

## RELEVANT ONTOLOGY CONTEXT
{ontology_context}

## ADDITIONAL TOPOLOGY ONTOLOGY CONTEXT
{topology_terms or '(none supplied)'}

## SHACL PATTERNS
{SHACL_TEMPLATES}

## TASK
1. Create a mapping table from concepts in the statement to ontology URIs.
2. Formalise the explicit regulatory logic in First-Order Logic (FOL).
3. Transform that FOL into a Turtle-formatted SHACL shape.

## CONSTRAINTS
- Only use classes and properties present in the supplied ontology context when possible.
- If a concept cannot be mapped to supplied ontology terms, use the FireBIM extension namespace:
  <http://www.firebim.org/ontologies/fbo-ext#>
- Check property directionality carefully.
- Classes use UpperCamelCase and properties use lowerCamelCase.
- Prefer the mapped ontology terms in the FOL.
- The antecedent (left side) of the FOL implication represents applicability and should normally be implemented through a SHACL SPARQL target.
- The consequent (right side) represents the requirement and should be represented by SHACL constraints.
- Preserve explicit exceptions and alternatives.
- Return valid Turtle in the SHACL field.
- Do not invent regulation content.

Return exactly the requested structured fields: mapping_table, fol, shacl.
""".strip()
