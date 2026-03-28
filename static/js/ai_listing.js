document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("ai_improve_root");
  if (!root) return;

  const endpoint = root.dataset.endpoint;
  const descriptionEl = document.getElementById("description");
  const improveBtn = document.getElementById("ai_improve_button");
  const loadingEl = document.getElementById("ai_improve_loading");
  const errorEl = document.getElementById("ai_improve_error");
  const outputEl = document.getElementById("ai_improve_output");
  const suggestionEl = document.getElementById("ai_improve_suggestion");
  const useBtn = document.getElementById("ai_use_improved_button");
  const summaryNoteEl = document.getElementById("ai_improve_summary_note");
  const improveTitleWrap = document.getElementById("ai_improve_title_wrap");
  const improveTitleText = document.getElementById("ai_improve_title_text");
  const improveTitleApply = document.getElementById("ai_improve_title_apply");
  const titleInputEl = document.getElementById("title");

  if (!endpoint || !descriptionEl || !improveBtn || !suggestionEl || !useBtn) return;

  const setError = (msg) => {
    if (!errorEl) return;
    errorEl.textContent = msg || "Bir hata oluştu.";
    errorEl.style.display = "block";
  };

  const clearError = () => {
    if (!errorEl) return;
    errorEl.textContent = "";
    errorEl.style.display = "none";
  };

  const setLoading = (on) => {
    if (!loadingEl) return;
    loadingEl.style.display = on ? "block" : "none";
  };

  improveBtn.addEventListener("click", async () => {
    const text = (descriptionEl.value || "").trim();
    clearError();

    if (!text) {
      setError("Açıklama boş olamaz.");
      return;
    }

    setLoading(true);
    useBtn.disabled = true;
    if (outputEl) outputEl.style.display = "none";
    if (summaryNoteEl) {
      summaryNoteEl.textContent = "";
      summaryNoteEl.style.display = "none";
    }
    if (improveTitleWrap) {
      improveTitleWrap.style.display = "none";
    }
    if (improveTitleText) {
      improveTitleText.textContent = "";
    }

    try {
      const resp = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: text }),
      });

      if (!resp.ok) {
        let detail = "";
        try {
          const data = await resp.json();
          detail = data.error || data.message || "";
        } catch (e) {
          // ignore
        }
        throw new Error(detail || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      const improved = data.improved_description || "";
      const shortSummary = (
        data.short_summary ||
        data.summary ||
        ""
      ).trim();
      const suggestedTitle = (
        data.suggested_title ||
        data.title_suggestion ||
        ""
      ).trim();

      suggestionEl.value = improved;
      if (summaryNoteEl) {
        if (shortSummary) {
          summaryNoteEl.textContent = "Kısa özet: " + shortSummary;
          summaryNoteEl.style.display = "block";
        } else {
          summaryNoteEl.textContent = "";
          summaryNoteEl.style.display = "none";
        }
      }
      if (improveTitleWrap && improveTitleText) {
        if (suggestedTitle) {
          improveTitleText.textContent = suggestedTitle;
          improveTitleWrap.style.display = "block";
        } else {
          improveTitleText.textContent = "";
          improveTitleWrap.style.display = "none";
        }
      }
      if (outputEl) outputEl.style.display = "block";
      useBtn.disabled = false;
    } catch (err) {
      setError(err?.message || "AI iyileştirme başarısız oldu.");
    } finally {
      setLoading(false);
    }
  });

  useBtn.addEventListener("click", () => {
    const text = (suggestionEl.value || "").trim();
    if (!text) return;
    descriptionEl.value = text;
    clearError();
  });

  if (improveTitleApply && titleInputEl && improveTitleText) {
    improveTitleApply.addEventListener("click", () => {
      const t = (improveTitleText.textContent || "").trim();
      if (!t) return;
      titleInputEl.value = t;
    });
  }
});

