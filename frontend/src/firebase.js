import { initializeApp } from "firebase/app";
import { GoogleAuthProvider, getAuth, onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth";

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const firebaseEnabled = Object.values(config).every(Boolean);
const auth = firebaseEnabled ? getAuth(initializeApp(config)) : null;

export async function signInWithGoogle() {
  if (!auth) return null;
  const credential = await signInWithPopup(auth, new GoogleAuthProvider());
  return credential.user;
}

export async function firebaseToken() {
  return auth?.currentUser ? auth.currentUser.getIdToken() : null;
}

export function observeAuth(callback) {
  return auth ? onAuthStateChanged(auth, callback) : () => {};
}

export function logout() {
  return auth ? signOut(auth) : Promise.resolve();
}
