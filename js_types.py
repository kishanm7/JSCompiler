"""
Custom Python classes that mirror JavaScript runtime types.
These wrap Python primitives/containers but enforce JS semantics
(e.g., equality rules, stringification, prototype-like methods).
"""
import math
import random
import datetime
import re

# ─── Sentinel values ───────────────────────────────────────────────
class _Undefined:
    """Singleton representing JavaScript `undefined`."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self):
        return "undefined"
    def __bool__(self):
        return False
    def __eq__(self, other):
        return isinstance(other, _Undefined)
    def __hash__(self):
        return hash("undefined")

UNDEFINED = _Undefined()

class _Null:
    """Singleton representing JavaScript `null`."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self):
        return "null"
    def __bool__(self):
        return False
    def __eq__(self, other):
        return isinstance(other, _Null)
    def __hash__(self):
        return hash("null")

NULL = _Null()


class _NaN:
    """Singleton representing JavaScript NaN (not-a-number)."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self):
        return "NaN"
    def __str__(self):
        return "NaN"
    def __bool__(self):
        return False
    def __float__(self):
        return float('nan')
    def __eq__(self, other):
        return False  # NaN !== NaN
    def __ne__(self, other):
        return True   # NaN != NaN is true (loose)
    def __hash__(self):
        return hash("NaN")
    def __add__(self, other): return NAN
    def __sub__(self, other): return NAN
    def __mul__(self, other): return NAN
    def __truediv__(self, other): return NAN
    def __mod__(self, other): return NAN
    def __pow__(self, other): return NAN
    def __neg__(self): return NAN

NAN = _NaN()

class _JSInfinity:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self):
        return "Infinity"
    def __str__(self):
        return "Infinity"
    def __bool__(self):
        return True
    def __float__(self):
        return float('inf')
    def __add__(self, other):
        if isinstance(other, _JSNegInfinity): return NAN
        if isinstance(other, _NaN): return NAN
        return JS_INF
    def __sub__(self, other):
        if isinstance(other, _JSInfinity): return NAN
        if isinstance(other, _NaN): return NAN
        return JS_INF
    def __mul__(self, other):
        v = js_to_number(other)
        if isinstance(v, _NaN): return NAN
        if v == 0: return NAN
        return JS_INF if v > 0 else JS_NEG_INF
    def __truediv__(self, other):
        v = js_to_number(other)
        if isinstance(v, _NaN): return NAN
        if v == float('inf') or isinstance(v, _JSInfinity) or isinstance(v, _JSNegInfinity): return NAN
        return JS_INF
    def __mod__(self, other):
        v = js_to_number(other)
        if isinstance(v, _NaN): return NAN
        if v == 0: return NAN
        return NAN
    def __gt__(self, other):
        if isinstance(other, _NaN): return False
        return True
    def __ge__(self, other):
        if isinstance(other, _NaN): return False
        return True
    def __lt__(self, other): return False
    def __le__(self, other):
        if isinstance(other, _JSInfinity): return True
        return False

class _JSNegInfinity:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __repr__(self):
        return "-Infinity"
    def __str__(self):
        return "-Infinity"
    def __bool__(self):
        return True
    def __float__(self):
        return float('-inf')
    def __add__(self, other):
        if isinstance(other, _JSInfinity): return NAN
        if isinstance(other, _NaN): return NAN
        return JS_NEG_INF
    def __sub__(self, other):
        if isinstance(other, _JSNegInfinity): return NAN
        if isinstance(other, _NaN): return NAN
        return JS_NEG_INF
    def __mul__(self, other):
        v = js_to_number(other)
        if isinstance(v, _NaN): return NAN
        if v == 0: return NAN
        return JS_NEG_INF if v > 0 else JS_INF
    def __truediv__(self, other):
        v = js_to_number(other)
        if isinstance(v, _NaN): return NAN
        if v == float('inf') or isinstance(v, _JSInfinity) or isinstance(v, _JSNegInfinity): return NAN
        return JS_NEG_INF
    def __gt__(self, other): return False
    def __ge__(self, other):
        if isinstance(other, _JSNegInfinity): return True
        return False
    def __lt__(self, other):
        if isinstance(other, _NaN): return False
        return True
    def __le__(self, other):
        if isinstance(other, _NaN): return False
        return True

JS_INF = _JSInfinity()
JS_NEG_INF = _JSNegInfinity()


# ─── Type checking helpers ─────────────────────────────────────────

def is_js_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not isinstance(v, (_NaN, _JSInfinity, _JSNegInfinity))

def is_js_nan(v):
    return isinstance(v, _NaN) or (isinstance(v, float) and math.isnan(v))

def is_js_infinity(v):
    return isinstance(v, _JSInfinity) or (isinstance(v, float) and math.isinf(v) and v > 0)

def is_js_neg_infinity(v):
    return isinstance(v, _JSNegInfinity) or (isinstance(v, float) and math.isinf(v) and v < 0)

def is_js_undefined(v):
    return v is UNDEFINED

def is_js_null(v):
    return v is NULL


# ─── JS type coercion functions ────────────────────────────────────

def js_typeof(val):
    """Returns the JavaScript typeof string for a value."""
    if val is UNDEFINED:
        return "undefined"
    if val is NULL:
        return "object"  # typeof null === "object" (JS bug)
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, str):
        return "string"
    if isinstance(val, (_NaN, _JSInfinity, _JSNegInfinity)):
        return "number"
    if isinstance(val, (int, float)):
        return "number"
    if isinstance(val, JSFunction):
        return "function"
    if isinstance(val, (JSArray, JSObject, JSSet, JSMap, JSDate)):
        return "object"
    if callable(val):
        return "function"
    return "object"


def js_to_primitive(val, preferred_type=None):
    """Convert a JS value to a primitive (ToPrimitive)."""
    if val is UNDEFINED or val is NULL or isinstance(val, (bool, str, int, float, _NaN, _JSInfinity, _JSNegInfinity)):
        return val
    if isinstance(val, JSDate):
        hint = "string"
    else:
        hint = preferred_type or "number"
    if isinstance(val, (JSObject, JSArray)):
        if hint == "string":
            result = val.js_toString()
            if not isinstance(result, (JSObject, JSArray)):
                return result
            result = val.js_valueOf()
            if not isinstance(result, (JSObject, JSArray)):
                return result
        else:
            result = val.js_valueOf()
            if not isinstance(result, (JSObject, JSArray)):
                return result
            result = val.js_toString()
            if not isinstance(result, (JSObject, JSArray)):
                return result
        raise TypeError("Cannot convert object to primitive value")
    if isinstance(val, JSSet):
        return "[object Set]"
    if isinstance(val, JSMap):
        return "[object Map]"
    if isinstance(val, JSDate):
        return val.js_toString()
    return str(val)


def js_to_number(val):
    """Convert a JS value to a JS number (ToNumber)."""
    if val is UNDEFINED:
        return NAN
    if val is NULL:
        return 0
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if isinstance(val, float) and math.isnan(val):
            return NAN
        if isinstance(val, float) and math.isinf(val):
            return JS_INF if val > 0 else JS_NEG_INF
        return val
    if isinstance(val, (_NaN, _JSInfinity, _JSNegInfinity)):
        return val
    if isinstance(val, str):
        s = val.strip()
        if s == "":
            return 0
        if s == "Infinity" or s == "+Infinity":
            return JS_INF
        if s == "-Infinity":
            return JS_NEG_INF
        try:
            # Try hex
            if s.startswith("0x") or s.startswith("0X"):
                return int(s, 16)
            # Try float
            f = float(s)
            if math.isnan(f):
                return NAN
            if math.isinf(f):
                return JS_INF if f > 0 else JS_NEG_INF
            # Return int if it's a whole number
            if f == int(f) and not math.isinf(f):
                return int(f)
            return f
        except (ValueError, OverflowError):
            return NAN
    # For objects, convert to primitive first
    prim = js_to_primitive(val, "number")
    if prim is not val:
        return js_to_number(prim)
    return NAN


def js_to_string(val):
    """Convert a JS value to a JS string (ToString)."""
    if val is UNDEFINED:
        return "undefined"
    if val is NULL:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, _NaN):
        return "NaN"
    if isinstance(val, _JSInfinity):
        return "Infinity"
    if isinstance(val, _JSNegInfinity):
        return "-Infinity"
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if isinstance(val, float) and math.isnan(val):
            return "NaN"
        if isinstance(val, float) and math.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        if isinstance(val, float):
            # JS-style number formatting
            if val == int(val) and abs(val) < 1e20:
                return str(int(val))
            return repr(val)
        return str(val)
    if isinstance(val, str):
        return val
    if isinstance(val, JSArray):
        return val.js_join(",")
    if isinstance(val, JSObject):
        return val.js_toString()
    if isinstance(val, JSSet):
        return "[object Set]"
    if isinstance(val, JSMap):
        return "[object Map]"
    if isinstance(val, JSDate):
        return val.js_toString()
    if isinstance(val, JSFunction):
        return f"function {val.name or 'anonymous'}() {{ [native code] }}"
    if callable(val):
        return f"function () {{ [native code] }}"
    return str(val)


def js_to_boolean(val):
    """Convert a JS value to a JS boolean (ToBoolean)."""
    # The 6 falsy values: false, 0, -0, "", null, undefined, NaN
    if val is UNDEFINED or val is NULL:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, _NaN):
        return False
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if isinstance(val, float) and (math.isnan(val) or val == 0):
            return False
        if val == 0:
            return False
        return True
    if isinstance(val, str):
        return len(val) > 0
    # All objects are truthy
    return True


def js_abstract_equals(x, y):
    """JavaScript abstract/loose equality (==)."""
    # Same type → strict equality
    tx, ty = js_typeof(x), js_typeof(y)

    # null == undefined (and vice versa)
    if (x is NULL and y is UNDEFINED) or (x is UNDEFINED and y is NULL):
        return True
    if x is NULL or x is UNDEFINED:
        if y is NULL or y is UNDEFINED:
            return True
        return False
    if y is NULL or y is UNDEFINED:
        return False

    # Same type
    if tx == ty:
        return js_strict_equals(x, y)

    # Number == String → Number == ToNumber(String)
    if tx == "number" and ty == "string":
        return js_abstract_equals(x, js_to_number(y))
    if tx == "string" and ty == "number":
        return js_abstract_equals(js_to_number(x), y)

    # Boolean == anything → ToNumber(boolean) == anything
    if tx == "boolean":
        return js_abstract_equals(js_to_number(x), y)
    if ty == "boolean":
        return js_abstract_equals(x, js_to_number(y))

    # Object == primitive → ToPrimitive(object) == primitive
    if tx == "object" and ty in ("string", "number"):
        return js_abstract_equals(js_to_primitive(x), y)
    if ty == "object" and tx in ("string", "number"):
        return js_abstract_equals(x, js_to_primitive(y))

    return False


def js_strict_equals(x, y):
    """JavaScript strict equality (===)."""
    # NaN !== NaN
    if is_js_nan(x) or is_js_nan(y):
        return False
    # Different types → false
    tx, ty = js_typeof(x), js_typeof(y)
    if tx != ty:
        return False
    # Same type comparisons
    if x is UNDEFINED and y is UNDEFINED:
        return True
    if x is NULL and y is NULL:
        return True
    if tx == "number":
        nx, ny = js_to_number(x), js_to_number(y)
        if is_js_nan(nx) or is_js_nan(ny):
            return False
        # Handle ±0
        if isinstance(nx, float) and isinstance(ny, float):
            if nx == 0 and ny == 0:
                return True
        return nx == ny
    if tx == "string":
        return x == y
    if tx == "boolean":
        return x == y
    # Objects: reference equality
    return x is y


def js_abstract_comparison(x, y):
    """JavaScript abstract relational comparison (<). Returns True/False/Undefined."""
    px, py = js_to_primitive(x, "number"), js_to_primitive(y, "number")
    if isinstance(px, str) and isinstance(py, str):
        if px < py:
            return True
        if px == py:
            return UNDEFINED
        return False
    nx, ny = js_to_number(px), js_to_number(py)
    if is_js_nan(nx) or is_js_nan(ny):
        return UNDEFINED
    return nx < ny


def js_format_output(val):
    """Format a JS value for console.log / REPL output."""
    if val is UNDEFINED:
        return "undefined"
    if val is NULL:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, _NaN):
        return "NaN"
    if isinstance(val, _JSInfinity):
        return "Infinity"
    if isinstance(val, _JSNegInfinity):
        return "-Infinity"
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if isinstance(val, float) and math.isnan(val):
            return "NaN"
        if isinstance(val, float) and math.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        if isinstance(val, float):
            if val == int(val) and abs(val) < 1e20:
                return str(int(val))
            # Match JS output: 0.30000000000000004
            s = repr(val)
            return s
        return str(val)
    if isinstance(val, str):
        return val
    if isinstance(val, JSArray):
        return val.to_display_string()
    if isinstance(val, JSObject):
        return val.to_display_string()
    if isinstance(val, JSSet):
        return val.to_display_string()
    if isinstance(val, JSMap):
        return val.to_display_string()
    if isinstance(val, JSDate):
        return val.js_toString()
    if isinstance(val, JSFunction):
        return f"function {val.name or 'anonymous'}() {{ [native code] }}"
    if callable(val):
        return "function () { [native code] }"
    return str(val)


# ─── JSArray ───────────────────────────────────────────────────────

class JSArray:
    def __init__(self, elements=None):
        self.properties = {}   # numeric indices stored as string keys + other named props
        self._length = 0
        if elements:
            for i, e in enumerate(elements):
                self.properties[str(i)] = e
            self._length = len(elements)

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, val):
        new_len = int(js_to_number(val))
        if new_len < self._length:
            for i in range(new_len, self._length):
                key = str(i)
                if key in self.properties:
                    del self.properties[key]
        self._length = new_len

    def _get_index(self, key):
        """Get numeric index from key, or -1 if not a valid array index."""
        try:
            idx = int(key)
            if idx >= 0 and str(idx) == str(key).rstrip('.0') if isinstance(key, float) else str(idx) == key:
                return idx
        except (ValueError, TypeError):
            pass
        return -1

    def get(self, key):
        k = str(key) if not isinstance(key, str) else key
        idx = self._get_index(k)
        if idx >= 0 and idx < self._length:
            return self.properties.get(k, UNDEFINED)
        if k == "length":
            return self._length
        return self.properties.get(k, UNDEFINED)

    def set(self, key, value):
        k = str(key) if not isinstance(key, str) else key
        idx = self._get_index(k)
        if idx >= 0:
            if idx >= self._length:
                self._length = idx + 1
            self.properties[k] = value
        else:
            self.properties[k] = value

    def push(self, *args):
        for a in args:
            self.properties[str(self._length)] = a
            self._length += 1
        return self._length

    def pop(self):
        if self._length == 0:
            return UNDEFINED
        self._length -= 1
        val = self.properties.pop(str(self._length), UNDEFINED)
        return val

    def shift(self):
        if self._length == 0:
            return UNDEFINED
        first = self.properties.get("0", UNDEFINED)
        for i in range(1, self._length):
            self.properties[str(i - 1)] = self.properties.pop(str(i), UNDEFINED)
        self.properties.pop(str(self._length - 1), None)
        self._length -= 1
        return first

    def unshift(self, *args):
        n = len(args)
        # Shift existing elements right
        for i in range(self._length - 1, -1, -1):
            self.properties[str(i + n)] = self.properties.pop(str(i), UNDEFINED)
        for i, a in enumerate(args):
            self.properties[str(i)] = a
        self._length += n
        return self._length

    def splice(self, start, delete_count=None, *items):
        start = int(js_to_number(start))
        if start < 0:
            start = max(self._length + start, 0)
        if start > self._length:
            start = self._length
        if delete_count is None:
            delete_count = self._length - start
        else:
            delete_count = int(js_to_number(delete_count))
        delete_count = min(delete_count, self._length - start)

        removed = JSArray()
        for i in range(delete_count):
            removed.push(self.properties.get(str(start + i), UNDEFINED))

        # Shift remaining elements
        items_len = len(items)
        diff = items_len - delete_count
        if diff < 0:
            # Removing more than adding - shift left
            for i in range(start + items_len, self._length + diff):
                self.properties[str(i)] = self.properties.get(str(i - diff), UNDEFINED)
            for i in range(self._length + diff, self._length):
                self.properties.pop(str(i), None)
        elif diff > 0:
            # Adding more than removing - shift right
            for i in range(self._length - 1, start + delete_count - 1, -1):
                self.properties[str(i + diff)] = self.properties.get(str(i), UNDEFINED)

        # Insert new items
        for i, item in enumerate(items):
            self.properties[str(start + i)] = item

        self._length += diff
        return removed

    def slice(self, start=0, end=None):
        start = int(js_to_number(start))
        if start < 0:
            start = max(self._length + start, 0)
        if end is None or end is UNDEFINED:
            end = self._length
        else:
            end = int(js_to_number(end))
            if end < 0:
                end = max(self._length + end, 0)
        result = JSArray()
        for i in range(start, min(end, self._length)):
            result.push(self.properties.get(str(i), UNDEFINED))
        return result

    def join(self, sep=","):
        if sep is UNDEFINED:
            sep = ","
        sep = js_to_string(sep)
        parts = []
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if val is UNDEFINED or val is NULL:
                parts.append("")
            else:
                parts.append(js_to_string(val))
        return sep.join(parts)

    def js_join(self, sep=","):
        return self.join(sep)

    def reverse(self):
        items = self.to_python_list()
        items.reverse()
        self.properties = {}
        for i, item in enumerate(items):
            self.properties[str(i)] = item
        return self

    def includes(self, search_element, from_index=0):
        from_index = int(js_to_number(from_index))
        if from_index < 0:
            from_index = max(self._length + from_index, 0)
        for i in range(from_index, self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if js_strict_equals(val, search_element):
                return True
        # NaN check
        if is_js_nan(search_element):
            for i in range(from_index, self._length):
                val = self.properties.get(str(i), UNDEFINED)
                if is_js_nan(val):
                    return True
        return False

    def indexOf(self, search_element, from_index=0):
        from_index = int(js_to_number(from_index))
        if from_index < 0:
            from_index = max(self._length + from_index, 0)
        for i in range(from_index, self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if js_strict_equals(val, search_element):
                return i
        return -1

    def lastIndexOf(self, search_element, from_index=None):
        if from_index is None:
            from_index = self._length - 1
        else:
            from_index = int(js_to_number(from_index))
        if from_index < 0:
            from_index = self._length + from_index
        if from_index >= self._length:
            from_index = self._length - 1
        for i in range(from_index, -1, -1):
            val = self.properties.get(str(i), UNDEFINED)
            if js_strict_equals(val, search_element):
                return i
        return -1

    def sort(self, compare_fn=None):
        items = self.to_python_list()
        if compare_fn is None:
            # Default: lexicographical sort
            def default_compare(a, b):
                sa, sb = js_to_string(a), js_to_string(b)
                if sa < sb:
                    return -1
                if sa > sb:
                    return 1
                return 0
            import functools
            items.sort(key=functools.cmp_to_key(default_compare))
        else:
            import functools
            def cmp(a, b):
                result = compare_fn.call(None, [a, b])
                n = js_to_number(result)
                if is_js_nan(n):
                    return 0
                return -1 if n < 0 else (1 if n > 0 else 0)
            items.sort(key=functools.cmp_to_key(cmp))
        self.properties = {}
        for i, item in enumerate(items):
            self.properties[str(i)] = item
        return self

    def forEach(self, callback, this_arg=None):
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            callback.call(this_arg, [val, i, self])

    def map(self, callback, this_arg=None):
        result = JSArray()
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            new_val = callback.call(this_arg, [val, i, self])
            result.push(new_val)
        return result

    def filter(self, callback, this_arg=None):
        result = JSArray()
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if js_to_boolean(callback.call(this_arg, [val, i, self])):
                result.push(val)
        return result

    def reduce(self, callback, initial_value=UNDEFINED):
        acc = initial_value
        start = 0
        if acc is UNDEFINED:
            if self._length == 0:
                raise Exception("TypeError: Reduce of empty array with no initial value")
            acc = self.properties.get("0", UNDEFINED)
            start = 1
        for i in range(start, self._length):
            val = self.properties.get(str(i), UNDEFINED)
            acc = callback.call(None, [acc, val, i, self])
        return acc

    def find(self, callback, this_arg=None):
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if js_to_boolean(callback.call(this_arg, [val, i, self])):
                return val
        return UNDEFINED

    def findIndex(self, callback, this_arg=None):
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if js_to_boolean(callback.call(this_arg, [val, i, self])):
                return i
        return -1

    def some(self, callback, this_arg=None):
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if js_to_boolean(callback.call(this_arg, [val, i, self])):
                return True
        return False

    def every(self, callback, this_arg=None):
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            if not js_to_boolean(callback.call(this_arg, [val, i, self])):
                return False
        return True

    def flat(self, depth=1):
        result = JSArray()
        # Handle Infinity depth
        is_inf = isinstance(depth, float) and math.isinf(depth)
        def flatten(arr, d):
            for i in range(arr._length):
                val = arr.properties.get(str(i), UNDEFINED)
                if isinstance(val, JSArray) and (is_inf or d > 0):
                    flatten(val, d - 1 if not is_inf else float('inf'))
                else:
                    result.push(val)
        flatten(self, depth)
        return result

    def concat(self, *args):
        result = JSArray()
        for i in range(self._length):
            result.push(self.properties.get(str(i), UNDEFINED))
        for arg in args:
            if isinstance(arg, JSArray):
                for i in range(arg._length):
                    result.push(arg.properties.get(str(i), UNDEFINED))
            else:
                result.push(arg)
        return result

    def to_python_list(self):
        return [self.properties.get(str(i), UNDEFINED) for i in range(self._length)]

    def js_toString(self):
        return self.js_join(",")

    def js_valueOf(self):
        return self

    def to_display_string(self):
        parts = []
        for i in range(self._length):
            val = self.properties.get(str(i), UNDEFINED)
            parts.append(js_format_display_value(val))
        return "[" + ", ".join(parts) + "]"

    def __repr__(self):
        return self.to_display_string()


def js_format_display_value(val):
    """Format a value for display inside arrays/objects (strings quoted with double quotes like JS)."""
    if isinstance(val, str):
        # Escape special characters inside the string for display
        escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{escaped}"'  # JS console shows strings with double quotes
    return js_format_output(val)


# ─── JSObject ──────────────────────────────────────────────────────

class JSObject:
    def __init__(self):
        self.properties = {}  # string key → value
        self._this = self     # for this binding

    def get(self, key):
        k = str(key) if not isinstance(key, str) else key
        if k in self.properties:
            return self.properties[k]
        return UNDEFINED

    def set(self, key, value):
        k = str(key) if not isinstance(key, str) else key
        self.properties[k] = value

    def has(self, key):
        k = str(key) if not isinstance(key, str) else key
        return k in self.properties

    def delete(self, key):
        k = str(key) if not isinstance(key, str) else key
        return self.properties.pop(k, UNDEFINED) is not UNDEFINED

    def keys(self):
        return list(self.properties.keys())

    def values(self):
        return list(self.properties.values())

    def entries(self):
        return [(k, v) for k, v in self.properties.items()]

    def js_toString(self):
        # Try to call toString method if it exists
        if "toString" in self.properties:
            fn = self.properties["toString"]
            if isinstance(fn, JSFunction) or callable(fn):
                return js_to_string(fn.call(self, []))
        return "[object Object]"

    def js_valueOf(self):
        if "valueOf" in self.properties:
            fn = self.properties["valueOf"]
            if isinstance(fn, JSFunction) or callable(fn):
                return fn.call(self, [])
        return self

    def to_display_string(self):
        parts = []
        for k, v in self.properties.items():
            parts.append(f"{k}: {js_format_display_value(v)}")
        return "{ " + ", ".join(parts) + " }"

    def __repr__(self):
        return self.to_display_string()


# ─── JSFunction ────────────────────────────────────────────────────

class JSFunction:
    def __init__(self, name, params, body, closure_env, interpreter, is_arrow=False, this_val=None):
        self.name = name or ""
        self.params = params           # list of param names
        self.body = body               # AST node of function body
        self.closure_env = closure_env # Environment for closure
        self.interpreter = interpreter
        self.is_arrow = is_arrow
        self.this_val = this_val       # bound this for arrow functions
        self.prototype = JSObject()    # for constructor support
        self.properties = {}
        self._is_builtin = False

    def call(self, this_arg, args):
        """Call this JS function with given this and arguments."""
        # For arrow functions, use lexical this
        if self.is_arrow and self.this_val is not None:
            this_arg = self.this_val
        return self.interpreter.call_function(self, this_arg, args)

    def js_toString(self):
        return f"function {self.name or 'anonymous'}() {{ [native code] }}"

    def js_valueOf(self):
        return self

    def get(self, key):
        k = str(key) if not isinstance(key, str) else key
        return self.properties.get(k, UNDEFINED)

    def set(self, key, value):
        k = str(key) if not isinstance(key, str) else key
        self.properties[k] = value


class JSNativeFunction:
    """A built-in function implemented in Python."""
    def __init__(self, name, fn, this_val=None):
        self.name = name or ""
        self.fn = fn
        self.this_val = this_val
        self.properties = {}
        self.is_arrow = False
        self._is_builtin = True

    def call(self, this_arg, args):
        return self.fn(this_arg, args)

    def js_toString(self):
        return f"function {self.name or 'anonymous'}() {{ [native code] }}"

    def js_valueOf(self):
        return self

    def get(self, key):
        return self.properties.get(str(key), UNDEFINED)

    def set(self, key, value):
        self.properties[str(key)] = value


# ─── JSSet ─────────────────────────────────────────────────────────

class JSSet:
    def __init__(self, iterable=None):
        self._items = []  # list of values (using JS equality)
        if iterable is not None:
            if isinstance(iterable, JSArray):
                for i in range(iterable._length):
                    val = iterable.properties.get(str(i), UNDEFINED)
                    self.add(val)
            elif isinstance(iterable, (list, tuple)):
                for val in iterable:
                    self.add(val)

    def add(self, value):
        if not self._has(value):
            self._items.append(value)
        return self

    def _has(self, value):
        for item in self._items:
            if js_strict_equals(item, value):
                return True
            # NaN === NaN should be false, but Set treats NaN as same
            if is_js_nan(item) and is_js_nan(value):
                return True
        return False

    def has(self, value):
        return self._has(value)

    def delete(self, value):
        for i, item in enumerate(self._items):
            if js_strict_equals(item, value) or (is_js_nan(item) and is_js_nan(value)):
                self._items.pop(i)
                return True
        return False

    def clear(self):
        self._items = []

    @property
    def size(self):
        return len(self._items)

    def keys(self):
        return list(self._items)

    def values(self):
        return list(self._items)

    def entries(self):
        return [(v, v) for v in self._items]

    def forEach(self, callback, this_arg=None):
        for val in self._items:
            callback.call(this_arg, [val, val, self])

    def to_js_array(self):
        arr = JSArray()
        for item in self._items:
            arr.push(item)
        return arr

    def to_display_string(self):
        return f"Set({self.size}) {{ {', '.join(js_format_display_value(v) for v in self._items)} }}"

    def js_toString(self):
        return "[object Set]"

    def js_valueOf(self):
        return self


# ─── JSMap ─────────────────────────────────────────────────────────

class JSMap:
    def __init__(self, iterable=None):
        self._keys = []
        self._values = []
        if iterable is not None:
            if isinstance(iterable, JSArray):
                for i in range(iterable._length):
                    entry = iterable.properties.get(str(i), UNDEFINED)
                    if isinstance(entry, JSArray) and entry._length >= 2:
                        k = entry.properties.get("0", UNDEFINED)
                        v = entry.properties.get("1", UNDEFINED)
                        self.set(k, v)

    def _find_index(self, key):
        for i, k in enumerate(self._keys):
            if js_strict_equals(k, key):
                return i
            if is_js_nan(k) and is_js_nan(key):
                return i
        return -1

    def set(self, key, value):
        idx = self._find_index(key)
        if idx >= 0:
            self._values[idx] = value
        else:
            self._keys.append(key)
            self._values.append(value)
        return self

    def get(self, key):
        idx = self._find_index(key)
        if idx >= 0:
            return self._values[idx]
        return UNDEFINED

    def has(self, key):
        return self._find_index(key) >= 0

    def delete(self, key):
        idx = self._find_index(key)
        if idx >= 0:
            self._keys.pop(idx)
            self._values.pop(idx)
            return True
        return False

    def clear(self):
        self._keys = []
        self._values = []

    @property
    def size(self):
        return len(self._keys)

    def keys(self):
        return list(self._keys)

    def values(self):
        return list(self._values)

    def entries(self):
        return list(zip(self._keys, self._values))

    def forEach(self, callback, this_arg=None):
        for i in range(len(self._keys)):
            callback.call(this_arg, [self._values[i], self._keys[i], self])

    def to_display_string(self):
        entries = ", ".join(
            f"{js_format_display_value(k)} => {js_format_display_value(v)}"
            for k, v in zip(self._keys, self._values)
        )
        return f"Map({self.size}) {{ {entries} }}"

    def js_toString(self):
        return "[object Map]"

    def js_valueOf(self):
        return self


# ─── JSDate ────────────────────────────────────────────────────────

class JSDate:
    def __init__(self, *args):
        if len(args) == 0:
            self._date = datetime.datetime.now(datetime.timezone.utc)
        elif len(args) == 1:
            if isinstance(args[0], str):
                # Parse ISO string
                try:
                    s = args[0].strip()
                    # Try various formats
                    for fmt in [
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%dT%H:%M:%S.%f%z",
                        "%Y-%m-%dT%H:%M:%S%z",
                        "%Y-%m-%d",
                    ]:
                        try:
                            self._date = datetime.datetime.strptime(s, fmt)
                            if fmt.endswith("Z") or fmt.endswith("%z"):
                                self._date = self._date.astimezone(datetime.timezone.utc)
                            else:
                                self._date = self._date.replace(tzinfo=datetime.timezone.utc)
                            break
                        except ValueError:
                            continue
                    else:
                        self._date = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
                        self._invalid = True
                except Exception:
                    self._date = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
                    self._invalid = True
            else:
                # Milliseconds since epoch
                ms = js_to_number(args[0])
                if is_js_nan(ms):
                    self._invalid = True
                    self._date = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
                else:
                    try:
                        ms_val = float(ms)
                        self._date = datetime.datetime.fromtimestamp(ms_val / 1000.0, tz=datetime.timezone.utc)
                    except (OSError, OverflowError, ValueError):
                        self._invalid = True
                        self._date = datetime.datetime(1970, 1, 1, tz=datetime.timezone.utc)
        else:
            # new Date(year, month, day, hour, min, sec, ms)
            year = int(js_to_number(args[0])) if len(args) > 0 else 0
            month = int(js_to_number(args[1])) if len(args) > 1 else 0
            day = int(js_to_number(args[2])) if len(args) > 2 else 1
            hour = int(js_to_number(args[3])) if len(args) > 3 else 0
            minute = int(js_to_number(args[4])) if len(args) > 4 else 0
            second = int(js_to_number(args[5])) if len(args) > 5 else 0
            ms = int(js_to_number(args[6])) if len(args) > 6 else 0
            # Handle year 0-99 → 1900-1999
            if 0 <= year <= 99:
                year += 1900
            try:
                self._date = datetime.datetime(year, month + 1, day, hour, minute, second, ms * 1000, tzinfo=datetime.timezone.utc)
            except ValueError:
                # Auto-correction like JS
                self._date = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc)
                self._invalid = True
        self._invalid = getattr(self, '_invalid', False)

    def getTime(self):
        if self._invalid:
            return NAN
        return int(self._date.timestamp() * 1000)

    def getFullYear(self):
        if self._invalid:
            return NAN
        return self._date.year

    def getMonth(self):
        if self._invalid:
            return NAN
        return self._date.month - 1  # 0-indexed

    def getDate(self):
        if self._invalid:
            return NAN
        return self._date.day

    def getDay(self):
        if self._invalid:
            return NAN
        return self._date.weekday()  # 0=Monday... but JS: 0=Sunday
        # Adjust: Python Monday=0, JS Sunday=0
        return (self._date.weekday() + 1) % 7

    def getHours(self):
        if self._invalid:
            return NAN
        return self._date.hour

    def getMinutes(self):
        if self._invalid:
            return NAN
        return self._date.minute

    def getSeconds(self):
        if self._invalid:
            return NAN
        return self._date.second

    def getMilliseconds(self):
        if self._invalid:
            return NAN
        return self._date.microsecond // 1000

    def getUTCFullYear(self):
        if self._invalid: return NAN
        return self._date.year

    def getUTCMonth(self):
        if self._invalid: return NAN
        return self._date.month - 1

    def getUTCDate(self):
        if self._invalid: return NAN
        return self._date.day

    def js_toString(self):
        if self._invalid:
            return "Invalid Date"
        return self._date.strftime("%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)")

    def toISOString(self):
        if self._invalid:
            raise Exception("RangeError: Invalid time value")
        return self._date.strftime("%Y-%m-%dT%H:%M:%S.") + f"{self._date.microsecond // 1000:03d}Z"

    def toDateString(self):
        if self._invalid:
            return "Invalid Date"
        return self._date.strftime("%a %b %d %Y")

    def js_valueOf(self):
        return self.getTime()

    def get(self, key):
        k = str(key) if not isinstance(key, str) else key
        method_map = {
            "getTime": JSNativeFunction("getTime", lambda this, args: this.getTime()),
            "getFullYear": JSNativeFunction("getFullYear", lambda this, args: this.getFullYear()),
            "getMonth": JSNativeFunction("getMonth", lambda this, args: this.getMonth()),
            "getDate": JSNativeFunction("getDate", lambda this, args: this.getDate()),
            "getDay": JSNativeFunction("getDay", lambda this, args: this.getDay()),
            "getHours": JSNativeFunction("getHours", lambda this, args: this.getHours()),
            "getMinutes": JSNativeFunction("getMinutes", lambda this, args: this.getMinutes()),
            "getSeconds": JSNativeFunction("getSeconds", lambda this, args: this.getSeconds()),
            "getMilliseconds": JSNativeFunction("getMilliseconds", lambda this, args: this.getMilliseconds()),
            "toISOString": JSNativeFunction("toISOString", lambda this, args: this.toISOString()),
            "toDateString": JSNativeFunction("toDateString", lambda this, args: this.toDateString()),
            "toString": JSNativeFunction("toString", lambda this, args: this.js_toString()),
            "valueOf": JSNativeFunction("valueOf", lambda this, args: this.js_valueOf()),
        }
        if k in method_map:
            return method_map[k]
        return UNDEFINED

    def set(self, key, value):
        pass  # Date methods are read-only in our implementation

    def to_display_string(self):
        return self.js_toString()
