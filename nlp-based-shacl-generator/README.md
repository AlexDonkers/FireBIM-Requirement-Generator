# NLP-based SHACL Generator

The NLP-based SHACL Generator is a lightweight prototype for transforming a regulatory sentence into an initial SHACL representation. It uses linguistic analysis to identify the main subject, relation, and object of a sentence and converts these components into RDF classes and properties.

The implementation is based on **spaCy** and represents the earlier NLP-based rule generation approach described in the FireBIM deliverables.

## Purpose

The tool provides a deterministic NLP approach for simple regulatory statements. It is intended as a prototype and as a transparent example of how linguistic structure can be mapped to a SHACL constraint.

## Input

The input is a regulatory sentence, for example:

```text
An occupied area is located in a protected sub-fire compartment.
```

The supplied prototype currently uses the spaCy `en_core_web_sm` language model.

## Processing

The sentence is processed using dependency parsing. The implementation identifies:

1. the root of the sentence;
2. the nominal subject and its modifiers;
3. noun compounds and adjectival modifiers;
4. other noun elements associated with the main relation.

These elements are used to construct FireBIM-style class and property identifiers.

## Output

The prototype generates a Turtle-formatted SHACL `NodeShape` containing a target class and a property constraint. A resulting structure follows this general pattern:

```turtle
:SHACLtemplate_01
    a sh:NodeShape ;
    sh:targetClass fbo:SubjectClass ;
    sh:property [
        sh:path fbo:relation ;
        sh:class fbo:ObjectClass ;
    ] .
```

## Files

- `NLP-based-regulation-converter.py` – supplied Python implementation of the prototype.

## Limitations

The prototype is intended for relatively simple relational statements. It does not provide the intermediate ontology mapping, FOL representation, structured LLM generation, or advanced SHACL modelling of the Neuro-symbolic Requirement Generator.

## Relation to D2.4

See **ITEA4 22003 FireBIM D2.4 – Requirement Generator**, section on the NLP-based SHACL generator.

[Back to the FireBIM Requirement Generator →](../)
