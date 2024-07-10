// Function to capture log messages
function captureLogMessage(level, message) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level}] ${message}`;

    // Add log message to the array
    user_websocket.send(JSON.stringify({'type': 'log', 'message': logEntry, 'level': level}));
}

// Override console.log
console.log = (function (origLogFunc) {
    return function (message) {
        captureLogMessage('LOG', message);
        origLogFunc.apply(console, arguments);
    };
})(console.log);

// Override console.warn
console.warn = (function (origWarnFunc) {
    return function (message) {
        captureLogMessage('WARN', message);
        origWarnFunc.apply(console, arguments);
    };
})(console.warn);

// Override console.error
console.error = (function (origErrorFunc) {
    return function (message) {
        captureLogMessage('ERROR', message);
        origErrorFunc.apply(console, arguments);
    };
})(console.error);

// Utility function to get past log messages
function getPastLogMessages() {
    return logMessages.slice();
}