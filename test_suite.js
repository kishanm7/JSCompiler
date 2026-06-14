// ╔══════════════════════════════════════════════════════════════╗
// ║  Thunder JS Interpreter — Full Test Suite                  ║
// ║  Run: python main.py test_suite.js                         ║
// ╚══════════════════════════════════════════════════════════════╝

console.log("═══════════════════════════════════════════");
console.log("  SECTION 1: VARIABLES & SCOPE");
console.log("═══════════════════════════════════════════");

// var hoisting
console.log("--- var hoisting ---");
console.log(x);          // undefined (hoisted)
var x = 5;
console.log(x);          // 5

// let with TDZ
console.log("--- let ---");
let y = 10;
console.log(y);          // 10

// const
console.log("--- const ---");
const z = 15;
console.log(z);          // 15

// Block scope
console.log("--- block scope ---");
{
    let blockVar = 20;
    var funcVar = 25;
    console.log(blockVar);  // 20
}
console.log(funcVar);       // 25 (var is function-scoped)
console.log(typeof blockVar);  // undefined (let is block-scoped)

// var function scope
console.log("--- var function scope ---");
function testVarScope() {
    var inner = 30;
}
testVarScope();
console.log(typeof inner);  // undefined

// var hoisting inside function
console.log("--- var hoisting in function ---");
function testHoist() {
    console.log(a);  // undefined
    var a = 100;
    console.log(a);  // 100
}
testHoist();

// Function hoisting
console.log("--- function hoisting ---");
console.log(hoistedFunc());  // "I'm hoisted!"
function hoistedFunc() { return "I'm hoisted!"; }

// Function expression NOT hoisted
console.log("--- function expression not hoisted ---");
console.log(typeof notHoisted);  // undefined
var notHoisted = function() { return "not hoisted"; };

// Shadowing
console.log("--- shadowing ---");
let shadow = "outer";
{
    let shadow = "inner";
    console.log(shadow);  // inner
}
console.log(shadow);  // outer


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 2: OPERATORS & TYPE COERCION");
console.log("═══════════════════════════════════════════");

// String + Number = String concatenation
console.log("--- string + number ---");
console.log("5" + 3);         // "53"
console.log(3 + "5");         // "35"
console.log("hello" + 5);    // "hello5"

// String - Number = Number subtraction
console.log("--- string - number ---");
console.log("5" - 3);         // 2
console.log("10" - "3");      // 7
console.log("hello" - 3);     // NaN

// Boolean arithmetic
console.log("--- boolean arithmetic ---");
console.log(true + 1);        // 2
console.log(false + 1);       // 1
console.log(true + true);     // 2
console.log(true * 5);        // 5

// Loose equality (==)
console.log("--- loose equality == ---");
console.log(5 == "5");           // true
console.log(0 == "");            // true
console.log(0 == false);         // true
console.log("" == false);        // true
console.log(null == undefined);  // true
console.log(null == 0);          // false
console.log(null == "");         // false
console.log(undefined == 0);     // false
console.log(undefined == "");    // false
console.log(1 == true);          // true

// Strict equality (===)
console.log("--- strict equality === ---");
console.log(5 === "5");          // false
console.log(5 === 5);            // true
console.log(null === undefined);  // false
console.log(null === null);       // true
console.log(undefined === undefined);  // true

// Comparison operators
console.log("--- comparison ---");
console.log(5 > 3);             // true
console.log(5 < 3);             // false
console.log(5 >= 5);            // true
console.log(5 <= 4);            // false
console.log(10 > "5");          // true (numeric coercion)
console.log("10" > "5");        // false (lexicographic)
console.log("10" > 5);          // true (numeric coercion)

// Unary operators
console.log("--- unary operators ---");
console.log(typeof 42);         // number
console.log(typeof "hello");    // string
console.log(typeof true);       // boolean
console.log(typeof undefined);  // undefined
console.log(typeof null);       // object (the bug!)
console.log(typeof {});         // object
console.log(typeof []);         // object
console.log(typeof function(){});  // function

// Unary plus/minus
console.log("--- unary plus/minus ---");
console.log(+"5");             // 5
console.log(+"hello");         // NaN
console.log(-"5");             // -5
console.log(+true);            // 1
console.log(+false);           // 0
console.log(+null);            // 0
console.log(+undefined);       // NaN

// Logical NOT
console.log("--- logical NOT ---");
console.log(!true);            // false
console.log(!false);           // true
console.log(!0);               // true
console.log(!"");              // true
console.log(!null);            // true
console.log(!undefined);       // true
console.log(!1);               // false
console.log(!"hello");         // false
console.log(!!"hello");        // true (double negation to boolean)


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 3: SHORT-CIRCUIT & LOGICAL");
console.log("═══════════════════════════════════════════");

// || returns first truthy or last value
console.log("--- || short-circuit ---");
console.log(0 || "default");       // "default"
console.log(1 || "default");       // 1
console.log("" || "fallback");     // "fallback"
console.log(null || "fallback");   // "fallback"
console.log(undefined || "fb");    // "fb"
console.log("first" || "second");  // "first"

// && returns first falsy or last value
console.log("--- && short-circuit ---");
console.log(0 && "default");       // 0
console.log(1 && "default");       // "default"
console.log("" && "fallback");     // ""
console.log(null && "fallback");   // null
console.log("first" && "second");  // "second"

// Nullish coalescing ??
console.log("--- ?? nullish coalescing ---");
console.log(null ?? "default");     // "default"
console.log(undefined ?? "default"); // "default"
console.log(0 ?? "default");        // 0
console.log("" ?? "default");       // ""
console.log(false ?? "default");    // false
console.log("value" ?? "default");  // "value"


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 4: SPECIAL VALUES");
console.log("═══════════════════════════════════════════");

// Floating point inaccuracy
console.log("--- floating point ---");
console.log(0.1 + 0.2);                    // 0.30000000000000004
console.log(0.1 + 0.2 === 0.3);            // false

// NaN
console.log("--- NaN ---");
console.log(NaN === NaN);                   // false
console.log(NaN == NaN);                    // false
console.log(typeof NaN);                    // number
console.log(isNaN(NaN));                    // true
console.log(isNaN("hello"));                // true
console.log(isNaN(42));                     // false

// Infinity
console.log("--- Infinity ---");
console.log(Infinity);                      // Infinity
console.log(-Infinity);                     // -Infinity
console.log(1 / 0);                         // Infinity
console.log(-1 / 0);                        // -Infinity
console.log(Infinity > 1000);               // true
console.log(-Infinity < -1000);             // true


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 5: ARITHMETIC & BITWISE");
console.log("═══════════════════════════════════════════");

console.log("--- arithmetic ---");
console.log(10 + 3);       // 13
console.log(10 - 3);       // 7
console.log(10 * 3);       // 30
console.log(10 / 3);       // 3.333...
console.log(10 % 3);       // 1
console.log(2 ** 10);      // 1024

console.log("--- increment/decrement ---");
let a = 5;
console.log(a++);          // 5 (postfix returns old value)
console.log(a);            // 6
let b = 5;
console.log(++b);          // 6 (prefix returns new value)
console.log(b);            // 6
let c = 5;
console.log(c--);          // 5
console.log(c);            // 4
let d = 5;
console.log(--d);          // 4
console.log(d);            // 4

console.log("--- compound assignment ---");
let e = 10;
e += 5;
console.log(e);            // 15
e -= 3;
console.log(e);            // 12
e *= 2;
console.log(e);            // 24
e /= 4;
console.log(e);            // 6

console.log("--- bitwise ---");
console.log(5 & 3);        // 1
console.log(5 | 3);        // 7
console.log(5 ^ 3);        // 6
console.log(~5);           // -6
console.log(~0);           // -1
console.log(1 << 3);       // 8
console.log(8 >> 2);       // 2
console.log(-1 >> 1);      // -1 (sign-propagating)


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 6: STRINGS & TEMPLATE LITERALS");
console.log("═══════════════════════════════════════════");

console.log("--- basic string ---");
let str = "Hello, World!";
console.log(str.length);               // 13
console.log(str[0]);                    // "H"
console.log(str.toUpperCase());         // "HELLO, WORLD!"
console.log(str.toLowerCase());         // "hello, world!"
console.log(str.indexOf("World"));      // 7
console.log(str.indexOf("xyz"));        // -1
console.log(str.includes("World"));     // true
console.log(str.includes("xyz"));       // false
console.log(str.slice(0, 5));           // "Hello"
console.log(str.slice(7));              // "World!"
console.log("  hi  ".trim());           // "hi"
console.log("  hi  ".trimStart());      // "hi  "
console.log("  hi  ".trimEnd());        // "  hi"

console.log("--- split/join ---");
console.log("a-b-c".split("-"));        // ["a", "b", "c"]
console.log("hello".split(""));         // ["h", "e", "l", "l", "o"]
console.log(["a", "b", "c"].join("-")); // "a-b-c"

console.log("--- replace ---");
console.log("hello world".replace("world", "JS"));  // "hello JS"

console.log("--- charAt ---");
console.log("hello".charAt(1));          // "e"

console.log("--- template literals ---");
let name = "Alice";
let age = 25;
console.log(`Hello, ${name}!`);          // "Hello, Alice!"
console.log(`${name} is ${age} years old`);  // "Alice is 25 years old"
console.log(`2 + 3 = ${2 + 3}`);         // "2 + 3 = 5"

console.log("--- multi-line template ---");
let multi = `Line1
Line2
Line3`;
console.log(multi);


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 7: ARRAYS");
console.log("═══════════════════════════════════════════");

console.log("--- basic array ---");
let arr = [1, 2, 3, 4, 5];
console.log(arr.length);         // 5
console.log(arr[0]);             // 1
console.log(arr[4]);             // 5

console.log("--- push/pop ---");
let arr1 = [1, 2];
arr1.push(3);
console.log(arr1);               // [1, 2, 3]
let popped = arr1.pop();
console.log(popped);             // 3
console.log(arr1);               // [1, 2]

console.log("--- unshift/shift ---");
let arr2 = [2, 3];
arr2.unshift(1);
console.log(arr2);               // [1, 2, 3]
let shifted = arr2.shift();
console.log(shifted);            // 1
console.log(arr2);               // [2, 3]

console.log("--- slice ---");
let arr3 = [1, 2, 3, 4, 5];
console.log(arr3.slice(1, 3));   // [2, 3]
console.log(arr3.slice(2));      // [3, 4, 5]
console.log(arr3.slice());       // [1, 2, 3, 4, 5] (copy)

console.log("--- splice ---");
let arr4 = [1, 2, 3, 4, 5];
arr4.splice(1, 2);
console.log(arr4);               // [1, 4, 5]

console.log("--- indexOf/includes ---");
let arr5 = [1, 2, 3, 2, 1];
console.log(arr5.indexOf(2));    // 1
console.log(arr5.lastIndexOf(2)); // 3
console.log(arr5.includes(3));   // true
console.log(arr5.includes(99));  // false

console.log("--- sort (lexicographic default!) ---");
let arr6 = [10, 2, 30, 1];
console.log(arr6.sort());        // [1, 10, 2, 30] (lexicographic!)

console.log("--- sort with compare function ---");
let arr7 = [10, 2, 30, 1];
console.log(arr7.sort((a, b) => a - b));  // [1, 2, 10, 30]

console.log("--- reverse ---");
let arr8 = [1, 2, 3];
console.log(arr8.reverse());     // [3, 2, 1]

console.log("--- flat ---");
console.log([1, [2, [3, [4]]]].flat(Infinity));  // [1, 2, 3, 4]

console.log("--- concat ---");
console.log([1, 2].concat([3, 4]));  // [1, 2, 3, 4]

console.log("--- join ---");
console.log([1, 2, 3].join(", "));   // "1, 2, 3"

console.log("--- forEach ---");
let forEachResult = [];
[1, 2, 3].forEach(x => forEachResult.push(x * 2));
console.log(forEachResult);       // [2, 4, 6]

console.log("--- map ---");
console.log([1, 2, 3].map(x => x * 2));  // [2, 4, 6]

console.log("--- filter ---");
console.log([1, 2, 3, 4, 5].filter(x => x > 3));  // [4, 5]

console.log("--- reduce ---");
console.log([1, 2, 3, 4].reduce((acc, val) => acc + val, 0));  // 10

console.log("--- find ---");
console.log([1, 2, 3, 4].find(x => x > 2));  // 3
console.log([1, 2, 3, 4].find(x => x > 10)); // undefined

console.log("--- findIndex ---");
console.log([1, 2, 3, 4].findIndex(x => x > 2));  // 2

console.log("--- some ---");
console.log([1, 2, 3].some(x => x > 2));    // true
console.log([1, 2, 3].some(x => x > 10));   // false

console.log("--- every ---");
console.log([1, 2, 3].every(x => x > 0));   // true
console.log([1, 2, 3].every(x => x > 2));   // false


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 8: OBJECTS");
console.log("═══════════════════════════════════════════");

console.log("--- basic object ---");
let obj = { name: "Alice", age: 25 };
console.log(obj.name);              // "Alice"
console.log(obj["age"]);            // 25
console.log("name" in obj);         // true
console.log("email" in obj);        // false

console.log("--- add/update/delete ---");
obj.email = "alice@test.com";
console.log(obj.email);             // "alice@test.com"
obj.age = 26;
console.log(obj.age);               // 26
delete obj.email;
console.log("email" in obj);        // false

console.log("--- methods & this ---");
let person = {
    name: "Bob",
    greet() { return "Hello, " + this.name; }
};
console.log(person.greet());        // "Hello, Bob"

console.log("--- Object.keys/values/entries ---");
let obj2 = { x: 1, y: 2, z: 3 };
console.log(Object.keys(obj2));     // ["x", "y", "z"]
console.log(Object.values(obj2));   // [1, 2, 3]

console.log("--- Object.assign ---");
let target = { a: 1 };
let source = { b: 2, c: 3 };
Object.assign(target, source);
console.log(target);                // { a: 1, b: 2, c: 3 }

console.log("--- computed property names ---");
let key = "dynamic";
let obj3 = { [key]: "value" };
console.log(obj3.dynamic);          // "value"

console.log("--- for...in ---");
let obj4 = { a: 1, b: 2, c: 3 };
let keys = "";
for (let k in obj4) { keys += k; }
console.log(keys);                  // "abc"

console.log("--- spread object ---");
let obj5 = { x: 1, y: 2 };
let obj6 = { ...obj5, z: 3 };
console.log(obj6);                  // { x: 1, y: 2, z: 3 }

console.log("--- property shorthand ---");
let px = 10, py = 20;
let point = { px, py };
console.log(point.px);             // 10
console.log(point.py);             // 20


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 9: DESTRUCTURING");
console.log("═══════════════════════════════════════════");

console.log("--- array destructuring ---");
let [d1, d2, d3] = [10, 20, 30];
console.log(d1, d2, d3);           // 10 20 30

console.log("--- array destructuring with skip ---");
let [, second, , fourth] = [10, 20, 30, 40];
console.log(second, fourth);       // 20 40

console.log("--- array destructuring with rest ---");
let [first, ...rest] = [1, 2, 3, 4, 5];
console.log(first);                // 1
console.log(rest);                 // [2, 3, 4, 5]

console.log("--- object destructuring ---");
let { name: n, age: a2 } = { name: "Alice", age: 25 };
console.log(n, a2);                // Alice 25

console.log("--- object destructuring with defaults ---");
let { x: ox = 10, y: oy = 20 } = { x: 5 };
console.log(ox, oy);               // 5 20

console.log("--- object destructuring shorthand ---");
let { x: sx, y: sy } = { x: 100, y: 200 };
console.log(sx, sy);               // 100 200


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 10: FUNCTIONS & CLOSURES");
console.log("═══════════════════════════════════════════");

console.log("--- function declaration ---");
function add(a, b) { return a + b; }
console.log(add(3, 4));            // 7

console.log("--- function expression ---");
const multiply = function(a, b) { return a * b; };
console.log(multiply(3, 4));       // 12

console.log("--- arrow function ---");
const square = (x) => x * x;
console.log(square(5));            // 25

console.log("--- arrow single param ---");
const double = x => x * 2;
console.log(double(7));            // 14

console.log("--- arrow with body ---");
const greet = (name) => {
    return "Hello, " + name;
};
console.log(greet("World"));       // "Hello, World"

console.log("--- default parameters ---");
function greetDefault(name = "World") {
    return "Hello, " + name;
}
console.log(greetDefault());       // "Hello, World"
console.log(greetDefault("JS"));   // "Hello, JS"

console.log("--- rest parameters ---");
function sum(...nums) {
    return nums.reduce((a, b) => a + b, 0);
}
console.log(sum(1, 2, 3, 4));      // 10

console.log("--- rest + regular params ---");
function log(level, ...msgs) {
    return level + ": " + msgs.join(", ");
}
console.log(log("INFO", "a", "b", "c"));  // "INFO: a, b, c"

console.log("--- closures ---");
function counter() {
    let count = 0;
    return function() {
        count++;
        return count;
    };
}
const c = counter();
console.log(c());                  // 1
console.log(c());                  // 2
console.log(c());                  // 3

console.log("--- closure with args ---");
function makeAdder(x) {
    return function(y) {
        return x + y;
    };
}
const add5 = makeAdder(5);
const add10 = makeAdder(10);
console.log(add5(3));              // 8
console.log(add10(3));             // 13

console.log("--- IIFE ---");
const iife = (function() { return 42; })();
console.log(iife);                 // 42

console.log("--- function returning function ---");
function multiplier(factor) {
    return (number) => number * factor;
}
const triple = multiplier(3);
console.log(triple(5));            // 15

console.log("--- typeof function ---");
console.log(typeof add);           // "function"
console.log(typeof double);        // "function"
console.log(typeof (() => 1));     // "function"


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 11: THIS BINDING");
console.log("═══════════════════════════════════════════");

console.log("--- this in method ---");
let user = {
    name: "Alice",
    greet() { return "Hi, " + this.name; }
};
console.log(user.greet());         // "Hi, Alice"

console.log("--- arrow function lexical this ---");
let obj = {
    value: 42,
    getValue() {
        const inner = () => this.value;
        return inner();
    }
};
console.log(obj.getValue());       // 42

console.log("--- nested method this ---");
let nested = {
    x: 10,
    getX() { return this.x; }
};
console.log(nested.getX());        // 10


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 12: SPREAD OPERATOR");
console.log("═══════════════════════════════════════════");

console.log("--- spread arrays ---");
let sa = [1, 2];
let sb = [3, 4];
console.log([...sa, ...sb]);       // [1, 2, 3, 4]

console.log("--- spread for copy ---");
let orig = [1, 2, 3];
let copy = [...orig];
copy.push(4);
console.log(orig);                 // [1, 2, 3] (unchanged)
console.log(copy);                 // [1, 2, 3, 4]

console.log("--- spread in function call ---");
function sum3(a, b, c) { return a + b + c; }
let sargs = [1, 2, 3];
console.log(sum3(...sargs));       // 6

console.log("--- spread objects ---");
let so1 = { a: 1, b: 2 };
let so2 = { ...so1, c: 3 };
console.log(so2);                  // { a: 1, b: 2, c: 3 }

console.log("--- spread override ---");
let so3 = { x: 1, y: 2 };
let so4 = { ...so3, y: 99 };
console.log(so4.y);                // 99


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 13: SET & MAP");
console.log("═══════════════════════════════════════════");

console.log("--- Set basics ---");
let set = new Set();
set.add(1);
set.add(2);
set.add(1);  // duplicate, ignored
console.log(set.size);             // 2
console.log(set.has(1));           // true
console.log(set.has(3));           // false
set.delete(1);
console.log(set.has(1));           // false
console.log(set.size);             // 1

console.log("--- Set from array (dedup) ---");
let unique = new Set([1, 2, 2, 3, 3, 3]);
console.log(unique.size);          // 3

console.log("--- Set spread to array ---");
let dedup = [...new Set([1, 2, 2, 3, 3, 3])];
console.log(dedup);                // [1, 2, 3]

console.log("--- for...of Set ---");
let setSum = 0;
let s2 = new Set([10, 20, 30]);
for (const val of s2) { setSum += val; }
console.log(setSum);               // 60

console.log("--- Map basics ---");
let map = new Map();
map.set("key", "value");
map.set(42, "number key");
console.log(map.get("key"));       // "value"
console.log(map.get(42));          // "number key"
console.log(map.size);             // 2
console.log(map.has("key"));       // true
map.delete("key");
console.log(map.has("key"));       // false

console.log("--- Map set returns map ---");
let m2 = new Map();
m2.set("a", 1).set("b", 2).set("c", 3);
console.log(m2.get("c"));          // 3


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 14: CONTROL FLOW");
console.log("═══════════════════════════════════════════");

console.log("--- if/else ---");
let cf_x = 10;
if (cf_x > 5) {
    console.log("greater");       // greater
} else {
    console.log("not greater");
}

console.log("--- else if ---");
let grade = 85;
if (grade >= 90) {
    console.log("A");
} else if (grade >= 80) {
    console.log("B");              // B
} else if (grade >= 70) {
    console.log("C");
} else {
    console.log("F");
}

console.log("--- for loop ---");
let forResult = "";
for (let i = 0; i < 5; i++) {
    forResult += i;
}
console.log(forResult);            // "01234"

console.log("--- for...of ---");
let ofResult = "";
for (const val of [10, 20, 30]) {
    ofResult += val + " ";
}
console.log(ofResult.trim());      // "10 20 30"

console.log("--- for...in ---");
let inResult = "";
for (const k in { a: 1, b: 2 }) {
    inResult += k;
}
console.log(inResult);             // "ab"

console.log("--- while ---");
let wi = 0;
let wResult = "";
while (wi < 3) {
    wResult += wi;
    wi++;
}
console.log(wResult);              // "012"

console.log("--- do...while ---");
let dwi = 0;
let dwResult = "";
do {
    dwResult += dwi;
    dwi++;
} while (dwi < 3);
console.log(dwResult);             // "012"

console.log("--- do...while runs at least once ---");
let dw2 = 10;
let dw2Result = "";
do {
    dw2Result += dw2;
    dw2++;
} while (dw2 < 5);
console.log(dw2Result);            // "10"

console.log("--- break ---");
let brResult = "";
for (let i = 0; i < 10; i++) {
    if (i === 3) break;
    brResult += i;
}
console.log(brResult);             // "012"

console.log("--- continue ---");
let contResult = "";
for (let i = 0; i < 6; i++) {
    if (i === 3) continue;
    contResult += i;
}
console.log(contResult);           // "01245"

console.log("--- nested loop with break ---");
let nestedResult = "";
for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
        if (j === 1) break;
        nestedResult += `${i}${j} `;
    }
}
console.log(nestedResult.trim());  // "00 10 20"

console.log("--- switch ---");
let day = "Monday";
let dayType;
switch (day) {
    case "Monday":
    case "Tuesday":
    case "Wednesday":
    case "Thursday":
    case "Friday":
        dayType = "weekday";
        break;
    case "Saturday":
    case "Sunday":
        dayType = "weekend";
        break;
    default:
        dayType = "unknown";
}
console.log(dayType);              // "weekday"


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 15: MATH & NUMBER");
console.log("═══════════════════════════════════════════");

console.log("--- Math methods ---");
console.log(Math.floor(4.7));      // 4
console.log(Math.ceil(4.2));       // 5
console.log(Math.round(4.5));      // 5
console.log(Math.round(4.4));      // 4
console.log(Math.trunc(4.9));      // 4
console.log(Math.abs(-5));         // 5
console.log(Math.pow(2, 10));      // 1024
console.log(Math.sqrt(16));        // 4
console.log(Math.max(1, 5, 3));    // 5
console.log(Math.min(1, 5, 3));    // 1
console.log(Math.sign(-3));        // -1
console.log(Math.sign(5));         // 1
console.log(Math.sign(0));         // 0

console.log("--- Math constants ---");
console.log(Math.PI > 3.14);       // true
console.log(Math.E > 2.71);        // true

console.log("--- parseInt ---");
console.log(parseInt("42"));       // 42
console.log(parseInt("0xFF", 16)); // 255
console.log(parseInt("hello"));    // NaN
console.log(parseInt("12.34"));    // 12
console.log(parseInt("  42  "));   // 42
console.log(parseInt("10", 2));    // 2

console.log("--- parseFloat ---");
console.log(parseFloat("3.14"));   // 3.14
console.log(parseFloat("42"));     // 42
console.log(parseFloat("hello"));  // NaN
console.log(parseFloat("3.14abc")); // 3.14

console.log("--- Number.isNaN ---");
console.log(Number.isNaN(NaN));    // true
console.log(Number.isNaN("hello")); // false

console.log("--- Number.isFinite ---");
console.log(Number.isFinite(42));  // true
console.log(Number.isFinite(Infinity)); // false
console.log(Number.isFinite("42")); // false

console.log("--- Number.isInteger ---");
console.log(Number.isInteger(5));     // true
console.log(Number.isInteger(5.5));   // false
console.log(Number.isInteger("5"));   // false


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 16: DATE");
console.log("═══════════════════════════════════════════");

let d = new Date(2024, 0, 15);  // Jan 15, 2024 (month is 0-indexed!)
console.log(d.getFullYear());       // 2024
console.log(d.getMonth());          // 0 (January)
console.log(d.getDate());           // 15


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 17: INSTANCEOF & IN");
console.log("═══════════════════════════════════════════");

console.log("--- instanceof ---");
console.log([] instanceof Array);     // true
console.log([] instanceof Object);    // true
console.log({} instanceof Object);    // true
console.log(5 instanceof Object);     // false
console.log("hi" instanceof Object);  // false

console.log("--- in operator ---");
console.log("name" in { name: "test" });   // true
console.log("age" in { name: "test" });    // false
console.log(0 in [10, 20, 30]);            // true
console.log(5 in [10, 20, 30]);            // false


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 18: JSON");
console.log("═══════════════════════════════════════════");

console.log("--- JSON.stringify ---");
console.log(JSON.stringify({ a: 1 }));             // {"a":1}
console.log(JSON.stringify([1, 2, 3]));            // [1,2,3]
console.log(JSON.stringify("hello"));               // "hello"
console.log(JSON.stringify(42));                    // 42
console.log(JSON.stringify(true));                  // true
console.log(JSON.stringify(null));                  // null

console.log("--- JSON.parse ---");
let parsed = JSON.parse('{"x": 1, "y": 2}');
console.log(parsed.x);                              // 1
console.log(parsed.y);                              // 2


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 19: CONSOLE");
console.log("═══════════════════════════════════════════");

console.log("--- console.log multiple args ---");
console.log("a", "b", "c");     // a b c
console.log(1, 2, 3);           // 1 2 3
console.log("result:", 42);     // result: 42


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 20: EDGE CASES");
console.log("═══════════════════════════════════════════");

console.log("--- typeof edge cases ---");
console.log(typeof null);           // "object" (famous bug)
console.log(typeof NaN);            // "number"
console.log(typeof undefined);      // "undefined"
console.log(typeof []);             // "object"
console.log(typeof {});             // "object"

console.log("--- NaN edge cases ---");
console.log(NaN === NaN);           // false
console.log(NaN == NaN);            // false
console.log(isNaN(NaN));            // true
console.log(typeof NaN);            // "number"

console.log("--- null arithmetic ---");
console.log(null + 1);              // 1 (null → 0)
console.log(null == 0);             // false
console.log(null >= 0);             // true

console.log("--- undefined arithmetic ---");
console.log(undefined + 1);         // NaN

console.log("--- empty array arithmetic ---");
console.log([] + []);               // "" (both coerce to "")
console.log([] + {});               // "[object Object]"

console.log("--- boolean in math ---");
console.log(true + true + true);    // 3
console.log(false == 0);            // true
console.log(true == 1);             // true

console.log("--- string comparison ---");
console.log("apple" < "banana");    // true
console.log("10" < "9");            // true (lexicographic)
console.log("10" < 9);             // false (numeric)

console.log("--- delete operator ---");
let delObj = { a: 1, b: 2, c: 3 };
delete delObj.b;
console.log("b" in delObj);         // false
console.log(Object.keys(delObj));   // ["a", "c"]

console.log("--- array as object ---");
let arrLike = [1, 2, 3];
arrLike.customProp = "hello";
console.log(arrLike.customProp);    // "hello"
console.log(arrLike.length);        // 3

console.log("--- void operator ---");
console.log(void 0);                // undefined

console.log("--- comma operator ---");
let commaResult = (1, 2, 3);
console.log(commaResult);           // 3

console.log("--- string to number ---");
console.log(Number("42"));          // 42
console.log(Number(""));            // 0
console.log(Number("  "));          // 0
console.log(Number("hello"));       // NaN
console.log(Number(true));          // 1
console.log(Number(false));         // 0
console.log(Number(null));          // 0
console.log(Number(undefined));     // NaN


console.log("\n═══════════════════════════════════════════");
console.log("  SECTION 21: COMPREHENSIVE INTEGRATION");
console.log("═══════════════════════════════════════════");

// Real-world-ish scenario combining many features
console.log("--- integration test ---");
const students = [
    { name: "Alice", scores: [90, 85, 92] },
    { name: "Bob", scores: [78, 82, 88] },
    { name: "Charlie", scores: [95, 92, 98] }
];

const results = students.map(student => {
    const avg = student.scores.reduce((sum, s) => sum + s, 0) / student.scores.length;
    const grade = avg >= 90 ? "A" : avg >= 80 ? "B" : "C";
    return { name: student.name, average: avg, grade };
});

const honorRoll = results.filter(r => r.grade === "A");
console.log(honorRoll.length);          // 1 (only Charlie has avg >= 90)

const allNames = results.map(r => r.name);
console.log(allNames);                  // ["Alice", "Bob", "Charlie"]

const { name: topName, grade: topGrade } = results.sort((a, b) => b.average - a.average)[0];
console.log(topName);                   // "Charlie"
console.log(topGrade);                  // "A"

// Chaining array methods
const chained = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    .filter(n => n % 2 === 0)
    .map(n => n * 3)
    .reduce((a, b) => a + b, 0);
console.log(chained);                   // 90


console.log("\n═══════════════════════════════════════════");
console.log("  ALL TESTS COMPLETE!");
console.log("═══════════════════════════════════════════");
