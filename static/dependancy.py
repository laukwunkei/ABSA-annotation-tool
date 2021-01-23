# Dependency extraction 
def apply_extraction(row,nlp):
            doc=nlp(row)
            ## FIRST RULE OF DEPENDANCY PARSE -
            ## M - Sentiment modifier || A - Aspect
            ## RULE = M is child of A with a relationshio of amod
            rule1_pairs = []
            for token in doc:
                if token.dep_ == "amod":
                    rule1_pairs.append((token.head.text, token.text))

            ## SECOND RULE OF DEPENDANCY PARSE -
            ## M - Sentiment modifier || A - Aspect
            #Direct Object - A is a child of something with relationship of nsubj, while
            # M is a child of the same something with relationship of dobj
            #Assumption - A verb will have only one NSUBJ and DOBJ
            rule2_pairs = []
            for token in doc:
                children = token.children
                A = "999999"
                M = "999999"
                for child in children :
                    if(child.dep_ == "nsubj"):
                        A = child.text
                    if(child.dep_ == "dobj"):
                        M = child.text
                if(A != "999999" and M != "999999"):
                    rule2_pairs.append((A, M))

            ## THIRD RULE OF DEPENDANCY PARSE -
            ## M - Sentiment modifier || A - Aspect
            #Adjectival Complement - A is a child of something with relationship of nsubj, while
            # M is a child of the same something with relationship of acomp
            #Assumption - A verb will have only one NSUBJ and DOBJ
            rule3_pairs = []
            for token in doc:
                children = token.children
                A = "999999"
                M = "999999"
                for child in children :
                    if(child.dep_ == "nsubj"):
                        A = child.text

                    if(child.dep_ == "acomp"):
                        M = child.text

                if(A != "999999" and M != "999999"):
                    rule3_pairs.append((A, M))

            ## FOURTH RULE OF DEPENDANCY PARSE -
            ## M - Sentiment modifier || A - Aspect
            #Adverbial modifier to a passive verb - A is a child of something with relationship of nsubjpass, while
            # M is a child of the same something with relationship of advmod
            #Assumption - A verb will have only one NSUBJ and DOBJ
            rule4_pairs = []
            for token in doc:
                children = token.children
                A = "999999"
                M = "999999"
                for child in children :
                    if(child.dep_ == "nsubjpass"):
                        A = child.text

                    if(child.dep_ == "advmod"):
                        M = child.text

                if(A != "999999" and M != "999999"):
                    rule4_pairs.append((A, M))


            ## FIFTH RULE OF DEPENDANCY PARSE -
            ## M - Sentiment modifier || A - Aspect
            #Complement of a copular verb - A is a child of M with relationship of nsubj, while
            # M has a child with relationship of cop
            #Assumption - A verb will have only one NSUBJ and DOBJ
            rule5_pairs = []
            for token in doc:
                children = token.children
                A = "999999"
                buf_var = "999999"
                for child in children :
                    if(child.dep_ == "nsubj"):
                        A = child.text

                    if(child.dep_ == "cop"):
                        buf_var = child.text

                if(A != "999999" and buf_var != "999999"):
                    rule3_pairs.append((A, token.text))

            aspects = []
            aspects = rule1_pairs + rule2_pairs + rule3_pairs + rule4_pairs + rule5_pairs
            return aspects