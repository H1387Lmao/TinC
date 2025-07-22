# TinC
`TinC` pronouced as `Tincy` is a small programming language built in python

# Why is it named TinC?

`TinC` is named after a common english phrase `Teeny Tiny` or the word `Tincy` meaning extremely small. Also can be interpreted as Garbage (*Tin*) C

# Syntax
---
* TinC statements are ended by a semi-colon, except for scopes
```
let x = 10;
fn HelloWorld(){
    printf("Hello world\n");
}
```
---
* TinC is dynamically typed, so no explicit types are needed
---
* TinC For Loop are like in rust, which returns a list of numbers from start all the way to end
```
for (i in start..end){
    printf(i);
}
```
* TinC While loops are the same, but no `break/continue` yet
---
* TinC indexing are like a mix of lua tables and C++ structs, since every single list can be indexed alphanumerically (even negative numbers), the operation for indexing is `->`
```
let x = [];
x->0 = "FIRST INDEX YAY";
printf("%1\n", x->0)
```
### Output

`FIRST INDEX YAY`


---

* TinC Assignments are like in Javascript
```
let x = 0;
let y = y + 10;
```
---
* TinC Reassignments can reassign any variable, like indexes and variables

```
let x = 10;
x = x + 10;
x = [];
x->10 = 10;
```

## Standard Library

* printf
```c
// 1 <- First, Second -> 2
printf("%1 <- First, Second-> %2", 1,2)

// Hello
printf("Hello")
```

* format
```c
// X Variable
let x = format("%1", "X Variable")

// Errors out, needs to be (Format, *args)
let x = format("X Variable")
```
