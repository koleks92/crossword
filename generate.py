import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):


                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Get the key.length and check if it equal with length of each value in the key
        for key in self.domains.keys():
            for value in self.domains[key].copy():
                if key.length != len(value):
                    self.domains[key].remove(value)
        

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
               
        revised = False

        if self.crossword.overlaps[x, y] is None:
            return False
        else:
            i, j = self.crossword.overlaps[x, y]
            remove = []

            for val_x in self.domains[x]: 
                for val_y in self.domains[y]:
                    if val_x[i] == val_y[j]:
                        break
                else:
                    remove.append(val_x)
                    revised = True

            for word in remove:
                self.domains[x].remove(word)    

            return revised 

    

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs:
            queue = list(arcs.keys())
        else:
            queue = []
            for x in self.domains:
                for y in self.domains:
                    if x != y:
                        queue.append((x, y))
        
        while queue:
            arc = queue.pop(0)
            if arc != None:
                X, Y = arc
                if self.revise(X, Y):
                    if len(self.domains[X]) == 0:
                        return False
                    for Z in self.crossword.neighbors(X):
                        if Z != Y:
                            queue.append((Z, X))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for domain in self.domains.keys():
            if domain not in assignment.keys():
                return False
        return True
        
    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        value_list = []

        # Check length and if values are distinct
        for key, value in assignment.items():
            if key.length != len(value):
                return False
            if value in value_list:
                return False
            else:
                value_list.append(value)

            # Check if neighbors values overlap 
            neighbors = self.crossword.neighbors(key)
            for n in neighbors:
                i, j = self.crossword.overlaps[key, n]
                for n_val in self.domains[n]:
                    if assignment[key][i] != n_val[j]:
                        return False
        
        return True

    
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Get values
        values = {}
        for val in self.domains[var]:
            values[val] = 0
            if val in assignment:
                continue
            # Get neighbors
            neighbors = self.crossword.neighbors(var)
            for neighbor in neighbors:
                for n_val in self.domains[neighbor]:
                    if val == n_val:
                        values[val] += 1

        sorted(values, key = lambda x: values[x])

        return values





    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Calculate remaning variables
        all = self.domains.keys()
        assigned = assignment.keys()
        unassigned = all - assigned

        # Get amount of remaining values
        remaining_values = {}
        for var in unassigned:
            remaining_values[var] = len(self.domains[var])
        
        # Get min and check if more than one
        min_val = min(remaining_values.values())
        keys = [key for key, value in remaining_values.items() if value == min_val]

        if len(keys) == 1:
            return keys[0]  
        else:
            # Get max and check degree
            degree_check = {}
            for key in keys:
                degree_check[key] = len(self.crossword.neighbors(key))
            
            max_val = max(degree_check.values())
            keys = [key for key, value in degree_check.items() if value == max_val]
            return keys[0]


            
                                  

            
            



    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for val in self.order_domain_values(var, assignment):
            assignment[var] = val
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result != None:
                    return result
            del assignment[var]
            
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
