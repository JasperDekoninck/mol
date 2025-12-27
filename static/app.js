const startAudio = document.getElementById("startAudio");
const backgroundAudio = document.getElementById("backgroundAudio");
const redAudio = document.getElementById("redAudio");
const form = document.querySelector(".name-form");
const nameInput = document.querySelector(".name-input");
const formWrap = document.querySelector(".form-wrap");
const errorMessage = document.getElementById("errorMessage");
let backgroundResumeTime = 0;
let hasStarted = false;
let startLocked = false;
let resultActive = false;
let enterHandlerBound = false;

function playBackground(restart = false) {
  if (!backgroundAudio) {
    return;
  }
  if (restart) {
    backgroundAudio.currentTime = 0;
  }
  if (backgroundAudio.paused) {
    if (backgroundResumeTime > 0) {
      backgroundAudio.currentTime = backgroundResumeTime;
    }
    backgroundAudio.play().catch(() => {});
  }
}

function playRedThenBackground() {
  if (!redAudio || !backgroundAudio) {
    return;
  }
  backgroundResumeTime = 0;
  backgroundAudio.pause();
  redAudio.currentTime = 0;
  redAudio.play().catch(() => {});
  redAudio.onended = () => {
    playBackground(true);
  };
}

function startSequence() {
  if (hasStarted) {
    return;
  }
  if (!startAudio) {
    playBackground();
    hasStarted = true;
    return;
  }
  if (startLocked) {
    return;
  }
  startLocked = true;
  startAudio.currentTime = 0;
  startAudio.play().then(() => {
    hasStarted = true;
  }).catch(() => {
    startLocked = false;
    playBackground();
  });
  startAudio.onended = () => {
    hasStarted = true;
    playBackground();
  };
}

function bindStartHandlers() {
  const handler = () => {
    startSequence();
    document.removeEventListener("keydown", handler);
    document.removeEventListener("click", handler);
  };
  document.addEventListener("keydown", handler);
  document.addEventListener("click", handler);
}

window.addEventListener("load", () => {
  bindStartHandlers();
});

function showForm() {
  document.body.dataset.color = "black";
  document.body.classList.remove("page--red", "page--green");
  document.body.classList.add("page--black");
  if (formWrap) {
    formWrap.classList.add("is-visible");
  }
  resultActive = false;
  if (enterHandlerBound) {
    document.removeEventListener("keydown", handleEnterToReset);
    enterHandlerBound = false;
  }
}

function showResult(color) {
  document.body.dataset.color = color;
  document.body.classList.remove("page--black", "page--red", "page--green");
  document.body.classList.add(`page--${color}`);
  if (formWrap) {
    formWrap.classList.remove("is-visible");
  }
  resultActive = true;
  if (!enterHandlerBound) {
    document.addEventListener("keydown", handleEnterToReset);
    enterHandlerBound = true;
  }
}

function handleEnterToReset(event) {
  if (!resultActive) {
    return;
  }
  if (event.key === "Enter") {
    showForm();
    if (nameInput) {
      nameInput.focus();
    }
  }
}

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!nameInput) {
      return;
    }
    if (!nameInput.value.trim()) {
      return;
    }
    const formData = new FormData(form);
    if (errorMessage) {
      errorMessage.textContent = "";
    }

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: formData,
      });
      if (response.status === 204) {
        return;
      }
      const payload = await response.json();
      if (!response.ok) {
        if (errorMessage) {
          errorMessage.textContent = "";
        }
        return;
      }

      const color = payload.color;
      showResult(color);
      if (color === "red") {
        playRedThenBackground();
      } else {
        playBackground();
      }

      nameInput.value = "";
    } catch (error) {
      if (errorMessage) {
        errorMessage.textContent = "";
      }
    }
  });
}
