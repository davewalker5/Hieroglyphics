(() => {
    const form = document.getElementById("transliteration-form");
    const word = form.elements.namedItem("word");
    const direction = form.elements.namedItem("direction");
    const result = document.getElementById("transliteration-result");
    let activeRequest;

    /** Refresh the result for the current text and reading direction. */
    async function updateResult() {
        activeRequest?.abort();
        if (!word.value) {
            result.replaceChildren();
            return;
        }

        const request = new AbortController();
        activeRequest = request;
        try {
            const response = await fetch(form.dataset.previewUrl, {
                method: "POST",
                body: new FormData(form),
                signal: request.signal,
            });
            if (!response.ok) {
                throw new Error(`Transliteration request failed (${response.status})`);
            }

            const markup = await response.text();
            // An older response may already have arrived when the input changes.
            if (!request.signal.aborted) {
                result.innerHTML = markup;
            }
        } catch (error) {
            if (!request.signal.aborted) {
                result.textContent = "We couldn’t update the transliteration. Please try again.";
            }
        }
    }

    word.addEventListener("input", updateResult);
    direction.addEventListener("change", updateResult);
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        updateResult();
    });
})();
