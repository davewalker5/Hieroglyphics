(() => {
    const form = document.getElementById("transliteration-form");
    const word = form.elements.namedItem("word");
    const result = document.getElementById("transliteration-result");
    const layout = form.elements.namedItem("layout");
    const boundaries = document.getElementById("show-quadrat-boundaries");
    let activeRequest;

    /** Show the setting only in Quadrat mode and retain it when switching layouts. */
    function updateBoundaryDisplay() {
        boundaries.parentElement.hidden = layout.value !== "quadrat";
        result.classList.toggle("quadrat-boundaries-hidden", !boundaries.checked);
    }

    /** Refresh the result for the current text, direction and layout. */
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

    updateBoundaryDisplay();
    boundaries.addEventListener("change", updateBoundaryDisplay);
    layout.addEventListener("change", updateBoundaryDisplay);
    result.addEventListener("click", (event) => {
        // Bootstrap cancels navigation for HTML anchors but not SVG anchors.
        if (event.target.closest('svg a[data-bs-toggle="modal"]')) {
            event.preventDefault();
        }
    });
    word.addEventListener("input", updateResult);
    form.addEventListener("change", (event) => {
        if (event.target.matches("select")) {
            updateResult();
        }
    });
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        updateResult();
    });
})();
