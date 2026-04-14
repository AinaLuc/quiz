const views = [...document.querySelectorAll(".view")];
const routeLinks = [...document.querySelectorAll("[data-route]")];
const defaultRoute = "landing";

function setActiveRoute(routeName) {
  const targetRoute = document.getElementById(routeName) ? routeName : defaultRoute;

  views.forEach((view) => {
    view.classList.toggle("active", view.id === targetRoute);
  });

  routeLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.route === targetRoute);
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function readRouteFromHash() {
  return window.location.hash.replace("#", "") || defaultRoute;
}

window.addEventListener("hashchange", () => {
  setActiveRoute(readRouteFromHash());
});

document.getElementById("signin-form").addEventListener("submit", (event) => {
  event.preventDefault();
  window.location.hash = "dashboard";
});

document.getElementById("signup-form").addEventListener("submit", (event) => {
  event.preventDefault();
  window.location.hash = "dashboard";
});

document.querySelectorAll("[data-google-auth]").forEach((button) => {
  button.addEventListener("click", () => {
    window.location.hash = "dashboard";
  });
});

setActiveRoute(readRouteFromHash());
