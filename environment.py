"""
Environment class for JavaScript scope management.

Key JS scoping rules:
- `let`/`const`: Block-scoped, subject to Temporal Dead Zone (TDZ)
- `var`: Function-scoped, hoisted to nearest function/global scope
- Scope chaining: inner scopes can access outer scope variables (closures)
- `this` binding per execution context
"""
from js_types import UNDEFINED, NULL, _Undefined


class _TDZSentinel:
    """Sentinel value indicating a variable is in the Temporal Dead Zone."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self):
        return "<TDZ>"

TDZ = _TDZSentinel()


class Environment:
    def __init__(self, parent=None, is_function_scope=False, function_name=None):
        self.parent = parent
        self.is_function_scope = is_function_scope  # True for function bodies and global
        self.function_name = function_name
        self.variables = {}     # name → value
        self.declarations = {}  # name → "let" | "const" | "var"
        self._this = UNDEFINED

    # ─── Variable declaration (hoisting phase) ──────────────────

    def hoist_var(self, name):
        """
        Hoist a var declaration. Traverses up to the nearest function scope
        and initializes the variable to undefined if not already declared.
        """
        scope = self._find_var_scope()
        if name not in scope.variables:
            scope.variables[name] = UNDEFINED
            scope.declarations[name] = "var"
        elif scope.declarations.get(name) == "let" or scope.declarations.get(name) == "const":
            # var can't override let/const in same scope
            pass
        else:
            scope.declarations[name] = "var"

    def hoist_function(self, name, value):
        """
        Hoist a function declaration. Goes to the nearest function scope
        and sets the variable to the function value.
        """
        scope = self._find_var_scope()
        # Function declarations override var in same scope
        if name not in scope.variables or scope.declarations.get(name) == "var":
            scope.variables[name] = value
            scope.declarations[name] = "var"  # Function declarations behave like var

    def declare_let(self, name):
        """Declare a let variable (in TDZ until assignment)."""
        self.variables[name] = TDZ
        self.declarations[name] = "let"

    def declare_const(self, name):
        """Declare a const variable (in TDZ until assignment)."""
        self.variables[name] = TDZ
        self.declarations[name] = "const"

    def declare_var(self, name):
        """Declare a var variable in the appropriate scope (not hoisting, just marking)."""
        scope = self._find_var_scope()
        if name not in scope.variables:
            scope.variables[name] = UNDEFINED
        scope.declarations[name] = "var"

    # ─── Variable access ────────────────────────────────────────

    def get(self, name):
        """Get a variable's value. Throws ReferenceError for TDZ or undeclared."""
        if name in self.variables:
            val = self.variables[name]
            if val is TDZ:
                raise Exception(f"ReferenceError: Cannot access '{name}' before initialization")
            return val
        if self.parent is not None:
            return self.parent.get(name)
        raise Exception(f"ReferenceError: {name} is not defined")

    def has(self, name):
        """Check if a variable exists in this scope chain."""
        if name in self.variables:
            return True
        if self.parent is not None:
            return self.parent.has(name)
        return False

    def set(self, name, value):
        """
        Set a variable's value. Respects const (no reassignment),
        finds the correct scope for var/let.
        """
        if name in self.variables:
            decl = self.declarations.get(name)
            if decl == "const":
                raise Exception(f"TypeError: Assignment to constant variable '{name}'")
            if self.variables[name] is TDZ:
                # Allow assignment to exit TDZ
                self.variables[name] = value
                return
            self.variables[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value)
            return
        # Implicit global (like JS in non-strict mode for var)
        self.variables[name] = value
        self.declarations[name] = "var"

    def set_local(self, name, value, decl_type="let"):
        """Set a variable in the current scope (used for initialization after declaration)."""
        if name in self.variables and self.declarations.get(name) == "const":
            # First assignment to const is OK (exiting TDZ)
            if self.variables[name] is TDZ:
                self.variables[name] = value
                return
            raise Exception(f"TypeError: Assignment to constant variable '{name}'")
        self.variables[name] = value

    def define(self, name, value, decl_type="let"):
        """Define a variable in the current scope with declaration type."""
        self.variables[name] = value
        self.declarations[name] = decl_type

    # ─── this binding ────────────────────────────────────────────

    def get_this(self):
        """Get the this value, searching up the scope chain."""
        if self._this is not UNDEFINED:
            return self._this
        if self.parent is not None:
            return self.parent.get_this()
        return UNDEFINED

    def set_this(self, value):
        """Set the this value for this scope."""
        self._this = value

    # ─── Helpers ─────────────────────────────────────────────────

    def _find_var_scope(self):
        """Find the nearest function scope (or global scope) for var declarations."""
        if self.is_function_scope:
            return self
        if self.parent is not None:
            return self.parent._find_var_scope()
        return self

    def create_child(self, is_function_scope=False, function_name=None):
        """Create a child environment."""
        return Environment(parent=self, is_function_scope=is_function_scope, function_name=function_name)

    def all_variables(self):
        """Return all variables in this scope (not including parents)."""
        return dict(self.variables)
