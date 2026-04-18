(function () {
  const cfg = window.__FIREBASE_WEB__ || {};
  if (!cfg.apiKey) {
    console.warn("Firebase web config missing — set FIREBASE_* in .env");
    return;
  }
  if (!firebase.apps.length) {
    firebase.initializeApp(cfg);
  }
  window.firebaseAuth = firebase.auth();
  window.firebaseDb = firebase.firestore();
})();
