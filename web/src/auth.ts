export const AUTH_SESSION_KEY = "statpro-demo-authenticated";

export function isAuthenticated() {
  return sessionStorage.getItem(AUTH_SESSION_KEY) === "true";
}

export function authenticate(username: string, password: string) {
  const valid = username.trim() === "admin" && password === "admin123";
  if (valid) sessionStorage.setItem(AUTH_SESSION_KEY, "true");
  return valid;
}

export function signOut() {
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}
