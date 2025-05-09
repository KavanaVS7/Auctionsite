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
safeRedirect("helpLink", "help.html");
safeRedirect("loginLink", "login.html");

// LOGIN FORM VALIDATION
const loginForm = document.querySelector("form");
if (loginForm) {
  loginForm.addEventListener("submit", function (event) {
    const loginSuccess = false; // Placeholder - replace with real login logic
    const errorMessage = document.getElementById("error-message");

    if (!loginSuccess && errorMessage) {
      errorMessage.style.display = "block";
      event.preventDefault(); // Prevent form submission
    }
  });
}