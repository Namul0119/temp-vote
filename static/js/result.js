function showPerson(index) {
    const blocks = document.querySelectorAll('.person-block');
    blocks.forEach(block => block.classList.add('hidden'));
    document.getElementById('person' + index).classList.remove('hidden');
}

function initTemperatureCounter() {

    const tempElement = document.getElementById("tempCounter");

    const targetTemp = tempElement
        ? Number(tempElement.dataset.targetTemp)
        : 0;

    if (tempElement) {

        let current = 0;

        const interval = setInterval(() => {

            current++;

            tempElement.innerText = current + "°C";

            if (current >= targetTemp) {
                clearInterval(interval);
            }

        }, 40);
    }
}

function copyResult() {
    const text =
`우리 방 AI 추천 온도는 {{ result }}°C 입니다!
예상 만족도: {{ satisfaction }}%
AI 집단 온도 추천 시스템`;

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            alert("결과가 복사되었습니다!");
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    try {
        document.execCommand("copy");
        alert("결과가 복사되었습니다!");
    } catch (err) {
        alert("복사에 실패했습니다. 직접 선택해서 복사해주세요.");
    }

    document.body.removeChild(textarea);
}

function initCopyButton() {

    const button = document.getElementById("copyResultBtn");

    if (!button) return;

    button.addEventListener("click", copyResult);
}

document.addEventListener("DOMContentLoaded", () => {

    initTemperatureCounter();

    initCopyButton();

});