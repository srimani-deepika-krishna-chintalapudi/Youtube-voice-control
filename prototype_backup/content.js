let recognition = null;
let listening = false;

const WAKE_WORD = "hey youtube";


// ========================================
// START SPEECH RECOGNITION
// ========================================

function startRecognition() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert("Speech recognition is not supported.");

        return;
    }

    recognition = new SpeechRecognition();

    recognition.lang = "en-US";

    recognition.continuous = true;

    recognition.interimResults = false;


    recognition.onstart = function () {

        console.log("🎤 Microphone started");

        showMessage('🎤 Say "Hey YouTube"');
    };


    recognition.onresult = function (event) {

        const text =
            event.results[
                event.results.length - 1
            ][0]
            .transcript
            .toLowerCase()
            .trim();


        console.log("HEARD:", text);


        // ====================================
        // CHECK WAKE WORD
        // ====================================

        const wakeIndex =
            text.indexOf(WAKE_WORD);


        // Wake word NOT present
        // Ignore everything
        if (wakeIndex === -1) {

            console.log(
                "Ignored - wake word not detected"
            );

            return;
        }


        // ====================================
        // REMOVE "HEY YOUTUBE"
        // ====================================

        let command =
            text.substring(
                wakeIndex + WAKE_WORD.length
            )
            .trim();


        // Remove punctuation

        command =
            command
            .replace(/[,.!?]/g, "")
            .trim();


        console.log(
            "COMMAND:",
            command
        );


        // ====================================
        // ONLY WAKE WORD
        // ====================================

        if (command === "") {

            showMessage(
                "👋 Yes? What should I do?"
            );

            return;
        }


        // ====================================
        // EXECUTE COMMAND
        // ====================================

        executeCommand(command);
    };


    recognition.onerror = function (event) {

        console.log(
            "Speech error:",
            event.error
        );
    };


    recognition.onend = function () {

        console.log(
            "🎤 Microphone ended"
        );


        // Restart automatically

        if (listening) {

            try {

                recognition.start();

            } catch (error) {

                console.log(
                    "Restart error:",
                    error
                );
            }
        }
    };


    recognition.start();

    listening = true;
}


// ========================================
// STOP RECOGNITION
// ========================================

function stopRecognition() {

    listening = false;

    if (recognition) {

        try {

            recognition.stop();

        } catch (error) {}
    }

    showMessage(
        "🛑 Voice control stopped"
    );
}


// ========================================
// GET VIDEO
// ========================================

function getVideo() {

    return document.querySelector("video");
}


// ========================================
// EXECUTE COMMAND
// ========================================

function executeCommand(command) {

    const video = getVideo();


    if (!video) {

        showMessage(
            "❌ YouTube video not found"
        );

        return;
    }


    console.log(
        "Executing:",
        command
    );


    // ====================================
    // PAUSE
    // ====================================

    if (
        command.includes("pause") ||
        command === "stop"
    ) {

        video.pause();

        showMessage(
            "⏸ Paused"
        );

        return;
    }


    // ====================================
    // PLAY
    // ====================================

    if (
        command.includes("play") ||
        command.includes("resume")
    ) {

        video.play();

        showMessage(
            "▶ Playing"
        );

        return;
    }


    // ====================================
    // REWIND / BACK
    // ====================================

    if (
        command.includes("rewind") ||
        command.includes("go back") ||
        command.includes("back") ||
        command.includes("replay")
    ) {

        const seconds =
            extractSeconds(command) || 10;


        video.currentTime =
            Math.max(
                0,
                video.currentTime - seconds
            );


        showMessage(
            `⏪ Back ${seconds} seconds`
        );

        return;
    }


    // ====================================
    // FORWARD
    // ====================================

    if (
        command.includes("forward") ||
        command.includes("go ahead") ||
        command.includes("skip")
    ) {

        const seconds =
            extractSeconds(command) || 10;


        video.currentTime =
            Math.min(
                video.duration,
                video.currentTime + seconds
            );


        showMessage(
            `⏩ Forward ${seconds} seconds`
        );

        return;
    }


    // ====================================
    // MUTE
    // ====================================

    if (
        command.includes("mute")
    ) {

        video.muted = true;

        showMessage(
            "🔇 Muted"
        );

        return;
    }


    // ====================================
    // UNMUTE
    // ====================================

    if (
        command.includes("unmute") ||
        command.includes("sound on")
    ) {

        video.muted = false;

        showMessage(
            "🔊 Sound on"
        );

        return;
    }


    // ====================================
    // VOLUME UP
    // ====================================

    if (
        command.includes("volume up") ||
        command.includes("increase volume")
    ) {

        video.volume =
            Math.min(
                1,
                video.volume + 0.1
            );

        showMessage(
            "🔊 Volume increased"
        );

        return;
    }


    // ====================================
    // VOLUME DOWN
    // ====================================

    if (
        command.includes("volume down") ||
        command.includes("decrease volume")
    ) {

        video.volume =
            Math.max(
                0,
                video.volume - 0.1
            );

        showMessage(
            "🔉 Volume decreased"
        );

        return;
    }


    // ====================================
    // SPEED UP
    // ====================================

    if (
        command.includes("speed up") ||
        command.includes("faster")
    ) {

        video.playbackRate =
            Math.min(
                2,
                video.playbackRate + 0.25
            );


        showMessage(
            `⚡ Speed ${video.playbackRate}x`
        );

        return;
    }


    // ====================================
    // SLOW DOWN
    // ====================================

    if (
        command.includes("slow down") ||
        command.includes("slower")
    ) {

        video.playbackRate =
            Math.max(
                0.25,
                video.playbackRate - 0.25
            );


        showMessage(
            `🐢 Speed ${video.playbackRate}x`
        );

        return;
    }


    // ====================================
    // NORMAL SPEED
    // ====================================

    if (
        command.includes("normal speed") ||
        command === "normal"
    ) {

        video.playbackRate = 1;

        showMessage(
            "▶ Normal speed"
        );

        return;
    }


    // ====================================
    // UNKNOWN COMMAND
    // ====================================

    showMessage(
        `❓ Unknown command: ${command}`
    );
}


// ========================================
// EXTRACT SECONDS
// ========================================

function extractSeconds(command) {

    const match =
        command.match(
            /(\d+)\s*(seconds|second|secs|sec)?/
        );


    if (match) {

        return parseInt(
            match[1]
        );
    }


    return null;
}


// ========================================
// SHOW MESSAGE
// ========================================

function showMessage(message) {

    let box =
        document.getElementById(
            "voice-message"
        );


    if (!box) {

        box =
            document.createElement(
                "div"
            );

        box.id =
            "voice-message";

        document.body.appendChild(
            box
        );
    }


    box.innerText = message;

    box.style.display =
        "block";


    clearTimeout(
        box.hideTimer
    );


    box.hideTimer =
        setTimeout(
            function () {

                box.style.display =
                    "none";

            },
            2500
        );
}


// ========================================
// CREATE BUTTON
// ========================================

function createButton() {

    if (
        document.getElementById(
            "voice-control-button"
        )
    ) {

        return;
    }


    const button =
        document.createElement(
            "button"
        );


    button.id =
        "voice-control-button";


    button.innerText =
        "🎤 Hey YouTube";


    button.onclick =
        function () {

            if (!listening) {

                startRecognition();

                button.innerText =
                    "🛑 Stop Voice";

                button.classList.add(
                    "active"
                );

            } else {

                stopRecognition();

                button.innerText =
                    "🎤 Hey YouTube";

                button.classList.remove(
                    "active"
                );
            }
        };


    document.body.appendChild(
        button
    );
}


// ========================================
// INITIALIZE
// ========================================

setTimeout(
    createButton,
    3000
);


setInterval(
    createButton,
    3000
);