document.addEventListener("DOMContentLoaded", () => {

    initCopyButton();

});

function initCopyButton() {

    const button = document.getElementById("copyLinkBtn");

    if (!button) return;

    button.addEventListener("click", copyLink);
}

function copyLink() {

    const link = document.getElementById("roomLink");

    link.select();

    document.execCommand("copy");

    alert("링크가 복사되었습니다!");
}