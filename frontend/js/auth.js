/**
 * Login / signup page handlers.
 */

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = new FormData(loginForm);
      try {
        const res = await apiPost("/auth/login", {
          username: form.get("username"),
          password: form.get("password"),
        });
        showToast(res.message || "Logged in successfully", "success");
        setTimeout(() => {
          window.location.href = "/";
        }, 400);
      } catch (err) {
        showToast(err.message, "warning");
      }
    });
  }

  const signupForm = document.getElementById("signup-form");
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = new FormData(signupForm);
      try {
        const res = await apiPost("/auth/signup", {
          username: form.get("username"),
          email: form.get("email"),
          fname: form.get("fname"),
          lname: form.get("lname"),
          password: form.get("password"),
          fam_size: Number(form.get("fam_size")),
        });
        showToast(res.message || "User Created Successfully", "success");
        setTimeout(() => {
          window.location.href = "/login.html";
        }, 500);
      } catch (err) {
        showToast(err.message, "warning");
      }
    });
  }
});
