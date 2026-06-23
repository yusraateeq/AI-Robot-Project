"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, useRef, createContext, useContext } from "react";
import { onAuthStateChanged, User } from "firebase/auth";
import { auth } from "@/src/lib/firebase";
import { getToken } from "@/src/lib/api";

interface AuthContextValue {
  firebaseUser: User | null;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  firebaseUser: null,
  loading: true,
});

export const useAuth = () => useContext(AuthContext);

function isPublicPage(path: string): boolean {
  return path === "/login" || path.startsWith("/register");
}

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    const unsub = onAuthStateChanged(auth, (user) => {
      setFirebaseUser(user);
      setLoading(false);
    });
    return () => { mountedRef.current = false; unsub(); };
  }, []);

  useEffect(() => {
    if (loading || !mountedRef.current) return;
    const hasToken = !!getToken();
    const publicPage = isPublicPage(pathname);
    if (!firebaseUser && !hasToken && !publicPage) {
      router.replace("/login");
      return;
    }
    if (hasToken && !publicPage) {
      fetch("/api/profile", {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("no profile");
          return res.json();
        })
        .then((profile) => {
          if (!profile.registration_complete && pathname !== "/register/complete") {
            router.replace("/register/complete");
          }
        })
        .catch(() => {
          // Token exists but no profile — go to /register/complete
          if (pathname !== "/register/complete") {
            router.replace("/register/complete");
          }
        });
    }
  }, [firebaseUser, loading, pathname, router]);

  return (
    <AuthContext.Provider value={{ firebaseUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
