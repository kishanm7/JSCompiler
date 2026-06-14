"""
Tree-Walking JavaScript Interpreter.

Uses esprima for parsing (ES6+ AST) and walks the tree to execute JS code.
Implements the complete syllabus: variables/scope, operators/coercion, types,
strings, arrays, objects, functions, closures, destructuring, Set/Map, etc.
"""
import esprima
import math
import re
from js_types import (
    UNDEFINED, NULL, NAN, JS_INF, JS_NEG_INF,
    _NaN, _JSInfinity, _JSNegInfinity,
    JSArray, JSObject, JSFunction, JSNativeFunction, JSDate, JSSet, JSMap,
    js_typeof, js_to_number, js_to_string, js_to_boolean, js_to_primitive,
    js_abstract_equals, js_strict_equals, js_abstract_comparison,
    js_format_output, is_js_nan, is_js_undefined, is_js_null
)
from environment import Environment, TDZ


class ReturnException(Exception):
    """Used to bubble up return values from functions."""
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    """Used to bubble up break statements."""
    pass

class ContinueException(Exception):
    """Used to bubble up continue statements."""
    pass


class Interpreter:
    def __init__(self):
        from js_builtins import create_global_environment
        self.global_env = create_global_environment()
        self.current_env = self.global_env

    # ─── Public API ──────────────────────────────────────────────

    @staticmethod
    def _preprocess_nullish(code):
        """
        Replace `??` operator with calls to a __nullish__ helper function.
        
        We inject: function __nullish__(a,b){return a!==null&&a!==undefined?a:b;}
        And replace: `a ?? b` => `__nullish__(a, b)` (with proper operand boundary detection)
        
        Operand boundary detection: scan backwards from ?? for the left operand start,
        scan forwards for the right operand end.
        """
        # First, find all ?? positions (not inside strings)
        nullish_positions = []
        i = 0
        in_string = False
        string_char = None
        escaped = False
        
        while i < len(code):
            ch = code[i]
            
            if escaped:
                escaped = False
                i += 1
                continue
            
            if ch == '\\' and in_string:
                escaped = True
                i += 1
                continue
            
            if in_string:
                if ch == string_char:
                    in_string = False
                i += 1
                continue
            
            if ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
                i += 1
                continue
            
            if ch == '?' and i + 1 < len(code) and code[i + 1] == '?':
                nullish_positions.append(i)
                i += 2
                continue
            
            i += 1
        
        if not nullish_positions:
            return code
        
        # Replace each ?? with __nullish__(LEFT, RIGHT)
        # Process from right to left to preserve positions
        helper = "function __nullish__(a,b){return a!==null&&a!==undefined?a:b;}"
        
        result = code
        for pos in reversed(nullish_positions):
            # Find left operand boundary
            left_end = pos - 1
            # Skip whitespace
            while left_end >= 0 and result[left_end] in ' \t':
                left_end -= 1
            
            # Find the start of the left operand
            left_start = left_end
            if left_start >= 0:
                # Simple approach: find matching delimiters
                ch = result[left_start]
                if ch in ')]}':  # closing bracket - find matching opening
                    depth = 1
                    left_start -= 1
                    while left_start >= 0 and depth > 0:
                        if result[left_start] in '([{':
                            depth -= 1
                        elif result[left_start] in ')]}':
                            depth += 1
                        left_start -= 1
                    left_start += 1
                elif ch in '"\'`':  # string
                    quote = ch
                    left_start -= 1
                    while left_start >= 0:
                        if result[left_start] == quote and (left_start == 0 or result[left_start-1] != '\\'):
                            break
                        left_start -= 1
                else:
                    # Identifier, number, or expression
                    # Scan back to the start of the operand
                    while left_start >= 0 and result[left_start] not in ' \t,;=+-*%&|!<>?:([{})]':
                        left_start -= 1
                    left_start += 1
            
            # Find right operand boundary  
            right_start = pos + 2  # skip ??
            while right_start < len(result) and result[right_start] in ' \t':
                right_start += 1
            
            right_end = right_start
            if right_end < len(result):
                ch = result[right_end]
                if ch in '([{':  # opening bracket - find matching closing
                    depth = 1
                    right_end += 1
                    while right_end < len(result) and depth > 0:
                        if result[right_end] in ')]}':
                            depth -= 1
                        elif result[right_end] in '([{':
                            depth += 1
                        right_end += 1
                elif ch in '"\'`':  # string
                    quote = ch
                    right_end += 1
                    while right_end < len(result):
                        if result[right_end] == quote and (right_end == 0 or result[right_end-1] != '\\'):
                            right_end += 1
                            break
                        right_end += 1
                else:
                    # Identifier, number, or expression until delimiter
                    while right_end < len(result) and result[right_end] not in ' \t,;=+-*%&|!<>?:)]}':
                        right_end += 1
            
            # Extract operands
            left_operand = result[left_start:left_end + 1].strip()
            right_operand = result[right_start:right_end].strip()
            
            # Replace in the code
            replacement = f"__nullish__(({left_operand}),({right_operand}))"
            result = result[:left_start] + replacement + result[right_end:]
        
        # Prepend the helper function
        result = helper + result
        return result

    def execute(self, code, env=None):
        """Parse and execute a string of JavaScript code."""
        if env is None:
            env = self.global_env
        self.current_env = env
        
        # Preprocess for ?? operator
        code = self._preprocess_nullish(code)
        
        try:
            ast = esprima.parseScript(code, tolerant=True)
        except esprima.Error as e:
            raise Exception(f"SyntaxError: {e.message}")
        # Two-pass: hoist first, then execute
        self._hoist(ast.body, env)
        return self._execute_body(ast.body, env)

    def execute_repl(self, code, env=None):
        """Execute code in REPL mode - supports incomplete expressions."""
        if env is None:
            env = self.global_env
        self.current_env = env
        # Preprocess for ?? operator
        code = self._preprocess_nullish(code)
        try:
            ast = esprima.parseScript(code, tolerant=True)
        except esprima.Error as e:
            # Try as expression
            try:
                ast = esprima.parseScript(f"({code})", tolerant=True)
            except esprima.Error:
                raise Exception(f"SyntaxError: {e.message}")
        self._hoist(ast.body, env)
        result = UNDEFINED
        for node in ast.body:
            result = self._exec(node, env)
        return result

    # ─── Hoisting ────────────────────────────────────────────────

    def _hoist(self, stmts, env):
        """First pass: hoist var declarations and function declarations."""
        for node in stmts:
            self._hoist_node(node, env)

    def _hoist_node(self, node, env):
        ntype = node.type

        if ntype == "VariableDeclaration":
            for decl in node.declarations:
                if node.kind == "var":
                    name = self._get_pattern_name(decl.id)
                    if name:
                        env.hoist_var(name)
                # let/const are NOT hoisted to parent scope
                # They get declared when the declaration is executed (with TDZ)

        elif ntype == "FunctionDeclaration":
            name = node.id.name if node.id else None
            if name:
                # Create the function object and hoist it
                params = [self._extract_param_name(p) for p in node.params]
                func = JSFunction(
                    name=name,
                    params=params,
                    body=node.body,
                    closure_env=env,
                    interpreter=self,
                    is_arrow=False
                )
                # Store rest param info
                self._process_func_params(node.params, func)
                env.hoist_function(name, func)

        elif ntype == "BlockStatement" or ntype == "Program":
            for child in node.body:
                self._hoist_node(child, env)

        elif ntype == "IfStatement":
            self._hoist_node(node.consequent, env)
            if node.alternate:
                self._hoist_node(node.alternate, env)

        elif ntype in ("ForStatement", "WhileStatement", "DoWhileStatement"):
            if ntype == "ForStatement" and node.init and node.init.type == "VariableDeclaration":
                for decl in node.init.declarations:
                    if node.init.kind == "var":
                        name = self._get_pattern_name(decl.id)
                        if name:
                            env.hoist_var(name)
            self._hoist_node(node.body, env)

        elif ntype == "ForInStatement" or ntype == "ForOfStatement":
            if node.left.type == "VariableDeclaration":
                if node.left.kind == "var":
                    name = self._get_pattern_name(node.left.declarations[0].id)
                    if name:
                        env.hoist_var(name)
            self._hoist_node(node.body, env)

        elif ntype == "SwitchStatement":
            for case in node.cases:
                for child in case.consequent:
                    self._hoist_node(child, env)

        elif ntype == "TryStatement":
            self._hoist_node(node.block, env)
            if node.handler:
                self._hoist_node(node.handler.body, env)
            if node.finalizer:
                self._hoist_node(node.finalizer, env)

        elif ntype == "LabeledStatement":
            self._hoist_node(node.body, env)

    def _get_pattern_name(self, pattern):
        """Extract variable name from a pattern (Identifier, ObjectPattern, ArrayPattern)."""
        if pattern.type == "Identifier":
            return pattern.name
        return None

    def _extract_param_name(self, param):
        """Extract parameter name from various parameter patterns."""
        if param.type == "Identifier":
            return param.name
        if param.type == "AssignmentPattern":
            return self._extract_param_name(param.left)
        if param.type == "RestElement":
            return self._extract_param_name(param.argument)
        return None

    def _process_func_params(self, params, func):
        """Process function parameters for rest params and defaults."""
        func._rest_param = None
        func._default_params = {}
        for i, param in enumerate(params):
            if param.type == "RestElement":
                func._rest_param = self._extract_param_name(param)
            elif param.type == "AssignmentPattern":
                name = self._extract_param_name(param)
                func._default_params[i] = param.right
            elif param.type == "ObjectPattern" or param.type == "ArrayPattern":
                func._destructured_params = func._destructured_params if hasattr(func, '_destructured_params') else {}
                func._destructured_params[i] = param

    def _set_default_params(self, param_names, body, args, env):
        """Set default parameter values for parameters not provided in args."""
        pass  # Handled in _exec_FunctionDeclaration

    # ─── Body execution ──────────────────────────────────────────

    def _execute_body(self, stmts, env):
        """Execute a list of statements, return the last expression result."""
        result = UNDEFINED
        for node in stmts:
            result = self._exec(node, env)
        return result

    # ─── Main execution dispatch ─────────────────────────────────

    def _exec(self, node, env):
        """Execute a single AST node."""
        ntype = node.type

        method = getattr(self, f"_exec_{ntype}", None)
        if method:
            return method(node, env)

        raise Exception(f"NotImplemented: node type '{ntype}'")

    # ─── Program / Block ─────────────────────────────────────────

    def _exec_Program(self, node, env):
        return self._execute_body(node.body, env)

    def _exec_BlockStatement(self, node, env):
        # Create block scope for let/const
        block_env = env.create_child()
        # Hoist var declarations in block (they go to function scope)
        self._hoist(node.body, block_env)
        return self._execute_body(node.body, block_env)

    # ─── Variable Declarations ───────────────────────────────────

    def _exec_VariableDeclaration(self, node, env):
        for decl in node.declarations:
            self._exec_variable_declarator(decl, env, node.kind)
        return UNDEFINED

    def _exec_variable_declarator(self, decl, env, kind):
        name = self._get_pattern_name(decl.id)
        value = UNDEFINED
        if decl.init is not None:
            value = self._exec(decl.init, env)

        if decl.id.type == "ObjectPattern":
            self._assign_object_pattern(decl.id, value, env, kind)
            return
        if decl.id.type == "ArrayPattern":
            self._assign_array_pattern(decl.id, value, env, kind)
            return

        if kind == "var":
            # var: assign in the nearest function scope
            scope = env._find_var_scope()
            scope.variables[name] = value
            scope.declarations[name] = "var"
        elif kind == "let":
            if name in env.variables and env.variables[name] is not TDZ:
                # Re-declaration check (let doesn't allow in same scope)
                pass
            env.variables[name] = value
            env.declarations[name] = "let"
        elif kind == "const":
            env.variables[name] = value
            env.declarations[name] = "const"

    def _assign_object_pattern(self, pattern, value, env, kind):
        """Handle object destructuring: const { a, b: renamed, c = default } = obj"""
        if value is UNDEFINED or value is NULL:
            raise Exception(f"TypeError: Cannot destructure property of {(js_to_string(value))}")

        for prop in pattern.properties:
            if prop.type == "RestElement":
                # Rest in destructuring: const {a, ...rest} = obj
                rest_obj = JSObject()
                source_keys = value.keys() if isinstance(value, JSObject) else []
                used_keys = set()
                for p2 in pattern.properties:
                    if p2.type == "Property":
                        key = self._get_property_key(p2.key)
                        used_keys.add(key)
                for k in source_keys:
                    if k not in used_keys:
                        rest_obj.set(k, value.get(k))
                rest_name = prop.argument.name
                env.variables[rest_name] = rest_obj
                env.declarations[rest_name] = kind
                continue

            key = self._get_property_key(prop.key)
            if prop.value.type == "Identifier":
                target_name = prop.value.name
                prop_value = value.get(key) if isinstance(value, (JSObject, JSArray)) else UNDEFINED
                env.variables[target_name] = prop_value
                env.declarations[target_name] = kind
            elif prop.value.type == "AssignmentPattern":
                # Default value: { a = 5 } or { b: renamed = 10 } or { a: {b = 5} = {} }
                inner = prop.value.left
                default_val = self._exec(prop.value.right, env)
                prop_value = value.get(key) if isinstance(value, (JSObject, JSArray)) else UNDEFINED
                if prop_value is UNDEFINED:
                    prop_value = default_val
                if inner.type == "Identifier":
                    env.variables[inner.name] = prop_value
                    env.declarations[inner.name] = kind
                elif inner.type == "ObjectPattern":
                    self._assign_object_pattern(inner, prop_value, env, kind)
                elif inner.type == "ArrayPattern":
                    self._assign_array_pattern(inner, prop_value, env, kind)
            elif prop.value.type == "ObjectPattern" or prop.value.type == "ArrayPattern":
                prop_value = value.get(key) if isinstance(value, (JSObject, JSArray)) else UNDEFINED
                if prop.value.type == "ObjectPattern":
                    self._assign_object_pattern(prop.value, prop_value, env, kind)
                else:
                    self._assign_array_pattern(prop.value, prop_value, env, kind)

    def _assign_array_pattern(self, pattern, value, env, kind):
        """Handle array destructuring: const [a, , b] = arr"""
        arr = value
        if isinstance(arr, JSArray):
            pass
        elif isinstance(arr, JSObject):
            # Convert object with numeric keys to array-like access
            pass
        else:
            if arr is UNDEFINED or arr is NULL:
                raise Exception(f"TypeError: Cannot destructure property of {js_to_string(arr)}")
            arr = JSArray()

        for i, elem in enumerate(pattern.elements):
            if elem is None:
                continue  # Skip: const [a, , b] = arr
            if elem.type == "Identifier":
                val = arr.get(str(i)) if isinstance(arr, JSArray) else arr.get(str(i))
                env.variables[elem.name] = val
                env.declarations[elem.name] = kind
            elif elem.type == "AssignmentPattern":
                inner = elem.left
                default_val = self._exec(elem.right, env)
                val = arr.get(str(i)) if isinstance(arr, JSArray) else UNDEFINED
                if val is UNDEFINED:
                    val = default_val
                if inner.type == "Identifier":
                    env.variables[inner.name] = val
                    env.declarations[inner.name] = kind
            elif elem.type == "RestElement":
                # Rest: const [a, ...rest] = arr
                rest_name = elem.argument.name
                rest_arr = JSArray()
                if isinstance(arr, JSArray):
                    for j in range(i, arr._length):
                        rest_arr.push(arr.get(str(j)))
                env.variables[rest_name] = rest_arr
                env.declarations[rest_name] = kind
            elif elem.type == "ObjectPattern":
                val = arr.get(str(i)) if isinstance(arr, JSArray) else UNDEFINED
                self._assign_object_pattern(elem, val, env, kind)
            elif elem.type == "ArrayPattern":
                val = arr.get(str(i)) if isinstance(arr, JSArray) else UNDEFINED
                self._assign_array_pattern(elem, val, env, kind)

    def _get_property_key(self, key_node):
        """Get the string key from a property key node."""
        if key_node.type == "Identifier":
            return key_node.name
        if key_node.type == "Literal":
            return str(key_node.value)
        if key_node.type == "TemplateLiteral":
            return self._exec_TemplateLiteral(key_node, self.current_env)
        # Computed property
        if hasattr(key_node, 'computed') and key_node.computed:
            val = self._exec(key_node, self.current_env)
            return js_to_string(val)
        return str(key_node.value) if hasattr(key_node, 'value') else ""

    # ─── Expressions ─────────────────────────────────────────────

    def _exec_Literal(self, node, env):
        val = node.value
        if val is None:
            return NULL
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            if isinstance(val, float) and math.isnan(val):
                return NAN
            if isinstance(val, float) and math.isinf(val):
                return JS_INF if val > 0 else JS_NEG_INF
            return val
        if isinstance(val, str):
            return val
        # Regex
        if hasattr(node, 'regex') and node.regex:
            return node.raw  # Return regex as string for now
        return val

    def _exec_Identifier(self, node, env):
        name = node.name
        try:
            return env.get(name)
        except Exception:
            # Check for global built-in values
            if name == "undefined":
                return UNDEFINED
            if name == "NaN":
                return NAN
            if name == "Infinity":
                return JS_INF
            raise

    def _exec_ThisExpression(self, node, env):
        return env.get_this()

    def _exec_TemplateLiteral(self, node, env):
        parts = []
        for i, quasi in enumerate(node.quasis):
            parts.append(quasi.value.cooked if quasi.value else "")
            if i < len(node.expressions):
                val = self._exec(node.expressions[i], env)
                parts.append(js_to_string(val))
        return "".join(parts)

    def _exec_TaggedTemplateExpression(self, node, env):
        # Simplified: just evaluate the template literal
        return self._exec_TemplateLiteral(node.quasi, env)

    # ─── Binary Expressions ──────────────────────────────────────

    def _exec_BinaryExpression(self, node, env):
        op = node.operator

        if op == "&&":
            left = self._exec(node.left, env)
            if not js_to_boolean(left):
                return left
            return self._exec(node.right, env)

        if op == "||":
            left = self._exec(node.left, env)
            if js_to_boolean(left):
                return left
            return self._exec(node.right, env)

        if op == "??":
            left = self._exec(node.left, env)
            if left is not UNDEFINED and left is not NULL:
                return left
            return self._exec(node.right, env)

        left = self._exec(node.left, env)
        right = self._exec(node.right, env)

        if op == "+":
            return self._js_add(left, right)
        if op == "-":
            return self._js_sub(left, right)
        if op == "*":
            return self._js_mul(left, right)
        if op == "/":
            return self._js_div(left, right)
        if op == "%":
            return self._js_mod(left, right)
        if op == "**":
            return self._js_pow(left, right)
        if op == "==":
            return js_abstract_equals(left, right)
        if op == "!=":
            return not js_abstract_equals(left, right)
        if op == "===":
            return js_strict_equals(left, right)
        if op == "!==":
            return not js_strict_equals(left, right)
        if op == "<":
            result = js_abstract_comparison(left, right)
            if result is UNDEFINED:
                return False
            return result
        if op == ">":
            result = js_abstract_comparison(right, left)
            if result is UNDEFINED:
                return False
            return result
        if op == "<=":
            result = js_abstract_comparison(right, left)
            if result is UNDEFINED:
                return False
            if result is True:
                return False
            return True
        if op == ">=":
            result = js_abstract_comparison(left, right)
            if result is UNDEFINED:
                return False
            if result is True:
                return False
            return True

        # Bitwise operators
        if op == "&":
            return self._js_bitwise_and(left, right)
        if op == "|":
            return self._js_bitwise_or(left, right)
        if op == "^":
            return self._js_bitwise_xor(left, right)
        if op == "<<":
            return self._js_bitwise_lshift(left, right)
        if op == ">>":
            return self._js_bitwise_rshift(left, right)
        if op == ">>>":
            return self._js_bitwise_urshift(left, right)

        # instanceof
        if op == "instanceof":
            if not isinstance(right, JSObject):
                raise Exception(f"TypeError: Right-hand side of 'instanceof' is not callable")
            # Look up known constructors from the global scope
            try:
                array_ctor = self.global_env.get("Array")
            except Exception:
                array_ctor = None
            try:
                object_ctor = self.global_env.get("Object")
            except Exception:
                object_ctor = None
            try:
                function_ctor = self.global_env.get("Function")
            except Exception:
                function_ctor = None
            try:
                date_ctor = self.global_env.get("Date")
            except Exception:
                date_ctor = None
            try:
                set_ctor = self.global_env.get("Set")
            except Exception:
                set_ctor = None
            try:
                map_ctor = self.global_env.get("Map")
            except Exception:
                map_ctor = None

            # JSArray instances
            if isinstance(left, JSArray):
                if right is array_ctor or right is object_ctor:
                    return True
                return False
            # JSFunction / JSNativeFunction instances
            if isinstance(left, (JSFunction, JSNativeFunction)):
                if right is function_ctor or right is object_ctor:
                    return True
                return False
            # JSDate instances
            if isinstance(left, JSDate):
                if right is date_ctor or right is object_ctor:
                    return True
                return False
            # JSSet instances
            if isinstance(left, JSSet):
                if right is set_ctor or right is object_ctor:
                    return True
                return False
            # JSMap instances
            if isinstance(left, JSMap):
                if right is map_ctor or right is object_ctor:
                    return True
                return False
            # JSObject instances (plain objects)
            if isinstance(left, JSObject):
                if right is object_ctor:
                    return True
                return False
            # Primitives are never instanceof Object
            return False

        # in
        if op == "in":
            key = js_to_string(left)
            if isinstance(right, JSObject):
                return right.has(key)
            if isinstance(right, JSArray):
                idx = self._try_parse_int(key)
                if idx is not None and 0 <= idx < right._length:
                    return True
                return key in right.properties
            return False

        raise Exception(f"NotImplemented: binary operator '{op}'")

    def _exec_LogicalExpression(self, node, env):
        return self._exec_BinaryExpression(node, env)

    # ─── JS arithmetic helpers ───────────────────────────────────

    def _js_add(self, left, right):
        # String concatenation takes priority if either is a string
        lprim = js_to_primitive(left, "default")
        rprim = js_to_primitive(right, "default")
        if isinstance(lprim, str) or isinstance(rprim, str):
            return js_to_string(left) + js_to_string(right)
        ln = js_to_number(left)
        rn = js_to_number(right)
        if is_js_nan(ln) or is_js_nan(rn):
            return NAN
        result = self._numeric_add(ln, rn)
        return result

    def _numeric_add(self, a, b):
        a, b = self._to_numeric(a), self._to_numeric(b)
        if isinstance(a, _JSInfinity) or isinstance(b, _JSInfinity):
            if isinstance(a, _JSNegInfinity) and isinstance(b, _JSInfinity):
                return NAN
            if isinstance(a, _JSInfinity) and isinstance(b, _JSNegInfinity):
                return NAN
            if isinstance(a, (_JSInfinity, _JSNegInfinity)):
                return a
            return b
        if isinstance(a, _JSNegInfinity) and isinstance(b, _JSNegInfinity):
            return JS_NEG_INF
        result = float(a) + float(b)
        if math.isnan(result):
            return NAN
        if math.isinf(result):
            return JS_INF if result > 0 else JS_NEG_INF
        if result == int(result) and abs(result) < 1e20:
            return int(result)
        return result

    def _js_sub(self, left, right):
        ln, rn = js_to_number(left), js_to_number(right)
        if is_js_nan(ln) or is_js_nan(rn):
            return NAN
        ln = float(self._to_numeric(ln))
        rn = float(self._to_numeric(rn))
        # Handle Infinity cases
        if math.isinf(ln) and math.isinf(rn):
            if ln == rn:
                return NAN  # Infinity - Infinity = NaN
            return JS_INF if ln > rn else JS_NEG_INF
        if math.isinf(ln):
            return JS_INF if ln > 0 else JS_NEG_INF
        if math.isinf(rn):
            return JS_INF if rn < 0 else JS_NEG_INF
        result = ln - rn
        if math.isnan(result):
            return NAN
        if not math.isinf(result) and result == int(result) and abs(result) < 1e20:
            return int(result)
        if math.isinf(result):
            return JS_INF if result > 0 else JS_NEG_INF
        return result

    def _js_mul(self, left, right):
        ln, rn = js_to_number(left), js_to_number(right)
        if is_js_nan(ln) or is_js_nan(rn):
            return NAN
        result = float(self._to_numeric(ln)) * float(self._to_numeric(rn))
        if result == int(result) and abs(result) < 1e20 and not math.isinf(result):
            return int(result)
        return result

    def _js_div(self, left, right):
        ln, rn = js_to_number(left), js_to_number(right)
        if is_js_nan(ln) or is_js_nan(rn):
            return NAN
        rn = float(self._to_numeric(rn))
        ln = float(self._to_numeric(ln))
        if rn == 0:
            if ln == 0:
                return NAN
            return JS_INF if ln > 0 else JS_NEG_INF
        result = ln / rn
        if math.isinf(result):
            return JS_INF if result > 0 else JS_NEG_INF
        if result == int(result) and abs(result) < 1e20:
            return int(result)
        return result

    def _js_mod(self, left, right):
        ln, rn = js_to_number(left), js_to_number(right)
        if is_js_nan(ln) or is_js_nan(rn):
            return NAN
        rn = float(self._to_numeric(rn))
        ln = float(self._to_numeric(ln))
        if rn == 0:
            return NAN
        result = math.fmod(ln, rn)
        if result == int(result) and abs(result) < 1e20:
            return int(result)
        return result

    def _js_pow(self, left, right):
        ln, rn = js_to_number(left), js_to_number(right)
        if is_js_nan(ln) or is_js_nan(rn):
            return NAN
        try:
            result = math.pow(float(self._to_numeric(ln)), float(self._to_numeric(rn)))
        except (ValueError, OverflowError):
            return NAN
        if math.isinf(result):
            return JS_INF if result > 0 else JS_NEG_INF
        if result == int(result) and abs(result) < 1e20:
            return int(result)
        return result

    def _to_numeric(self, val):
        if isinstance(val, (_NaN, _JSInfinity, _JSNegInfinity)):
            return val
        if isinstance(val, bool):
            return 1 if val else 0
        if isinstance(val, (int, float)):
            return val
        return js_to_number(val)

    def _try_parse_int(self, s):
        try:
            return int(s)
        except (ValueError, TypeError):
            return None

    # ─── Bitwise operations ──────────────────────────────────────

    def _js_to_int32(self, val):
        n = js_to_number(val)
        if is_js_nan(n):
            return 0
        f = float(self._to_numeric(n))
        if math.isinf(f) or f == 0:
            return 0
        i = int(f) if f >= 0 else int(f)
        i = i & 0xFFFFFFFF
        if i >= 0x80000000:
            i -= 0x100000000
        return i

    def _js_bitwise_and(self, left, right):
        return self._js_to_int32(left) & self._js_to_int32(right)

    def _js_bitwise_or(self, left, right):
        return self._js_to_int32(left) | self._js_to_int32(right)

    def _js_bitwise_xor(self, left, right):
        return self._js_to_int32(left) ^ self._js_to_int32(right)

    def _js_bitwise_lshift(self, left, right):
        l = self._js_to_int32(left)
        r = self._js_to_int32(right) & 0x1F
        return (l << r) & 0xFFFFFFFF
        result = l << r
        result = result & 0xFFFFFFFF
        if result >= 0x80000000:
            result -= 0x100000000
        return result

    def _js_bitwise_rshift(self, left, right):
        l = self._js_to_int32(left)
        r = self._js_to_int32(right) & 0x1F
        return l >> r

    def _js_bitwise_urshift(self, left, right):
        l = self._js_to_int32(left) & 0xFFFFFFFF
        r = self._js_to_int32(right) & 0x1F
        return l >> r

    # ─── Unary Expressions ───────────────────────────────────────

    def _exec_UnaryExpression(self, node, env):
        op = node.operator

        if op == "typeof":
            # typeof on undeclared variable should not throw
            if node.argument.type == "Identifier":
                try:
                    val = self._exec(node.argument, env)
                except Exception:
                    return "undefined"
                return js_typeof(val)
            val = self._exec(node.argument, env)
            return js_typeof(val)

        if op == "void":
            self._exec(node.argument, env)
            return UNDEFINED

        if op == "delete":
            return self._exec_delete(node.argument, env)

        val = self._exec(node.argument, env)

        if op == "!":
            return not js_to_boolean(val)
        if op == "-":
            n = js_to_number(val)
            if is_js_nan(n):
                return NAN
            n = self._to_numeric(n)
            if isinstance(n, _JSInfinity):
                return JS_NEG_INF
            if isinstance(n, _JSNegInfinity):
                return JS_INF
            result = -float(n)
            if result == int(result) and abs(result) < 1e20:
                return int(result)
            return result
        if op == "+":
            return js_to_number(val)
        if op == "~":
            return ~self._js_to_int32(val)

        raise Exception(f"NotImplemented: unary operator '{op}'")

    def _exec_delete(self, node, env):
        if node.type == "MemberExpression":
            obj = self._exec(node.object, env)
            prop = self._get_member_key(node, env)
            if isinstance(obj, JSObject):
                return obj.delete(prop)
            if isinstance(obj, JSArray):
                idx = self._try_parse_int(str(prop))
                if idx is not None and 0 <= idx < obj._length:
                    # delete on array creates hole
                    obj.properties[str(idx)] = UNDEFINED
                    return True
                return obj.delete(str(prop)) if isinstance(prop, str) else False
        return True

    # ─── Update Expressions (++/--) ──────────────────────────────

    def _exec_UpdateExpression(self, node, env):
        op = node.operator
        prefix = node.prefix

        if node.argument.type == "Identifier":
            name = node.argument.name
            old_val = env.get(name)
            old_num = js_to_number(old_val)
            if is_js_nan(old_num):
                old_num = NAN
            if op == "++":
                new_val = self._numeric_add(old_num, 1)
            else:
                new_val = self._js_sub(old_num, 1)
            env.set(name, new_val)
            return new_val if prefix else old_num

        if node.argument.type == "MemberExpression":
            obj = self._exec(node.argument.object, env)
            prop = self._get_member_key(node.argument, env)
            old_val = self._get_property(obj, prop)
            old_num = js_to_number(old_val)
            if is_js_nan(old_num):
                old_num = NAN
            if op == "++":
                new_val = self._numeric_add(old_num, 1)
            else:
                new_val = self._js_sub(old_num, 1)
            self._set_property(obj, prop, new_val)
            return new_val if prefix else old_num

        raise Exception(f"Invalid update expression target: {node.argument.type}")

    # ─── Assignment Expressions ──────────────────────────────────

    def _exec_AssignmentExpression(self, node, env):
        op = node.operator
        right = self._exec(node.right, env)

        if node.left.type == "Identifier":
            name = node.left.name
            if op == "=":
                env.set(name, right)
                return right
            old = env.get(name)
            val = self._compute_assignment(op, old, right)
            env.set(name, val)
            return val

        if node.left.type == "MemberExpression":
            obj = self._exec(node.left.object, env)
            prop = self._get_member_key(node.left, env)
            if op == "=":
                self._set_property(obj, prop, right)
                return right
            old = self._get_property(obj, prop)
            val = self._compute_assignment(op, old, right)
            self._set_property(obj, prop, val)
            return val

        if node.left.type == "ObjectPattern":
            if op == "=":
                self._assign_object_pattern(node.left, right, env, "let")
                return right
            raise Exception("Compound assignment with destructuring not supported")

        if node.left.type == "ArrayPattern":
            if op == "=":
                self._assign_array_pattern(node.left, right, env, "let")
                return right
            raise Exception("Compound assignment with destructuring not supported")

        raise Exception(f"Invalid assignment target: {node.left.type}")

    def _compute_assignment(self, op, old, right):
        if op == "+=":
            return self._js_add(old, right)
        if op == "-=":
            return self._js_sub(old, right)
        if op == "*=":
            return self._js_mul(old, right)
        if op == "/=":
            return self._js_div(old, right)
        if op == "%=":
            return self._js_mod(old, right)
        if op == "**=":
            return self._js_pow(old, right)
        if op == "<<=":
            return self._js_bitwise_lshift(old, right)
        if op == ">>=":
            return self._js_bitwise_rshift(old, right)
        if op == ">>>=":
            return self._js_bitwise_urshift(old, right)
        if op == "&=":
            return self._js_bitwise_and(old, right)
        if op == "|=":
            return self._js_bitwise_or(old, right)
        if op == "^=":
            return self._js_bitwise_xor(old, right)
        raise Exception(f"NotImplemented: assignment operator '{op}'")

    # ─── Conditional / Ternary ───────────────────────────────────

    def _exec_ConditionalExpression(self, node, env):
        test = self._exec(node.test, env)
        if js_to_boolean(test):
            return self._exec(node.consequent, env)
        return self._exec(node.alternate, env)

    # ─── Sequence Expression ─────────────────────────────────────

    def _exec_SequenceExpression(self, node, env):
        result = UNDEFINED
        for expr in node.expressions:
            result = self._exec(expr, env)
        return result

    # ─── Member Expression (property access) ─────────────────────

    def _exec_MemberExpression(self, node, env):
        obj = self._exec(node.object, env)
        prop = self._get_member_key(node, env)
        return self._get_property(obj, prop)

    def _get_member_key(self, node, env):
        """Get the property key from a MemberExpression."""
        if node.computed:
            val = self._exec(node.property, env)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return str(int(val)) if val == int(val) else str(val)
            return js_to_string(val)
        return node.property.name

    def _get_property(self, obj, prop):
        """Get a property from a JS value."""
        if obj is UNDEFINED or obj is NULL:
            raise Exception(f"TypeError: Cannot read properties of {js_to_string(obj)} (reading '{prop}')")

        prop_str = str(prop)

        # String properties
        if isinstance(obj, str):
            if prop_str == "length":
                return len(obj)
            # String methods
            methods = self._get_string_methods(obj)
            if prop_str in methods:
                return methods[prop_str]
            # Character access
            try:
                idx = int(prop_str)
                if 0 <= idx < len(obj):
                    return obj[idx]
            except (ValueError, TypeError):
                pass
            return UNDEFINED

        # Number methods
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            if prop_str == "toFixed":
                return JSNativeFunction("toFixed", lambda this, args: self._number_toFixed(obj, args))
            if prop_str == "toString":
                return JSNativeFunction("toString", lambda this, args: self._number_toString(obj, args))
            if prop_str == "toPrecision":
                return JSNativeFunction("toPrecision", lambda this, args: self._number_toPrecision(obj, args))
            return UNDEFINED

        # JSArray
        if isinstance(obj, JSArray):
            if prop_str == "length":
                return obj._length
            if prop_str == "push":
                return JSNativeFunction("push", lambda this, args: obj.push(*args))
            if prop_str == "pop":
                return JSNativeFunction("pop", lambda this, args: obj.pop())
            if prop_str == "shift":
                return JSNativeFunction("shift", lambda this, args: obj.shift())
            if prop_str == "unshift":
                return JSNativeFunction("unshift", lambda this, args: obj.unshift(*args))
            if prop_str == "splice":
                return JSNativeFunction("splice", lambda this, args: obj.splice(*args))
            if prop_str == "slice":
                return JSNativeFunction("slice", lambda this, args: obj.slice(*args))
            if prop_str == "join":
                return JSNativeFunction("join", lambda this, args: obj.join(*args) if args else obj.join())
            if prop_str == "reverse":
                return JSNativeFunction("reverse", lambda this, args: obj.reverse())
            if prop_str == "includes":
                return JSNativeFunction("includes", lambda this, args: obj.includes(*args))
            if prop_str == "indexOf":
                return JSNativeFunction("indexOf", lambda this, args: obj.indexOf(*args))
            if prop_str == "lastIndexOf":
                return JSNativeFunction("lastIndexOf", lambda this, args: obj.lastIndexOf(*args))
            if prop_str == "sort":
                return JSNativeFunction("sort", lambda this, args: obj.sort(args[0] if args else None))
            if prop_str == "forEach":
                return JSNativeFunction("forEach", lambda this, args: obj.forEach(*args) if args else UNDEFINED)
            if prop_str == "map":
                return JSNativeFunction("map", lambda this, args: obj.map(*args) if args else UNDEFINED)
            if prop_str == "filter":
                return JSNativeFunction("filter", lambda this, args: obj.filter(*args) if args else UNDEFINED)
            if prop_str == "reduce":
                return JSNativeFunction("reduce", lambda this, args: obj.reduce(*args) if args else UNDEFINED)
            if prop_str == "find":
                return JSNativeFunction("find", lambda this, args: obj.find(*args) if args else UNDEFINED)
            if prop_str == "findIndex":
                return JSNativeFunction("findIndex", lambda this, args: obj.findIndex(*args) if args else UNDEFINED)
            if prop_str == "some":
                return JSNativeFunction("some", lambda this, args: obj.some(*args) if args else UNDEFINED)
            if prop_str == "every":
                return JSNativeFunction("every", lambda this, args: obj.every(*args) if args else UNDEFINED)
            if prop_str == "flat":
                return JSNativeFunction("flat", lambda this, args: obj.flat(float('inf') if args and (isinstance(args[0], type(JS_INF)) or (isinstance(args[0], float) and math.isinf(args[0]))) else (int(js_to_number(args[0])) if args else 1)))
            if prop_str == "concat":
                return JSNativeFunction("concat", lambda this, args: obj.concat(*args))
            if prop_str == "fill":
                return JSNativeFunction("fill", lambda this, args: self._array_fill(obj, args))
            if prop_str == "constructor":
                return env.get("Array") if env.has("Array") else UNDEFINED
            return obj.get(prop_str)

        # JSObject
        if isinstance(obj, JSObject):
            return obj.get(prop_str)

        # JSSet
        if isinstance(obj, JSSet):
            if prop_str == "add":
                return JSNativeFunction("add", lambda this, args: obj.add(args[0]) if args else obj)
            if prop_str == "has":
                return JSNativeFunction("has", lambda this, args: obj.has(args[0]) if args else False)
            if prop_str == "delete":
                return JSNativeFunction("delete", lambda this, args: obj.delete(args[0]) if args else False)
            if prop_str == "clear":
                return JSNativeFunction("clear", lambda this, args: obj.clear())
            if prop_str == "size":
                return obj.size
            if prop_str == "forEach":
                return JSNativeFunction("forEach", lambda this, args: obj.forEach(*args) if args else UNDEFINED)
            if prop_str == "keys":
                return JSNativeFunction("keys", lambda this, args: self._set_iterator(obj.keys()))
            if prop_str == "values":
                return JSNativeFunction("values", lambda this, args: self._set_iterator(obj.values()))
            if prop_str == "entries":
                return JSNativeFunction("entries", lambda this, args: self._set_entries_iterator(obj.entries()))
            return UNDEFINED

        # JSMap
        if isinstance(obj, JSMap):
            if prop_str == "set":
                return JSNativeFunction("set", lambda this, args: obj.set(args[0], args[1]) if len(args) >= 2 else obj)
            if prop_str == "get":
                return JSNativeFunction("get", lambda this, args: obj.get(args[0]) if args else UNDEFINED)
            if prop_str == "has":
                return JSNativeFunction("has", lambda this, args: obj.has(args[0]) if args else False)
            if prop_str == "delete":
                return JSNativeFunction("delete", lambda this, args: obj.delete(args[0]) if args else False)
            if prop_str == "clear":
                return JSNativeFunction("clear", lambda this, args: obj.clear())
            if prop_str == "size":
                return obj.size
            if prop_str == "forEach":
                return JSNativeFunction("forEach", lambda this, args: obj.forEach(*args) if args else UNDEFINED)
            return UNDEFINED

        # JSDate
        if isinstance(obj, JSDate):
            return obj.get(prop_str)

        # JSFunction
        if isinstance(obj, (JSFunction, JSNativeFunction)):
            if prop_str == "call":
                return JSNativeFunction("call", lambda this, args: self._function_call(obj, args))
            if prop_str == "apply":
                return JSNativeFunction("apply", lambda this, args: self._function_apply(obj, args))
            if prop_str == "bind":
                return JSNativeFunction("bind", lambda this, args: self._function_bind(obj, args))
            if prop_str == "length":
                return len(obj.params) if isinstance(obj, JSFunction) else 0
            if prop_str == "name":
                return obj.name or ""
            return obj.get(prop_str) if hasattr(obj, 'get') else UNDEFINED

        # Boolean
        if isinstance(obj, bool):
            return UNDEFINED

        return UNDEFINED

    def _set_property(self, obj, prop, value):
        """Set a property on a JS value."""
        prop_str = str(prop)

        if isinstance(obj, JSArray):
            obj.set(prop_str, value)
            return
        if isinstance(obj, JSObject):
            obj.set(prop_str, value)
            return
        if isinstance(obj, (JSFunction, JSNativeFunction)):
            obj.set(prop_str, value)
            return
        # Can't set properties on primitives in JS (silent fail in non-strict)

    # ─── String methods ──────────────────────────────────────────

    def _get_string_methods(self, s):
        return {
            "charAt": JSNativeFunction("charAt", lambda this, args: s[int(js_to_number(args[0]))] if args and 0 <= int(js_to_number(args[0])) < len(s) else ""),
            "charCodeAt": JSNativeFunction("charCodeAt", lambda this, args: ord(s[int(js_to_number(args[0]))]) if args and 0 <= int(js_to_number(args[0])) < len(s) else NAN),
            "concat": JSNativeFunction("concat", lambda this, args: s + "".join(js_to_string(a) for a in args)),
            "includes": JSNativeFunction("includes", lambda this, args: js_to_string(args[0]) in s if args else False),
            "endsWith": JSNativeFunction("endsWith", lambda this, args: s.endswith(js_to_string(args[0])) if args else False),
            "indexOf": JSNativeFunction("indexOf", lambda this, args: s.find(js_to_string(args[0]), int(js_to_number(args[1])) if len(args) > 1 else 0) if args else -1),
            "lastIndexOf": JSNativeFunction("lastIndexOf", lambda this, args: s.rfind(js_to_string(args[0]), 0, int(js_to_number(args[1])) + 1 if len(args) > 1 else len(s)) if args else -1),
            "match": JSNativeFunction("match", lambda this, args: self._string_match(s, args)),
            "padStart": JSNativeFunction("padStart", lambda this, args: s.rjust(int(js_to_number(args[0])), js_to_string(args[1]) if len(args) > 1 else " ") if args else s),
            "padEnd": JSNativeFunction("padEnd", lambda this, args: s.ljust(int(js_to_number(args[0])), js_to_string(args[1]) if len(args) > 1 else " ") if args else s),
            "repeat": JSNativeFunction("repeat", lambda this, args: s * int(js_to_number(args[0])) if args else ""),
            "replace": JSNativeFunction("replace", lambda this, args: self._string_replace(s, args)),
            "replaceAll": JSNativeFunction("replaceAll", lambda this, args: s.replace(js_to_string(args[0]), js_to_string(args[1])) if len(args) >= 2 else s),
            "search": JSNativeFunction("search", lambda this, args: self._string_search(s, args)),
            "slice": JSNativeFunction("slice", lambda this, args: self._string_slice(s, args)),
            "split": JSNativeFunction("split", lambda this, args: self._string_split(s, args)),
            "startsWith": JSNativeFunction("startsWith", lambda this, args: s.startswith(js_to_string(args[0])) if args else False),
            "substring": JSNativeFunction("substring", lambda this, args: self._string_substring(s, args)),
            "toLowerCase": JSNativeFunction("toLowerCase", lambda this, args: s.lower()),
            "toUpperCase": JSNativeFunction("toUpperCase", lambda this, args: s.upper()),
            "trim": JSNativeFunction("trim", lambda this, args: s.strip()),
            "trimStart": JSNativeFunction("trimStart", lambda this, args: s.lstrip()),
            "trimEnd": JSNativeFunction("trimEnd", lambda this, args: s.rstrip()),
            "toString": JSNativeFunction("toString", lambda this, args: s),
            "valueOf": JSNativeFunction("valueOf", lambda this, args: s),
        }

    def _string_replace(self, s, args):
        if not args:
            return s
        pattern = args[0]
        replacement = args[1] if len(args) > 1 else UNDEFINED
        if isinstance(pattern, str):
            return s.replace(pattern, js_to_string(replacement), 1)
        return s

    def _string_search(self, s, args):
        if not args:
            return -1
        pattern = js_to_string(args[0])
        m = re.search(pattern, s)
        return m.start() if m else -1

    def _string_match(self, s, args):
        if not args:
            return NULL
        pattern = js_to_string(args[0])
        m = re.search(pattern, s)
        if m:
            arr = JSArray()
            for g in m.groups():
                arr.push(g if g is not None else UNDEFINED)
            if not arr._length:
                arr.push(m.group(0))
            return arr
        return NULL

    def _string_slice(self, s, args):
        start = int(js_to_number(args[0])) if args else 0
        end = int(js_to_number(args[1])) if len(args) > 1 and args[1] is not UNDEFINED else len(s)
        if start < 0:
            start = max(len(s) + start, 0)
        if end < 0:
            end = max(len(s) + end, 0)
        return s[start:end]

    def _string_split(self, s, args):
        arr = JSArray()
        if not args or args[0] is UNDEFINED:
            arr.push(s)
            return arr
        sep = args[0]
        if isinstance(sep, str):
            if sep == "":
                for c in s:
                    arr.push(c)
                return arr
            parts = s.split(sep)
            for p in parts:
                arr.push(p)
            return arr
        # Regex separator
        parts = re.split(js_to_string(sep), s)
        for p in parts:
            arr.push(p)
        return arr

    def _string_substring(self, s, args):
        start = int(js_to_number(args[0])) if args else 0
        end = int(js_to_number(args[1])) if len(args) > 1 and args[1] is not UNDEFINED else len(s)
        if start < 0: start = 0
        if end < 0: end = 0
        if start > end:
            start, end = end, start
        return s[start:end]

    # ─── Number methods ──────────────────────────────────────────

    def _number_toFixed(self, num, args):
        digits = int(js_to_number(args[0])) if args else 0
        digits = max(0, min(digits, 20))
        return f"{float(num):.{digits}f}"

    def _number_toString(self, num, args):
        radix = int(js_to_number(args[0])) if args else 10
        if radix == 10:
            return js_to_string(num)
        return format(int(num), f'0{radix}')

    def _number_toPrecision(self, num, args):
        precision = int(js_to_number(args[0])) if args else None
        if precision is None:
            return js_to_string(num)
        return f"{float(num):.{precision}g}"

    # ─── Array helpers ───────────────────────────────────────────

    def _array_fill(self, arr, args):
        value = args[0] if args else UNDEFINED
        start = int(js_to_number(args[1])) if len(args) > 1 else 0
        end = int(js_to_number(args[2])) if len(args) > 2 else arr._length
        if start < 0:
            start = max(arr._length + start, 0)
        if end < 0:
            end = max(arr._length + end, 0)
        for i in range(start, min(end, arr._length)):
            arr.properties[str(i)] = value
        return arr

    def _set_iterator(self, items):
        arr = JSArray()
        for item in items:
            arr.push(item)
        return JSNativeFunction("next", lambda this, args: self._iterator_next(arr))

    def _set_entries_iterator(self, entries):
        arr = JSArray()
        for k, v in entries:
            entry = JSArray([k, v])
            arr.push(entry)
        return JSNativeFunction("next", lambda this, args: self._iterator_next(arr))

    def _iterator_next(self, arr):
        # Simplified iterator protocol
        return UNDEFINED

    # ─── Function call/apply/bind ────────────────────────────────

    def _function_call(self, func, args):
        this_arg = args[0] if args else UNDEFINED
        call_args = args[1:] if args else []
        if isinstance(func, (JSFunction, JSNativeFunction)):
            return func.call(this_arg, call_args)
        raise Exception(f"TypeError: {js_to_string(func)} is not a function")

    def _function_apply(self, func, args):
        this_arg = args[0] if args else UNDEFINED
        args_arr = args[1] if len(args) > 1 else UNDEFINED
        if isinstance(args_arr, JSArray):
            call_args = [args_arr.get(str(i)) for i in range(args_arr._length)]
        else:
            call_args = []
        if isinstance(func, (JSFunction, JSNativeFunction)):
            return func.call(this_arg, call_args)
        raise Exception(f"TypeError: {js_to_string(func)} is not a function")

    def _function_bind(self, func, args):
        this_arg = args[0] if args else UNDEFINED
        bound_args = args[1:]
        def bound_fn(t, call_args):
            return func.call(this_arg, list(bound_args) + list(call_args))
        return JSNativeFunction(func.name or "bound", bound_fn)

    # ─── Call Expression ─────────────────────────────────────────

    def _build_call_args(self, arg_nodes, env):
        """Build the argument list for a function call, handling SpreadElement."""
        args = []
        for arg in arg_nodes:
            if arg.type == "SpreadElement":
                spread_val = self._exec(arg.argument, env)
                if isinstance(spread_val, JSArray):
                    for i in range(spread_val._length):
                        args.append(spread_val.get(str(i)))
                elif isinstance(spread_val, JSSet):
                    for item in spread_val._items:
                        args.append(item)
                elif isinstance(spread_val, str):
                    for c in spread_val:
                        args.append(c)
                else:
                    # Try to iterate
                    try:
                        for item in spread_val:
                            args.append(item)
                    except TypeError:
                        args.append(spread_val)
            else:
                args.append(self._exec(arg, env))
        return args

    def _exec_CallExpression(self, node, env):
        # Determine this binding
        if node.callee.type == "MemberExpression":
            obj = self._exec(node.callee.object, env)
            prop = self._get_member_key(node.callee, env)
            func = self._get_property(obj, prop)
            args = self._build_call_args(node.arguments, env)
            if not isinstance(func, (JSFunction, JSNativeFunction)):
                raise Exception(f"TypeError: {js_to_string(func)} is not a function")
            # this = the object for method calls
            return func.call(obj, args)

        if node.callee.type == "Identifier":
            func_name = node.callee.name
            func = env.get(func_name)
            args = self._build_call_args(node.arguments, env)
            # Handle built-in constructors called as functions
            if func_name == "Boolean" and isinstance(func, JSObject):
                return js_to_boolean(args[0]) if args else False
            if func_name == "Number" and isinstance(func, JSObject):
                return js_to_number(args[0]) if args else 0
            if func_name == "String" and isinstance(func, JSObject):
                return js_to_string(args[0]) if args else ""
            if func_name == "Object" and isinstance(func, JSObject):
                if args and args[0] is not UNDEFINED and args[0] is not NULL:
                    return args[0]
                return JSObject()
            if func_name == "Array" and isinstance(func, JSObject):
                arr = JSArray()
                for a in args:
                    arr.push(a)
                return arr
            if isinstance(func, (JSFunction, JSNativeFunction)):
                # For regular function calls, this = undefined (strict) or global (non-strict)
                this_arg = UNDEFINED
                return func.call(this_arg, args)
            raise Exception(f"TypeError: {func_name} is not a function")

        # General case
        func = self._exec(node.callee, env)
        args = self._build_call_args(node.arguments, env)
        if isinstance(func, (JSFunction, JSNativeFunction)):
            return func.call(UNDEFINED, args)
        raise Exception(f"TypeError: {js_to_string(func)} is not a function")

    # ─── New Expression ──────────────────────────────────────────

    def _exec_NewExpression(self, node, env):
        callee = self._exec(node.callee, env)
        args = self._build_call_args(node.arguments, env)

        # Date constructor
        if isinstance(callee, JSObject) and env.has("Date") and callee is env.get("Date"):
            return JSDate(*args)

        # Set constructor
        if isinstance(callee, JSObject) and env.has("Set") and callee is env.get("Set"):
            iterable = args[0] if args else UNDEFINED
            return JSSet(iterable)

        # Map constructor
        if isinstance(callee, JSObject) and env.has("Map") and callee is env.get("Map"):
            iterable = args[0] if args else UNDEFINED
            return JSMap(iterable)

        # Array constructor
        if isinstance(callee, JSObject) and env.has("Array") and callee is env.get("Array"):
            if len(args) == 1 and isinstance(args[0], (int, float)):
                arr = JSArray()
                arr._length = int(args[0])
                return arr
            arr = JSArray()
            for a in args:
                arr.push(a)
            return arr

        # Object constructor
        if isinstance(callee, JSObject) and env.has("Object") and callee is env.get("Object"):
            if args and args[0] is not UNDEFINED and args[0] is not NULL:
                return args[0]
            return JSObject()

        # Number constructor
        if isinstance(callee, JSObject) and env.has("Number") and callee is env.get("Number"):
            return js_to_number(args[0]) if args else 0

        # String constructor
        if isinstance(callee, JSObject) and env.has("String") and callee is env.get("String"):
            return js_to_string(args[0]) if args else ""

        # Boolean constructor
        if isinstance(callee, JSObject) and env.has("Boolean") and callee is env.get("Boolean"):
            return js_to_boolean(args[0]) if args else False

        # JSFunction as constructor
        if isinstance(callee, JSFunction):
            new_obj = JSObject()
            # Set prototype chain
            if hasattr(callee, 'prototype') and isinstance(callee.prototype, JSObject):
                new_obj._proto = callee.prototype
            # Call the constructor with this = new_obj
            result = self.call_function(callee, new_obj, args)
            # If constructor returns an object, use that instead
            if isinstance(result, (JSObject, JSArray, JSSet, JSMap, JSDate)):
                return result
            return new_obj

        raise Exception(f"TypeError: {js_to_string(callee)} is not a constructor")

    # ─── Function Expressions & Declarations ─────────────────────

    def _exec_FunctionDeclaration(self, node, env):
        # Already hoisted, but we need to update the function body/params
        # in case of closures capturing the right environment
        name = node.id.name if node.id else None
        params = [self._extract_param_name(p) for p in node.params]
        func = JSFunction(
            name=name,
            params=params,
            body=node.body,
            closure_env=env,
            interpreter=self,
            is_arrow=False
        )
        self._process_func_params(node.params, func)

        # Handle default parameters, rest, and destructuring
        func._default_param_nodes = {}
        func._default_param_patterns = {}  # for destructuring with defaults
        func._rest_param_node = None
        func._destructured_param_nodes = {}
        for i, param in enumerate(node.params):
            if param.type == "AssignmentPattern":
                func._default_param_nodes[i] = param.right
                # If left side is a pattern (destructuring with default), store it
                if param.left.type in ("ObjectPattern", "ArrayPattern"):
                    func._default_param_patterns[i] = param.left
            elif param.type == "RestElement":
                func._rest_param_node = param.argument
                func._rest_param = self._extract_param_name(param)
            elif param.type == "ObjectPattern" or param.type == "ArrayPattern":
                func._destructured_param_nodes[i] = param

        # Override the hoisted function
        if name:
            env.hoist_function(name, func)
        return UNDEFINED

    def _exec_FunctionExpression(self, node, env):
        name = node.id.name if node.id else None
        params = [self._extract_param_name(p) for p in node.params]
        func = JSFunction(
            name=name,
            params=params,
            body=node.body,
            closure_env=env,
            interpreter=self,
            is_arrow=False
        )
        self._process_func_params(node.params, func)

        # Handle default parameters, rest, and destructuring
        func._default_param_nodes = {}
        func._default_param_patterns = {}  # for destructuring with defaults
        func._rest_param_node = None
        func._destructured_param_nodes = {}
        for i, param in enumerate(node.params):
            if param.type == "AssignmentPattern":
                func._default_param_nodes[i] = param.right
                if param.left.type in ("ObjectPattern", "ArrayPattern"):
                    func._default_param_patterns[i] = param.left
            elif param.type == "RestElement":
                func._rest_param_node = param.argument
                func._rest_param = self._extract_param_name(param)
            elif param.type == "ObjectPattern" or param.type == "ArrayPattern":
                func._destructured_param_nodes[i] = param

        # If named function expression, bind name inside the function
        if name:
            # Create a scope where the function name is bound
            inner_env = env.create_child()
            inner_env.define(name, func, "const")
            func.closure_env = inner_env

        return func

    def _exec_ArrowFunctionExpression(self, node, env):
        params = [self._extract_param_name(p) for p in node.params]
        func = JSFunction(
            name="",
            params=params,
            body=node.body,
            closure_env=env,
            interpreter=self,
            is_arrow=True,
            this_val=env.get_this()  # Lexical this
        )
        self._process_func_params(node.params, func)

        # Handle default parameters, rest, and destructuring
        func._default_param_nodes = {}
        func._default_param_patterns = {}  # for destructuring with defaults
        func._rest_param_node = None
        func._destructured_param_nodes = {}
        for i, param in enumerate(node.params):
            if param.type == "AssignmentPattern":
                func._default_param_nodes[i] = param.right
                if param.left.type in ("ObjectPattern", "ArrayPattern"):
                    func._default_param_patterns[i] = param.left
            elif param.type == "RestElement":
                func._rest_param_node = param.argument
                func._rest_param = self._extract_param_name(param)
            elif param.type == "ObjectPattern" or param.type == "ArrayPattern":
                func._destructured_param_nodes[i] = param

        return func

    def call_function(self, func, this_arg, args):
        """Override to handle default params and rest params properly."""
        if isinstance(func, JSNativeFunction):
            return func.call(this_arg, args)

        # Create new function scope
        func_env = func.closure_env.create_child(is_function_scope=True, function_name=func.name)

        # Bind this
        if func.is_arrow and func.this_val is not None:
            func_env.set_this(func.this_val)
        elif this_arg is not UNDEFINED:
            func_env.set_this(this_arg)

        # Bind arguments object
        args_obj = JSArray()
        for a in args:
            args_obj.push(a)
        func_env.define("arguments", args_obj, "var")

        # Bind parameters with defaults and rest
        i = 0
        args_idx = 0
        while i < len(func.params):
            param_name = func.params[i]

            # Check for rest param
            if hasattr(func, '_rest_param') and func._rest_param and param_name == func._rest_param:
                rest_arr = JSArray()
                while args_idx < len(args):
                    rest_arr.push(args[args_idx])
                    args_idx += 1
                func_env.define(param_name, rest_arr, "let")
                i += 1
                continue

            # Check for default param
            if hasattr(func, '_default_param_nodes') and i in func._default_param_nodes:
                # Check if this default param also has a destructuring pattern
                has_pattern = hasattr(func, '_default_param_patterns') and i in func._default_param_patterns

                if has_pattern:
                    pattern = func._default_param_patterns[i]
                    if args_idx < len(args):
                        val = args[args_idx]
                    else:
                        # No argument provided — evaluate the default (e.g., {} in ={})
                        val = self._exec(func._default_param_nodes[i], func_env)
                    # Apply destructuring pattern to the value
                    if pattern.type == "ObjectPattern":
                        self._assign_object_pattern(pattern, val, func_env, "let")
                    elif pattern.type == "ArrayPattern":
                        self._assign_array_pattern(pattern, val, func_env, "let")
                else:
                    # Regular default param (e.g., x = 10)
                    if args_idx < len(args):
                        func_env.define(param_name, args[args_idx], "let")
                    else:
                        # Evaluate default value
                        default_val = self._exec(func._default_param_nodes[i], func_env)
                        func_env.define(param_name, default_val, "let")
                i += 1
                args_idx += 1
                continue

            # Check for destructured param
            if hasattr(func, '_destructured_param_nodes') and i in func._destructured_param_nodes:
                pattern = func._destructured_param_nodes[i]
                val = args[args_idx] if args_idx < len(args) else UNDEFINED
                if pattern.type == "ObjectPattern":
                    self._assign_object_pattern(pattern, val, func_env, "let")
                elif pattern.type == "ArrayPattern":
                    self._assign_array_pattern(pattern, val, func_env, "let")
                args_idx += 1
                i += 1
                continue

            # Normal param
            if args_idx < len(args):
                func_env.define(param_name, args[args_idx], "let")
            else:
                func_env.define(param_name, UNDEFINED, "let")
            args_idx += 1
            i += 1

        # Handle rest param at the end
        if hasattr(func, '_rest_param') and func._rest_param and func._rest_param not in func_env.variables:
            rest_arr = JSArray()
            func_env.define(func._rest_param, rest_arr, "let")

        # Hoist declarations in function body
        if hasattr(func.body, 'body') and func.body.body is not None:
            self._hoist(func.body.body, func_env)

        # Execute function body
        old_env = self.current_env
        self.current_env = func_env
        try:
            if hasattr(func.body, 'body') and func.body.body is not None:
                self._execute_body(func.body.body, func_env)
            else:
                # Arrow function with expression body (implicit return)
                result = self._exec(func.body, func_env)
                raise ReturnException(result)
        except ReturnException as ret:
            self.current_env = old_env
            return ret.value
        self.current_env = old_env
        return UNDEFINED

    # ─── Spread / Rest Elements ──────────────────────────────────

    def _exec_SpreadElement(self, node, env):
        """Evaluate a spread element (...arr) - returns the array/object."""
        return self._exec(node.argument, env)

    # ─── Array Expression ────────────────────────────────────────

    def _exec_ArrayExpression(self, node, env):
        arr = JSArray()
        for elem in node.elements:
            if elem is None:
                arr.push(UNDEFINED)
                continue
            if elem.type == "SpreadElement":
                spread_val = self._exec(elem.argument, env)
                if isinstance(spread_val, JSArray):
                    for i in range(spread_val._length):
                        arr.push(spread_val.get(str(i)))
                elif isinstance(spread_val, JSSet):
                    for item in spread_val._items:
                        arr.push(item)
                elif isinstance(spread_val, str):
                    for c in spread_val:
                        arr.push(c)
                continue
            val = self._exec(elem, env)
            arr.push(val)
        return arr

    # ─── Object Expression ───────────────────────────────────────

    def _exec_ObjectExpression(self, node, env):
        obj = JSObject()
        for prop in node.properties:
            if prop.type == "SpreadElement":
                spread_val = self._exec(prop.argument, env)
                if isinstance(spread_val, JSObject):
                    for k, v in spread_val.properties.items():
                        obj.set(k, v)
                elif isinstance(spread_val, JSArray):
                    for i in range(spread_val._length):
                        obj.set(str(i), spread_val.get(str(i)))
                continue

            key = self._get_property_key(prop.key)
            if prop.computed:
                key_val = self._exec(prop.key, env)
                key = js_to_string(key_val)

            # Handle shorthand: { name } is equivalent to { name: name }
            if prop.shorthand:
                val = env.get(key)
            else:
                val = self._exec(prop.value, env)

            # Handle method shorthand: { foo() {} }
            if prop.method and prop.value.type in ("FunctionExpression", "ArrowFunctionExpression"):
                val = self._exec(prop.value, env)

            obj.set(key, val)
        return obj

    # ─── Statements ──────────────────────────────────────────────

    def _exec_ExpressionStatement(self, node, env):
        return self._exec(node.expression, env)

    def _exec_IfStatement(self, node, env):
        test = self._exec(node.test, env)
        if js_to_boolean(test):
            return self._exec(node.consequent, env)
        elif node.alternate:
            return self._exec(node.alternate, env)
        return UNDEFINED

    def _exec_ForStatement(self, node, env):
        # For loop creates a block scope
        for_env = env.create_child()

        # Check if init uses let/const (needs per-iteration scope)
        has_let_init = False
        if node.init and node.init.type == "VariableDeclaration" and node.init.kind in ("let", "const"):
            has_let_init = True

        # Init
        if node.init:
            if node.init.type == "VariableDeclaration":
                self._exec_VariableDeclaration(node.init, for_env)
            else:
                self._exec(node.init, for_env)

        # Loop
        while True:
            if node.test:
                test = self._exec(node.test, for_env)
                if not js_to_boolean(test):
                    break

            # For let variables, create a new scope per iteration (closure correctness)
            if has_let_init:
                iter_env = for_env.create_child()
                # Copy let variables from for_env to iter_env
                for var_name in for_env.variables:
                    if for_env.declarations.get(var_name) in ("let", "const"):
                        iter_env.define(var_name, for_env.variables[var_name], for_env.declarations[var_name])
                try:
                    self._exec(node.body, iter_env)
                except BreakException:
                    break
                except ContinueException:
                    pass
                # Copy back modified values
                for var_name in iter_env.variables:
                    if var_name in for_env.variables and for_env.declarations.get(var_name) in ("let", "const"):
                        for_env.variables[var_name] = iter_env.variables[var_name]
            else:
                try:
                    self._exec(node.body, for_env)
                except BreakException:
                    break
                except ContinueException:
                    pass

            if node.update:
                self._exec(node.update, for_env)
        return UNDEFINED

    def _exec_WhileStatement(self, node, env):
        while js_to_boolean(self._exec(node.test, env)):
            try:
                self._exec(node.body, env)
            except BreakException:
                break
            except ContinueException:
                pass
        return UNDEFINED

    def _exec_DoWhileStatement(self, node, env):
        while True:
            try:
                self._exec(node.body, env)
            except BreakException:
                break
            except ContinueException:
                pass
            if not js_to_boolean(self._exec(node.test, env)):
                break
        return UNDEFINED

    def _exec_ForInStatement(self, node, env):
        obj = self._exec(node.right, env)
        for_env = env.create_child()

        # Get the variable/property to assign
        if node.left.type == "VariableDeclaration":
            kind = node.left.kind
            var_name = self._get_pattern_name(node.left.declarations[0].id)
            if kind == "var":
                env._find_var_scope().declare_var(var_name)
        elif node.left.type == "Identifier":
            var_name = node.left.name
            kind = None
        else:
            var_name = None
            kind = None

        if isinstance(obj, JSObject):
            keys = obj.keys()
            for key in keys:
                if var_name:
                    if kind == "var":
                        env._find_var_scope().variables[var_name] = key
                    else:
                        for_env.define(var_name, key, kind or "let")
                try:
                    self._exec(node.body, for_env)
                except BreakException:
                    break
                except ContinueException:
                    continue
        elif isinstance(obj, JSArray):
            for i in range(obj._length):
                if var_name:
                    if kind == "var":
                        env._find_var_scope().variables[var_name] = str(i)
                    else:
                        for_env.define(var_name, str(i), kind or "let")
                try:
                    self._exec(node.body, for_env)
                except BreakException:
                    break
                except ContinueException:
                    continue
        return UNDEFINED

    def _exec_ForOfStatement(self, node, env):
        iterable = self._exec(node.right, env)
        for_env = env.create_child()

        # Get the variable/property to assign
        if node.left.type == "VariableDeclaration":
            kind = node.left.kind
            pattern = node.left.declarations[0].id
            var_name = self._get_pattern_name(pattern)
            if kind == "var":
                env._find_var_scope().declare_var(var_name)
        elif node.left.type == "Identifier":
            var_name = node.left.name
            kind = None
            pattern = node.left
        else:
            var_name = None
            kind = None
            pattern = node.left

        items = []
        if isinstance(iterable, JSArray):
            items = [iterable.get(str(i)) for i in range(iterable._length)]
        elif isinstance(iterable, str):
            items = list(iterable)
        elif isinstance(iterable, JSSet):
            items = iterable._items

        for item in items:
            if pattern.type == "ObjectPattern":
                self._assign_object_pattern(pattern, item, for_env, kind or "let")
            elif pattern.type == "ArrayPattern":
                self._assign_array_pattern(pattern, item, for_env, kind or "let")
            elif var_name:
                if kind == "var":
                    env._find_var_scope().variables[var_name] = item
                else:
                    for_env.define(var_name, item, kind or "let")
            try:
                self._exec(node.body, for_env)
            except BreakException:
                break
            except ContinueException:
                continue
        return UNDEFINED

    def _exec_BreakStatement(self, node, env):
        raise BreakException()

    def _exec_ContinueStatement(self, node, env):
        raise ContinueException()

    def _exec_ReturnStatement(self, node, env):
        val = UNDEFINED
        if node.argument:
            val = self._exec(node.argument, env)
        raise ReturnException(val)

    def _exec_ThrowStatement(self, node, env):
        val = self._exec(node.argument, env)
        raise Exception(js_to_string(val))

    def _exec_TryStatement(self, node, env):
        try:
            self._exec(node.block, env)
        except (ReturnException, BreakException, ContinueException):
            raise
        except Exception as e:
            if node.handler:
                catch_env = env.create_child()
                if node.handler.param:
                    var_name = node.handler.param.name
                    # Create a JS Error-like object
                    err_obj = JSObject()
                    err_obj.set("message", str(e))
                    err_obj.set("stack", str(e))
                    err_obj.set("toString", JSNativeFunction("toString", lambda this, args: str(e)))
                    catch_env.define(var_name, err_obj, "let")
                try:
                    self._exec(node.handler.body, catch_env)
                except (ReturnException, BreakException, ContinueException):
                    raise
        finally:
            if node.finalizer:
                self._exec(node.finalizer, env)
        return UNDEFINED

    def _exec_SwitchStatement(self, node, env):
        disc = self._exec(node.discriminant, env)
        matched = False
        try:
            for case in node.cases:
                if not matched and case.test is not None:
                    test_val = self._exec(case.test, env)
                    if js_strict_equals(disc, test_val):
                        matched = True
                if matched:
                    for stmt in case.consequent:
                        self._exec(stmt, env)
            # Default case
            if not matched:
                for case in node.cases:
                    if case.test is None:
                        matched = True
                    if matched:
                        for stmt in case.consequent:
                            self._exec(stmt, env)
        except BreakException:
            pass
        return UNDEFINED

    def _exec_SwitchCase(self, node, env):
        # Handled in SwitchStatement
        return UNDEFINED

    def _exec_EmptyStatement(self, node, env):
        return UNDEFINED

    def _exec_LabeledStatement(self, node, env):
        return self._exec(node.body, env)

    # ─── Conditional compilation for `with` ─────────────────────

    def _exec_WithStatement(self, node, env):
        obj = self._exec(node.object, env)
        with_env = env.create_child()
        if isinstance(obj, JSObject):
            for k, v in obj.properties.items():
                with_env.define(k, v, "let")
        return self._exec(node.body, with_env)

    # ─── Comma expression ────────────────────────────────────────

    def _exec_SequenceExpression(self, node, env):
        result = UNDEFINED
        for expr in node.expressions:
            result = self._exec(expr, env)
        return result

    # ─── Class expression ────────────────────────────────────────

    def _exec_ClassDeclaration(self, node, env):
        class_name = node.id.name if node.id else "Anonymous"
        # Create a constructor function
        constructor = None
        methods = {}

        if node.body and node.body.body:
            for item in node.body.body:
                if item.type == "MethodDefinition":
                    method_name = self._get_property_key(item.key)
                    if method_name == "constructor":
                        func = self._exec_FunctionExpression(item.value, env)
                        func.name = class_name
                        constructor = func
                    else:
                        func = self._exec_FunctionExpression(item.value, env)
                        methods[method_name] = func

        if constructor is None:
            constructor = JSFunction(
                name=class_name,
                params=[],
                body=type('Node', (), {'type': 'BlockStatement', 'body': []})(),
                closure_env=env,
                interpreter=self
            )

        # Set up prototype with methods
        for method_name, method_func in methods.items():
            constructor.prototype.set(method_name, method_func)

        if class_name:
            env.define(class_name, constructor, "let")

        return constructor

    def _exec_ClassExpression(self, node, env):
        return self._exec_ClassDeclaration(node, env)
