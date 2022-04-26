const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('drop-zone__file-input');
const pFileName = document.getElementById('drop-zone__file-name');
let animation = false;

function clickDropZoneHandler() {
    fileInput.click();
}

function changeFileHandler() {
    const file = fileInput.files[0];
    pFileName.innerHTML = file.name;
    changeFontSize();
}

function dropHandler(e) {
    Promise.resolve().then(() => {
            console.log("File dropped");
            let file = null;
            // Prevent default behavior (Prevent file from being opened)
            e.preventDefault();

            if (e.dataTransfer.items) {
                if (e.dataTransfer.items[0].kind !== 'file') {
                    return;
                }
                if (e.dataTransfer.items.length <= 1) {
                    file = e.dataTransfer.items[0].getAsFile();
                    console.log(e.dataTransfer.items[0].kind);
                } else {
                    console.log(e.dataTransfer.items.length + " files dropped");
                    file = e.dataTransfer.items[0].getAsFile();
                    console.log(e.dataTransfer.items[0]);
                    console.log(file.name);
                    alert('You can only upload one file.');
                    return;
                }
            } else {
                if (e.dataTransfer.files[0].type !== 'file') {
                    return;
                }
                // Use DataTransfer interface to access the file(s)
                if (e.dataTransfer.files.length <= 1) {
                    file = e.dataTransfer.files[0];
                } else {
                    alert('You can only upload one file.');
                    return;
                }
            }
            // Change the content of the p file-name to the name of the file
            pFileName.innerHTML = file.name;
            changeFontSize();
        }
    )

}

function dragOverHandler(e) {
    if (!animation) {
        animation = true;
        playBorderRadiusAnimation(dropZone)
    }
    console.log('File(s) in drop zone');
    // Prevent default behavior (Prevent file from being opened)
    e.preventDefault();
}

function dragLeaveHandler(e) {
    if (animation) {
        animation = false;
        playReverseBorderRadiusAnimation(dropZone)
    }
    console.log('File(s) leave drop zone');
    // Prevent default behavior (Prevent file from being opened)
    e.preventDefault();
}

function playBorderRadiusAnimation(element) {
    element.animate(
        [
            {borderRadius: "120px"},
            {borderRadius: "30px"}
        ], {
            duration: 300,
            iterations: 1,
            direction: "alternate",
            easing: "ease-in-out",
            fill: "forwards"
        }
    )
}

function playReverseBorderRadiusAnimation(element) {
    element.animate(
        [
            {borderRadius: "30px"},
            {borderRadius: "120px"}
        ], {
            duration: 300,
            iterations: 1,
            direction: "alternate",
            easing: "ease-in-out",
            fill: "forwards"
        }
    )
}


// Change the font size of the p file-name to fit the width of the drop zone and of the length of the file name
// skip line in the filename if there is more than 50 characters
function changeFontSize() {
    console.log("Change font size");
    // skip line after the end of the word that contains the 50th character of the filename

    let fileName = pFileName.innerHTML;
    let fileNameLength = fileName.length;
    if (fileNameLength > 30) {
        console.log("More than 30 characters");
        // if there is no space from the first to the 20th character, add one at the 21st character
        if (fileName.substring(0, 20).indexOf(" ") === -1) {
            fileName = fileName.substring(0, 20) + " " + fileName.substring(20, fileNameLength);
        }

        // Take the first whole words until the 10th character
        let firstWord = fileName.substring(0, fileName.indexOf(' ', 20));
        // Take the last whole words until the 10th character
        let lastWord = fileName.substring(fileName.lastIndexOf(' '), fileName.length);
        console.log(firstWord);
        console.log(lastWord);
        pFileName.innerHTML = firstWord + '...' + lastWord;
    }
    fileName = pFileName.innerHTML;
    fileNameLength = fileName.length;
    let dropZoneWidth = dropZone.offsetWidth;
    console.log(dropZoneWidth);
    let fontSize = dropZoneWidth / fileNameLength * 1.5;
    if (fontSize < 20) {
        fontSize = 20;
    } else if (fontSize > 30) {
        fontSize = 30;
    }
    pFileName.style.fontSize = fontSize+ "px";
}

// skip line (add \n) after the end of the word that contains the 50th character of the given string
function skipLine(string) {
    let stringLength = string.length;
    let baseStringArray = string.split("");
    let stringArray = baseStringArray;
    let line = "";
    let character = "";
    for (let [char_i, i] = [0, 0]; char_i < stringLength; [char_i++, i++]) {
        character = baseStringArray[char_i];
        if (i % 30 === 0 && char_i !== 0) {
            console.log("After 30 characters: " + character);
            let j = char_i
            for (j; j < stringLength; j++) {
                console.log("j: " + j);
                if (baseStringArray[j] === " ") {
                    line += "<br>";
                    console.log("Found space");
                    console.log("line: " + line);
                    i = 0;
                    break;
                } else {
                    line += baseStringArray[j];
                }
            }
            console.log("j after if: " + j);
            char_i = j;
        } else {
            line += character;

        }
    }
    return line;
}


changeFontSize();
// Listeners
dropZone.addEventListener('click', clickDropZoneHandler, false);
dropZone.addEventListener('drop', (e) => {
    dropHandler(e);
    playReverseBorderRadiusAnimation(dropZone)
}, false);
dropZone.addEventListener('dragover', dragOverHandler, false);
dropZone.addEventListener('dragleave', dragLeaveHandler, false);

fileInput.addEventListener('change', changeFileHandler, false);

window.addEventListener('resize', changeFontSize, false);