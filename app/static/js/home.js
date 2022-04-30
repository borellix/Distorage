const dropZone = document.getElementById('drop-zone');
const dropZoneBorderInner = document.getElementById('drop-zone-border--inner');
const dropZoneBorderOuter = document.getElementById('drop-zone-border--outer');
const dropZoneBorder = [dropZone, dropZoneBorderInner, dropZoneBorderOuter];
const fileInput = document.getElementById('drop-zone__file-input');
const fileKeyInput = document.getElementById('file-key');
const dropZoneFileName = document.getElementById('drop-zone__file-name');
const dropZoneText = document.getElementById('drop-zone__text');
let animation = false;

class Api {
    static upload() {
        const formData = new FormData();
        if (fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
            fetch('/api/file/', {
                method: 'POST', body: formData
            }).then(response => {
                if (response.ok) {
                    Promise.resolve(response.json()).then(data => {
                        console.log(data)
                        fileKeyInput.value = data['file_key'];
                        fileKeyInput.disabled = true;
                    });

                } else {
                    alert("An error occurred");
                }
            })
        } else {
            alert('No file selected');
        }
    }

    static download() {
        let fileKey = fileKeyInput.value;

        if (fileKey) {
            fetch('/api/file/' + fileKey).then(response => {
                if (response.ok) {
                    response.json().then(data => {
                        // Download the file from data['file_url']
                        window.location.href = data['url'];
                    });
                }
            });
        }
    }

    static patch() {
        let fileKey = fileKeyInput.value;

        if (fileKey) {
            let formData = new FormData();
            formData.append('file', fileInput.files[0]);
            fetch('/api/file/' + fileKey, {
                method: 'PATCH',
                body: formData
            }).then(response => {
                if (response.ok) {
                    Promise.resolve(response.json()).then(data => {
                        console.log(data)
                        fileKeyInput.value = data['file_key'];
                        fileKeyInput.disabled = true;
                    });
                    }
                });
            }
    }

    static delete() {
        let fileKey = fileKeyInput.value;

        if (fileKey) {
            fetch('/api/file/' + fileKey, {
                method: 'DELETE'
            }).then(response => {
                if (response.ok) {
                    fileKeyInput.value = '';
                    fileKeyInput.disabled = false;
                }
            });
        }
    }
}

function clickDropZoneHandler() {
    fileInput.click();
}

function changeFileHandler() {
    const file = fileInput.files[0];
    dropZoneFileName.innerHTML = file.name;
    dropZoneText.style.display = 'none';
    adaptText();
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
        dropZoneFileName.innerHTML = file.name;
        dropZoneText.style.display = 'none';
        adaptText();
    })

}

function dragOverHandler(e) {
    if (!animation) {
        animation = true;
        playBorderRadiusAnimation(dropZone);
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

function playBorderRadiusAnimation() {
    dropZoneBorder.forEach(function (element) {
        console.log(element.style);
        element.animate([{borderRadius: getComputedStyle(element).borderRadius}, {borderRadius: parseInt(getComputedStyle(element).borderRadius) - 90 + 'px'}], {
            duration: 300, iterations: 1, direction: "alternate", easing: "ease-in-out", fill: "forwards"
        })
    });
}

function playReverseBorderRadiusAnimation() {
    dropZoneBorder.forEach(function (element) {
        element.animate([{borderRadius: getComputedStyle(element).borderRadius}, {
            borderRadius: (parseInt(getComputedStyle(element).borderRadius.replace('px', '')) + 90).toString() + 'px'
        }], {
            duration: 300, iterations: 1, direction: "alternate", easing: "ease-in-out", fill: "forwards"
        })
    });
}


// Change the font size of the p file-name to fit the width of the drop zone and of the length of the file name
// skip line in the filename if there is more than 50 characters
function adaptText() {
    console.log("Change font size");
    // skip line after the end of the word that contains the 50th character of the filename

    let fileName = dropZoneFileName.innerHTML;
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
        dropZoneFileName.innerHTML = firstWord + '...' + lastWord;
    }
    fileName = dropZoneFileName.innerHTML;
    fileNameLength = fileName.length;
    let dropZoneWidth = dropZone.offsetWidth;
    console.log(dropZoneWidth);
    let fontSize = dropZoneWidth / fileNameLength * 1.5;
    if (fontSize < 20) {
        fontSize = 20;
    } else if (fontSize > 30) {
        fontSize = 30;
    }
    dropZoneFileName.style.fontSize = fontSize + "px";
}


adaptText();

// Listeners
dropZone.addEventListener('click', clickDropZoneHandler, false);
dropZone.addEventListener('drop', (e) => {
        dropHandler(e);

        playReverseBorderRadiusAnimation(dropZone)
    }

    , false);
dropZone.addEventListener('dragover', dragOverHandler, false);
dropZone.addEventListener('dragleave', dragLeaveHandler, false);

fileInput.addEventListener('change', changeFileHandler, false);

window.addEventListener('resize', adaptText, false);