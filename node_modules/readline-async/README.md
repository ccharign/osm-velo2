# readline-async

Very simple bluebird promise version of node's readline.

Error handling is incomplete, this is mostly for illustrative purposes.

See fpsokobanjs for an example how it is used.

```javascript
console.log("Starting, please enter something");

readlineAsync()
.then( line => {
        console.log("You said " + line);
        return readlineAsync();
})
.then( line => {
        console.log("and this " + line);
        return "done";
})
.then(console.log);
```
