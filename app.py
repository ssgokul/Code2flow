from flask import Flask, request, jsonify
from flask_cors import CORS
import ast
import graphviz

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Add a configuration option to enable/disable debug logging
DEBUG_MODE = True  # Set to True/False to Enable/Disable debug logging

if DEBUG_MODE:
    import logging
    logging.basicConfig(level=logging.DEBUG)
else:
    import logging
    logging.basicConfig(level=logging.INFO)

import ast
from graphviz import Digraph

class FlowchartGenerator(ast.NodeVisitor):
    def __init__(self):
        self.dot = Digraph(format='svg')
        self.dot.attr(rankdir='TB')
        self.node_counter = 0
        self.last_node = 'start'
        self.dot.node('start', 'Start', shape='oval', style='filled', color='lightgreen')
        self.function_nodes = {}  # Dictionary to store function definitions

    def new_node(self, label, shape='ellipse', style='filled', color='lightgrey'):
        node_id = f'node{self.node_counter}'
        self.node_counter += 1
        self.dot.node(node_id, label, shape=shape, style=style, color=color)
        return node_id

    def add_edge(self, from_node, to_node, label=None, edge_type=None):
        if edge_type == 'success':
            self.dot.edge(from_node, to_node, label=label if label else '', _attributes={'class': 'success'})
        else:
            self.dot.edge(from_node, to_node, label=label if label else '')

    def visit_Assign(self, node):
        targets = ', '.join([ast.unparse(t) for t in node.targets])
        value = ast.unparse(node.value)
        label = f'{targets} = {value}'
        new_node = self.new_node(label, shape='parallelogram', color='lightpink')
        self.add_edge(self.last_node, new_node)
        self.last_node = new_node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            # Create a node for the function call
            label = ast.unparse(node.value)
            call_node = self.new_node(label, shape='parallelogram', color='lightblue')
            self.add_edge(self.last_node, call_node)

            # Link the function call to its definition and body
            func_name = node.value.func.id if isinstance(node.value.func, ast.Name) else None
            if func_name and func_name in self.function_nodes:
                func_def_node, func_body_last_node = self.function_nodes[func_name]
                self.add_edge(call_node, func_def_node)  # Link call to function definition
                self.last_node = func_body_last_node  # Set the last node to the function body last node

            else:
                self.last_node = call_node

    def visit_If(self, node):
        condition = ast.unparse(node.test)
        condition_node = self.new_node(f'If: {condition}', shape='diamond', color='yellow')
        self.add_edge(self.last_node, condition_node)

        # True branch
        true_last_node = condition_node
        for stmt in node.body:
            self.visit(stmt)
            true_last_node = self.last_node
        self.add_edge(condition_node, true_last_node, label='True')

        # False branch
        false_last_node = condition_node
        if node.orelse:
            for stmt in node.orelse:
                self.visit(stmt)
                false_last_node = self.last_node
            self.add_edge(condition_node, false_last_node, label='False')

        # Merge point
        merge_node = self.new_node('Merge', shape='circle', color='black')
        self.add_edge(true_last_node, merge_node)
        self.add_edge(false_last_node, merge_node)
        self.last_node = merge_node

    def visit_For(self, node):
        loop_label = f'For: {ast.unparse(node.target)} in {ast.unparse(node.iter)}'
        loop_node = self.new_node(loop_label, shape='diamond', color='yellow')
        self.add_edge(self.last_node, loop_node)

        # Loop body
        body_last_node = loop_node
        for stmt in node.body:
            self.visit(stmt)
            body_last_node = self.last_node
        self.add_edge(body_last_node, loop_node, label='Loop')

        # Exit point
        exit_node = self.new_node('Exit Loop', shape='circle', color='black')
        self.add_edge(loop_node, exit_node, label='False')
        self.last_node = exit_node

    def visit_While(self, node):
        condition = ast.unparse(node.test)
        loop_node = self.new_node(f'While: {condition}', shape='diamond', color='yellow')
        self.add_edge(self.last_node, loop_node)

        # Loop body
        body_last_node = loop_node
        for stmt in node.body:
            self.visit(stmt)
            body_last_node = self.last_node
        self.add_edge(body_last_node, loop_node, label='Loop')

        # Exit point
        exit_node = self.new_node('Exit Loop', shape='circle', color='black')
        self.add_edge(loop_node, exit_node, label='False')
        self.last_node = exit_node

    def visit_FunctionDef(self, node):
        # Create a node for the function definition (not part of immediate control flow)
        func_label = f'Def: {node.name}()'
        func_node = self.new_node(func_label, shape='box', color='lightgreen')

        # Traverse the function body
        previous_last_node = self.last_node  # Save the current last node
        self.last_node = func_node  # Temporarily set the last node to the function definition
        for stmt in node.body:
            self.visit(stmt)
        body_last_node = self.last_node  # Capture the last node of the function body
        self.last_node = previous_last_node  # Restore the last node after processing the function body

        # Store the function definition and body last node for linking
        self.function_nodes[node.name] = (func_node, body_last_node)

    def visit_Try(self, node):
        # Create a node for the try block
        try_node = self.new_node('Try block', shape='box', color='orange')
        self.add_edge(self.last_node, try_node)

        # Process the try block
        previous_last_node = self.last_node
        self.last_node = try_node
        for stmt in node.body:
            self.visit(stmt)
        try_last_node = self.last_node

        # Process the except blocks
        except_last_nodes = []
        for handler in node.handlers:
            except_label = f'Except: {ast.unparse(handler.type)}'
            except_node = self.new_node(except_label, shape='diamond', color='red')
            self.add_edge(try_node, except_node, label=f'if {ast.unparse(handler.type)}')
            self.last_node = except_node
            for stmt in handler.body:
                self.visit(stmt)
            except_last_nodes.append(self.last_node)

        # Add a merge node after the try and except blocks
        merge_node = self.new_node('Merge', shape='circle', color='black')
        self.add_edge(try_last_node, merge_node)
        for except_last_node in except_last_nodes:
            self.add_edge(except_last_node, merge_node)

        self.last_node = merge_node

    def visit_Match(self, node):
        match_node = self.new_node('Match', shape='diamond', color='cyan')
        self.add_edge(self.last_node, match_node)

        for case in node.cases:
            case_label = f'Case: {ast.unparse(case.pattern)}'
            case_node = self.new_node(case_label, shape='box', color='lightblue')
            self.add_edge(match_node, case_node, label='Match')

            case_last_node = case_node
            for stmt in case.body:
                self.visit(stmt)
                case_last_node = self.last_node
            self.add_edge(case_last_node, match_node, label='Next Case')

        self.last_node = match_node

    def generate(self, code):
        tree = ast.parse(code)
        self.visit(tree)
        self.dot.node('end', 'End', shape='oval', style='filled', color='red')
        self.add_edge(self.last_node, 'end')
        return self.dot.pipe().decode('utf-8')

@app.route('/generate', methods=['POST'])
def generate_flowchart():
    try:
        code = request.data.decode('utf-8')
        if not code.strip():
            return jsonify({'error': 'No Python code provided'}), 400

        generator = FlowchartGenerator()
        svg_output = generator.generate(code)
        return svg_output, 200, {'Content-Type': 'image/svg+xml'}

    except Exception as e:
        logging.error(f'Error generating flowchart: {e}', exc_info=True)
        return jsonify({'error': 'An error occurred while generating the flowchart.'}), 500

@app.route('/example_program', methods=['GET'])
def example_program():
    """
    Example Python program demonstrating various programming concepts.
    """
    code = """
# Sequential execution
print("Program Started")
x = 10
y = 20
z = x + y
print(f"Sum of x and y: {z}")

# Function definition and function call
def multiply(a, b):
    \"\"\"Multiply two numbers and return the result.\"\"\"
    result = a * b
    print(f"Multiplying {a} and {b}: {result}")
    return result

product = multiply(x, y)

# For loop: Iterating through a range of numbers
print("Iterating through a range:")
for i in range(1, 6):
    print(f"Current number: {i}")

# While loop: Countdown
print("Countdown:")
count = 5
while count > 0:
    print(f"Count: {count}")
    count -= 1

# Nested conditions inside a loop
print("Checking even or odd numbers:")
for num in range(1, 6):
    if num % 2 == 0:
        print(f"{num} is even")
    else:
        print(f"{num} is odd")

# Match-case logic (Python 3.10+)
print("Match-case example:")
operation = "add"
match operation:
    case "add":
        print(f"Addition result: {x + y}")
    case "multiply":
        print(f"Multiplication result: {x * y}")
    case _:
        print("Unknown operation")

# Exception handling with try-except
print("Exception handling example:")
try:
    result = z / 0  # This will raise a ZeroDivisionError
except ZeroDivisionError:
    print("Error: Division by zero is not allowed.")

# Program end
print("Program Ended")
"""
    return jsonify({'example_code': code}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)