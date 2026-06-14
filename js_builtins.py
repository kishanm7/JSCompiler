"""
Built-in JavaScript objects and functions injected into the global environment.
Provides: console, Math, Date, parseInt, parseFloat, Number, Object, Array, Set, Map, etc.
"""
import math
import random
import datetime
from js_types import (
    UNDEFINED, NULL, NAN, JS_INF, JS_NEG_INF,
    JSObject, JSArray, JSFunction, JSNativeFunction, JSDate, JSSet, JSMap,
    js_to_number, js_to_string, js_to_boolean, js_typeof, js_format_output,
    js_strict_equals, js_abstract_equals, is_js_nan
)


class JSGlobalObject(JSObject):
    """
    A special JSObject that proxies property access to the global Environment.
    In JavaScript, `this` at the global scope refers to the global object,
    which has all global variables as properties. This class makes that work
    by delegating `get`/`has` to the Environment when a property isn't found
    locally.
    """
    def __init__(self, env):
        super().__init__()
        self._env = env

    def get(self, key):
        # Check local properties first (e.g., built-in overrides)
        if key in self.properties:
            return self.properties[key]
        # Then delegate to the environment
        try:
            return self._env.get(key)
        except Exception:
            return UNDEFINED

    def has(self, key):
        if key in self.properties:
            return True
        return self._env.has(key)

    def keys(self):
        # Combine local properties and environment variables
        env_keys = list(self._env.variables.keys())
        local_keys = list(self.properties.keys())
        seen = set()
        result = []
        for k in local_keys + env_keys:
            if k not in seen:
                seen.add(k)
                result.append(k)
        return result


def create_global_environment():
    """Create and return a global environment with all built-ins."""
    from environment import Environment
    env = Environment(is_function_scope=True, function_name="global")
    _inject_builtins(env)

    # Set up the global `this` object — proxies to the global environment
    global_this = JSGlobalObject(env)
    env.set_this(global_this)

    return env


def _inject_builtins(env):
    """Inject all built-in objects and functions into the environment."""

    # ─── Global functions ────────────────────────────────────────

    env.define("parseInt", JSNativeFunction("parseInt", _parseInt), "var")
    env.define("parseFloat", JSNativeFunction("parseFloat", _parseFloat), "var")
    env.define("isNaN", JSNativeFunction("isNaN", _isNaN), "var")
    env.define("isFinite", JSNativeFunction("isFinite", _isFinite), "var")
    env.define("NaN", NAN, "var")
    env.define("Infinity", JS_INF, "var")
    env.define("undefined", UNDEFINED, "var")

    # ─── console ─────────────────────────────────────────────────

    console_obj = JSObject()
    console_obj.set("log", JSNativeFunction("log", _console_log))
    console_obj.set("error", JSNativeFunction("error", _console_error))
    console_obj.set("warn", JSNativeFunction("warn", _console_warn))
    console_obj.set("info", JSNativeFunction("info", _console_info))
    console_obj.set("table", JSNativeFunction("table", _console_table))
    console_obj.set("time", JSNativeFunction("time", _console_time))
    console_obj.set("timeEnd", JSNativeFunction("timeEnd", _console_timeEnd))
    env.define("console", console_obj, "var")

    # ─── Math ────────────────────────────────────────────────────

    math_obj = JSObject()
    math_obj.set("floor", JSNativeFunction("floor", lambda this, args: int(math.floor(js_to_number(args[0] if args else UNDEFINED)))))
    math_obj.set("ceil", JSNativeFunction("ceil", lambda this, args: int(math.ceil(js_to_number(args[0] if args else UNDEFINED)))))
    math_obj.set("round", JSNativeFunction("round", lambda this, args: _math_round(args)))
    math_obj.set("trunc", JSNativeFunction("trunc", lambda this, args: int(math.trunc(js_to_number(args[0] if args else UNDEFINED)))))
    math_obj.set("abs", JSNativeFunction("abs", lambda this, args: abs(js_to_number(args[0] if args else UNDEFINED))))
    math_obj.set("pow", JSNativeFunction("pow", lambda this, args: _safe_pow(args)))
    math_obj.set("sqrt", JSNativeFunction("sqrt", lambda this, args: _math_sqrt(args)))
    math_obj.set("min", JSNativeFunction("min", lambda this, args: _math_min(args)))
    math_obj.set("max", JSNativeFunction("max", lambda this, args: _math_max(args)))
    math_obj.set("random", JSNativeFunction("random", lambda this, args: random.random()))
    math_obj.set("sign", JSNativeFunction("sign", lambda this, args: _math_sign(args)))
    math_obj.set("PI", math.pi)
    math_obj.set("E", math.e)
    math_obj.set("LN2", math.log(2))
    math_obj.set("LN10", math.log(10))
    math_obj.set("LOG2E", math.log2(math.e))
    math_obj.set("LOG10E", math.log10(math.e))
    math_obj.set("SQRT2", math.sqrt(2))
    math_obj.set("SQRT1_2", math.sqrt(0.5))
    math_obj.set("MAX_SAFE_INTEGER", 9007199254740991)
    math_obj.set("MIN_SAFE_INTEGER", -9007199254740991)
    env.define("Math", math_obj, "var")

    # ─── Number ──────────────────────────────────────────────────

    number_obj = JSObject()
    number_obj.set("isNaN", JSNativeFunction("isNaN", lambda this, args: is_js_nan(args[0]) if args else True))
    number_obj.set("isFinite", JSNativeFunction("isFinite", lambda this, args: _number_isFinite(args)))
    number_obj.set("isInteger", JSNativeFunction("isInteger", lambda this, args: _number_isInteger(args)))
    number_obj.set("parseInt", JSNativeFunction("parseInt", _parseInt))
    number_obj.set("parseFloat", JSNativeFunction("parseFloat", _parseFloat))
    number_obj.set("MAX_SAFE_INTEGER", 9007199254740991)
    number_obj.set("MIN_SAFE_INTEGER", -9007199254740991)
    number_obj.set("EPSILON", 2.220446049250313e-16)
    number_obj.set("POSITIVE_INFINITY", JS_INF)
    number_obj.set("NEGATIVE_INFINITY", JS_NEG_INF)
    number_obj.set("NaN", NAN)
    env.define("Number", number_obj, "var")

    # ─── Boolean ────────────────────────────────────────────────

    boolean_obj = JSObject()
    env.define("Boolean", boolean_obj, "var")

    # ─── String ──────────────────────────────────────────────────

    string_obj = JSObject()
    env.define("String", string_obj, "var")

    # ─── Object ──────────────────────────────────────────────────

    object_obj = JSObject()
    object_obj.set("keys", JSNativeFunction("keys", lambda this, args: _object_keys(args)))
    object_obj.set("values", JSNativeFunction("values", lambda this, args: _object_values(args)))
    object_obj.set("entries", JSNativeFunction("entries", lambda this, args: _object_entries(args)))
    object_obj.set("assign", JSNativeFunction("assign", lambda this, args: _object_assign(args)))
    object_obj.set("freeze", JSNativeFunction("freeze", lambda this, args: args[0] if args else UNDEFINED))
    object_obj.set("create", JSNativeFunction("create", lambda this, args: JSObject()))
    object_obj.set("getOwnPropertyNames", JSNativeFunction("getOwnPropertyNames", lambda this, args: _object_getOwnPropertyNames(args)))
    env.define("Object", object_obj, "var")

    # ─── Array ───────────────────────────────────────────────────

    array_obj = JSObject()
    array_obj.set("isArray", JSNativeFunction("isArray", lambda this, args: isinstance(args[0], JSArray) if args else False))
    array_obj.set("from", JSNativeFunction("from", lambda this, args: _array_from(args)))
    env.define("Array", array_obj, "var")

    # ─── Set ─────────────────────────────────────────────────────

    set_obj = JSObject()
    env.define("Set", set_obj, "var")

    # ─── Map ─────────────────────────────────────────────────────

    map_obj = JSObject()
    env.define("Map", map_obj, "var")

    # ─── Date ────────────────────────────────────────────────────

    date_obj = JSObject()
    env.define("Date", date_obj, "var")

    # ─── JSON ────────────────────────────────────────────────────

    json_obj = JSObject()
    json_obj.set("stringify", JSNativeFunction("stringify", lambda this, args: _json_stringify(args)))
    json_obj.set("parse", JSNativeFunction("parse", lambda this, args: _json_parse(args)))
    env.define("JSON", json_obj, "var")


# ─── Global function implementations ──────────────────────────────

def _parseInt(this, args):
    s = args[0] if args else UNDEFINED
    radix = args[1] if len(args) > 1 else UNDEFINED
    s = js_to_string(s).strip()
    if not s:
        return NAN
    radix_val = None
    if radix is not UNDEFINED:
        radix_val = int(js_to_number(radix))
        if radix_val < 2 or radix_val > 36:
            return NAN
    # Handle 0x prefix
    if s.startswith("0x") or s.startswith("0X"):
        if radix_val is None:
            radix_val = 16
        try:
            return int(s, radix_val)
        except ValueError:
            return NAN
    if radix_val is None:
        radix_val = 10
    # Parse leading digits
    result = ""
    i = 0
    if i < len(s) and s[i] in '+-':
        result += s[i]
        i += 1
    while i < len(s) and s[i].isdigit():
        result += s[i]
        i += 1
    if not result or result in ('+', '-'):
        return NAN
    try:
        return int(result, radix_val)
    except ValueError:
        return NAN


def _parseFloat(this, args):
    s = js_to_string(args[0]) if args else ""
    s = s.strip()
    result = ""
    i = 0
    if i < len(s) and s[i] in '+-':
        result += s[i]
        i += 1
    has_dot = False
    has_e = False
    while i < len(s):
        c = s[i]
        if c.isdigit():
            result += c
        elif c == '.' and not has_dot and not has_e:
            result += c
            has_dot = True
        elif c in 'eE' and not has_e and result:
            result += c
            has_e = True
        elif c in '+-' and has_e and result[-1] in 'eE':
            result += c
        else:
            break
        i += 1
    if not result or result in ('+', '-', '.', '+.', '-.'):
        return NAN
    try:
        f = float(result)
        if math.isinf(f):
            return JS_INF if f > 0 else JS_NEG_INF
        if f == int(f) and abs(f) < 1e20:
            return int(f)
        return f
    except ValueError:
        return NAN


def _isNaN(this, args):
    val = args[0] if args else UNDEFINED
    n = js_to_number(val)
    return is_js_nan(n)


def _isFinite(this, args):
    val = args[0] if args else UNDEFINED
    n = js_to_number(val)
    if is_js_nan(n):
        return False
    if isinstance(n, (int, float)):
        return not math.isinf(n)
    return True


def _number_isFinite(args):
    val = args[0] if args else UNDEFINED
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        return False
    if is_js_nan(val):
        return False
    return not math.isinf(val)


def _number_isInteger(args):
    val = args[0] if args else UNDEFINED
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        return False
    if is_js_nan(val) or (isinstance(val, float) and math.isinf(val)):
        return False
    if isinstance(val, int):
        return True
    return val == int(val)


# ─── Console ──────────────────────────────────────────────────────

def _console_log(this, args):
    parts = [js_format_output(a) for a in args]
    print(" ".join(parts))
    return UNDEFINED

def _console_error(this, args):
    parts = [js_format_output(a) for a in args]
    print(" ".join(parts), flush=True)
    return UNDEFINED

def _console_warn(this, args):
    parts = [js_format_output(a) for a in args]
    print(" ".join(parts), flush=True)
    return UNDEFINED

def _console_info(this, args):
    parts = [js_format_output(a) for a in args]
    print(" ".join(parts), flush=True)
    return UNDEFINED

def _console_table(this, args):
    if args and isinstance(args[0], (JSObject, JSArray)):
        print(js_format_output(args[0]))
    else:
        parts = [js_format_output(a) for a in args]
        print(" ".join(parts))
    return UNDEFINED

_console_timers = {}

def _console_time(this, args):
    label = js_to_string(args[0]) if args else "default"
    _console_timers[label] = datetime.datetime.now()
    return UNDEFINED

def _console_timeEnd(this, args):
    label = js_to_string(args[0]) if args else "default"
    if label in _console_timers:
        elapsed = (datetime.datetime.now() - _console_timers[label]).total_seconds() * 1000
        print(f"{label}: {elapsed}ms")
        del _console_timers[label]
    else:
        print(f"Warning: No such label '{label}'")
    return UNDEFINED


# ─── Math helpers ─────────────────────────────────────────────────

def _math_round(args):
    val = js_to_number(args[0]) if args else NAN
    if is_js_nan(val):
        return NAN
    n = float(val)
    if isinstance(val, float) and math.isinf(n):
        return val
    # JS Math.round: round half towards +infinity
    # Math.round(0.5) = 1, Math.round(-0.5) = -0, Math.round(-1.5) = -1
    result = math.floor(n + 0.5)
    if result == 0 and n < 0:
        return 0  # -0 case
    return int(result)

def _safe_pow(args):
    base = js_to_number(args[0]) if args else NAN
    exp = js_to_number(args[1]) if len(args) > 1 else NAN
    if is_js_nan(base) or is_js_nan(exp):
        return NAN
    try:
        result = math.pow(float(base), float(exp))
        if math.isinf(result):
            return JS_INF if result > 0 else JS_NEG_INF
        if result == int(result) and abs(result) < 1e20:
            return int(result)
        return result
    except (ValueError, OverflowError):
        return NAN

def _math_sqrt(args):
    val = js_to_number(args[0]) if args else NAN
    if is_js_nan(val):
        return NAN
    n = float(val)
    if n < 0:
        return NAN
    result = math.sqrt(n)
    if result == int(result) and result < 1e20:
        return int(result)
    return result

def _math_min(args):
    if not args:
        return JS_INF
    vals = [js_to_number(a) for a in args]
    nums = []
    for v in vals:
        if is_js_nan(v):
            return NAN
        nums.append(float(v))
    return min(nums)

def _math_max(args):
    if not args:
        return JS_NEG_INF
    vals = [js_to_number(a) for a in args]
    nums = []
    for v in vals:
        if is_js_nan(v):
            return NAN
        nums.append(float(v))
    return max(nums)

def _math_sign(args):
    val = js_to_number(args[0]) if args else NAN
    if is_js_nan(val):
        return NAN
    n = float(val)
    if n > 0:
        return 1
    elif n < 0:
        return -1
    else:
        return 0


# ─── Object static methods ────────────────────────────────────────

def _object_keys(args):
    obj = args[0] if args else UNDEFINED
    if isinstance(obj, JSObject):
        arr = JSArray()
        for k in obj.keys():
            arr.push(k)
        return arr
    if isinstance(obj, JSArray):
        arr = JSArray()
        for i in range(obj._length):
            arr.push(str(i))
        for k in obj.properties:
            if not k.isdigit():
                arr.push(k)
        return arr
    return JSArray()

def _object_values(args):
    obj = args[0] if args else UNDEFINED
    if isinstance(obj, JSObject):
        arr = JSArray()
        for v in obj.values():
            arr.push(v)
        return arr
    if isinstance(obj, JSArray):
        arr = JSArray()
        for i in range(obj._length):
            arr.push(obj.properties.get(str(i), UNDEFINED))
        return arr
    return JSArray()

def _object_entries(args):
    obj = args[0] if args else UNDEFINED
    if isinstance(obj, JSObject):
        arr = JSArray()
        for k, v in obj.entries():
            entry = JSArray([k, v])
            arr.push(entry)
        return arr
    if isinstance(obj, JSArray):
        arr = JSArray()
        for i in range(obj._length):
            entry = JSArray([str(i), obj.properties.get(str(i), UNDEFINED)])
            arr.push(entry)
        return arr
    return JSArray()

def _object_assign(args):
    target = args[0] if args else JSObject()
    for source in args[1:]:
        if isinstance(source, JSObject):
            for k, v in source.properties.items():
                target.properties[k] = v
        elif isinstance(source, JSArray):
            for i in range(source._length):
                target.properties[str(i)] = source.properties.get(str(i), UNDEFINED)
    return target

def _object_getOwnPropertyNames(args):
    obj = args[0] if args else UNDEFINED
    if isinstance(obj, JSObject):
        arr = JSArray()
        for k in obj.keys():
            arr.push(k)
        return arr
    if isinstance(obj, JSArray):
        arr = JSArray()
        for k in obj.properties:
            arr.push(k)
        return arr
    return JSArray()


# ─── Array static methods ─────────────────────────────────────────

def _array_from(args):
    source = args[0] if args else UNDEFINED
    if isinstance(source, JSArray):
        return source.slice(0)
    if isinstance(source, str):
        arr = JSArray()
        for c in source:
            arr.push(c)
        return arr
    return JSArray()


# ─── JSON ─────────────────────────────────────────────────────────

def _json_stringify(args):
    val = args[0] if args else UNDEFINED
    return _js_value_to_json(val)

def _js_value_to_json(val):
    if val is UNDEFINED:
        return UNDEFINED  # JSON.stringify returns undefined for undefined
    if val is NULL:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return js_format_output(val)
    if isinstance(val, str):
        return '"' + val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t') + '"'
    if isinstance(val, JSArray):
        items = []
        for i in range(val._length):
            v = val.properties.get(str(i), UNDEFINED)
            items.append(_js_value_to_json(v) if v is not UNDEFINED else "null")
        return "[" + ",".join(items) + "]"
    if isinstance(val, JSObject):
        pairs = []
        for k, v in val.properties.items():
            if v is not UNDEFINED and v is not NULL and not callable(v) and not isinstance(v, (JSFunction, JSNativeFunction)):
                json_v = _js_value_to_json(v)
                if json_v is not UNDEFINED:
                    pairs.append('"' + k + '":' + json_v)
        return "{" + ",".join(pairs) + "}"
    return UNDEFINED

def _json_parse(args):
    import json as json_mod
    s = js_to_string(args[0]) if args else ""
    try:
        parsed = json_mod.loads(s)
        return _python_to_js(parsed)
    except json_mod.JSONDecodeError:
        raise Exception("SyntaxError: JSON.parse: unexpected character")

def _python_to_js(val):
    if val is None:
        return NULL
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        arr = JSArray()
        for item in val:
            arr.push(_python_to_js(item))
        return arr
    if isinstance(val, dict):
        obj = JSObject()
        for k, v in val.items():
            obj.set(k, _python_to_js(v))
        return obj
    return UNDEFINED
