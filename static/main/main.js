document.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.querySelector(".btn.login");
    const registerBtn = document.querySelector(".btn.register");

    if (loginBtn) {
        loginBtn.addEventListener("click", () => {
            window.location.href = "/login";
        });
    }

    if (registerBtn) {
        registerBtn.addEventListener("click", () => {
            window.location.href = "/register";
        });
    }
});
