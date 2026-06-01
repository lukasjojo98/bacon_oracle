// Use event delegation so the handler still works after container replacement
document.addEventListener("click", (event) => {
    const btn = event.target.closest && event.target.closest("#link-finder");
    if (!btn) return;

    const actorInput = document.getElementById("actor_name");
    const actorName = actorInput ? actorInput.value : "";

    const formData = new FormData();
    formData.append("to_actor", actorName);
    // show loading indicator (animated dots)
    let loading = btn.parentElement.querySelector('.loading');
    if (!loading) {
        loading = document.createElement('span');
        loading.className = 'loading';
        loading.textContent = 'Loading';
        const dots = document.createElement('span');
        dots.className = 'dots';
        loading.appendChild(dots);
        btn.after(loading);
    }
    // clear any previous interval
    if (window._loadingInterval) {
        clearInterval(window._loadingInterval);
        window._loadingInterval = null;
    }
    let _dotState = 0;
    window._loadingInterval = setInterval(() => {
        const dotsSpan = loading.querySelector('.dots');
        if (dotsSpan) {
            _dotState = (_dotState + 1) % 4;
            dotsSpan.textContent = '.'.repeat(_dotState);
        }
    }, 400);
    fetch("/links", {
        method: "POST",
        body: formData
    })
    .then(response => response.text())
    .then(htmlText => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, "text/html");
        const newContainer = doc.querySelector(".connection-container");
        const currentContainer = document.querySelector(".connection-container");
        if (newContainer && currentContainer) {
            currentContainer.innerHTML = newContainer.innerHTML;
        } else if (newContainer) {
            const main = document.querySelector("main");
            if (main) {
                const existing = main.querySelector(".connection-container");
                if (existing) existing.replaceWith(newContainer);
                else main.appendChild(newContainer);
            }
        }
        // clear loading indicator
        if (window._loadingInterval) {
            clearInterval(window._loadingInterval);
            window._loadingInterval = null;
        }
        const loadingElm = document.querySelector('.button-container .loading');
        if (loadingElm && loadingElm.parentNode) loadingElm.parentNode.removeChild(loadingElm);
    })
    .catch(error => {
        console.error("Error:", error);
        if (window._loadingInterval) {
            clearInterval(window._loadingInterval);
            window._loadingInterval = null;
        }
        const loadingElm = document.querySelector('.button-container .loading');
        if (loadingElm && loadingElm.parentNode) loadingElm.parentNode.removeChild(loadingElm);
    });
});