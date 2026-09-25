from requirement_generator.visualisation.mermaid import SHACLDiagramGenerator


def test_generates_shacl_mermaid_diagram():
    ttl = '''
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix fbo: <http://example.org/fbo#> .
    @prefix bot: <https://w3id.org/bot#> .

    fbo:EnclosedSpaceShape a sh:NodeShape ;
        sh:target [
            a sh:SPARQLTarget ;
            sh:select "SELECT ?this WHERE { ?this a fbo:Space . FILTER EXISTS { ?this fbo:isEnclosedSpace true . } }"
        ] ;
        sh:property [
            sh:path [ sh:inversePath bot:containsZone ] ;
            sh:or (
                [ sh:class fbo:FireCompartment ]
                [ sh:class fbo:ToiletSpace ]
            )
        ] .
    '''

    mermaid = SHACLDiagramGenerator().generate(ttl)

    assert "flowchart TD" in mermaid
    assert "SPARQLTarget" in mermaid
    assert "OR" in mermaid
    assert "FireCompartment" in mermaid
    assert "ToiletSpace" in mermaid
    assert "Complies" in mermaid
    assert "Does not comply" in mermaid
    assert "click" in mermaid


def test_mermaid_click_syntax_places_tooltip_before_target():
    ttl = '''
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix fbo: <http://example.org/fbo#> .
    fbo:Shape a sh:NodeShape ;
        sh:targetClass fbo:Space ;
        sh:property [
            sh:path fbo:hasFireCompartment ;
            sh:class fbo:FireCompartment ;
        ] .
    '''
    mermaid = SHACLDiagramGenerator().generate(ttl)
    assert ' href "http://example.org/fbo#Shape" "Open SHACL shape" _blank' in mermaid
    assert ' _blank "Open SHACL shape"' not in mermaid



def test_blank_node_shacl_shape_is_rendered():
    ttl = '''
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix fbo: <http://example.org/fbo#> .

    [ a sh:NodeShape ;
      sh:targetClass fbo:Space ;
      sh:property [
          sh:path fbo:isContainedIn ;
          sh:class fbo:FireCompartment ;
          sh:minCount 1
      ]
    ] .
    '''
    mermaid = SHACLDiagramGenerator().generate(ttl)
    assert "No sh:NodeShape found" not in mermaid
    assert "Target class" in mermaid
    assert "Fire Compartment" in mermaid or "FireCompartment" in mermaid


def test_html_renderer_patches_xlink_namespace():
    from requirement_generator.visualisation.mermaid import render_mermaid_html

    html = render_mermaid_html("flowchart TD\n    A[Shape]\n    click A href \"http://example.org/shape\" \"Open\" _blank")
    assert "xmlns:xlink=\"http://www.w3.org/1999/xlink\"" in html
    assert "svg.includes(\"xmlns:xlink=\")" in html



def test_blank_node_shape_gets_generic_rule_title():
    ttl = '''
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix fbo: <http://example.org/fbo#> .
    [ a sh:NodeShape ; sh:targetClass fbo:Space ] .
    '''
    mermaid = SHACLDiagramGenerator().generate(ttl)
    assert "SHACL Rule 1" in mermaid
