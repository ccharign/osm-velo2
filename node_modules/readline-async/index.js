var readline = require('readline');
var Promise = require('bluebird');

var mutablePromiseQue = [];

var rl = null;
var paused = false;

// Promise String
module.exports = () => {
	var deferred = Promise.pending();
	
	mutablePromiseQue = [deferred].concat(mutablePromiseQue)

	if(rl == null) {
		rl = readline.createInterface({
			input: process.stdin,
			output: process.stdout
		});

		rl.on('line', (line) => {
			var p = mutablePromiseQue.pop();

			if(mutablePromiseQue.length == 0) {
				rl.pause();
				paused = true;	
			}

			p.resolve(line);	
		})
	}

	if(paused) {
		rl.resume();
	}

	return deferred.promise;
}
/*
console.log("Starting, please enter something");

readlineAsync()
.then( line => {
	console.log("You said " + line);
	return readlineAsync();
})
.then( line => {
	console.log("and this " + line);
	return "fertig";
})
.then(console.log);
*/
