// NAVIGATION HANDLERS
function safeRedirect(linkId, targetPage) {
  const link = document.getElementById(linkId);
  if (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      window.location.href = targetPage;
    });
  }
}

safeRedirect("indexLink", "index.html");
safeRedirect("auctionsLink", "auctions.html");
safeRedirect("categoriesLink", "categories.html");
safeRedirect("helpLink", "help.html");
safeRedirect("loginLink", "login.html");

// IMAGE SLIDER
const sliderImages = document.querySelectorAll(".slider-img");
const prevBtn = document.querySelector(".prev");
const nextBtn = document.querySelector(".next");
let currentImage = 0;

function showImage(index) {
  sliderImages.forEach((img, i) => {
    img.classList.remove("active");
    if (i === index) {
      img.classList.add("active");
    }
  });
}

if (prevBtn && nextBtn && sliderImages.length > 0) {
  prevBtn.addEventListener("click", () => {
    currentImage = (currentImage - 1 + sliderImages.length) % sliderImages.length;
    showImage(currentImage);
  });

  nextBtn.addEventListener("click", () => {
    currentImage = (currentImage + 1) % sliderImages.length;
    showImage(currentImage);
  });

  // Initialize
  showImage(currentImage);
}

// LOGIN FORM VALIDATION
const loginForm = document.querySelector("form");
if (loginForm) {
  loginForm.addEventListener("submit", function (event) {
    const loginSuccess = false; // You can replace this with actual logic
    const errorMessage = document.getElementById("error-message");

    if (!loginSuccess && errorMessage) {
      errorMessage.style.display = "block";
      event.preventDefault(); // Prevent actual submission
    }
  });
}
