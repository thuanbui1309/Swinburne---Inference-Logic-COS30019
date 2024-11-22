import re
from collections import deque
from typing import Dict, List, Tuple

class ForwardChaining:
    def __init__(self, filename: str):
        # Rules stored as { conclusion: [([premises], is_negated)] }
        self.rules: Dict[str, List[Tuple[List[Tuple[str, bool]], bool]]] = {}
        # Facts stored with negation flag
        self.facts: Dict[str, bool] = {}
        self.query: Tuple[str, bool] = None
        self.derived_facts = set()  # Set of facts derived during execution
        self.entailments = []  # List of derived symbols
        self.parse_kb_and_query(filename)
    
    def is_horn_form(self, tell_part: str) -> bool:
        """
        Check if the given knowledge base is in Horn form.
        :param tell_part: String representation of the knowledge base, clauses separated by ";".
        :return: True if all clauses are in Horn form, False otherwise.
        """
        # Tách từng mệnh đề
        clauses = tell_part.split(";")
        
        for clause in clauses:
            clause = clause.strip()
            
            # Kiểm tra các phép không hợp lệ (<=> không được phép trong Horn Form)
            if "<=>" in clause:
                return False
            
            if "=>" in clause:
                # Phân tách premise và conclusion
                parts = clause.split("=>")
                if len(parts) != 2:
                    print(f"Invalid syntax (more than 1 =>): {clause}")
                    return False  # Sai cú pháp nếu có nhiều hơn 1 "=>"
                
                premises, conclusion = parts
                premises = premises.strip()
                conclusion = conclusion.strip()

                # Kiểm tra conclusion (chỉ chứa 1 literal dương)
                conclusion_literals = conclusion.split()
                if conclusion.startswith("~") or len(conclusion_literals) > 1:
                    print(f"Invalid syntax (invalid conclusion): {clause}")
                    return False
            else:
                # Nếu không có "=>", kiểm tra dạng disjunction
                literals = clause.split("||")  # Tách literal theo phép OR
                literals = [lit.strip() for lit in literals]  # Loại bỏ khoảng trắng thừa
                
                # Phân loại literal dương và âm
                positive_literals = [lit for lit in literals if not lit.startswith("~")]
                negative_literals = [lit for lit in literals if lit.startswith("~")]
                
                # Điều kiện:
                # - Tối đa một literal dương
                if len(positive_literals) > 1:
                    return False
        return True


    def parse_kb_and_query(self, filename: str) -> None:
        """Parse the input file to get KB and query."""
        with open(filename, 'r') as file:
            content = file.read()

        # Separate TELL and ASK parts
        tell_part = re.search(r'TELL\s+([\s\S]*?)\s+ASK', content).group(1).strip()[:-1]
        ask_part = re.search(r'ASK\s+(.*)', content).group(1).strip()

        # Check if the input is in Horn form
        if not self.is_horn_form(tell_part):
            print("The input knowledge base is not in Horn form.")
            exit(1)
        print("It is in Horn form.")
        # Parse conditions in TELL
        clauses = tell_part.split(";")
        for clause in clauses:
            clause = clause.strip()
            if "||" in clause:
                print(f"Disjunction found in TELL: {clause}")
                # Convert disjunction to implication
                clause = self.disjunction_to_implication(clause)
                print(f"Converted to implication: {clause}")
                if not clause:
                    exit(1)
            if "=>" in clause:
                print(f"Rule found: {clause}")
                # Parse left-hand side and right-hand side
                premises, conclusion = clause.split("=>")
                premises = [
                    (p.strip().lstrip("~"), p.strip().startswith("~")) for p in premises.split("&")
                ]
                conclusion = conclusion.strip().lstrip("~")
                is_negated_conclusion = clause.strip().startswith("~")
                
                # Add to self.rules
                if conclusion not in self.rules:
                    self.rules[conclusion] = []
                self.rules[conclusion].append((premises, is_negated_conclusion))
            else:
                # If it is a fact
                literal = clause.strip().lstrip("~")
                is_positive = clause.strip().startswith("~")
                self.facts[literal] = not is_positive

        # Store query with negation flag if any
        self.query = (ask_part.strip().lstrip("~"), ask_part.strip().startswith("~"))
    
    def disjunction_to_implication(self, disjunction):
        """
        Chuyển đổi biểu thức disjunction thành implication.
        Biểu thức disjunction có thể có các ký hiệu như ~ (phủ định), || (phép OR).
        """
        # Tìm tất cả các biểu thức phủ định và không phủ định
        terms = disjunction.split("||")  # Chia disjunction theo phép OR
        negations = [term[1:] for term in terms if term.startswith("~")]  # Các phần phủ định
        non_negations = [term for term in terms if not term.startswith("~")]  # Các phần không phủ định

        # Kiểm tra nếu có ít nhất 1 phần phủ định và 1 phần không phủ định
        if len(negations) >= 1 and len(non_negations) == 1:
            # Dạng chung: ~A||~B||...||C
            implication_parts = [f"{negation}" for negation in negations]
            implication_parts.append(f"{non_negations[0]}")

            # Chuyển đổi thành A&B&...⇒ C
            implication = "&".join(implication_parts[:-1]) + "=>" + implication_parts[-1]
            return implication
        else:
            print("Không thể chuyển đổi disjunction thành implication.")
            return False

    def run(self):
        """Run the algorithm and print YES or NO with the required format."""
        # Initialize known facts
        agenda = deque([fact for fact, is_true in self.facts.items() if is_true])
        self.derived_facts = set(agenda)

        while agenda:
            fact = agenda.popleft()
            self.entailments.append(fact)

            # Check if fact matches the query
            if fact == self.query[0] and self.facts[fact] == (not self.query[1]):
                print(f"YES: {', '.join(self.entailments)}")
                return

            # Process rules that have `fact` in their premises
            for conclusion, rules in self.rules.items():
                for premises, is_negated_conclusion in rules:
                    # Check if all premises are in derived facts
                    if all((p in self.derived_facts) == (not neg) for p, neg in premises):
                        if conclusion not in self.derived_facts:
                            agenda.append(conclusion)
                            self.derived_facts.add(conclusion)
                            self.facts[conclusion] = not is_negated_conclusion
                        
        # If the query cannot be derived
        print("NO")