# Thunder JS Interpreter

> A Tree-Walking JavaScript Runtime built from scratch in Python — submitted for **Thunder Hackathon 2.0**

---

## Overview

**Thunder JS** is a fully functional JavaScript interpreter written entirely in Python. It parses ES6+ JavaScript code, walks the Abstract Syntax Tree, and executes it — all without relying on any existing JS engine. The project demonstrates a deep understanding of how programming languages work under the hood: lexing/parsing, scope management, type coercion, closure semantics, prototype-based `this` binding, and more.

This is not a transpiler or a wrapper around V8 — it is a **from-scratch runtime** that faithfully reproduces JavaScript's sometimes-surprising semantics in Python.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│            (REPL + File Execution Entry)            │
│         Auto-installs dependencies on first run     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 interpreter.py                      │
│           (Tree-Walking AST Executor)               │
│   2169 lines · 44 AST node handlers                │
│   Executes every ES6+ construct in the syllabus     │
└──────┬──────────────┬──────────────┬───────────────┘
       │              │              │
       ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────────────┐
│environment │ │  js_types  │ │    js_builtins     │
│  .py       │ │   .py      │ │      .py           │
│            │ │            │ │                    │
│ Scope      │ │ JS Runtime │ │ Global Objects:    │
│ chaining,  │ │ Types:     │ │ console, Math,     │
│ var/let/   │ │ UNDEFINED, │ │ Number, String,    │
│ const TDZ, │ │ NULL, NaN, │ │ Object, Array,     │
│ hoisting,  │ │ Infinity,  │ │ Set, Map, Date,    │
│ this bind  │ │ JSArray,   │ │ JSON, parseInt,    │
│            │ │ JSObject,  │ │ parseFloat,        │
│ 168 lines  │ │ JSFunction,│ │ JSGlobalObject     │
│            │ │ JSDate,    │ │                    │
│            │ │ JSSet,     │ │ 578 lines          │
│            │ │ JSMap      │ │                    │
│            │ │            │ │                    │
│            │ │ 1294 lines │ │                    │
└────────────┘ └────────────┘ └────────────────────┘
```

### Design Decisions

| Decision | Rationale |
|---|---|
| **Tree-Walking over Bytecode VM** | Simpler to implement, easier to debug, and directly maps JS semantics to Python operations — ideal for an educational interpreter |
| **esprima for parsing** | Production-grade ES6+ parser that produces a standardized AST — lets us focus on runtime semantics rather than lexer/parser edge cases |
| **Custom JS type wrappers** | Python's native types don't match JS semantics (e.g., `typeof null === "object"`, `NaN !== NaN`). Dedicated classes (`JSArray`, `JSObject`, `JSFunction`, etc.) enforce correct behavior |
| **Exception-based control flow** | `ReturnException`, `BreakException`, `ContinueException` bubble up through the call stack — mirrors how real engines implement these statements |
| **Environment scope chain** | Each scope has a parent pointer. Variable lookup walks the chain, exactly matching JS's lexical scoping rules |

---

## Quick Start

### Prerequisites

- **Python 3.8+** (no other setup needed)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd js-interpreter

# That's it — dependencies auto-install on first run!
# (esprima is installed automatically via pip)
```

No manual `pip install` needed. On first run, the interpreter checks for `esprima` and installs it automatically (handles both regular pip and `--break-system-packages` environments like Colab).

### Running

```bash
# Interactive REPL
python main.py

# Execute a JavaScript file
python main.py script.js

# Run the automated test suite
python test_runner.py
```

---

## REPL Commands

| Command | Action |
|---|---|
| `exit` / `quit` | Exit the REPL |
| `clear` / `cls` | Clear the terminal screen |
| `help` | Show available commands |
| `Ctrl+C` | Force exit |

The REPL supports **multi-line input** — it tracks unmatched `{}`, `()`, `[]` delimiters and shows a `... ` continuation prompt until the block is complete:

```
js> function greet(name) {
...     return `Hello, ${name}!`;
... }
js> greet("Thunder")
Hello, Thunder!
```

---

## Supported JavaScript Features

### Variables & Scope

```javascript
// var hoisting
console.log(x);    // undefined (hoisted, not initialized)
var x = 5;

// let/const with Temporal Dead Zone (TDZ)
let y = 10;
const z = 15;

// Block scope
{
    let blockVar = 20;
    var funcVar = 25;   // var is function-scoped
}
console.log(funcVar);       // 25
console.log(typeof blockVar); // undefined
```

### Operators & Type Coercion

Full JavaScript coercion semantics — including the tricky ones:

```javascript
console.log("5" + 3);       // "53"   (string concatenation)
console.log("5" - 3);       // 2      (numeric coercion)
console.log(0 == false);    // true   (loose equality)
console.log(null == undefined); // true
console.log(5 === "5");     // false  (strict equality)
console.log(0.1 + 0.2 === 0.3); // false (floating point)
```

### Nullish Coalescing (`??`) & Short-Circuit

```javascript
console.log(null ?? "default");    // "default"
console.log(undefined ?? "default"); // "default"
console.log(0 ?? "default");       // 0  (0 is not nullish)
console.log("" ?? "default");      // "" (empty string is not nullish)
```

### Strings & Template Literals

```javascript
"hello".toUpperCase();            // "HELLO"
"hello world".indexOf("world");  // 6
"hello".includes("ell");         // true
"a-b-c".split("-");              // ["a", "b", "c"]

let name = "Thunder";
console.log(`Hello, ${name}!`);  // "Hello, Thunder!"
```

### Arrays (Full Method Support)

```javascript
// All standard methods
[1,2,3].push(4);          // 4
[1,2,3].pop();            // 3
[1,2,3].map(x => x * 2);     // [2, 4, 6]
[1,2,3,4,5].filter(x => x > 3); // [4, 5]
[1,2,3,4].reduce((a, b) => a + b, 0); // 10
[1,2,3,4].find(x => x > 2);    // 3
[1,2,3].some(x => x > 2);      // true
[1,2,3].every(x => x > 0);     // true

// Sort (lexicographic by default, like real JS!)
[10, 2, 30, 1].sort();           // [1, 10, 2, 30]
[10, 2, 30, 1].sort((a, b) => a - b); // [1, 2, 10, 30]

// Flat with Infinity depth
[1, [2, [3, [4]]]].flat(Infinity); // [1, 2, 3, 4]
```

### Objects & `this`

```javascript
const user = {
    name: "Thunder",
    score: 50,
    addScore(points) {
        this.score += points;  // 'this' correctly refers to 'user'
        return this;           // enables method chaining
    }
};
user.addScore(10).addScore(5);
console.log(user.score); // 65

// Object static methods
Object.keys({ x: 1, y: 2 });     // ["x", "y"]
Object.values({ x: 1, y: 2 });   // [1, 2]
Object.assign({ a: 1 }, { b: 2 }); // { a: 1, b: 2 }
```

### Destructuring (Array, Object, Nested, with Defaults)

```javascript
// Array destructuring
const [a, b, ...rest] = [1, 2, 3, 4];  // a=1, b=2, rest=[3,4]

// Object destructuring with rename & defaults
const { name: userName, age = 21 } = { name: "Lightning" };
// userName = "Lightning", age = 21

// Nested destructuring in function params
const configure = ({
    db: { host = "localhost", port = 3306 } = {}
} = {}) => `${host}:${port}`;

configure();              // "localhost:3306"
configure({ db: { host: "prod" } }); // "prod:3306"
```

### Functions, Closures, Arrows

```javascript
// Closures
function makeMultiplier(factor = 2) {
    return (num) => num * factor;  // captures 'factor'
}
const triple = makeMultiplier(3);
triple(10);  // 30

// Arrow functions with lexical 'this'
const obj = {
    value: 42,
    getValue() {
        return (() => this.value)();  // arrow inherits 'this'
    }
};
obj.getValue(); // 42

// Rest parameters & spread in calls
function sum(...nums) {
    return nums.reduce((a, b) => a + b, 0);
}
sum(...[1, 2, 3]); // 6

// IIFE
(function() { return 42; })(); // 42
```

### Set & Map

```javascript
// Set — automatic deduplication
const unique = [...new Set([1, 1, 2, 3, 3, 4])];
console.log(unique); // [1, 2, 3, 4]

// Map — any key type
const m = new Map();
const objKey = { id: 1 };
m.set(objKey, "Object Value");
m.set("stringKey", 100);
m.get(objKey);      // "Object Value"
m.get("stringKey"); // 100
m.size;             // 2
```

### Control Flow

```javascript
// if/else, else if
// for, for...of, for...in
// while, do...while
// switch/case with break
// break & continue
// Labeled statements

for (const x of [10, 20, 30]) {
    console.log(x);
}
```

### Error Handling

```javascript
try {
    throw new Error("Something went wrong");
} catch (e) {
    console.log(e.message); // "Something went wrong"
} finally {
    console.log("Cleanup");
}
```

### Classes

```javascript
class Animal {
    constructor(name) {
        this.name = name;
    }
    speak() {
        return `${this.name} makes a sound`;
    }
}

class Dog extends Animal {
    speak() {
        return `${this.name} barks`;
    }
}
```

### Built-in Objects

| Object | Features |
|---|---|
| **console** | `log`, `error`, `warn`, `info`, `table`, `time`, `timeEnd` |
| **Math** | `floor`, `ceil`, `round`, `trunc`, `abs`, `pow`, `sqrt`, `min`, `max`, `random`, `sign`, `PI`, `E` |
| **Number** | `isNaN`, `isFinite`, `isInteger`, `parseInt`, `parseFloat`, `MAX_SAFE_INTEGER`, `EPSILON` |
| **Object** | `keys`, `values`, `entries`, `assign`, `freeze`, `create`, `getOwnPropertyNames` |
| **Array** | `isArray`, `from` |
| **JSON** | `stringify`, `parse` |
| **Date** | Constructor with `new Date()`, `toISOString()`, `getTime()` |
| **Set** | `add`, `has`, `delete`, `clear`, `size`, iterable via `for...of` |
| **Map** | `set`, `get`, `has`, `delete`, `clear`, `size`, iterable via `for...of` |

### Global Functions

`parseInt`, `parseFloat`, `isNaN`, `isFinite`, `NaN`, `Infinity`, `undefined`

### Special Values & Edge Cases

```javascript
typeof null;            // "object"  (the famous JS quirk)
typeof NaN;             // "number"
NaN === NaN;            // false
0.1 + 0.2;             // 0.30000000000000004
null + 1;              // 1  (null coerces to 0)
undefined + 1;         // NaN
[] instanceof Array;   // true
[] instanceof Object;  // true
5 instanceof Object;   // false
```

---

## Project Structure

```
js-interpreter/
├── main.py            # Entry point — REPL & file execution, auto-dependency install
├── interpreter.py     # Core tree-walking AST executor (44 node handlers)
├── environment.py     # Scope chain — var/let/const TDZ, hoisting, this binding
├── js_types.py        # JS runtime types — JSArray, JSObject, JSFunction, etc.
├── js_builtins.py     # Built-in objects — console, Math, Number, Object, etc.
├── test_suite.js      # Human-readable test suite (21 sections)
├── test_runner.py     # Automated test runner (215 tests)
├── requirements.txt   # Python dependencies (esprima)
└── README.md          # This file
```

### File Breakdown

| File | Lines | Purpose |
|---|---|---|
| `interpreter.py` | 2169 | The heart of the project. 44 `_exec_*` methods that walk every AST node type. Handles all JS semantics: coercion, closures, `this` binding, destructuring, spread, classes, try/catch, etc. |
| `js_types.py` | 1294 | Custom Python classes mirroring JS runtime types. Implements `js_to_number`, `js_to_string`, `js_to_boolean`, `js_abstract_equals`, `js_strict_equals` — faithfully reproducing JS coercion rules. |
| `js_builtins.py` | 578 | Injects the global environment with all built-in objects and functions. Includes `JSGlobalObject` that proxies property access to the Environment for correct `this` binding at global scope. |
| `main.py` | 211 | REPL with multi-line delimiter tracking, file execution mode, auto-dependency installation, and `clear`/`exit` commands. |
| `environment.py` | 168 | Scope chain implementation with `var` hoisting to nearest function scope, `let`/`const` TDZ enforcement, and `this` binding lookup. |
| `test_runner.py` | 326 | 215 automated tests comparing expected vs actual output across all JS features. |

**Total: ~4,745 lines of Python**

---

## Test Results

```
  Results: 215 passed, 0 failed, 0 errors
  Total:   215 tests
  Pass rate: 100.0%
```

Run the full suite:

```bash
python test_runner.py
```

The test suite covers all 22 sections of the syllabus:

1. Variables & Scope (10 tests)
2. Operators & Coercion (20 tests)
3. typeof (9 tests)
4. Short-circuit operators (8 tests)
5. Special Values (8 tests)
6. Arithmetic & Bitwise (15 tests)
7. Strings (11 tests)
8. Template Literals (2 tests)
9. Arrays (21 tests)
10. Objects (12 tests)
11. Destructuring (6 tests)
12. Functions & Closures (13 tests)
13. this Binding (2 tests)
14. Spread Operator (5 tests)
15. Set & Map (8 tests)
16. Control Flow (11 tests)
17. Math & Number (17 tests)
18. instanceof & in (4 tests)
19. JSON (3 tests)
20. Edge Cases (17 tests)
21. Destructuring with Defaults in Params (7 tests)
22. Integration (2 tests)

---

## Key Technical Highlights

### Temporal Dead Zone (TDZ)

Accessing a `let` or `const` variable before its declaration throws a `ReferenceError`, exactly like real JS:

```javascript
console.log(x);  // ReferenceError: Cannot access 'x' before initialization
let x = 5;
```

This is implemented via a `_TDZSentinel` value in the Environment that is detected on variable access.

### var Hoisting

`var` declarations are hoisted to the nearest function scope (or global), initialized to `undefined`:

```javascript
function test() {
    console.log(a);  // undefined (not ReferenceError!)
    var a = 100;
}
```

The Environment's `hoist_var()` method traverses up the scope chain to find the nearest function scope.

### `this` Binding & Arrow Functions

Regular functions get `this` from the call site. Arrow functions capture `this` lexically from their enclosing scope. The `JSGlobalObject` class proxies property access to the global Environment, ensuring `this` works correctly at the global scope:

```javascript
const obj = {
    value: 42,
    getValue() {
        return (() => this.value)();  // arrow captures 'this' from getValue
    }
};
obj.getValue(); // 42
```

### JavaScript Coercion Semantics

The interpreter faithfully reproduces all of JavaScript's type coercion rules, including the edge cases that trip up even experienced developers:

```javascript
null == undefined;   // true   (null only equals null and undefined)
null == 0;           // false  (null does NOT coerce to 0 in ==)
"" == false;         // true   (both coerce to 0)
"10" > "5";          // false  (string comparison, char by char)
"10" > 5;            // true   (numeric coercion when one operand is number)
```

### Spread & Rest

Full support for spread in arrays, objects, and function calls, plus rest parameters:

```javascript
// Spread in array literal
[...[1, 2], ...[3, 4]];  // [1, 2, 3, 4]

// Spread in function call
function add(a, b, c) { return a + b + c; }
add(...[10, 20, 30]);  // 60

// Spread in object
const merged = { ...{ x: 1 }, y: 2 }; // { x: 1, y: 2 }

// Rest parameters
function sum(...nums) {
    return nums.reduce((a, b) => a + b, 0);
}
```

### Destructuring with Defaults in Parameters

One of the trickiest features to implement — nested destructuring with default values in function parameters:

```javascript
const configure = ({
    db: { host = "localhost", port = 3306 } = {}
} = {}) => `${host}:${port}`;

configure();                          // "localhost:3306"
configure({ db: { host: "prod" } }); // "prod:3306"
```

This requires storing the destructuring pattern separately from the parameter name, then applying the pattern after evaluating the default value.

---

## How It Works

### Step-by-step Execution Flow

```
JavaScript Source Code
        │
        ▼
   ┌──────────┐
   │  esprima │  ── Parse to AST
   │  parser  │
   └────┬─────┘
        │
        ▼
   ┌──────────────┐
   │ Preprocessor │  ── Replace `??` with helper function
   └────┬─────────┘
        │
        ▼
   ┌──────────────┐
   │  Hoisting    │  ── Scan for var/function declarations
   │    Phase     │     Initialize vars to undefined,
   └────┬─────────┘     function declarations to their values
        │
        ▼
   ┌──────────────┐
   │   Execute    │  ── Walk the AST node by node
   │    Phase     │     _exec_Program → _exec_Statement → _exec_Expression
   └──────────────┘     Recursively evaluates each node type
```

### The Hoisting Phase

Before executing any code, the interpreter scans the entire program for:

1. **`var` declarations** → hoisted to nearest function scope, initialized to `undefined`
2. **Function declarations** → hoisted with their full function value (so you can call them before they appear in source)
3. **`let`/`const` declarations** → entered into scope but marked as TDZ (accessing before initialization throws `ReferenceError`)

This two-phase approach exactly mirrors how real JavaScript engines work.

---

## Dependencies

| Package | Purpose |
|---|---|
| `esprima` | Production-grade ES6+ JavaScript parser — converts source code to AST |

That's the only dependency. Everything else is written from scratch.

---

## Limitations & Known Issues

- **REPL method chaining**: Multi-line method chains pasted into the REPL (where each `.method()` is on a new line) cause `SyntaxError`. This works correctly when run as a file. This is a REPL input-collection limitation, not an interpreter limitation.
- **Async/await**: Not implemented (not in the syllabus).
- **Generators/yield**: Not implemented.
- **Proxies/Reflect**: Not implemented.
- **RegExp exec details**: Basic regex support exists but advanced features (named groups, lookbehind) are limited by Python's `re` module.
- **`with` statement**: Handler exists but with minimal semantics (not recommended in modern JS anyway).

---

## License

This project was built for **Thunder Hackathon 2.0**.

---

## Team

Built with dedication for Thunder Hackathon 2.0 — proving that building a JavaScript runtime from scratch is not just possible, it's enlightening.
