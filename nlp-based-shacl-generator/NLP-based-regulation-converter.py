import spacy 
from spacy import displacy
from spacy.tokens import Span
import time

nlp = spacy.load("en_core_web_sm")
doc = nlp("An occupied area is located in a protected sub-fire compartment.") 

# "Material applied to the inside of a shaft or a duct adjacent to more than one fire compartment or sub-fire compartment with an internal cross-section greater than 0.015 m2, complies with fire class A2, determined in accordance with NEN-EN 13501-1"
# "An occupied area is located in a protected sub-fire compartment."
# "A road tunnel tube with a length of more than 250 m is located in a fire compartment."


### Print statements

for token in doc:
    print("tokens: " +token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.shape_, token.is_alpha, token.is_stop, [child for child in token.children])

for chunk in doc.noun_chunks:
    print("chunks: " +chunk.text, chunk.root.text, chunk.root.dep_, chunk.root.head.text)

for ent in doc.ents:
    print("ents: " + ent.text, ent.start_char, ent.end_char, ent.label_)


### Display

displacy.serve(doc, style='dep')
displacy.serve(doc, style="ent")  # there's some good visualization options at https://spacy.io/usage/visualizers
displacy.serve(doc, style="span")

#### Graph creation

for root in doc:
    if root.dep_ == 'ROOT':                                     # Step 1: Find the ROOT
        print('ROOT: '+str(root))
        
        children = [child for child in root.children]           # Step 2: Find the children of the ROOT

        for nsubj_child in children:                            # Step 3: Find the child that is 'nsubj' or 'nsubjpass'
            for token in doc:
                if nsubj_child == token:
                    if nsubj_child.dep_ in ('nsubj', 'nsubjpass'):
                        print('nsubj or nsubjpass: '+str(nsubj_child))

                        nsubj_children = [child for child in nsubj_child.children]          # Step 4: Find the 'compounds' and 'amods' of the 'nsubj' or 'nsubjpass'
                        compound_or_amod_string = ""                                        # Step 4.1: Initialize an empty string
                        for compound_or_amod in nsubj_children:
                            if compound_or_amod.dep_ in ('amod','compound'):
                                compound_or_amod_string += compound_or_amod.text.title()    # Step 4.2: Append all amods and compounds to this string
                                print(compound_or_amod_string)
                                                            
                            print('fbo:'+compound_or_amod_string+str(nsubj_child).title())      # Step 4.3: Create a firebim class
                            print('fbo:'+compound_or_amod_string+str(nsubj_child).title()+' rdfs:SubClassOf fbo:'+str(nsubj_child).title())       # Step 4.4: Create subclass structure
                            var_s = 'fbo:'+compound_or_amod_string+str(nsubj_child).title()

        for root_noun_chunk in doc.noun_chunks:                     # Step 5: Find the noun chunk around the 'ROOT', if this exists
            if root in root_noun_chunk:
                print('fbo:'+str(root_noun_chunk).replace(" ","").replace(".",""))
                var_p = 'fbo:'+str(root)
            else:
                print('fbo:'+str(root))
                var_p = 'fbo:'+str(root)

        for noun_child in children:                                                             # Step 6: Find the other 'noun child' of the ROOT or the 'noun child' of children of the ROOT
            if noun_child.pos_ == 'NOUN' and noun_child.dep_ not in ('nsubj','nsubjpass'):
                print('NOUN child: '+str(noun_child))
            else: 
                for non_noun_child in children:
                    if non_noun_child.dep_ not in ('nsubj', 'nsubjpass'):
                        non_noun_child_children = [child for child in non_noun_child.children]
                        for non_noun_child_child in non_noun_child_children:
                            if non_noun_child_child.pos_ == 'NOUN':
                                non_noun_child_child = non_noun_child_child                     
        print('NOUN child: '+str(non_noun_child_child))

        non_noun_child_child_children = [child for child in non_noun_child_child.children]    
        non_noun_child_child_compound_or_amod_string = ""                                        # Step 4.1: Initialize an empty string
        for non_noun_child_child_compound_or_amod in non_noun_child_child_children:
            if non_noun_child_child_compound_or_amod.dep_ in ('amod','compound'):
                non_noun_child_child_compound_or_amod_string += non_noun_child_child_compound_or_amod.text.title()    # Step 4.2: Append all amods and compounds to this string
                                                            
        print('fbo:'+non_noun_child_child_compound_or_amod_string+str(non_noun_child_child).title())      # Step 4.3: Create a firebim class
        print('fbo:'+non_noun_child_child_compound_or_amod_string+str(non_noun_child_child).title()+' rdfs:SubClassOf fbo:'+str(non_noun_child_child).title())       # Step 4.4: Create subclass structure
        var_o = 'fbo:'+non_noun_child_child_compound_or_amod_string+str(non_noun_child_child).title()




####### SHACL

shacl = """:SHACLtemplate_01
    a sh:NodeShape                          ;
    rdfs:comment    "Specific relation"     ;
    sh:targetClass """+var_s+"""                       ; 
    sh:property [
        sh:path    """+var_p+"""                       ; 
        sh:class   """+var_o+"""                       ; 
    ]"""

print(shacl)





