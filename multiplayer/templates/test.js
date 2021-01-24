
Streamer: function(config, socket) {    
    this.config = config || {};
    this.config.codec = this.config.codec || defaultConfig.codec;
    this.config.server = this.config.server || defaultConfig.server;
    this.sampler = new Resampler(audioContext.sampleRate, this.config.codec.sampleRate, 1, this.config.codec.bufferSize);
    this.parentSocket = socket;
    this.encoder = new OpusEncoder(this.config.codec.sampleRate, this.config.codec.channels, this.config.codec.app, this.config.codec.frameDuration);
    var _this = this;
    function _successCallback(stream) {
        _this.stream = stream;
        _this.audioInput = audioContext.createMediaStreamSource(stream);
        _this.gainNode = audioContext.createGain();
        _this.recorder = audioContext.createScriptProcessor(_this.config.codec.bufferSize, 1, 1);
        _this.recorder.onaudioprocess = function(e) {
            var resampled = _this.sampler.resampler(e.inputBuffer.getChannelData(0));
            var packets = _this.encoder.encode_float(resampled);
            for (var i = 0; i < packets.length; i++) {
                if (_this.socket.readyState == 1) _this.socket.send(packets[i]);
            }
        };
        _this.audioInput.connect(_this.gainNode);
        _this.gainNode.connect(_this.recorder);
        _this.recorder.connect(audioContext.destination);
    }
    
    navigator.getUserMedia = (navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia ||
        navigator.msGetUserMedia);
    
    this._makeStream = function(onError) {
        var _errorCallback = onError || _this.onError;
        if(navigator.getUserMedia) {
            navigator.getUserMedia({ audio: true, video: false }, _successCallback, _errorCallback);
        }
        else {
            navigator.mediaDevices.getUserMedia({ audio: true, video: false }).then(_successCallback).catch(_errorCallback);
        }
    }
}
