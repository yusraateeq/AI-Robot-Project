"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [authorized] = useState(() => {
    if (typeof window === "undefined") return false;
    return pathname === "/login" || !!localStorage.getItem("token");
  });

  useEffect(() => {
    if (pathname !== "/login" && !localStorage.getItem("token")) {
      router.replace("/login");
    }
  }, [pathname, router]);

  if (!authorized) return null;
  return <>{children}</>;
}
