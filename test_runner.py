"""
Automated test runner for the Thunder JS Interpreter.
Compares expected output against actual output.

Usage:
  python test_runner.py
"""
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interpreter import Interpreter
from js_types import UNDEFINED, js_format_output


# (test_name, js_code, expected_output)
TESTS = [
    # ─── SECTION 1: Variables & Scope ─────────────────────────────
    ("var hoisting", "console.log(x); var x = 5;", "undefined"),
    ("var after assign", "var x = 5; console.log(x);", "5"),
    ("let basic", "let y = 10; console.log(y);", "10"),
    ("const basic", "const z = 15; console.log(z);", "15"),
    ("block scope let", "{ let x = 20; } console.log(typeof x);", "undefined"),
    ("var function scope", "function f() { var x = 10; } f(); console.log(typeof x);", "undefined"),
    ("var hoisting in func", "function f() { console.log(a); var a = 100; console.log(a); } f();", "undefined\n100"),
    ("function hoisting", "console.log(hoisted()); function hoisted() { return 'hoisted'; }", "hoisted"),
    ("func expression not hoisted", "console.log(typeof notHoisted); var notHoisted = function() {};", "undefined"),
    ("shadowing", "let s = 'outer'; { let s = 'inner'; console.log(s); }", "inner"),

    # ─── SECTION 2: Operators & Coercion ──────────────────────────
    ("string+number", 'console.log("5" + 3);', "53"),
    ("number+string", 'console.log(3 + "5");', "35"),
    ("string-number", 'console.log("5" - 3);', "2"),
    ("string-string", 'console.log("10" - "3");', "7"),
    ("nonNumeric-string-3", 'console.log("hello" - 3);', "NaN"),
    ("true+1", "console.log(true + 1);", "2"),
    ("false+1", "console.log(false + 1);", "1"),
    ("loose 5=='5'", 'console.log(5 == "5");', "true"),
    ("loose 0==''", 'console.log(0 == "");', "true"),
    ("loose 0==false", "console.log(0 == false);", "true"),
    ("loose ''==false", 'console.log("" == false);', "true"),
    ("loose null==undefined", "console.log(null == undefined);", "true"),
    ("loose null==0", "console.log(null == 0);", "false"),
    ("strict 5==='5'", 'console.log(5 === "5");', "false"),
    ("strict 5===5", "console.log(5 === 5);", "true"),
    ("strict null===undefined", "console.log(null === undefined);", "false"),
    ("comparison 10>'5'", 'console.log(10 > "5");', "true"),
    ("comparison '10'>'5'", 'console.log("10" > "5");', "false"),
    ("comparison '10'>5", 'console.log("10" > 5);', "true"),

    # ─── SECTION 3: typeof ────────────────────────────────────────
    ("typeof 42", "console.log(typeof 42);", "number"),
    ("typeof string", 'console.log(typeof "hello");', "string"),
    ("typeof true", "console.log(typeof true);", "boolean"),
    ("typeof undefined", "console.log(typeof undefined);", "undefined"),
    ("typeof null", "console.log(typeof null);", "object"),
    ("typeof object", "console.log(typeof {});", "object"),
    ("typeof array", "console.log(typeof []);", "object"),
    ("typeof function", "console.log(typeof function(){});", "function"),
    ("typeof arrow", "console.log(typeof (() => 1));", "function"),

    # ─── SECTION 4: Short-circuit ─────────────────────────────────
    ("0||default", 'console.log(0 || "default");', "default"),
    ("1||default", 'console.log(1 || "default");', "1"),
    ("0&&default", 'console.log(0 && "default");', "0"),
    ("1&&default", 'console.log(1 && "default");', "default"),
    ("null??default", 'console.log(null ?? "default");', "default"),
    ("undefined??default", 'console.log(undefined ?? "default");', "default"),
    ("0??default", 'console.log(0 ?? "default");', "0"),
    ("empty??default", 'console.log("" ?? "default");', ""),

    # ─── SECTION 5: Special Values ────────────────────────────────
    ("0.1+0.2", "console.log(0.1 + 0.2);", "0.30000000000000004"),
    ("0.1+0.2===0.3", "console.log(0.1 + 0.2 === 0.3);", "false"),
    ("NaN===NaN", "console.log(NaN === NaN);", "false"),
    ("isNaN(NaN)", "console.log(isNaN(NaN));", "true"),
    ("typeof NaN", "console.log(typeof NaN);", "number"),
    ("Infinity", "console.log(Infinity);", "Infinity"),
    ("-Infinity", "console.log(-Infinity);", "-Infinity"),
    ("1/0", "console.log(1 / 0);", "Infinity"),

    # ─── SECTION 6: Arithmetic & Bitwise ──────────────────────────
    ("addition", "console.log(10 + 3);", "13"),
    ("subtraction", "console.log(10 - 3);", "7"),
    ("multiplication", "console.log(10 * 3);", "30"),
    ("modulo", "console.log(10 % 3);", "1"),
    ("exponent", "console.log(2 ** 10);", "1024"),
    ("postfix++", "let a = 5; console.log(a++);", "5"),
    ("after postfix++", "let a = 5; a++; console.log(a);", "6"),
    ("prefix++", "let b = 5; console.log(++b);", "6"),
    ("5&3", "console.log(5 & 3);", "1"),
    ("5|3", "console.log(5 | 3);", "7"),
    ("5^3", "console.log(5 ^ 3);", "6"),
    ("~5", "console.log(~5);", "-6"),
    ("1<<3", "console.log(1 << 3);", "8"),
    ("8>>2", "console.log(8 >> 2);", "2"),

    # ─── SECTION 7: Strings ───────────────────────────────────────
    ("str.length", 'console.log("hello".length);', "5"),
    ("toUpperCase", 'console.log("hello".toUpperCase());', "HELLO"),
    ("toLowerCase", 'console.log("HELLO".toLowerCase());', "hello"),
    ("indexOf", 'console.log("hello world".indexOf("world"));', "6"),
    ("includes true", 'console.log("hello".includes("ell"));', "true"),
    ("includes false", 'console.log("hello".includes("xyz"));', "false"),
    ("slice", 'console.log("hello".slice(1, 3));', "el"),
    ("trim", 'console.log("  hi  ".trim());', "hi"),
    ("split", 'console.log("a-b-c".split("-"));', '["a", "b", "c"]'),
    ("join", 'console.log(["a","b","c"].join("-"));', "a-b-c"),
    ("replace", 'console.log("hello world".replace("world", "JS"));', "hello JS"),

    # ─── SECTION 8: Template Literals ─────────────────────────────
    ("template basic", 'let x = 5; console.log(`val: ${x}`);', "val: 5"),
    ("template expr", 'console.log(`${2 + 3}`);', "5"),

    # ─── SECTION 9: Arrays ────────────────────────────────────────
    ("arr.length", "console.log([1,2,3].length);", "3"),
    ("arr[0]", "console.log([10,20,30][0]);", "10"),
    ("push", "let a = [1]; a.push(2); console.log(a);", "[1, 2]"),
    ("pop", "let a = [1,2,3]; a.pop(); console.log(a);", "[1, 2]"),
    ("unshift", "let a = [2,3]; a.unshift(1); console.log(a);", "[1, 2, 3]"),
    ("shift", "let a = [1,2,3]; a.shift(); console.log(a);", "[2, 3]"),
    ("slice", "console.log([1,2,3,4,5].slice(1,3));", "[2, 3]"),
    ("splice", "let a = [1,2,3,4,5]; a.splice(1,2); console.log(a);", "[1, 4, 5]"),
    ("indexOf", "console.log([1,2,3,2,1].indexOf(2));", "1"),
    ("lastIndexOf", "console.log([1,2,3,2,1].lastIndexOf(2));", "3"),
    ("includes true", "console.log([1,2,3].includes(2));", "true"),
    ("includes false", "console.log([1,2,3].includes(99));", "false"),
    ("sort default", "console.log([10,2,30,1].sort());", "[1, 10, 2, 30]"),
    ("sort numeric", "console.log([10,2,30,1].sort((a,b)=>a-b));", "[1, 2, 10, 30]"),
    ("reverse", "console.log([1,2,3].reverse());", "[3, 2, 1]"),
    ("flat", "console.log([1,[2,[3,[4]]]].flat(Infinity));", "[1, 2, 3, 4]"),
    ("concat", "console.log([1,2].concat([3,4]));", "[1, 2, 3, 4]"),
    ("map", "console.log([1,2,3].map(x=>x*2));", "[2, 4, 6]"),
    ("filter", "console.log([1,2,3,4,5].filter(x=>x>3));", "[4, 5]"),
    ("reduce", "console.log([1,2,3,4].reduce((a,b)=>a+b,0));", "10"),
    ("find", "console.log([1,2,3,4].find(x=>x>2));", "3"),
    ("find none", "console.log([1,2,3].find(x=>x>10));", "undefined"),
    ("some true", "console.log([1,2,3].some(x=>x>2));", "true"),
    ("some false", "console.log([1,2,3].some(x=>x>10));", "false"),
    ("every true", "console.log([1,2,3].every(x=>x>0));", "true"),
    ("every false", "console.log([1,2,3].every(x=>x>2));", "false"),

    # ─── SECTION 10: Objects ───────────────────────────────────────
    ("obj.dot", 'console.log({name:"Alice"}.name);', "Alice"),
    ("obj.bracket", 'console.log({name:"Alice"}["name"]);', "Alice"),
    ("in operator true", 'console.log("name" in {name:"Alice"});', "true"),
    ("in operator false", 'console.log("age" in {name:"Alice"});', "false"),
    ("delete operator", 'let o = {a:1,b:2}; delete o.a; console.log("a" in o);', "false"),
    ("Object.keys", 'console.log(Object.keys({x:1,y:2}));', '["x", "y"]'),
    ("Object.values", 'console.log(Object.values({x:1,y:2}));', "[1, 2]"),
    ("Object.assign", 'let t={a:1}; Object.assign(t,{b:2}); console.log(t);', "{ a: 1, b: 2 }"),
    ("computed prop", 'let k="name"; let o={[k]:"Alice"}; console.log(o.name);', "Alice"),
    ("for...in", 'let r=""; for(let k in {a:1,b:2}){r+=k;} console.log(r);', "ab"),
    ("spread object", 'console.log({...{x:1}, y:2});', "{ x: 1, y: 2 }"),
    ("this in method", 'console.log({n:"A",g(){return this.n}}.g());', "A"),

    # ─── SECTION 11: Destructuring ────────────────────────────────
    ("array destr", "const [a,b] = [1,2]; console.log(a,b);", "1 2"),
    ("array destr skip", "const [,b,,d] = [10,20,30,40]; console.log(b,d);", "20 40"),
    ("array destr rest", "const [a,...r] = [1,2,3,4]; console.log(a,r);", "1 [2, 3, 4]"),
    ("obj destr rename", 'const {name:n} = {name:"Alice"}; console.log(n);', "Alice"),
    ("obj destr default", "const {x=10} = {}; console.log(x);", "10"),
    ("obj destr default override", "const {x=10} = {x:5}; console.log(x);", "5"),

    # ─── SECTION 12: Functions & Closures ──────────────────────────
    ("func declaration", "function add(a,b){return a+b;} console.log(add(3,4));", "7"),
    ("func expression", "const m = function(a,b){return a*b;}; console.log(m(3,4));", "12"),
    ("arrow implicit", "const sq = (x) => x*x; console.log(sq(5));", "25"),
    ("arrow single param", "const d = x => x*2; console.log(d(7));", "14"),
    ("arrow with body", 'const g = (n) => {return "Hi "+n;}; console.log(g("A"));', "Hi A"),
    ("default param", 'function g(n="World"){return "Hello "+n;} console.log(g());', "Hello World"),
    ("default param override", 'function g(n="World"){return "Hello "+n;} console.log(g("JS"));', "Hello JS"),
    ("rest params", "function s(...n){return n.reduce((a,b)=>a+b,0);} console.log(s(1,2,3));", "6"),
    ("closure counter", "function c(){let n=0; return ()=>{n++; return n;};} const f=c(); console.log(f(),f(),f());", "1 2 3"),
    ("closure adder", "function adder(x){return y=>x+y;} console.log(adder(5)(3));", "8"),
    ("IIFE", "console.log((function(){return 42;})());", "42"),
    ("typeof func", "console.log(typeof function(){});", "function"),
    ("typeof arrow", "console.log(typeof (()=>1));", "function"),

    # ─── SECTION 13: this Binding ──────────────────────────────────
    ("this method", 'const o={n:"A",g(){return this.n;}}; console.log(o.g());', "A"),
    ("arrow lexical this", 'const o={v:42,g(){return(()=>this.v)();}}; console.log(o.g());', "42"),

    # ─── SECTION 14: Spread Operator ──────────────────────────────
    ("spread arrays", "console.log([...[1,2],...[3,4]]);", "[1, 2, 3, 4]"),
    ("spread copy", "let a=[1,2,3]; let b=[...a]; b.push(4); console.log(a.length);", "3"),
    ("spread in call", "function s(a,b,c){return a+b+c;} console.log(s(...[1,2,3]));", "6"),
    ("spread object", "console.log({...{x:1},y:2});", "{ x: 1, y: 2 }"),
    ("spread override", "let o={...{x:1,y:2},y:99}; console.log(o.y);", "99"),

    # ─── SECTION 15: Set & Map ────────────────────────────────────
    ("Set add/size", "const s=new Set(); s.add(1); s.add(2); s.add(1); console.log(s.size);", "2"),
    ("Set has", "const s=new Set([1,2,3]); console.log(s.has(2));", "true"),
    ("Set delete", "const s=new Set([1,2,3]); s.delete(2); console.log(s.has(2));", "false"),
    ("Set dedup", "console.log([...new Set([1,2,2,3,3])]);", "[1, 2, 3]"),
    ("for...of Set", "let r=0; for(const v of new Set([10,20,30])){r+=v;} console.log(r);", "60"),
    ("Map set/get", 'const m=new Map(); m.set("k","v"); console.log(m.get("k"));', "v"),
    ("Map size", 'const m=new Map(); m.set("a",1).set("b",2); console.log(m.size);', "2"),
    ("Map has/delete", 'const m=new Map(); m.set("k","v"); m.delete("k"); console.log(m.has("k"));', "false"),

    # ─── SECTION 16: Control Flow ──────────────────────────────────
    ("if/else", "let x=10; if(x>5){console.log('big');}else{console.log('small');}", "big"),
    ("else if", "let g=85; if(g>=90){console.log('A');}else if(g>=80){console.log('B');}else{console.log('C');}", "B"),
    ("for loop", "let r=''; for(let i=0;i<5;i++){r+=i;} console.log(r);", "01234"),
    ("for...of", "let r=''; for(const x of [10,20,30]){r+=x+' ';} console.log(r.trim());", "10 20 30"),
    ("for...in", 'let r=""; for(const k in {a:1,b:2}){r+=k;} console.log(r);', "ab"),
    ("while", "let i=0,r=''; while(i<3){r+=i;i++;} console.log(r);", "012"),
    ("do...while", "let i=0,r=''; do{r+=i;i++;}while(i<3); console.log(r);", "012"),
    ("do...while once", "let i=10,r=''; do{r+=i;i++;}while(i<5); console.log(r);", "10"),
    ("break", "let r=''; for(let i=0;i<10;i++){if(i===3)break;r+=i;} console.log(r);", "012"),
    ("continue", "let r=''; for(let i=0;i<6;i++){if(i===3)continue;r+=i;} console.log(r);", "01245"),
    ("switch", 'let d="M"; let t; switch(d){case "M":t="w";break;default:t="u";} console.log(t);', "w"),

    # ─── SECTION 17: Math & Number ────────────────────────────────
    ("Math.floor", "console.log(Math.floor(4.7));", "4"),
    ("Math.ceil", "console.log(Math.ceil(4.2));", "5"),
    ("Math.round", "console.log(Math.round(4.5));", "5"),
    ("Math.abs", "console.log(Math.abs(-5));", "5"),
    ("Math.pow", "console.log(Math.pow(2,10));", "1024"),
    ("Math.sqrt", "console.log(Math.sqrt(16));", "4"),
    ("Math.max", "console.log(Math.max(1,5,3));", "5"),
    ("Math.min", "console.log(Math.min(1,5,3));", "1"),
    ("parseInt str", 'console.log(parseInt("42"));', "42"),
    ("parseInt hex", 'console.log(parseInt("0xFF",16));', "255"),
    ("parseInt NaN", 'console.log(parseInt("hello"));', "NaN"),
    ("parseFloat", 'console.log(parseFloat("3.14"));', "3.14"),
    ("Number.isNaN true", "console.log(Number.isNaN(NaN));", "true"),
    ("Number.isNaN false", 'console.log(Number.isNaN("hello"));', "false"),
    ("Number.isFinite", "console.log(Number.isFinite(42));", "true"),
    ("Number.isInteger true", "console.log(Number.isInteger(5));", "true"),
    ("Number.isInteger false", "console.log(Number.isInteger(5.5));", "false"),

    # ─── SECTION 18: instanceof & in ──────────────────────────────
    ("[] instanceof Array", "console.log([] instanceof Array);", "true"),
    ("[] instanceof Object", "console.log([] instanceof Object);", "true"),
    ("{} instanceof Object", "console.log({} instanceof Object);", "true"),
    ("5 instanceof Object", "console.log(5 instanceof Object);", "false"),

    # ─── SECTION 19: JSON ─────────────────────────────────────────
    ("JSON.stringify obj", 'console.log(JSON.stringify({a:1}));', '{"a":1}'),
    ("JSON.stringify arr", "console.log(JSON.stringify([1,2,3]));", "[1,2,3]"),
    ("JSON.parse", 'console.log(JSON.parse(\'{"x":1}\').x);', "1"),

    # ─── SECTION 20: Edge Cases ────────────────────────────────────
    ("null+1", "console.log(null + 1);", "1"),
    ("undefined+1", "console.log(undefined + 1);", "NaN"),
    ("true+true+true", "console.log(true + true + true);", "3"),
    ("false==0", "console.log(false == 0);", "true"),
    ("true==1", "console.log(true == 1);", "true"),
    ("void 0", "console.log(void 0);", "undefined"),
    ("comma operator", "console.log((1,2,3));", "3"),
    ("Number('42')", 'console.log(Number("42"));', "42"),
    ("Number('')", 'console.log(Number(""));', "0"),
    ("Number('hello')", 'console.log(Number("hello"));', "NaN"),
    ("Number(null)", "console.log(Number(null));", "0"),
    ("Number(undefined)", "console.log(Number(undefined));", "NaN"),
    ("+true", "console.log(+true);", "1"),
    ("+false", "console.log(+false);", "0"),
    ("+null", "console.log(+null);", "0"),
    ("+undefined", "console.log(+undefined);", "NaN"),
    ("!!value", 'console.log(!!"hello");', "true"),

    # ─── SECTION 21: Destructuring with Defaults in Params ─────────
    ("obj destr default param", 'const f = ({ name, age = 20 } = {}) => `${name} is ${age}`; console.log(f({ name: "Alex" }));', "Alex is 20"),
    ("obj destr default no arg", 'const f = ({ name, age = 20 } = {}) => `${name} is ${age}`; console.log(f());', "undefined is 20"),
    ("obj destr default full arg", 'const f = ({ name, age = 20 } = {}) => `${name} is ${age}`; console.log(f({ name: "Bob", age: 30 }));', "Bob is 30"),
    ("arr destr default param", 'const head = ([first = 0] = []) => first; console.log(head([5]));', "5"),
    ("arr destr default no arg", 'const head = ([first = 0] = []) => first; console.log(head());', "0"),
    ("arr destr default empty arr", 'const head = ([first = 0] = []) => first; console.log(head([]));', "0"),
    ("nested destr default param", 'const cfg = ({ db: { host = "localhost", port = 3306 } = {} } = {}) => `${host}:${port}`; console.log(cfg());', "localhost:3306"),
    ("nested destr default override", 'const cfg = ({ db: { host = "localhost", port = 3306 } = {} } = {}) => `${host}:${port}`; console.log(cfg({ db: { host: "prod" } }));', "prod:3306"),

    # ─── SECTION 22: Integration ──────────────────────────────────
    ("chained methods", "[1,2,3,4,5,6,7,8,9,10].filter(n=>n%2===0).map(n=>n*3).reduce((a,b)=>a+b,0)", None),  # just no crash
    ("real-world map/filter", "const r=[1,2,3,4,5].filter(x=>x>3).map(x=>x*10); console.log(r);", "[40, 50]"),
]


def run_tests():
    passed = 0
    failed = 0
    errors = 0

    for name, code, expected in TESTS:
        interp = Interpreter()
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        try:
            interp.execute(code)
            output = buffer.getvalue().strip()
            sys.stdout = old_stdout

            if expected is not None:
                if output == expected:
                    print(f"  ✓ {name}")
                    passed += 1
                else:
                    print(f"  ✗ {name}")
                    print(f"    Expected: {repr(expected)}")
                    print(f"    Got:      {repr(output)}")
                    failed += 1
            else:
                # Just check it doesn't crash
                print(f"  ✓ {name} (no crash)")
                passed += 1
        except Exception as e:
            sys.stdout = old_stdout
            print(f"  ✗ {name}")
            print(f"    ERROR: {e}")
            errors += 1

    print()
    print(f"{'='*50}")
    print(f"  Results: {passed} passed, {failed} failed, {errors} errors")
    total = passed + failed + errors
    print(f"  Total:   {total} tests")
    print(f"  Pass rate: {passed/total*100:.1f}%")
    print(f"{'='*50}")

    return failed == 0 and errors == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
